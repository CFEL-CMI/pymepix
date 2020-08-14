# This file is part of Pymepix
#
# In all scientific work using Pymepix, please reference it as
#
# A. F. Al-Refaie, M. Johny, J. Correa, D. Pennicard, P. Svihra, A. Nomerotski, S. Trippel, and J. Küpper:
# "PymePix: a python library for SPIDR readout of Timepix3", J. Inst. 14, P10003 (2019)
# https://doi.org/10.1088/1748-0221/14/10/P10003
# https://arxiv.org/abs/1905.07999
#
# Pymepix is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <https://www.gnu.org/licenses/>.

import threading
import zmq
import time
import os

import logging

# Create the logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Class to write raw data to files using ZMQ and a new thread to prevent IO blocking
class Raw2Disk():
    """
        Class for asynchronously writing raw files
        Intended to allow writing of raw data while minimizing impact on UDP reception reliability

        Constructor
        ------
        Raw2Disk(context): Constructor. Need to pass a ZMQ context object to ensure that inproc sockets can be created

        Methods
        -------

        open_file(filename): Creates a file with a given filename and path

        write(data): Writes data to the file. Parameter is buffer type (e.g. bytearray or memoryview)

        close(): Close the file currently in progress
        """

    def __init__(self, context=None):
        self.writing = False  # Keep track of whether we're currently writing a file
        self.stop_thr = False

        self.sock_addr = f'inproc://filewrite-42'
        self.my_context = context or zmq.Context.instance()
        self.my_sock = self.my_context.socket(zmq.PAIR)  # Paired socket allows two-way communication
        self.my_sock.bind(self.sock_addr)

        self.write_thr = threading.Thread(target=self._run_filewriter_thr, args=(self.sock_addr, None))
        # self.write_thr.daemon = True
        self.write_thr.start()

        time.sleep(1)

    def _run_filewriter_thr(self, sock_addr, context=None):
        """
        Private method that runs in a new thread after initialization.

        Parameters
        ----------
        sock_addr : str
            socket address for ZMQ to bind to
        context
            ZMQ context
        """
        context = context or zmq.Context.instance()
        sock = context.socket(zmq.PAIR)
        sock.connect(sock_addr)

        # State machine etc.
        waiting = True
        writing = False
        close_file = False
        shutdown = False

        while not shutdown:
            while waiting:
                instruction = sock.recv_string()
                if instruction == "SHUTDOWN":
                    logging.debug("SHUTDOWN received")
                    waiting = False
                    shutdown = True
                else:  # Interpret as file name / path
                    directory, name = os.path.split(instruction)
                    if (not os.path.exists(instruction)) and os.path.isdir(directory):
                        logging.debug(f"File {instruction} opening")
                        # Open filehandle
                        filehandle = open(instruction, "wb")
                        sock.send_string("OPENED")
                        waiting = False
                        writing = True
                    else:
                        sock.send_string(f"{instruction} in an INVALID command")

            while writing:
                # Receive in efficient manner (noncopy with memoryview) and write to file
                # Check for special message that indicates EOF.
                dataframe = sock.recv(copy=False)
                dataview = memoryview(dataframe.buffer)
                if (len(dataview) == 3):
                    if dataview.tobytes() == "EOF":
                        logging.debug("EOF received")
                        writing = False
                        close_file = True

                if writing == True:
                    filehandle.write(dataview)

            if close_file:
                logging.debug('closing file')
                filehandle.close()
                sock.send_string("CLOSED")
                close_file = False
                waiting = True

        # We reach this point only after "SHUTDOWN" command received
        logging.debug("Thread is finishing")
        sock.close()
        logging.debug("Thread is finished")

    def open_file(self, filename):
        if self.writing == False:
            self.my_sock.send_string(filename)
            response = self.mysock.recv()  # Check reply from thread
            if response.decode("utf-8") == "OPENED":
                self.writing = True
                return True
            else:
                logging.WARN("File name not valid")
                return False
        else:
            logging.info("Already writing file!")
            return False

    def close(self):
        if self.writing == True:
            self.mysock.send(b'EOF')
            response = self.mysock.recv_string()
            self.writing = False
            if response != "CLOSED":
                logging.WARN("Didn't get expected response when closing file")
                return False
            else:
                return True
        else:
            print("Cannot close file - we are not writing anything!")
            return False

    def write(self, data):
        if self.writing == True:
            self.my_sock.send(data, copy=False)
        else:
            logging.WARN("Cannot write data - file not open")
            return False

    # Destructor - called automatically when object garbage collected
    def __del__(self):
        '''Stuff to make sure sockets and files are closed...'''
        if self.write_thr.is_alive():
            if self.writing == True:
                self.close()
            self.my_sock.send_string("SHUTDOWN")
            self.write_thr.join()
            time.sleep(1)
            self.my_sock.close()
            logging.debug('object deleted')
        else:
            logging.debug('thread already closed')


def spawn_process():
    '''not strictly necessary, just to double check if this also works with multiprocessing'''
    write2disk = Raw2Disk()
    write2disk.my_sock.send_string('hallo 2')
    logging.info(write2disk.my_sock.recv_string())

    write2disk.my_sock.send(b'EOF')
    logging.info(write2disk.my_sock.recv())

    write2disk.my_sock.send_string('SHUTDOWN')
    # print(write2disk.my_sock.recv())
    write2disk.write_thr.join()


def main():
    from multiprocessing import Process
    Process(target=spawn_process).start()


if __name__ == '__main__':
    main()
