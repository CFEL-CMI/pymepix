##############################################################################
##
# This file is part of Pymepix
#
# https://arxiv.org/abs/1905.07999
#
#
# Pymepix is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pymepix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pymepix.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from .basepipeline import BasePipelineObject
import socket, sys
from .datatypes import MessageType
import time
import numpy as np
from multiprocessing import Queue
from multiprocessing.sharedctypes import Value
from pymepix.processing.rawtodisk import raw2Disk
# TODO: xfelTrainID
#from pymepix.processing.xfeltrainid import xfelTrainID
import ctypes


class UdpSampler(BasePipelineObject):
    """Recieves udp packets from SPDIR

    This class, creates a UDP socket connection to SPIDR and recivies the UDP packets from Timepix
    It them pre-processes them and sends them off for more processing



    """

    def __init__(self, address, longtime, chunk_size=1000, flush_timeout=0.3, input_queue=None, create_output=True,
                 num_outputs=1, shared_output=None):
        BasePipelineObject.__init__(self, 'UdpSampler', input_queue=input_queue, create_output=create_output, num_outputs=num_outputs,
                                    shared_output=shared_output)

        try:
            self.createConnection(address)
            self._chunk_size = chunk_size * 8192
            self._flush_timeout = flush_timeout
            self._packets_collected = 0
            self._packet_buffer = bytearray()
            self._total_time = 0.0
            self._longtime = longtime
            self._dataq = Queue()
            self._record = Value(ctypes.c_bool, 0)
            self._outfile_name = 'test'
        except Exception as e:
            self.error('Exception occured in init!!!')
            self.error(e, exc_info=True)
            raise

    def createConnection(self, address):
        """Establishes a UDP connection to spidr"""
        self._sock = socket.socket(socket.AF_INET,  # Internet
                                   socket.SOCK_DGRAM)  # UDP
        self._sock.settimeout(1.0)
        self.info('Establishing connection to : {}'.format(address))
        self._sock.bind(address)

    def preRun(self):
        self._last_update = time.time()

    def get_useful_packets(self, packet):
        # Get the header
        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF
        pix_filter = (header == 0xA) | (header == 0xB)
        trig_filter = ((header == 0x4) | (header == 0x6)) & (subheader == 0xF)
        tpx_filter = pix_filter | trig_filter
        tpx_packets = packet[tpx_filter]
        return tpx_packets

    @property
    def record(self):
        """Enables saving data to disk

        Determines whether the class will perform processing, this has the result of signalling the process to terminate.
        If there are objects ahead of it then they will stop recieving data
        if an input queue is required then it will get from the queue before checking processing
        This is done to prevent the queue from growing when a process behind it is still working

        Parameters
        -----------
        value : bool
            Enable value


        Returns
        -----------
        bool:
            Whether the process should record and write to disk or not


        """
        return bool(self._record.value)

    @record.setter
    def record(self, value):
        self.debug(f'Setting record flag to {value}')
        self._record.value = int(value)

    @property
    def outfile_name(self):
        #return self._outfile_name.value
        return self._outfile_name

    @outfile_name.setter
    def outfile_name(self, fileN):
        self.info(f'Setting file name flag to {fileN}')
        #self._outfile_name.value = fileN
        # start raw2Disk
        self._outfile_name = fileN
        self.stopRaw2Disk()
        self.startRaw2Disk()
        # start xfel train ID
        # TODO: xfelTrainID start stop...
        #self.stopTrainID()
        #self.startTrainID()

    def process(self, data_type=None, data=None):
        start = time.time()
        # self.debug('Reading')
        try:
            self._packet_buffer.extend(self._sock.recv(16384))
        except socket.timeout:
            return None, None
        except socket.error:
            return None, None
        # self.debug('Read {}'.format(raw_packet))

        self._packets_collected += 1
        end = time.time()

        self._total_time += end - start
        if self._packets_collected % 1000 == 0:
            self.debug('Packets collected {}'.format(self._packets_collected))
            self.debug('Total time {} s'.format(self._total_time))

        flush_time = end - self._last_update

        if (len(self._packet_buffer) > self._chunk_size) or (flush_time > self._flush_timeout):
            packet = np.frombuffer(self._packet_buffer, dtype='<u8')

            # tpx_packets = self.get_useful_packets(packet)

            self._packet_buffer = bytearray()
            self._last_update = time.time()
            if packet.size > 0:
                if self.record:
                    self._dataq.put(packet)
                return MessageType.RawData, (packet, self._longtime.value)
            else:
                return None, None
        else:
            return None, None

    def startRaw2Disk(self):
        self.info(f'start raw2Disk process')

        # generate worker to save the data directly to disk
        self._raw2Disk = raw2Disk(dataq=self._dataq, fileN=self.outfile_name)
        self._raw2Disk.enable = True
        self._raw2Disk.start()

    def stopRaw2Disk(self):
        self.info(f'stopping raw2Disk process')
        self._raw2Disk.enable = False
        self._raw2Disk.join(5.0) # give it a chance to empty some more of the queue
        self._raw2Disk.terminate()
        self._raw2Disk.join()

        while not self._dataq.empty():
            self._dataq.get()
        self.info('Process Raw2Disk stop complete')

    def startTrainID(self):
        self.info(f'start xfelTrainID process')

        # generate worker to save the data directly to disk
        self._trainIDRec = xfelTrainID(filename=self.outfile_name)
        self._trainIDRec.enable = True
        self._trainIDRec.start()

    def stopTrainID(self):
        self.info(f'stopping xfelTrainID process')
        self._trainIDRec.enable = False
        self._trainIDRec.join(2.0) # file still needs to be saved
        self._trainIDRec.terminate()
        self._trainIDRec.join()


def main():
    import time
    sampler = UdpSampler(('127.0.0.1', 50000), longtime=1, create_output=False)
    sampler._last_update = time.time()
    print(sampler.process())

if __name__ == '__main__':
    main()