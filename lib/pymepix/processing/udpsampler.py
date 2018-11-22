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

    def __init__(self,address,longtime,chunk_size=1000,flush_timeout=0.3):
        BasePipelineObject.__init__(self,'UdpSampler',input_queue=None,create_output=True,num_outputs=1)

        try:
            self.createConnection(address)
            self._chunk_size = chunk_size*8192
            self._flush_timeout = flush_timeout
            self._packets_collected = 0
            self._packet_buffer = None
            self._total_time = 0.0
            self._longtime = longtime
        except Exception as e:
            self.error('Exception occured in init!!!')
            self.error(e,exc_info=True)
            raise       
    def createConnection(self,address):
        """Establishes a UDP connection to spidr"""
        self._sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP

        self.info('Establishing connection to : {}'.format(address))
        self._sock.bind(address)
    

    def preRun(self):
        self._last_update = time.time()

    def process(self,data_type=None,data=None):

        start = time.time()
        raw_packet = self._sock.recv(16384) # buffer size is 1024 bytes

        if self._packet_buffer is None:
            self._packet_buffer = raw_packet
        else:
            self._packet_buffer+= raw_packet

        
        self._packets_collected+=1
        end = time.time()

        self._total_time += end-start
        if self._packets_collected % 1000 == 0:
            self.debug('Packets collected {}'.format(self._packets_collected))
            self.debug('Total time {} s'.format(self._total_time))

        flush_time = end - self._last_update

        if (len(self._packet_buffer) > self._chunk_size) or (flush_time > self._flush_timeout):
            packet = np.frombuffer(self._packet_buffer,dtype='<u8')
            self._last_update = time.time()
            return MessageType.RawData,(packet,self._longtime.value)
        else:
            return None,None