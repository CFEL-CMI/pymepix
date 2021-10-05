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
from multiprocessing.sharedctypes import Value

from pymepix.processing.acquisition import PixelPipeline

from .config import DefaultConfig, SophyConfig, TimepixConfig

# from .config.sophyconfig import SophyConfig
from .core.log import Logger
from .timepixdef import *


class ConfigClassException(Exception):
    pass


class BadPixelFormat(Exception):
    pass


class TimepixDevice(Logger):
    """ Provides high level control of a timepix/medipix object """

    def update_timer(self):
        """Heartbeat thread"""
        self.info("Heartbeat thread starting")
        while self._run_timer:
            while self._pause_timer and self._run_timer:
                time.sleep(1.0)
                continue

            self._timer_lsb, self._timer_msb = self._device.timer
            self._timer = (self._timer_msb & 0xFFFFFFFF) << 32 | (
                self._timer_lsb & 0xFFFFFFFF
            )
            self._longtime.value = self._timer
            self.debug(
                "Reading heartbeat LSB: {} MSB: {} TIMER: {} ".format(
                    self._timer_lsb, self._timer_msb, self._timer
                )
            )
            time.sleep(1.0)

    def __init__(self, spidr_device, data_queue, pipeline_class=PixelPipeline):

        self._device = spidr_device
        Logger.__init__(self, "Timepix " + self.devIdToString())
        self._data_queue = data_queue
        self._udp_address = (self._device.ipAddrDest, self._device.serverPort)
        self.info("UDP Address is {}:{}".format(*self._udp_address))
        self._pixel_offset_coords = (0, 0)
        self._device.reset()
        self._device.reinitDevice()

        self._longtime = Value("L", 0)
        
        self.setupAcquisition(pipeline_class)

        self._initDACS()

        self._event_callback = None

        self._run_timer = True
        self._pause_timer = False

        self.setEthernetFilter(0xFFFF)

        # Start the timer thread
        self._timer_thread = threading.Thread(target=self.update_timer)
        self._timer_thread.daemon = True
        self._timer_thread.start()
        self.pauseHeartbeat()
        self._acq_running = False

    @property
    def config(self):
        return self.__config

    def setupAcquisition(self, acquisition_klass, *args, **kwargs):
        self.info("Setting up acquisition class")
        self._acquisition_pipeline = acquisition_klass(
            self._data_queue, self._udp_address, self._longtime, *args, **kwargs
        )

    def _initDACS(self):
        self.setConfigClass(DefaultConfig)
        self.loadConfig()
        self.setConfigClass(SophyConfig)

    def setConfigClass(self, klass: TimepixConfig):
        if issubclass(klass, TimepixConfig):
            self._config_class = klass
        else:
            raise ConfigClassException

    def loadConfig(self, *args, **kwargs):
        """ Loads dac settings from the Config class """

        self.__config = self._config_class(*args, **kwargs)

        for code, value in self.__config.dacCodes():
            self.info("Setting DAC {},{}".format(code, value))
            self.setDac(code, value)

        if self.__config.thresholdPixels is not None:
            self.pixelThreshold = self.__config.thresholdPixels

        if self.__config.maskPixels is not None:
            self.pixelMask = self.__config.maskPixels

        if self.__config.testPixels is not None:
            self.pixelTest = self.__config.testPixels

        self.uploadPixels()
        self.refreshPixels()

    def setupDevice(self):
        """
        Sets up valid paramters for acquisition

        This will be manual when other acqusition parameters are working
        """
        self.debug("Setting up acqusition")
        self.polarity = Polarity.Positive
        self.debug("Polarity set to {}".format(Polarity(self.polarity)))
        self.operationMode = OperationMode.ToAandToT
        self.debug("OperationMode set to {}".format(OperationMode(self.operationMode)))
        self.grayCounter = GrayCounter.Enable
        self.debug("GrayCounter set to {}".format(GrayCounter(self.grayCounter)))
        self.superPixel = SuperPixel.Enable
        self.debug("SuperPixel set to {}".format(SuperPixel(self.superPixel)))
        pll_cfg = 0x01E | 0x100
        self._device.pllConfig = pll_cfg
        # self._device.setTpPeriodPhase(10,0)
        # self._device.tpNumber = 1
        # self._device.columnTestPulseRegister

    @property
    def acquisition(self):
        """Returns the acquisition object

        Can be used to set parameters in the acqusition directly for example,
        to setup TOF calculation when using a :class:`PixelPipeline`

        >>> tpx.acqusition.enableEvents
        False
        >>> tpx.acquistion.enableEvents = True

        """
        return self._acquisition_pipeline

    def pauseHeartbeat(self):
        self._pause_timer = True

    def resumeHeartbeat(self):
        self._pause_timer = False

    def devIdToString(self):
        """Converts device ID into readable string

        Returns
        --------
        str
            Device string identifier

        """
        devId = self._device.deviceId
        waferno = (devId >> 8) & 0xFFF
        id_y = (devId >> 4) & 0xF
        id_x = (devId >> 0) & 0xF
        return "W{:04d}_{}{:02d}".format(waferno, chr(ord("A") + id_x - 1), id_y)

    @property
    def deviceName(self):
        return self.devIdToString()

    def setEthernetFilter(self, eth_filter):
        """Sets the packet filter, usually set to 0xFFFF to all all packets"""
        eth_mask, cpu_mask = self._device.headerFilter
        eth_mask = eth_filter
        self._device.setHeaderFilter(eth_mask, cpu_mask)
        eth_mask, cpu_mask = self._device.headerFilter
        self.info(
            "Dev: {} eth_mask :{:8X} cpu_mask: {:8X}".format(
                self._device.deviceId, eth_mask, cpu_mask
            )
        )

    def resetPixels(self):
        """Clears pixel configuration"""
        self._device.clearPixelConfig()
        self._device.resetPixels()

    @property
    def pixelThreshold(self):
        """Threshold set for timepix device

        Parameters
        ----------
        value : :obj:`numpy.array` of :obj:`int`
            256x256 uint8 threshold to set locally


        Returns
        -----------
        :obj:`numpy.array` of :obj:`int` or :obj:`None`:
            Locally stored threshold  matrix

        """
        # self._device.getPixelConfig()
        return self._device._pixel_threshold

    @pixelThreshold.setter
    def pixelThreshold(self, value):
        self._device._pixel_threshold = value

    @property
    def pixelMask(self):
        """Pixel mask set for timepix device

        Parameters
        ----------
        value : :obj:`numpy.array` of :obj:`int`
            256x256 uint8 threshold mask to set locally


        Returns
        -----------
        :obj:`numpy.array` of :obj:`int` or :obj:`None`:
            Locally stored pixel mask matrix


        """
        # self._device.getPixelConfig()
        return self._device._pixel_mask

    @pixelMask.setter
    def pixelMask(self, value):
        self._device._pixel_mask = value

    @property
    def pixelTest(self):
        """Pixel test set for timepix device

        Parameters
        ----------
        value : :obj:`numpy.array` of :obj:`int`
            256x256 uint8 pixel test to set locally


        Returns
        -----------
        :obj:`numpy.array` of :obj:`int` or :obj:`None`:
            Locally stored pixel test matrix


        """
        # self._device.getPixelConfig()
        return self._device._pixel_test

    @pixelTest.setter
    def pixelTest(self, value):
        self._device._pixel_test = value

    def uploadPixels(self):
        """Uploads local pixel configuration to timepix"""

        self._device.uploadPixelConfig()

    def refreshPixels(self):
        """Loads timepix pixel configuration to local array"""
        self._device.getPixelConfig()

    def start(self):
        self.stop()
        self.info("Beginning acquisition")
        self.resumeHeartbeat()
        if self._acquisition_pipeline is not None:
            self._acquisition_pipeline.start()
            self._acq_running = True

    def stop(self):

        if self._acq_running:
            self.info("Stopping acquisition")
            if self._acquisition_pipeline is not None:
                self._acquisition_pipeline.stop()
            self.pauseHeartbeat()
            self._acq_running = False

    # -----General Configuration-------
    @property
    def polarity(self):
        return Polarity(self._device.genConfig & 0x1)

    @polarity.setter
    def polarity(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~1) | value

    @property
    def operationMode(self):
        return OperationMode(self._device.genConfig & OperationMode.Mask)

    @operationMode.setter
    def operationMode(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~OperationMode.Mask) | (value)

    @property
    def grayCounter(self):
        return GrayCounter(self._device.genConfig & GrayCounter.Mask)

    @grayCounter.setter
    def grayCounter(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~GrayCounter.Mask) | (value)

    @property
    def testPulse(self):
        return TestPulse(self._device.genConfig & TestPulse.Mask)

    @testPulse.setter
    def testPulse(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~TestPulse.Mask) | (value)

    @property
    def superPixel(self):
        return SuperPixel(self._device.genConfig & SuperPixel.Mask)

    @superPixel.setter
    def superPixel(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~SuperPixel.Mask) | (value)

    @property
    def timerOverflowControl(self):
        return TimerOverflow(self._device.genConfig & TimerOverflow.Mask)

    @timerOverflowControl.setter
    def timerOverflowControl(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~TimerOverflow.Mask) | (value)

    @property
    def testPulseDigitalAnalog(self):
        return TestPulseDigAnalog(self._device.genConfig & TestPulseDigAnalog.Mask)

    @testPulseDigitalAnalog.setter
    def testPulseDigitalAnalog(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~TestPulseDigAnalog.Mask) | (value)

    @property
    def testPulseGeneratorSource(self):
        return TestPulseGenerator(self._device.genConfig & TestPulseGenerator.Mask)

    @testPulseGeneratorSource.setter
    def testPulseGeneratorSource(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~TestPulseGenerator.Mask) | (value)

    @property
    def timeOfArrivalClock(self):
        return TimeofArrivalClock(self._device.genConfig & TimeofArrivalClock.Mask)

    @timeOfArrivalClock.setter
    def timeOfArrivalClock(self, value):
        gen_config = self._device.genConfig
        self._device.genConfig = (gen_config & ~TimeofArrivalClock.Mask) | (value)

    @property
    def Ibias_Preamp_ON(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_Preamp_ON)
        return value & 0xFF

    @Ibias_Preamp_ON.setter
    def Ibias_Preamp_ON(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_Preamp_ON, nint & 0xFF)

    @property
    def Ibias_Preamp_OFF(self):
        """[0, 15]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_Preamp_OFF)
        return value & 0xF

    @Ibias_Preamp_OFF.setter
    def Ibias_Preamp_OFF(self, value):
        """[0, 15]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_Preamp_OFF, nint & 0xF)

    @property
    def VPreamp_NCAS(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.VPreamp_NCAS)
        return value & 0xFF

    @VPreamp_NCAS.setter
    def VPreamp_NCAS(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.VPreamp_NCAS, nint & 0xFF)

    @property
    def Ibias_Ikrum(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_Ikrum)
        return value & 0xFF

    @Ibias_Ikrum.setter
    def Ibias_Ikrum(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_Ikrum, nint & 0xFF)

    @property
    def Vfbk(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.Vfbk)
        return value & 0xFF

    @Vfbk.setter
    def Vfbk(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Vfbk, nint & 0xFF)

    @property
    def Vthreshold_fine(self):
        """[0, 511]"""
        value = self._device.getDac(DacRegisterCodes.Vthreshold_fine)
        return value & 0x1FF

    @Vthreshold_fine.setter
    def Vthreshold_fine(self, value):
        """[0, 511]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Vthreshold_fine, nint & 0x1FF)

    @property
    def Vthreshold_coarse(self):
        """[0, 15]"""
        value = self._device.getDac(DacRegisterCodes.Vthreshold_coarse)
        return value & 0xF

    @Vthreshold_coarse.setter
    def Vthreshold_coarse(self, value):
        """[0, 15]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Vthreshold_coarse, nint & 0xF)

    @property
    def Ibias_DiscS1_ON(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_DiscS1_ON)
        return value & 0xFF

    @Ibias_DiscS1_ON.setter
    def Ibias_DiscS1_ON(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_DiscS1_ON, nint & 0xFF)

    @property
    def Ibias_DiscS1_OFF(self):
        """[0, 15]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_DiscS1_OFF)
        return value & 0xF

    @Ibias_DiscS1_OFF.setter
    def Ibias_DiscS1_OFF(self, value):
        """[0, 15]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_DiscS1_OFF, nint & 0xF)

    @property
    def Ibias_DiscS2_ON(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_DiscS2_ON)
        return value & 0xFF

    @Ibias_DiscS2_ON.setter
    def Ibias_DiscS2_ON(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_DiscS2_ON, nint & 0xFF)

    @property
    def Ibias_DiscS2_OFF(self):
        """[0, 15]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_DiscS2_OFF)
        return value & 0xF

    @Ibias_DiscS2_OFF.setter
    def Ibias_DiscS2_OFF(self, value):
        """[0, 15]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_DiscS2_OFF, nint & 0xF)

    @property
    def Ibias_PixelDAC(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_PixelDAC)
        return value & 0xFF

    @Ibias_PixelDAC.setter
    def Ibias_PixelDAC(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_PixelDAC, nint & 0xFF)

    @property
    def Ibias_TPbufferIn(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_TPbufferIn)
        return value & 0xFF

    @Ibias_TPbufferIn.setter
    def Ibias_TPbufferIn(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_TPbufferIn, nint & 0xFF)

    @property
    def Ibias_TPbufferOut(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.Ibias_TPbufferOut)
        return float((value & 0xFF))

    @Ibias_TPbufferOut.setter
    def Ibias_TPbufferOut(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.Ibias_TPbufferOut, nint & 0xFF)

    @property
    def VTP_coarse(self):
        """[0, 255]"""
        value = self._device.getDac(DacRegisterCodes.VTP_coarse)
        return float((value & 0xFF))

    @VTP_coarse.setter
    def VTP_coarse(self, value):
        """[0, 255]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.VTP_coarse, nint & 0xFF)

    @property
    def VTP_fine(self):
        """[0, 511]"""
        value = self._device.getDac(DacRegisterCodes.VTP_fine)
        return float((value & 0x1FF))

    @VTP_fine.setter
    def VTP_fine(self, value):
        """[0, 511]"""
        nint = int(value)
        self._device.setDac(DacRegisterCodes.VTP_fine, nint & 0x1FF)

    def setDac(self, code, value):
        """Sets the DAC parameter using codes

        Parameters
        ----------
        code: :obj:`int`
            DAC code to set

        value: :obj:`int`
            value to set
        """
        self._device.setDac(code, value)


def main():
    import logging
    from multiprocessing import Queue

    from .SPIDR.spidrcontroller import SPIDRController

    logging.basicConfig(level=logging.INFO)
    end_queue = Queue()

    def get_queue_thread(queue):
        while True:
            value = queue.get()
            print(value)
            if value is None:
                break

    t = threading.Thread(target=get_queue_thread, args=(end_queue,))
    t.daemon = True
    t.start()

    spidr = SPIDRController(("192.168.100.10", 50000))

    timepix = TimepixDevice(spidr[0], end_queue)
    timepix.loadSophyConfig(
        "/Users/alrefaie/Documents/repos/libtimepix/config/eq-norm-50V.spx"
    )

    # spidr.shutterTriggerMode = SpidrShutterMode.Auto
    spidr.disableExternalRefClock()
    TdcEnable = 0x0000
    spidr.setSpidrReg(0x2B8, TdcEnable)
    spidr.enableDecoders(True)
    spidr.resetTimers()
    spidr.restartTimers()

    spidr.datadrivenReadout()
    timepix.setupDevice()

    spidr.openShutter()
    timepix.start()
    time.sleep(4.0)
    timepix.stop()
    logging.info("DONE")
    spidr.closeShutter()


if __name__ == "__main__":
    main()
