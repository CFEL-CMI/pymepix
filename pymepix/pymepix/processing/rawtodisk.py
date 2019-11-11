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
import time
from pymepix.core.log import ProcessLogger
import multiprocessing
from multiprocessing.sharedctypes import Value
import queue
from pymepix.util.storage import open_output_file, store_raw

class raw2Disk (multiprocessing.Process, ProcessLogger):
    def __init__(self, name='raw2Disk', dataq=None, fileN=None):
        multiprocessing.Process.__init__(self)
        ProcessLogger.__init__(self, name)

        self.info(f'initialising raw2Disk')
        if dataq is not None:
            self._dataq = dataq
            try:
                self._raw_file = open_output_file(fileN, 'raw')
            except:
                self.info(f'Cannot open file {fileN}')
        else:
            self.error('Exception occured in init; no data queue provided?')

        self._enable = Value('I', 1)
        self._timerBool = Value('I', 0)
        import ctypes
        self._startTime = Value(ctypes.c_double, 0)
        self._stopTime  = Value(ctypes.c_double, 1)

    @property
    def enable(self):
        """Enables processing

        Determines wheter the class will perform processing, this has the result of signalling the process to terminate.
        If there are objects ahead of it then they will stop recieving data
        if an input queue is required then it will get from the queue before checking processing
        This is done to prevent the qwueue from growing when a process behind it is still working

        Parameters
        -----------
        value : bool
            Enable value


        Returns
        -----------
        bool:
            Whether the process is enabled or not


        """
        return bool(self._enable.value)

    @enable.setter
    def enable(self, value):
        self.debug('Setting enabled flag to {}'.format(value))
        self._enable.value = int(value)

    @property
    def timer(self):
        return bool(self._timerBool.value)

    @enable.setter
    def timer(self, value):
        self.debug('Setting timer flag to {}'.format(value))
        if value == 1:
            self._startTime.value = time.time()
        elif value == 0:
            self._stopTime.value = time.time()
        self._timerBool.value = int(value)

    def run(self):
        while True:
            enabled = self.enable
            if not enabled:
                self.debug('I am leaving')
                break
            try:
                # I picked the timeout randomly; use what works
                data = self._dataq.get(block=False, timeout=0.1)
                self.debug(f'get data {data}')
            except queue.Empty:
                continue  # try again
            except:
                self.info('error')

            store_raw(self._raw_file, (data, 1))

        self._raw_file.close()
        import numpy as np
        size = np.fromfile(self._raw_file.name, dtype=np.uint64).shape[0]
        timeDiff = self._stopTime.value - self._startTime.value
        print(f'recieved {size} packets; {64 * size * 1e-6:.2f}MBits {(64 * size * 1e-6) / timeDiff:.2f}MBits/sec; {(64 * size * 1e-6 / 8) / timeDiff:.2f}MByte/sec')
        self.info("finished saving data")

