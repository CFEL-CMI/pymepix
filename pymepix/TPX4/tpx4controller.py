
import socket
import threading

import numpy as np

from pymepix.core.log import Logger
from .tpx4chipdevice import Tpx4ChipDevice

class Timepix4Controller(Logger):

    def __init__(self, dst_ip_port, pc_ip, udp_ip_port):
        Logger.__init__(self, Timepix4Controller.__name__)

        self._spidrAddr = dst_ip_port
        self._pc_ip = pc_ip
        self._udp_ip_port = udp_ip_port

        self._devices = []
        self._initDevices()


    def __getitem__(self, key):
        return self._devices[key]

    def __len__(self):
        return len(self._devices)


    def _initDevices(self):

        count = self.deviceCount

        for x in range(count):
            self._devices.append(Tpx4ChipDevice(self, x))
            self._devices[x].ipAddrDest = self._udp_ip_port[0]
            self._devices[x].serverPort = self._udp_ip_port[1] + x



    @property
    def deviceCount(self):
        # NEEDS IMPLEMENTATION

        """Returns devices count

        """
        return 1

    def setBiasSupplyEnable(self, enable):
        """Enables/Disables bias supply voltage

        Parameters
        -----------
        enable : bool
            True - enables bias supply voltage
            False - disables bias supply voltage

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """

        # NEEDS IMPLEMENTATION
        pass


    def prepare(self):

        # NEEDS IMPLEMENTATION
        pass

    def resetTimers(self):
        """Resets all timers to zero

        Sets the internal 48-bit timers for all Timepix/Medipix devices to zero


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        # NEEDS IMPLEMENTATION
        pass

    def restartTimers(self):
        """Restarts SPIDR and Device timers

        Synchronizes both the SPIDR clock and Timepix/Medipix clocks so both trigger
        and ToA timestamps match

        .. Important::
            This must be done if event selection is required (e.g. time of flight) otherwise
            the timestamps will be offset




        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        # NEEDS IMPLEMENTATION
        pass

    def openShutter(self):
        """Immediately opens the shutter indefinetly

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        Notes
        ---------
        This overwrites shutter configurations with one that forces
        an open shutter

        """
        # NEEDS IMPLEMENTATION
        pass

    def closeShutter(self):
        """Immediately closes the shutter

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        # NEEDS IMPLEMENTATION
        pass

    def setShutterTriggerConfig(self, mode, length_us, freq_hz, count, delay_ns=0):
        """Set the shutter configuration in one go


        Parameters
        ----------
        mode: int
            Shutter trigger mode

        length_us: int
            Shutter open time in microseconds

        freq_hz: int
            Auto trigger frequency in Hertz

        count: int
            Number of triggers

        delay_ns: int, optional
            Delay between each trigger (Default: 0)

        Raises
        ----------
        :class:`PymePixException`
            Communication error


        """

        # NEEDS IMPLEMENTATION
        pass

    @property
    def localTemperature(self):
        """Local ????!?!? Temperature read from sensor

        Returns
        --------
        float:
            Temperature in Celsius


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        # NEEDS IMPLEMENTATION
        return 0

    @property
    def remoteTemperature(self):
        """Remote ????!?!? Temperature read from sensor

        Returns
        --------
        float:
            Temperature in Celsius


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        # NEEDS IMPLEMENTATION
        return 0

    @property
    def fpgaTemperature(self):
        """Temperature of FPGA board read from sensor

        Returns
        --------
        float:
            Temperature in Celsius


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        # NEEDS IMPLEMENTATION
        return 0

    @property
    def humidity(self):
        """Humidity read from sensor

        Returns
        --------
        int:
            Humidity as percentage


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        # NEEDS IMPLEMENTATION
        return 0

    @property
    def pressure(self):
        """Pressure read from sensor

        Returns
        --------
        int:
            Pressure in bar


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        # NEEDS IMPLEMENTATION
        return 0

    @property
    def chipboardFanSpeed(self):
        # NEEDS IMPLEMENTATION
        return 0

    @property
    def boardFanSpeed(self):
        # NEEDS IMPLEMENTATION
        return 0
