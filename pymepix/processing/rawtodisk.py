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

        open(filename): Creates a file with a given filename and path

        write(data): Writes data to the file. Parameter is buffer type (e.g. bytearray or memoryview)

        close(): Close the file currently in progress
        """

    def __init__(self, context):
        print(f'init {__name__}')

        self.writing = False  # Keep track of whether we're currently writing a file

        self.sock_addr = f'inproc://filewrite-42}'

        self.my_sock = self.my_context.socket(zmq.PAIR)  # Paired socket allows two-way communication
        self.my_sock.bind(self.sock_addr)

        self.write_thr = threading.Thread(target=self._run_filewriter_thr, args=(self.my_context, self.sock_addr))
        self.write_thr.daemon = True
        self.write_thr.start()

        time.sleep(1)

    def _run_filewriter_thr(self, context, sock_addr):
        """
        Private method that gets run in a new thread after initialization.

        Parameters
        ----------
        context
            ZMQ context
        sock_addr : str
            socket address for ZMQ to bind to
        """
        print("This is where the magic happens...")

    def open(self, filename):
        pass

    def close(self):
        pass

    def write(self, data):
        pass

    # Destructor - called automatically when object garbage collected
    def __del__(self):
        '''Stuff to make sure sockets and files are closed...'''
        if self.writing == True:
            self.close()
        self.my_sock.send_string("SHUTDOWN")
        time.sleep(1)
        self.my_sock.close()
