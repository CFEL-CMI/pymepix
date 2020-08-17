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
from pymepix.core.log import Logger

# Class to write raw data to files using ZMQ and a new thread to prevent IO blocking
class Raw2Disk(Logger):
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
        Logger.__init__(self, 'Raw2Disk')

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

        # State machine etc. local variables
        waiting = True
        writing = False
        shutdown = False

        while not shutdown:
            # wait for instructions, valid commands are
            # "SHUTDOWN": exits this loop and ends thread
            # "filename" in the form "/filename
            while waiting:
                instruction = sock.recv_string()
                if instruction == "SHUTDOWN":
                    self.debug("SHUTDOWN received")
                    waiting = False
                    shutdown = True
                else:  # Interpret as file name / path
                    directory, name = os.path.split(instruction)
                    if (not os.path.exists(instruction)) and os.path.isdir(directory):
                        self.debug(f"File {instruction} opening")
                        # Open filehandle
                        filehandle = open(instruction, "wb")
                        sock.send_string("OPENED")
                        waiting = False
                        writing = True
                    else:
                        sock.send_string(f"{instruction} in an INVALID command")

            # start writing received data to a file
            while writing:
                # Receive in efficient manner (noncopy with memoryview) and write to file
                # Check for special message that indicates EOF.
                data_view = memoryview(sock.recv(copy=False).buffer)
                self.debug(data_view.tobytes())
                if (len(data_view) == 3):
                    if data_view.tobytes() == b'EOF':
                        self.debug("EOF received")
                        writing = False

                if writing == True:
                    filehandle.write(data_view)

            # close file
            self.debug('closing file')
            filehandle.close()
            sock.send_string("CLOSED")
            waiting = True

        # We reach this point only after "SHUTDOWN" command received
        self.debug("Thread is finishing")
        sock.close()
        self.debug("Thread is finished")

    def open_file(self, filename):
        if self.writing == False:
            self.my_sock.send_string(filename)
            response = self.my_sock.recv_string()  # Check reply from thread
            if response == "OPENED":
                self.writing = True
                return True
            else:
                self.warn("File name not valid")
                return False
        else:
            self.warn("Already writing file!")
            return False

    def close(self):
        if self.writing == True:
            self.my_sock.send(b'EOF')
            response = self.my_sock.recv_string()
            if response != "CLOSED":
                self.warn("Didn't get expected response when closing file")
                return False
            else:
                return True
        else:
            self.info("Cannot close file - we are not writing anything!")
            return False

    def write(self, data):
        '''Not sure how useful this function actually is...
           It completes the interface for this class but from a performance point of view it doesn't improve things.
           How could this be benchmarked?
        '''
        if self.writing == True:
            self.my_sock.send(data, copy=False)
        else:
            self.warn("Cannot write data - file not open")
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
            self.debug('object deleted')
        else:
            self.debug('thread already closed')


def main_process():
    # Create the logger
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    '''not strictly necessary, just to double check if this also works with multiprocessing'''
    write2disk = Raw2Disk()

    ######
    # test 0
    write2disk.my_sock.send_string('hallo echo')
    logging.info(write2disk.my_sock.recv_string())

    '''
    these example only work if thread uses self.writing directly
    ######
    # test 1
    filename = './test1.raw'
    write2disk.my_sock.send_string(filename)
    if write2disk.my_sock.recv_string() != 'OPENED':
        logging.error("Huston, here's a problem, file cannot be created.")

    text = b'Hallo, heute ist ein guter Tag.'
    write2disk.my_sock.send(text)
    write2disk.my_sock.send(b'EOF')
    assert write2disk.my_sock.recv_string() == "CLOSED"
    logging.debug("File closed")

    with open(filename, 'rb') as f:
        file_content = f.read()
    assert file_content == text

    ######
    # test 2
    filename = './test2.raw'
    write2disk.my_sock.send_string(filename)
    if write2disk.my_sock.recv_string() != 'OPENED':
        logging.error("Huston, here's a problem, file cannot be created.")

    text = b'Hallo, heute ist immer noch ein guter Tag.'
    write2disk.my_sock.send(text)
    if write2disk.close():
        logging.debug('file closed')
    else:
        logging.error('something went wrong closing the file')

    with open(filename, 'rb') as f:
        file_content = f.read()
    assert file_content == text
    '''

    ######
    # test 3
    filename = './test3.raw'

    if write2disk.open_file(filename):
        logging.info(f"file {filename} opened")
    else:
        logging.error("Huston, here's a problem, file cannot be created.")

    text = b'What a nice day!'
    write2disk.my_sock.send(text, copy=False)
    write2disk.write(text)
    if write2disk.close():
        logging.info(f"File {filename} closed.")
    else:
        logging.error(f"File {filename} could not be closed.")

    # check actual file content
    with open(filename, 'rb') as f:
        file_content = f.read()
    assert file_content == text + text


    write2disk.my_sock.send_string('SHUTDOWN')
    # print(write2disk.my_sock.recv())
    write2disk.write_thr.join()


def main():
    from multiprocessing import Process
    Process(target=main_process).start()


if __name__ == '__main__':
    main()
