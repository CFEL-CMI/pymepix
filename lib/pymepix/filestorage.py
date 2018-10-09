import multiprocessing

from multiprocessing.sharedctypes import RawArray 
import numpy as np
import socket
from multiprocessing import Queue
class FileStorage(multiprocessing.Process):

    def __init__(self,data_queue):
        multiprocessing.Process.__init__(self)

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
                data = packet[1]
                #Check signal type
                if message == 'OPEN':
                    filename = packet[1]
                    if self._file_io is not None:
                        self._file_io.close()
                    
                    self._file_io = open(filename,'w')
                elif message == 'WRITE':
                    if self._file_io is not None:
                        self._file_io.write(data)
                elif message == 'CLOSE':
                    if self._file_io is not None:
                        self._file_io.close()
                        self._file_io = None

