import multiprocessing

from multiprocessing.sharedctypes import RawArray 
import numpy as np
import socket
from multiprocessing import Queue
class PacketSampler(multiprocessing.Process):

    def __init__(self,address,file_queue,shared_long_time,acq_status,sample_buffer_size=100000):
        multiprocessing.Process.__init__(self)
        self._acq_status = acq_status
        self._long_time = shared_long_time
        self.createSampleBuffer(sample_buffer_size)
        self.createConnection(address)
        self._packets_collected = 0
        self._output_queue = Queue()
        self._file_queue = Queue()
    @property
    def outputQueue(self):
        return self._output_queue

    def createSampleBuffer(self,sample_buffer_size):
        # shape = (sample_buffer_size,2)
        # self._sample_buffer_size = sample_buffer_size
        # self._sample_buffer =RawArray(np.int64, int(np.prod(shape)))
        # self._numpy_buffer = np.frombuffer(self._sample_buffer,dtype=np.int64).reshape(shape)
        self._packet_buffer= np.ndarray(shape=(2048,),dtype='<u8')
    def createConnection(self,address):
        self._sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        self._sock.bind(address)

    
    def run(self):
        while True:
            if self._acq_status.value==0:
                
                continue


            size = self._sock.recv_into(self._packet_buffer,16384) # buffer size is 1024 bytes
            packet = self._packet_buffer[0:size//8]
            #self._file_queue.put(('WRITE',packet.tostring()))
            current_time = self._long_time.value
            #Get the header
            header = packet &  0xF000000000000000
            tpx_packets = np.logical_or.reduce((header == 0xB000000000000000,header == 0xA000000000000000,(packet & 0xFF00000000000000)==0x6F00000000000000))
            self._output_queue.put((tpx_packets,current_time))

            self._packets_collected+=1










