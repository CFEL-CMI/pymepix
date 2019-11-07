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
import socket
from .datatypes import MessageType
import time
import numpy as np


class UdpSampler(BasePipelineObject):
    """Recieves udp packets from SPDIR

    This class, creates a UDP socket connection to SPIDR and recivies the UDP packets from Timepix
    It them pre-processes them and sends them off for more processing



    """

    def __init__(self, address, longtime, chunk_size=1000, flush_timeout=0.3, input_queue=None, create_output=True,
                 num_outputs=1, shared_output=None):
        BasePipelineObject.__init__(self, 'UdpSampler', input_queue=None, create_output=True, num_outputs=1,
                                    shared_output=shared_output)

        try:
            self.createConnection(address)
            self._chunk_size = chunk_size * 8192
            self._flush_timeout = flush_timeout
            self._packets_collected = 0
            self._packet_buffer = None
            self._total_time = 0.0
            self._longtime = longtime
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

    def process(self, data_type=None, data=None):

        start = time.time()
        # self.debug('Reading')
        try:
            raw_packet = self._sock.recv(16384)  # buffer size is 1024 bytes
        except socket.timeout:
            return None, None
        except socket.error:
            return None, None
        # self.debug('Read {}'.format(raw_packet))
        if self._packet_buffer is None:
            self._packet_buffer = raw_packet
        else:
            self._packet_buffer += raw_packet

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

            self._packet_buffer = None
            self._last_update = time.time()
            if packet.size > 0:
                return MessageType.RawData, (packet, self._longtime.value)
            else:
                return None, None
        else:
            return None, None
