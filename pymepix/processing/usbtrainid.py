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

import multiprocessing
import glob
import os
import serial
from datetime import datetime
import threading
import time

# Checking if device is there
import stat, os

import numpy as np
import zmq
from pymepix.core.log import ProcessLogger
import pymepix.config.load_config as cfg


# Class to write raw data to files using ZMQ and a new thread to prevent IO blocking
class USBTrainID(multiprocessing.Process, ProcessLogger):
    """
    Class for asynchronously writing raw files
    Intended to allow writing of raw data while minimizing impact on UDP reception reliability
    """

    def __init__(self, name="USBTrainId"):
        multiprocessing.Process.__init__(self)
        ProcessLogger.__init__(self, name)

        device = cfg.default_cfg["trainID"]["device"]
        try:
            self._ser = None
            self.connect_device(device)
        except:
            self.error(f"Failure connecting {device}")

    def connect_device(self, device):
        """ Establish connection to USB device"""
        # doesn't work
        try:
            stat.S_ISBLK(os.stat(device).st_mode)
            self.info(f"{device} connected")
        except:
            self.error(f"Problem in init connecting to {device}")

        # Configure serial interface
        self._ser = serial.Serial(device, 115200)

    def run(self):
        ctx = zmq.Context.instance()
        z_sock = ctx.socket(zmq.PAIR)
        z_sock.connect("ipc:///tmp/train_sock")

        # variables needed in loop
        times, ids = [], []
        # Information fields read from the USB interface
        timingInfoNames = ["Train ID", "Beam Mode", "CRC"]
        # Number of bytes in each information field
        timingInfoLength = [16, 8, 2]

        # State machine etc. local variables
        waiting = True
        record = False
        shutdown = False
        filehandle = None

        while not shutdown:
            # wait for instructions, valid commands are
            # "SHUTDOWN": exits this loop and ends thread
            # "filename" in the form "/filename
            while waiting:
                cmd = z_sock.recv_string()
                if cmd == "SHUTDOWN":
                    self.info("SHUTDOWN received")
                    waiting = False
                    shutdown = True
                else:  # Interpret as file name / path
                    filename = cmd
                    directory, name = os.path.split(filename)
                    if (not os.path.exists(filename)) and os.path.isdir(directory):
                        self.info(f"File {filename} opening")
                        # Open filehandle
                        filehandle = open(filename, "wb")
                        z_sock.send_string("OPENED")
                        waiting = False
                        record = True
                        z_sock.send_string(filename)
                    else:
                        self.info(f'"{cmd}" not a valid command')
                        z_sock.send_string(f'"{cmd}" in an INVALID command')

            while record:
                # Align with beginning of word (STX = ASCII 02)
                while bytes([2]) != self._ser.read(1):
                    pass

                # Reset information on each run
                timingInfo = {k: "" for k in timingInfoNames}
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

                crc = ""
                # Calculate crc
                crcVal = 0
                # data payload
                timingPayload = timingInfo["Train ID"] + timingInfo["Beam Mode"]
                for i in range(0, len(timingPayload), 2):
                    crcVal ^= int(timingPayload[i : i + 2], 16)
                if crcVal != int(timingInfo["CRC"], 16):
                    crc = " !!!Problem!!! Calculated CRC: " + str(hex(crcVal)[2:]).upper()
                    continue

                # Train ID in decimal
                timingInfo["Train ID"] = int(timingInfo["Train ID"], 16)

                # ids.append(timingInfo['Train ID'])
                # times.append(zeit)
                # directly store data to disk
                np.save(filehandle, zeit)
                np.save(filehandle, timingInfo["Train ID"])
                # print(timingInfo['Train ID'], zeit)

                if z_sock.poll(timeout=0):
                    cmd = z_sock.recv_string()
                    if cmd == "STOP RECORDING":
                        record = False
                    else:
                        z_sock.send_string(f'"{cmd}" in this context invalid')

            # close file
            if filehandle is not None:
                self.debug("closing file")
                filehandle.flush()
                filehandle.close()
                self.debug("file closed")
                z_sock.send_string("CLOSED")
                filehandle = None
            waiting = True

        # We reach this point only after "SHUTDOWN" command received
        self.debug("Process is finishing")
        z_sock.close()
        self.debug("Thread is finished")


def main():
    pass


if __name__ == "__main__":
    main()
