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
        self.createConnection(address)
        self._packets_collected = 0
        self._output_queue = Queue()
        self._file_queue = Queue()
    @property
    def outputQueue(self):
        return self._output_queue

    def createConnection(self,address):
        self._sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        self._sock.bind(address)

    def upload_packet(self,packet,longtime):
        #Get the header
        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF
        pix_filter = (header ==0xA) |(header==0xB) 
        trig_filter =  ((header==0x4)|(header==0x6) & (subheader == 0xF))
        tpx_filter = pix_filter | trig_filter
        tpx_packets = packet[tpx_filter]
        #print(tpx_packets)
        if tpx_packets.size > 0 and self._output_queue is not None:
            #print('UPLOADING')
            self._output_queue.put((tpx_packets,longtime))
    
    def run(self):
        while True:
            if self._acq_status.value==0:
                
                continue


            raw_packet = self._sock.recv(16384) # buffer size is 1024 bytes
            packet = np.frombuffer(raw_packet,dtype=np.uint64)
            #self._file_queue.put(('WRITE',packet.tostring()))
            current_time = self._long_time.value
            self.upload_packet(packet,current_time)

            self._packets_collected+=1










