##############################################################################
##
# This file is part of Pymepix
#
# https://arxiv.org/abs/1905.07999
#
#
# Pymepix is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pymepix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pymepix.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""Main module for pymepix"""

import numpy as np
from .SPIDR.spidrcontroller import SPIDRController
from .SPIDR.spidrdefs import SpidrReadoutSpeed
from pymepix.core.log import Logger
from .timepixdevice import TimepixDevice
from multiprocessing import Queue
from collections import deque
import threading
import time


class PollBufferEmpty(Exception):
    pass


class Pymepix(Logger):
    """High level class to work with timepix and perform acquistion

    This class performs connection to SPIDR, initilization of timepix and handling of acquisition.
    Each individual timepix device can be accessed using the square bracket operator.


    Parameters
    ----------
    spidr_address : :obj:`tuple` of :obj:`str` and :obj:`int`
        socket style tuple of SPIDR ip address and port
    src_ip_port : :obj:`tuple` of :obj:`str` and :obj:`int`, optional
        socket style tuple of the IP address and port of the interface that is connecting to SPIDR

    Examples
    --------
    
    Startup device

    >>> timepix = Pymepix(('192.168.1.10',50000))
    
    Find how many Timepix are connected

    >>> len(timepix)
    1

    Set the Bias voltage
    >>> timepix.biasVoltage = 50

    Access a specific Timepix device:

    >>> timepix[0].deviceName
    W0026_K06

    Load a config file into timepix

    >>> timepix[0].loadSophyConfig('W0026_K06_50V.spx')
    

    
    """

    def data_thread(self):
        self.info('Starting data thread')
        while True:
            value = self._data_queue.get()
            self.debug('Popped value {}'.format(value))
            if value is None:
                break

            data_type, data = value
            self._event_callback(data_type, data)

    def __init__(self, spidr_address, src_ip_port=('192.168.1.1', 0)):
        Logger.__init__(self, 'Pymepix')
        self._spidr = SPIDRController(spidr_address, src_ip_port)

        self._timepix_devices = []

        self._data_queue = Queue()
        self._createTimepix()
        self._spidr.setBiasSupplyEnable(True)
        self.biasVoltage = 50
        self.enablePolling()
        self._data_thread = threading.Thread(target=self.data_thread)
        self._data_thread.daemon = True
        self._data_thread.start()

        self._running = False

    @property
    def biasVoltage(self):
        """Bias voltage in volts"""
        return self._bias_voltage

    @biasVoltage.setter
    def biasVoltage(self, value):
        self._bias_voltage = value
        self._spidr.biasVoltage = value

    def poll(self, block=False):
        """If polling is used, returns data stored in data buffer.


        the buffer is in the form of a ring and will overwrite older
        values if it becomes full


        Returns
        --------
        :obj:`MessageType` , data


        """
        if block:
            while True:
                try:
                    return self._poll_buffer.popleft()
                except IndexError:
                    time.sleep(0.5)
                    continue
        else:
            try:
                return self._poll_buffer.popleft()
            except IndexError:
                raise PollBufferEmpty

    @property
    def pollBufferLength(self):
        """ Get/Set polling buffer length
        
        Clears buffer on set

        """
        return self._poll_buffer.maxlen

    @pollBufferLength.setter
    def pollBufferLength(self, value):
        self.warning('Clearing polling buffer')
        self._poll_buffer = deque(maxlen=value)

    @property
    def dataCallback(self):
        """Function to call when data is recieved from a timepix device

        This has the effect of disabling polling. 

        """
        return self._event_callback

    @dataCallback.setter
    def dataCallback(self, value):
        self._event_callback = value
        self.warning('Clearing polling buffer')
        self._poll_buffer.clear()

    def enablePolling(self, maxlen=100):
        """Enables polling mode

        This clears any user defined callbacks and the polling buffer

        """

        self.info('Enabling polling')

        self.pollBufferLength = maxlen
        self.dataCallback = self._pollCallback

    def _pollCallback(self, data_type, data):
        self._poll_buffer.append((data_type, data))

    def _createTimepix(self):

        for x in self._spidr:
            status, enabled, locked = x.linkStatus
            if enabled != 0 and locked == enabled:
                self._timepix_devices.append(TimepixDevice(x, self._data_queue))

        self._num_timepix = len(self._timepix_devices)
        self.info('Found {} Timepix/Medipix devices'.format(len(self._timepix_devices)))
        for idx, tpx in enumerate(self._timepix_devices):
            self.info('Device {} - {}'.format(idx, tpx.devIdToString()))

    def _prepare(self):
        self._spidr.disableExternalRefClock()
        TdcEnable = 0x0000
        self._spidr.setSpidrReg(0x2B8, TdcEnable)
        self._spidr.enableDecoders(True)
        self._spidr.datadrivenReadout()

    def start(self):
        """Starts acquisition"""

        if self._running == True:
            self.stop()

        self.info('Starting acquisition')
        self._prepare()
        self._spidr.resetTimers()
        self._spidr.restartTimers()

        for t in self._timepix_devices:
            self.info('Setting up {}'.format(t.deviceName))
            t.setupDevice()
        self._spidr.restartTimers()
        self._spidr.openShutter()
        for t in self._timepix_devices:
            self.info('Starting {}'.format(t.deviceName))
            t.start()

        self._running = True

    def stop(self):
        """Stops acquisition"""

        if self._running == False:
            return
        self.info('Stopping acquisition')
        trig_mode = 0
        trig_length_us = 10000
        trig_freq_hz = 5
        nr_of_trigs = 1

        self._spidr.setShutterTriggerConfig(trig_mode, trig_length_us,
                                            trig_freq_hz, nr_of_trigs, 0)
        self._spidr.closeShutter()
        self.debug('Closing shutter')
        for t in self._timepix_devices:
            self.debug('Stopping {}'.format(t.deviceName))
            t.stop()
        self._running = False

    @property
    def isAcquiring(self):
        return self._running

    @property
    def numDevices(self):
        return self._num_timepix

    def __getitem__(self, key):
        return self._timepix_devices[key]

    def __len__(self):
        return len(self._timepix_devices)

    def getDevice(self, num):
        return self._timepix_devices[num]


def main():
    import logging
    from .processing.datatypes import MessageType
    from .processing import CentroidPipeline
    from .util.storage import open_output_file, store_raw, store_toa, store_tof
    import argparse
    import time

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description='Timepix acquisition script')
    parser.add_argument("-i", "--ip", dest='ip', type=str, default='192.168.1.10', help="IP address of Timepix")
    parser.add_argument("-p", "--port", dest='port', type=int, default=50000, help="TCP port to use for the connection")
    parser.add_argument("-s", "--spx", dest='spx', type=str, help="Sophy config file to load")
    parser.add_argument("-v", "--bias", dest='bias', type=float, default=50, help="Bias voltage in Volts")
    parser.add_argument("-t", "--time", dest='time', type=float, help="Acquisition time in seconds", required=True)
    parser.add_argument("-o", "--output", dest='output', type=str, help="output filename prefix", required=True)
    parser.add_argument("-d", "--decode", dest='decode', type=bool, help="Store decoded values instead", default=False)
    parser.add_argument("-T", "--tof", dest='tof', type=bool, help="Compute TOF if decode is enabled", default=False)

    args = parser.parse_args()

    # Connect to SPIDR
    pymepix = Pymepix((args.ip, args.port))
    # If there are no valid timepix detected then quit()
    if len(pymepix) == 0:
        logging.error('-------ERROR: SPIDR FOUND BUT NO VALID TIMEPIX DEVICE DETECTED ---------- ')
        quit()
    if args.spx:
        logging.info('Opening Sophy file {}'.format(args.spx))
        pymepix[0].loadConfig(args.spx)

    # Switch to TOF mode if set
    if args.decode and args.tof:
        pymepix[0].acquisition.enableEvents = True

    # Set the bias voltage
    pymepix.biasVoltage = args.bias

    ext = 'raw'
    if args.decode:
        logging.info('Decoding data enabled')
        if args.tof:
            logging.info('Tof calculation enabled')
            ext = 'tof'
        else:
            ext = 'toa'
    else:
        logging.info('No decoding selected')

    output_file = open_output_file(args.output, ext)

    total_time = args.time

    start_time = time.time()

    logging.info('------Starting acquisition---------')
    # Start acquisition
    pymepix.start()
    while time.time() - start_time < total_time:
        try:
            data_type, data = pymepix.poll()
        except PollBufferEmpty:
            continue
        logging.debug('Datatype: {} Data:{}'.format(data_type, data))
        if data_type is MessageType.RawData:
            if not args.decode:
                store_raw(output_file, data)
        elif data_type is MessageType.PixelData:
            if args.decode and not args.tof:
                store_toa(output_file, data)
        elif data_type is MessageType.PixelData:
            if args.decode and args.tof:
                store_tof(output_file, data)

    pymepix.stop()


if __name__ == "__main__":
    main()
