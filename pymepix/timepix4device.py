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

from .core.log import Logger
from .timepix4def import *


class ConfigClassException(Exception):
    pass


class BadPixelFormat(Exception):
    pass


class Timepix4Device(Logger):
    """ Provides a control of a timepix4 object """

    def __init__(self, tpx4_device, data_queue, pipeline_class=PixelPipeline):

        self._device = tpx4_device
        Logger.__init__(self, "Timepix " + self.devIdToString())
        self._data_queue = data_queue
        self._udp_address = (self._device.ipAddrDest, self._device.serverPort)
        self.info("UDP Address is {}:{}".format(*self._udp_address))


        self.camera_generation = 4

        #self._device.reset()
        #self._device.reinitDevice()

        self._longtime = Value("L", 0)

        self.setupAcquisition(pipeline_class)

        self._run_timer = True
        self._pause_timer = False

        self.setEthernetFilter(0xFFFF)

        # Start the timer thread
        self._acq_running = False

    @property
    def config(self):
        return self.__config

    def setupAcquisition(self, acquisition_klass, *args, **kwargs):
        self.info("Setting up acquisition class")
        self._acquisition_pipeline = acquisition_klass(
            self._data_queue, self._udp_address, self._longtime, camera_generation=self.camera_generation, *args, **kwargs
        )

    def _initDACS(self):
        pass
        #self.setConfigClass(DefaultConfig)
        #self.loadConfig()
        #self.setConfigClass(SophyConfig)

    def setConfigClass(self,):# klass: TimepixConfig):
        pass
        #if issubclass(klass, TimepixConfig):
        #    self._config_class = klass
        #else:
        #    raise ConfigClassException

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
        Sets up valid parameters for acquisition

        This will be manual when other acquisition parameters are working
        """

        pass

        self.debug("Setting up acqusition")
        #self.polarity = Polarity.Positive
        #self.debug("Polarity set to {}".format(Polarity(self.polarity)))
        #self.operationMode = OperationMode.ToAandToT
        #self.debug("OperationMode set to {}".format(OperationMode(self.operationMode)))
        #self.grayCounter = GrayCounter.Enable
        #self.debug("GrayCounter set to {}".format(GrayCounter(self.grayCounter)))
        #self.superPixel = SuperPixel.Enable
        #self.debug("SuperPixel set to {}".format(SuperPixel(self.superPixel)))

        #pll_cfg = 0x01E | 0x100
        #self._device.pllConfig = pll_cfg
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
        pass

    def resumeHeartbeat(self):
        pass

    def devIdToString(self):
        """Converts device ID into readable string

        Returns
        --------
        str
            Device string identifier

        """
        # NEEDS IMPLEMENTATION
        return ''


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

        # NEEDS IMPLEMENTATION
        pass

        #self._device.clearPixelConfig()
        #self._device.resetPixels()


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
        # NEEDS IMPLEMENTATION
        pass
        # self._device.getPixelConfig()
        #return self._device._pixel_threshold

    @pixelThreshold.setter
    def pixelThreshold(self, value):
        # NEEDS IMPLEMENTATION
        pass
        #self._device._pixel_threshold = value

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

        # NEEDS IMPLEMENTATION
        pass

        # self._device.getPixelConfig()
        #return self._device._pixel_mask

    @pixelMask.setter
    def pixelMask(self, value):
        # NEEDS IMPLEMENTATION
        pass
        #self._device._pixel_mask = value

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
        # NEEDS IMPLEMENTATION
        pass

        # self._device.getPixelConfig()
        #return self._device._pixel_test

    @pixelTest.setter
    def pixelTest(self, value):
        pass
        #self._device._pixel_test = value

    def uploadPixels(self):
        """Uploads local pixel configuration to timepix"""
        pass
        #self._device.uploadPixelConfig()

    def refreshPixels(self):
        """Loads timepix pixel configuration to local array"""
        pass
        #self._device.getPixelConfig()

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

    def start_recording(self, path):
        udp_sampler = self._acquisition_pipeline._stages[0]
        udp_sampler._pipeline_objects[0].record = True
        udp_sampler.udp_sock.send_string(path)
        res = udp_sampler.udp_sock.recv_string()
        if res == "OPENED":
            path = udp_sampler.udp_sock.recv_string()
            self.debug(f"Started recording to {path}")
        else:
            self.warning(f"Error while starting recording: {res}")

    def stop_recording(self):
        pipeline = self._acquisition_pipeline._stages[0]
        pipeline._pipeline_objects[0].record = False
        pipeline._pipeline_objects[0].close_file = True
        res = pipeline.udp_sock.recv_string()
        if res == "CLOSED":
            self.info(f"Finished recording")
        else:
            self.warning(f"Error during recording: {res}")


    @property
    def Vthreshold_fine(self):

        # NEEDS IMPLEMENTATION

        return 0

    @Vthreshold_fine.setter
    def Vthreshold_fine(self, value):

        # NEEDS IMPLEMENTATION

        pass

    @property
    def Vthreshold_coarse(self):

        # NEEDS IMPLEMENTATION

        return 0

    @Vthreshold_coarse.setter
    def Vthreshold_coarse(self, value):

        # NEEDS IMPLEMENTATION

        pass






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

    timepix = Timepix4Device(spidr[0], end_queue)
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
