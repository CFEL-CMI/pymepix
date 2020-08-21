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
import ctypes
from multiprocessing import Queue
from multiprocessing.sharedctypes import Value
import numpy as np
import socket
import time
import zmq
import os

from .basepipeline import BasePipelineObject
from .datatypes import MessageType
from pymepix.processing.rawtodisk import Raw2Disk


class UdpSampler(BasePipelineObject):
    """Recieves udp packets from SPDIR

    This class, creates a UDP socket connection to SPIDR and recivies the UDP packets from Timepix
    It them pre-processes them and sends them off for more processing

    """

    def __init__(self, address, longtime, chunk_size=10_000, flush_timeout=0.3, input_queue=None, create_output=True,
                 num_outputs=1, shared_output=None):
        BasePipelineObject.__init__(self, 'UdpSampler', input_queue=input_queue, create_output=create_output,
                                    num_outputs=num_outputs, shared_output=shared_output)

        self.init_param = {'address': address,
                           'chunk_size': chunk_size,
                           'flush_timeout': flush_timeout,
                           'longtime': longtime}
        self._record = Value(ctypes.c_bool, 0)
        self._close_file = Value(ctypes.c_bool, 0)

    def init_new_process(self):
        try:
            self.createConnection(self.init_param['address'])
            self._chunk_size = self.init_param['chunk_size'] * 8192
            self._flush_timeout = self.init_param['flush_timeout']
            self._packets_collected = 0
            self._packet_buffer_list = [bytearray(2 * self._chunk_size) for i in
                                        range(5)]  # ring buffer to put received data in
            self._buffer_list_idx = 0
            self._packet_buffer_view = memoryview(self._packet_buffer_list[self._buffer_list_idx])
            self._recv_bytes = 0
            self._total_time = 0.0
            self._longtime = self.init_param['longtime']
        except Exception as e:
            self.error('Exception occured in init!!!')
            self.error(e, exc_info=True)
            raise

    def createConnection(self, address):
        """Establishes a UDP connection to spidr"""
        self._sock = socket.socket(socket.AF_INET,  # Internet
                                   socket.SOCK_DGRAM)  # UDP
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 5_500_000) # TODO: change for BT NIC buffer 5.5Mb?
        self._sock.settimeout(1.0)
        self.info('Establishing connection to : {}'.format(address))
        self._sock.bind(address)

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
    def close_file(self):
        return bool(self._close_file.value)

    @close_file.setter
    def close_file(self, value):
        self.debug(f'Setting close_file to {value}')
        self._close_file.value = value

    @property
    def outfile_name(self):
        return self._outfile_name

    @outfile_name.setter
    def outfile_name(self, fileN):
        self.info(f'Setting file name flag to {fileN}')
        if self.write2disk.open_file(fileN):
            self.info(f"file {fileN} opened")
        else:
            self.error("Huston, here's a problem, file cannot be created.")

    def pre_run(self):
        self.init_new_process()
        self.write2disk = Raw2Disk()
        self._last_update = time.time()

    def post_run(self):
        if self._recv_bytes > 1:
            bytes_to_send = self._recv_bytes
            self._recv_bytes = 0
            curr_list_idx = self._buffer_list_idx
            self._buffer_list_idx = (self._buffer_list_idx + 1) % len(self._packet_buffer_list)
            self._packet_buffer_view = memoryview(self._packet_buffer_list[self._buffer_list_idx])
            self.write2disk.my_sock.send(
                self._packet_buffer_list[curr_list_idx][:bytes_to_send], copy=False)
            if self.write2disk.writing:
                self.write2disk.my_sock.send(b'EOF')  # we should get a response here, this ends up in nirvana at this point
                self.debug('post_run: closed file')
            #return MessageType.RawData, (
            #    self._packet_buffer_list[curr_list_idx][:bytes_to_send], self._longtime.value)
            return None, None
        else:
            if self.write2disk.writing:
                self.debug('post_run: close file')
                self.write2disk.my_sock.send(b'EOF')  # we should get a response here, but the socket is elsewhere...
                self.debug('post_run: closed file')
            return None, None


    def process(self, data_type=None, data=None):
        start = time.time()
        # self.debug('Reading')
        try:
            self._recv_bytes += self._sock.recv_into(self._packet_buffer_view[self._recv_bytes:])
        except socket.timeout:
            # put close file here to get the cases where there's no data coming and file should be closed
            # mainly there for test to succeed
            if self.close_file:
                self.close_file = 0
                return self.post_run()
            else:
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

        if (self._recv_bytes > self._chunk_size) or (flush_time > self._flush_timeout):
            #packet = np.frombuffer(self._packet_buffer_view[:self._recv_bytes], dtype=np.uint64) # TODO: put this in packet processor
            #print(packet)

            # tpx_packets = self.get_useful_packets(packet)

            bytes_to_send = self._recv_bytes
            self._recv_bytes = 0
            curr_list_idx = self._buffer_list_idx
            print('curr idx', curr_list_idx)
            self._buffer_list_idx = (self._buffer_list_idx + 1) % len(self._packet_buffer_list)
            self._packet_buffer_view = memoryview(self._packet_buffer_list[self._buffer_list_idx])
            self._last_update = time.time()
            #if len(packet) > 1:
            if self.record:
                self.write2disk.my_sock.send(self._packet_buffer_list[curr_list_idx][:bytes_to_send], copy=False)
            elif self.close_file:
                self.close_file = 0
                self.debug('received close file')
                self.write2disk.my_sock.send(self._packet_buffer_list[curr_list_idx][:bytes_to_send], copy=False)
                self.write2disk.my_sock.send(b'EOF')
            #if not curr_list_idx % 20:
            #   return MessageType.RawData, (self._packet_buffer_list[curr_list_idx][:bytes_to_send], self._longtime.value)
            #else:
            return None, None
            #else:
            #    return None, None
        else:
            return None, None


    def stopRaw2Disk(self):
        # TODO: this doesn't work for now. should probably go to post_run
        '''
        self.debug('Stopping Raw2Disk')
        self.write2disk.close()
        self.write2disk.my_sock.send_string('SHUTDOWN')
        # print(write2disk.my_sock.recv())
        self.write2disk.write_thr.join()
        self.debug('Raw2Disk stopped')
        '''