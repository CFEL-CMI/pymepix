import multiprocessing

from multiprocessing.sharedctypes import RawArray 
import numpy as np
import socket
from multiprocessing import Queue
class FileStorage(multiprocessing.Process):

    def __init__(self,data_queue,file_status):
        multiprocessing.Process.__init__(self)
        self._input_queue = data_queue
        self._file_io = None
    def run(self):

        while True:
            try:
                # get a new message
                packet = self._input_queue.get()
                # this is the 'TERM' signal
                if packet is None:
                    break

                message = packet[0]
                # print(packet)
                #Check signal type
                if message == 'OPEN':
                    filename = packet[1]
                    print('Opening filename ',filename)
                    if self._file_io is not None:
                        self._file_io.close()
                    
                    self._file_io = open(filename,'wb')
                elif message == 'WRITE':
                    data = packet[1]
                    # print(packet)
                    if self._file_io is not None:
                        self._file_io.write(data)
                elif message == 'CLOSE':
                    if self._file_io is not None:
                        self._file_io.close()
                        self._file_io = None
            except Exception as e:
                print(str(e))
            
        

