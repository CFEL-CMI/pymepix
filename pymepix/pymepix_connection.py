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
import time
from collections import deque
from multiprocessing import Queue

import pymepix.config.load_config as cfg
from pymepix.core.log import Logger
from pymepix.processing.acquisition import PixelPipeline
from .SPIDR.spidrcontroller import SPIDRController
from .TPX4.tpx4controller import Timepix4Controller
from .timepixdevice import TimepixDevice
from pymepix.channel.channel_types import Commands, ChannelDataType
from pymepix.channel.data_channel import Data_Channel

from .timepix4device import Timepix4Device


class PollBufferEmpty(Exception):
    pass


class PymepixConnection(Logger):
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

    >>> timepix = PymepixConnection(('192.168.1.10',50000))

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
        self.info("Starting data thread")
        while True:
            value = self._data_queue.get()
            self.debug("Popped value {}".format(value))
            if value is None:
                break

            data_type, data = value
            self._event_callback(data_type, data)

            self._channel.send_data_by_message_type(data_type, data)

    def __init__(self,
                 spidr_address=(cfg.default_cfg['timepix']['tpx_ip'],
                                int(cfg.default_cfg.get('timepix').get('tpx_port', 50000))),
                 udp_ip_port=(cfg.default_cfg['timepix']['udp_ip'], cfg.default_cfg['timepix']['udp_port']),
                 pc_ip = cfg.default_cfg['timepix']['pc_ip'],
                 api_address=(cfg.default_cfg['api_channel']['ip'],
                              cfg.default_cfg['api_channel']['port']),

                 pipeline_class=PixelPipeline,
                 camera_generation=3,
                 ):
        Logger.__init__(self, "Pymepix")

        self._channel = Data_Channel()
        self._channel.start()
        self._channel.register(f'tcp://{api_address[0]}:{api_address[1]}')

        self.camera_generation = camera_generation

        controllerClass = self._timepix_controller_class_factory(camera_generation)

        self._controller = controllerClass(spidr_address, pc_ip, udp_ip_port)

        TimepixDeviceClass = self._timepix_device_class_factory(camera_generation)
        self._timepix_devices: list[TimepixDeviceClass] = []

        self._data_queue = Queue()
        self._createTimepix(pipeline_class)
        self._controller.setBiasSupplyEnable(True)
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
        self._controller.biasVoltage = value

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
        """Get/Set polling buffer length

        Clears buffer on set

        """
        return self._poll_buffer.maxlen

    @pollBufferLength.setter
    def pollBufferLength(self, value):
        self.warning("Clearing polling buffer")
        self._poll_buffer = deque(maxlen=value)

    @property
    def dataCallback(self):
        """Function to call when data is received from a timepix device

        This has the effect of disabling polling.

        """
        return self._event_callback

    @dataCallback.setter
    def dataCallback(self, value):
        self._event_callback = value
        self.warning("Clearing polling buffer")
        self._poll_buffer.clear()

    def enablePolling(self, maxlen=100):
        """Enables polling mode

        This clears any user defined callbacks and the polling buffer

        """

        self.info("Enabling polling")

        self.pollBufferLength = maxlen
        self.dataCallback = self._pollCallback

    def _pollCallback(self, data_type, data):
        self._poll_buffer.append((data_type, data))

    def _createTimepix(self, pipeline_class=PixelPipeline):
        TimepixDeviceClass = self._timepix_device_class_factory(self.camera_generation)
        for x in self._controller:
            status, enabled, locked = x.linkStatus
            if enabled != 0 and locked == enabled:
                self._timepix_devices.append(TimepixDeviceClass(x, self._data_queue, pipeline_class))

        self._num_timepix = len(self._timepix_devices)
        self.info("Found {} Timepix/Medipix devices".format(len(self._timepix_devices)))
        for idx, tpx in enumerate(self._timepix_devices):
            self.info("Device {} - {}".format(idx, tpx.devIdToString()))

    def start_recording(self, path):
        self._controller.resetTimers()
        self._controller.restartTimers()
        time.sleep(1)  # give camera time to reset timers

        self._timepix_devices[0].start_recording(path)

        self._channel.send(ChannelDataType.COMMAND, Commands.START_RECORD)

    def stop_recording(self):
        self._timepix_devices[0].stop_recording()
        self._channel.send(ChannelDataType.COMMAND, Commands.STOP_RECORD)

    def start(self):
        """Starts acquisition"""

        if self._running is True:
            self.stop()

        self.info("Starting acquisition")
        self._controller.prepare()
        self._controller.resetTimers()
        self._controller.restartTimers()

        for t in self._timepix_devices:
            self.info("Setting up {}".format(t.deviceName))
            t.setupDevice()
        self._controller.restartTimers()
        self._controller.openShutter()
        for t in self._timepix_devices:
            self.info("Starting {}".format(t.deviceName))
            t.start()

        self._running = True

    def stop(self):
        """Stops acquisition"""

        if self._running is False:
            return
        self.info("Stopping acquisition")
        trig_mode = 0
        trig_length_us = 10000
        trig_freq_hz = 5
        nr_of_trigs = 1

        self._controller.setShutterTriggerConfig(
            trig_mode, trig_length_us, trig_freq_hz, nr_of_trigs, 0
        )
        self._controller.closeShutter()
        self.debug("Closing shutter")
        for t in self._timepix_devices:
            self.debug("Stopping {}".format(t.deviceName))
            t.stop()
        self._running = False

    @property
    def isAcquiring(self):
        return self._running

    @property
    def numDevices(self):
        return self._num_timepix

    @property
    def chanAddress(self):
        """Bias voltage in volts"""
        return self._channel_address

    @chanAddress.setter
    def chanAddress(self, value):
        self._channel_address = value
        self._channel.unregister()
        self._channel.register(f'tcp://{value[0]}:{value[1]}')

    def __getitem__(self, key) -> TimepixDevice:
        return self._timepix_devices[key]

    def __len__(self):
        return len(self._timepix_devices)

    def getDevice(self, num) -> TimepixDevice:
        return self._timepix_devices[num]

    def _timepix_device_class_factory(self, camera_generation):
        timepix_device_classes = {3: TimepixDevice,\
                                  4: Timepix4Device}
        if camera_generation in timepix_device_classes:
            return timepix_device_classes[camera_generation]
        else:
            raise ValueError(f'No timepix device for camera generation {camera_generation}')

    def _timepix_controller_class_factory(self, camera_generation):

        timepix_controller_classes = {3: SPIDRController, \
                                      4: Timepix4Controller}

        if camera_generation in timepix_controller_classes:
            return timepix_controller_classes[camera_generation]
        else:
            raise ValueError(f'No timepix controller for camera generation {camera_generation}')
