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


import serial
from datetime import datetime
# Checking if device is there
import stat, os
# Arguments
import sys, getopt
# Signal to stop script
import signal
import numpy as np
import ctypes
import time
import multiprocessing
from pymepix.core.log import ProcessLogger
from multiprocessing.sharedctypes import Value
from pymepix.util.storage import open_output_file, store_trainID


class xfelTrainID(multiprocessing.Process, ProcessLogger):
    def __init__(self, name='xfelTrainID', filename='test', device='/dev/ttyUSB0'):
        multiprocessing.Process.__init__(self)
        ProcessLogger.__init__(self, name)

        self.info(f'initialising {name}')

        try:
            self.connect_device(device)
        except:
            self.error(f'Failure connecting {device}')
        try:
            self._outfile = open_output_file(filename, 'trainID')
        except:
            self.info(f'Cannot open file {filename}')
        self._enable = Value(ctypes.c_bool, 1)
        self._record = Value(ctypes.c_bool, 0)

    def connect_device(self, device):
        """ Establish connection to USB device"""

        # doesn't work
        try:
            stat.S_ISBLK(os.stat(device).st_mode)
        except:
            self.error('Problem in init')

        # Configure serial interface
        self._ser = serial.Serial(device, 115200)

    @property
    def enable(self):
        """Indicator if we want to run this process and save data"""
        return self._enable.value

    @enable.setter
    def enable(self, value):
        self._enable.value = int(value)

    @property
    def record(self):
        """Indicator if we want to run this process and save data"""
        return self._record.value

    @record.setter
    def record(self, value):
        self._record.value = int(value)

    def run(self):
        times, ids = [], []
        # Information fields read from the USB interface
        timingInfoNames = ['Train ID', 'Beam Mode', 'CRC']
        # Number of bytes in each information field
        timingInfoLength = [16, 8, 2]

        while True:
            if not self.enable:
                self.info("I am leaving")
                break
            if self.record:
                '''
                #print(f'{time.time_ns()} hallo')
                times.append(time.time_ns())
                ids.append(12)
                print(times, id)
                time.sleep(0.3)
                '''

                # Align with beginning of word (STX = ASCII 02)
                while bytes([2]) != self._ser.read(1):
                    pass
    
                # Reset information on each run
                timingInfo = {k: '' for k in timingInfoNames}
                # Get info according to Information fields and bytes fields
                # Information fields are in order, so do not use standard Python dictionary
                for info in range(len(timingInfoNames)):
                    for sizeInfo in range(timingInfoLength[info]):
                        timingInfo[timingInfoNames[info]] += self._ser.read(1).decode("utf-8")
                zeit = time.time_ns()
                # Check if last byte is a ETX
                if bytes([3]) != self._ser.read(1):
                    self.info("Not properly align, skipping this run.")
                    continue
    
                crc = ''
                # Calculate crc
                crcVal = 0
                # data payload
                timingPayload = timingInfo['Train ID'] + timingInfo['Beam Mode']
                for i in range(0, len(timingPayload), 2):
                    crcVal ^= int(timingPayload[i:i + 2], 16)
                if crcVal != int(timingInfo['CRC'], 16):
                    crc = ' !!!Problem!!! Calculated CRC: ' + str(hex(crcVal)[2:]).upper()
                    continue
    
                # Train ID in decimal
                timingInfo['Train ID'] = int(timingInfo['Train ID'], 16)
    
                ids.append(timingInfo['Train ID'])
                times.append(zeit)
                #print(timingInfo['Train ID'], zeit)
                '''
                import pydoocs
                from datetime import datetime
                try:
                    test_var = pydoocs.read("FLASH.FEL/ADC.ADQ.BL1/EXP1.CH01/CH00.DAQ.TD", macropulse = timingInfo['Train ID'])
                    print(datetime.fromtimestamp(zeit*1e-9).strftime('%H:%M:%S.%f'),
                          datetime.fromtimestamp(test_var['timestamp']).strftime('%H:%M:%S.%f'),
                          timingInfo['Train ID'], test_var['macropulse'] )
                    #print(dt.strftime('%H:%M:%S.%f'), timingInfo['Train ID'])
                except:
                    pass
                '''

        self.info("finished saving data")
        store_trainID(self._outfile, times, ids)


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fname = 'test'
    p = xfelTrainID(filename=fname)
    p.start()
    time.sleep(1)
    p.record = True

    time.sleep(2)

    p.enable = False
    p.join()


if __name__ == '__main__':
    main()
