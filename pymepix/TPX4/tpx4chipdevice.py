


import weakref

import numpy as np

from pymepix.core.log import Logger

class Tpx4ChipDevice(Logger):

    def __init__(self, _ctrl, device_num):
        Logger.__init__(self, Tpx4ChipDevice.__name__)
        self._ctrl = weakref.proxy(_ctrl)
        self._dev_num = device_num

        self.info("Device {} with device number {} created".format(self._dev_num, self._dev_num))


    @property
    def linkStatus(self):
        # NEEDS IMPLEMENTATION

        return True, True, True

    @property
    def ipAddrSrc(self):
        return self._ctrl._camera_ip_address[0]

    @ipAddrSrc.setter
    def ipAddrSrc(self, ipaddr):
        ip_port = list(self._ctrl._camera_ip_address)
        ip_port[0] = ipaddr
        self._ctrl._camera_ip_address = tuple(ip_port)

    @property
    def ipAddrDest(self):
        return self._ctrl._camera_ip_address[0]

    @ipAddrDest.setter
    def ipAddrDest(self, ipaddr):
        ip_port = list(self._ctrl._camera_ip_address)
        ip_port[0] = ipaddr
        self._ctrl._camera_ip_address = tuple(ip_port)

    @property
    def serverPort(self):
        return self._ctrl._udp_port

    @serverPort.setter
    def serverPort(self, value):
        self._ctrl._udp_port = value

    @property
    def headerFilter(self):
        # NEEDS IMPLEMENTATION

        eth_mask = 0xFFFF
        cpu_mask = 0xFFFF

        return eth_mask, cpu_mask

    def setHeaderFilter(self, eth_mask, cpu_mask):
        # NEEDS IMPLEMENTATION
        pass

    @property
    def deviceId(self):
        """Returns unique device Id

        Parameters
        ----------
        spidr_ctrl: :class:`SpidrController`
            SPIDR controller object the device belongs to
        device_num:
            Device index from SPIDR (Starts from 1)


        """
        # NEEDS IMPLEMENTATION

        return ''