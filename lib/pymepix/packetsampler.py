import multiprocessing
import time
from multiprocessing.sharedctypes import RawArray 
import numpy as np
import socket
from multiprocessing import Queue
import struct
class PacketSampler(multiprocessing.Process):

    def __init__(self,address,shared_long_time,acq_status,file_queue,sample_buffer_size=100000):
        multiprocessing.Process.__init__(self)
        self._acq_status = acq_status
        self._long_time = shared_long_time
        self._file_queue = file_queue
        self.createConnection(address)
        self._packets_collected = 0
        self._output_queue = Queue()

        self._max_bytes = 16384*1000
        self._flush_timeout = 0.3
        self._packet_buffer = None

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
        
        if packet.size > 0 and self._output_queue is not None:
            #print('UPLOADING')
            #self._file_queue.put(('WRITE',tpx_packets.tostring()))
            self._output_queue.put((tpx_packets,longtime))

    def convert_data_to_ints(self,data, big_endian=True):
        #print(len(data))
        int_count = len(data) // 8  # Assuming uint is 4 bytes long !!!
        fmt = ">" if big_endian else "<"
        fmt += "q" * int_count
        return struct.unpack(fmt, data[:int_count * 8])

    def run(self):
        self._start = time.time()
        while True:
            if self._acq_status.value==0:
                
                continue


            raw_packet = self._sock.recv(16384) # buffer size is 1024 bytes

            if self._packet_buffer is None:
                self._packet_buffer = raw_packet
            else:
                self._packet_buffer+= raw_packet

            
            self._packets_collected+=1

            end = time.time()-self._start
            # assert (len(raw_packet) % 8 == 0)

            # print(len(self._packet_buffer),self._max_bytes)

            # little = int.from_bytes(raw_packet, byteorder='little')
            # big = int.from_bytes(raw_packet, byteorder='big')
                    
            # print('Little: {:16X} Big: {:16X} '.format(little,big))
            if (len(self._packet_buffer) > self._max_bytes) or (end > self._flush_timeout):
                packet = np.frombuffer(self._packet_buffer,dtype='<u8')
                self._file_queue.put(('WRITE',self._packet_buffer))
                current_time = self._long_time.value
                self.upload_packet(packet,current_time)
                self._packet_buffer = None
                self._start = time.time()

           















