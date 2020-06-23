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
import numpy as np
from pymepix.core.log import ProcessLogger
import multiprocessing
from multiprocessing.sharedctypes import Value
import queue
from pymepix.util.storage import open_output_file, store_raw
import ctypes
import subprocess, os

class raw2Disk (multiprocessing.Process, ProcessLogger):
    def __init__(self, name='raw2Disk', dataq=None, fileN=None):
        multiprocessing.Process.__init__(self)
        ProcessLogger.__init__(self, name)

        self.info(f'initialising {name}')
        if dataq is not None:
            self._dataq = dataq
            try:
                self._raw_file = open_output_file(fileN, 'raw')
            except:
                self.info(f'Cannot open file {fileN}')
        else:
            self.error('Exception occured in init; no data queue provided?')

        self._buffer = np.array([], dtype=np.uint64)
        self._enable = Value(ctypes.c_bool, 1)
        self._timerBool = Value(ctypes.c_bool, 0)
        self._startTime = Value(ctypes.c_double, 0)
        self._stopTime  = Value(ctypes.c_double, 1)

    @property
    def enable(self):
        """Enables processing

        Determines wheter the class will perform processing, this has the result of signalling the process to terminate.
        If there are objects ahead of it then they will stop recieving data
        if an input queue is required then it will get from the queue before checking processing
        This is done to prevent the queue from growing when a process behind it is still working

        Parameters
        -----------
        value : bool
            Enable value


        Returns
        -----------
        bool:
            Whether the process is enabled or not


        """
        return self._enable.value

    @enable.setter
    def enable(self, value):
        self.debug('Setting enabled flag to {}'.format(value))
        self._enable.value = int(value)

    @property
    def timer(self):
        return self._timerBool.value

    @enable.setter
    def timer(self, value):
        self.debug('Setting timer flag to {}'.format(value))
        if value == 1:
            self._startTime.value = time.time()
        elif value == 0:
            self._stopTime.value = time.time()
        self._timerBool.value = int(value)

    def run(self):
        print(f'!!!! {__name__} GO!')
        while True:
            enabled = self.enable
            if not enabled:
                self.debug('I am leaving')
                break
            try:
                # I picked the timeout randomly; use what works
                data = self._dataq.get(timeout=0.1) # block=False results in high CPU without doing anything
                #self.debug(f'get data {data}')
            except queue.Empty:
                continue  # try again
            except:
                self.info('error')

            self._buffer = np.append(self._buffer, data)
            if len(self._buffer) > 10000:
                store_raw(self._raw_file, (self._buffer, 1))
                self._buffer = np.array([], dtype=np.uint64)

        # empty buffer before closing
        if len(self._buffer) > 0:
            store_raw(self._raw_file, (self._buffer, 1))
        #store_raw(self._raw_file, (self._buffer, 1))
        # empty queue before closing
        if not self._dataq.empty():
            remains = []
            item = self._dataq.get(block=False)
            while item:
                try:
                    remains.append(self._dataq.get(block=False))
                except queue.Empty:
                    break
            print(f'{len(remains)} remains collected')
            store_raw(self._raw_file, (np.asarray(remains), 1))
        self._raw_file.close()

        # TODO: print only if in debug mode
        #size = np.fromfile(self._raw_file.name, dtype=np.uint64).shape[0]
        #timeDiff = self._stopTime.value - self._startTime.value
        #print(f'recieved {size} packets; {64 * size * 1e-6:.2f}MBits {(64 * size * 1e-6) / timeDiff:.2f}MBits/sec; {(64 * size * 1e-6 / 8) / timeDiff:.2f}MByte/sec')
        self.info("finished saving data")
        if os.path.getsize(self._raw_file.name) > 0:
            from subprocess import Popen
            self.info(f'start process data from: {self._raw_file.name}')
            # TODO: FLASH specific
            #Popen(['python', '/home/bl1user/timepix/conversionClient.py', self._raw_file.name])


def main():
    import numpy as np
    from multiprocessing import Queue
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fname = '/Users/brombh/PycharmProjects/timepix/analysis/data/pyrrole__100.raw'
    data = np.fromfile(fname, dtype=np.uint64)
    total = int(np.floor((len(data) - 10) / 10))
    total = len(data)
    total = 10005
    last_progress = 0

    dataq = Queue()
    fname = 'test.raw'
    p = raw2Disk(dataq=dataq, fileN=fname)
    p.start()
    p.timer = 1
    # time.sleep(30)

    for i, d in enumerate(data[:(total+1)]):
        dataq.put(d)
        progress = int(i / total * 100)
        if progress != 0 and progress % 5 == 0 and progress != last_progress:
            print(f'Progress {i / total * 100:.1f}%')
            last_progress = progress
        # time.sleep(100e-9)
    print(f'sent {i+1} packets')
    time.sleep(2)

    p.timer = 0
    p.enable = 0
    p.join()


if __name__ == '__main__':
    main()