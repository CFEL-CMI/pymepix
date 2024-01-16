


import weakref

from pymepix.core.log import Logger

class Tpx4ChipDevice(Logger):

    def __init__(self, _ctrl, device_num):
        Logger.__init__(self, Tpx4ChipDevice.__name__)
        self._ctrl = weakref.proxy(_ctrl)
        self._dev_num = device_num

        self.info("Device {} with device number {} created".format(self._dev_num, self._dev_num))

        self._ipAddrDest = None
        self._serverPort = None


    @property
    def linkStatus(self):
        # NEEDS IMPLEMENTATION
        return True, True, True

    @property
    def ipAddrSrc(self):
        # NEEDS IMPLEMENTATION
        return "{}.{}.{}.{}".format(127,0,0,1)

    @ipAddrSrc.setter
    def ipAddrSrc(self, ipaddr):
        self._ipAddrDest = ipaddr

    @property
    def ipAddrDest(self):
        return self._ipAddrDest

    @ipAddrDest.setter
    def ipAddrDest(self, ipaddr):
        self._ipAddrDest = ipaddr

    @property
    def serverPort(self):
        return self._serverPort

    @serverPort.setter
    def serverPort(self, value):
        self._serverPort = value


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