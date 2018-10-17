from .SPIDR.spidrcontroller import SPIDRController
from .udplistener import TimepixUDPListener
import numpy as np
from .timepixdef import *
from .SPIDR.spidrdefs import SpidrShutterMode
import time
import queue
import threading
import multiprocessing
from multiprocessing.sharedctypes import Value
from .packetsampler import PacketSampler
from .packetprocessor import PacketProcessor
from .filestorage import FileStorage
class TimePixAcq(object):


    def updateTimer(self):

        while self._run_timer:
            self._timer_lsb,self._timer_msb = self._device.timer
            self._timer = (self._timer_msb & 0xFFFFFFFF)<<32 |(self._timer_lsb & 0xFFFFFFFF)
            self._shared_timer.value = self._timer
            while self._pause and self._run_timer:
                continue
    def dataThread(self):

        while True:

            value = self._data_queue.get()
            if value is None:
                break
            self.onEvent(value)


    def __init__(self,ip_port,device_num=0):
        self._spidr = SPIDRController(ip_port)

        self._device = self._spidr[device_num]
        #self._device.reinitDevice()
        #self._device.getPixelConfig()
        self._eventCallback = None
        UDP_IP = self._device.ipAddrDest
        UDP_PORT = self._device.serverPort
        self._open_shutter = True
        #self._device.outBlockConfig &= ~(0x1000)

        self._data_queue = multiprocessing.Queue()
        self._file_queue =  multiprocessing.Queue()
        self._pause = False
        #self._spidr.datadrivenReadout()

        self._run_timer = True

        self._timer = 0
        self._shared_timer = Value('I',0)
        self._shared_acq = Value('I',0)
        self._shared_exp_time = Value('I',10000)
        self._timer_lsb = 0
        self._timer_msb = 0
        self._timer_thread = threading.Thread(target = self.updateTimer)
        self._timer_thread.start()

        self.pauseTimer()
        self._data_thread = threading.Thread(target=self.dataThread)
        self._data_thread.start()
        self._file_storage = FileStorage(self._file_queue)
        self._packet_sampler = PacketSampler((UDP_IP,UDP_PORT),self._file_queue,self._shared_timer,self._shared_acq)
        self._packet_processor = PacketProcessor(self._packet_sampler.outputQueue,self._data_queue)

        self._packet_processor.start()
        self._file_storage.start()
        self._packet_sampler.start()

    def pauseTimer(self):
        self._pause = True

    def resumeTimer(self):
        self._pause = False

    @property
    def deviceInfoString(self):

        output_string = "-------------------SPIDR Board Info----------------------\n"
        output_string += "\tFW version: {:8X}\n SW Version: {:8X}\n".format(self._spidr.firmwareVersion,self._spidr.softwareVersion)
        output_string += "\tNumber of devices: {} \nDevice Ids: {}\n".format(len(self._spidr),self._spidr.deviceIds)
        output_string += "\tPressure: {} mbar\n Temperature {}".format(self._spidr.pressure,self._spidr.localTemperature)

        return output_string
    
    def attachEventCallback(self,callback):
        self._eventCallback = callback


    def onEvent(self,data):
        if self._eventCallback is not None:
            self._eventCallback(data)



    #-----General Configuration-------
    @property
    def polarity(self):
        return Polarity(self._device.genConfig & 0x1)
    @polarity.setter
    def polarity(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~1) | value

    @property
    def operationMode(self):
        return OperationMode(self._device.genConfig & OperationMode.Mask)
    
    @operationMode.setter
    def operationMode(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~OperationMode.Mask) | (value)
    
    @property
    def grayCounter(self):
        return GrayCounter(self._device.genConfig & GrayCounter.Mask)

    @grayCounter.setter
    def grayCounter(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~GrayCounter.Mask) | (value)    

    @property
    def testPulse(self):
        return TestPulse(self._device.genConfig & TestPulse.Mask)

    @testPulse.setter
    def testPulse(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~TestPulse.Mask) | (value)    

    @property
    def superPixel(self):
        return SuperPixel(self._device.genConfig & SuperPixel.Mask)

    @superPixel.setter
    def superPixel(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~SuperPixel.Mask) | (value)  

    @property
    def timerOverflowControl(self):
        return TimerOverflow(self._device.genConfig & TimerOverflow.Mask)

    @timerOverflowControl.setter
    def timerOverflowControl(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~TimerOverflow.Mask) | (value)  

    @property
    def testPulseDigitalAnalog(self):
        return TestPulseDigAnalog(self._device.genConfig & TestPulseDigAnalog.Mask)
    
    @testPulseDigitalAnalog.setter
    def testPulseDigitalAnalog(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~TestPulseDigAnalog.Mask) | (value)  

    @property
    def testPulseGeneratorSource(self):
        return TestPulseGenerator(self._device.genConfig & TestPulseGenerator.Mask)

    @testPulseGeneratorSource.setter
    def testPulseGeneratorSource(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~TestPulseGenerator.Mask) | (value) 

    @property
    def timeOfArrivalClock(self):
        return TimeofArrivalClock(self._device.genConfig & TimeofArrivalClock.Mask)

    @timeOfArrivalClock.setter
    def timeOfArrivalClock(self,value):
        gen_config = self._device.genConfig 
        self._device.genConfig = (gen_config & ~TimeofArrivalClock.Mask) | (value) 

    #------------Timepix pixel configuration-------------------
    @property
    def thresholdMask(self):
        #self._device.getPixelConfig()
        pixel_config = self._device.currentPixelConfig
        return (pixel_config >> 1) &0x1E
    
    @thresholdMask.setter
    def thresholdMask(self,threshold):
        self._device.setPixelThreshold(threshold.astype(np.uint8))
    
    @property
    def pixelMask(self):
        #self._device.getPixelConfig()
        pixel_config = self._device.currentPixelConfig
        return pixel_config&0x1

    @pixelMask.setter
    def pixelMask(self,mask):
        self._device.setPixelMask(mask.astype(np.uint8))
    

    def uploadPixels(self):
        self.pauseTimer()
        self._device.uploadPixelConfig()
        self.resumeTimer()
    def refreshPixels(self):
        self.pauseTimer()
        self._device.getPixelConfig()
        self.resumeTimer()
    
    @property
    def eventWindowTime(self):
        return self._shared_exp_time.value

    @eventWindowTime.setter
    def eventWindowTime(self,value):
        self._shared_exp_time.value = value

    @property
    def shutterTriggerMode(self):
        if self._open_shutter:
            return SpidrShutterMode.Open
        else:
            return self._spidr.ShutterTriggerMode
    @shutterTriggerMode.setter
    def shutterTriggerMode(self,value):
        if value is SpidrShutterMode.Open:
            self._open_shutter = True
        else:
            self._spidr.ShutterTriggerMode = value
            self._open_shutter = False

    @property
    def shutterTriggerFreqMilliHz(self):
        return self._spidr.ShutterTriggerFreq

    @shutterTriggerFreqMilliHz.setter
    def shutterTriggerFreqMilliHz(self,value):
        self._spidr.ShutterTriggerFreq = int(value)

    @property
    def shutterTriggerExposureTime(self):
        return self._spidr.ShutterTriggerLength
    
    @shutterTriggerExposureTime.setter
    def shutterTriggerExposureTime(self,value):
        self._spidr.ShutterTriggerLength = int(value)

    @property
    def shutterNumOfTriggers(self):
        return self._spidr.ShutterTriggerCount
    
    @shutterNumOfTriggers.setter
    def shutterNumOfTriggers(self,value):
        self._spidr.ShutterTriggerCount = int(value)

    @property
    def shutterTriggerDelay(self):
        return self._spidr.ShutterTriggerDelay
    
    @shutterTriggerDelay.setter
    def shutterTriggerDelay(self,value):
        self._spidr.ShutterTriggerDelay = int(value)

    @property
    def triggerPulseCount(self):
        return self._spidr.TdcTriggerCounter


    @property
    def shutterCount(self):
        pass


    #-----------DAC FUNCTIONS----------------
    # TODO: Replace them with meaningful names once I figure out what they mean 
    #       Otherwise just using from Timepix3 Documentation Table 11

    @property
    def Ibias_Preamp_ON(self):
        """nanoAmps"""
        value = self._device.getDac(DacRegisterCodes.Ibias_Preamp_ON)
        return ((value & 0xFF)*20.0)

    @Ibias_Preamp_ON.setter
    def Ibias_Preamp_ON(self,value):
        """nanoAmps"""
        nA = value
        nAint = int(nA/20.0)
        self._device.setDac(DacRegisterCodes.Ibias_Preamp_ON,nAint & 0xFF)
    
    @property
    def Ibias_Preamp_OFF(self):
        """nanoAmps"""
        value = self._device.getDac(DacRegisterCodes.Ibias_Preamp_OFF)
        return ((value & 0xF)*20.0)

    @Ibias_Preamp_OFF.setter
    def Ibias_Preamp_OFF(self,value):
        """nanoAmps"""
        nA = value
        nAint = int(nA/20.0)
        self._device.setDac(DacRegisterCodes.Ibias_Preamp_OFF,nAint & 0xF)

    @property
    def VPreamp_NCAS(self):
        """Volts"""
        value = self._device.getDac(DacRegisterCodes.VPreamp_NCAS)
        return ((value & 0xFF)*5.0)/1000.0

    @VPreamp_NCAS.setter
    def VPreamp_NCAS(self,value):
        """Volts"""
        n = value*1000.0
        nint = int(n/5.0)
        self._device.setDac(DacRegisterCodes.VPreamp_NCAS,nint & 0xFF)    

    @property
    def Ibias_Ikrum(self):
        """nA"""
        value = self._device.getDac(DacRegisterCodes.Ibias_Ikrum)
        return ((value & 0xFF)*240.0)/1000.0

    @Ibias_Ikrum.setter
    def Ibias_Ikrum(self,value):
        """nA"""
        n = value*1000.0
        nint = int(n/240.0)
        self._device.setDac(DacRegisterCodes.Ibias_Ikrum,nint & 0xFF)  

    @property
    def Vfbk(self):
        """V"""
        value = self._device.getDac(DacRegisterCodes.Vfbk)
        return ((value & 0xFF)*5.0)/1000.0

    @Vfbk.setter
    def Vfbk(self,value):
        """V"""
        n = value*1000.0
        nint = int(n/5.0)
        self._device.setDac(DacRegisterCodes.Vfbk,nint & 0xFF)  

    @property
    def Vthreshold_fine(self):
        """mV"""
        value = self._device.getDac(DacRegisterCodes.Vthreshold_fine)
        return ((value & 0x1FF)*500.0)/1000.0

    @Vthreshold_fine.setter
    def Vthreshold_fine(self,value):
        """mV"""
        n = value*1000.0
        nint = int(n/500.0)
        self._device.setDac(DacRegisterCodes.Vthreshold_fine,nint & 0x1FF)  

    @property
    def Vthreshold_coarse(self):
        """V"""
        value = self._device.getDac(DacRegisterCodes.Vthreshold_coarse)
        return ((value & 0xF)*80.0)/1000.0

    @Vthreshold_coarse.setter
    def Vthreshold_coarse(self,value):
        """V"""
        n = value*1000.0
        nint = int(n/80.0)
        self._device.setDac(DacRegisterCodes.Vthreshold_coarse,nint & 0xF)  

    @property
    def Ibias_DiscS1_ON(self):
        """uA"""
        value = self._device.getDac(DacRegisterCodes.Ibias_DiscS1_ON)
        return ((value & 0xFF)*20.0)/1000.0

    @Ibias_DiscS1_ON.setter
    def Ibias_DiscS1_ON(self,value):
        """uA"""
        n = value*1000.0
        nint = int(n/20.0)
        self._device.setDac(DacRegisterCodes.Ibias_DiscS1_ON,nint & 0xFF)  

    @property
    def Ibias_DiscS1_OFF(self):
        """nA"""
        value = self._device.getDac(DacRegisterCodes.Ibias_DiscS1_OFF)
        return ((value & 0xF)*20.0)

    @Ibias_DiscS1_OFF.setter
    def Ibias_DiscS1_OFF(self,value):
        """nA"""
        n = value
        nint = int(n/20.0)
        self._device.setDac(DacRegisterCodes.Ibias_DiscS1_OFF,nint & 0xF)  

    @property
    def Ibias_DiscS2_ON(self):
        """uA"""
        value = self._device.getDac(DacRegisterCodes.Ibias_DiscS2_ON)
        return ((value & 0xFF)*13.0)/1000.0

    @Ibias_DiscS2_ON.setter
    def Ibias_DiscS2_ON(self,value):
        """uA"""
        n = value*1000.0
        nint = int(n/13.0)
        self._device.setDac(DacRegisterCodes.Ibias_DiscS2_ON,nint & 0xFF)  

    @property
    def Ibias_DiscS2_OFF(self):
        """nA"""
        value = self._device.getDac(DacRegisterCodes.Ibias_DiscS2_OFF)
        return ((value & 0xF)*13.0)

    @Ibias_DiscS2_OFF.setter
    def Ibias_DiscS2_OFF(self,value):
        """nA"""
        n = value
        nint = int(n/13.0)
        self._device.setDac(DacRegisterCodes.Ibias_DiscS2_OFF,nint & 0xF)  

    @property
    def Ibias_PixelDAC(self):
        """nA"""
        value = self._device.getDac(DacRegisterCodes.Ibias_PixelDAC)
        return ((value & 0xFF)*1.08)

    @Ibias_PixelDAC.setter
    def Ibias_PixelDAC(self,value):
        """nA"""
        n = value
        nint = int(n/1.08)
        self._device.setDac(DacRegisterCodes.Ibias_PixelDAC,nint & 0xFF)  

    @property
    def Ibias_TPbufferIn(self):
        """uA"""
        value = self._device.getDac(DacRegisterCodes.Ibias_TPbufferIn)
        return ((value & 0xFF)*40.0)/1000.0

    @Ibias_TPbufferIn.setter
    def Ibias_TPbufferIn(self,value):
        """uA"""
        n = value*1000.0
        nint = int(n/40.0)
        self._device.setDac(DacRegisterCodes.Ibias_TPbufferIn,nint & 0xFF) 

    @property
    def Ibias_TPbufferOut(self):
        """uA"""
        value = self._device.getDac(DacRegisterCodes.Ibias_TPbufferOut)
        return float((value & 0xFF))

    @Ibias_TPbufferOut.setter
    def Ibias_TPbufferOut(self,value):
        """uA"""
        n = value
        nint = int(n)
        self._device.setDac(DacRegisterCodes.Ibias_TPbufferOut,nint & 0xFF) 

    @property
    def VTP_coarse(self):
        """V"""
        value = self._device.getDac(DacRegisterCodes.VTP_coarse)*5.0
        return float((value & 0xFF))/1000.0

    @VTP_coarse.setter
    def VTP_coarse(self,value):
        """V"""
        n = value*1000.0
        nint = int(n/5.0)
        self._device.setDac(DacRegisterCodes.VTP_coarse,nint & 0xFF) 
    @property
    def VTP_fine(self):
        """V"""
        value = self._device.getDac(DacRegisterCodes.VTP_fine)*2.5
        return float((value & 0x1FF))/1000.0

    @VTP_fine.setter
    def VTP_fine(self,value):
        """V"""
        n = value*1000.0
        nint = int(n/2.5)
        self._device.setDac(DacRegisterCodes.VTP_fine,nint & 0x1FF) 

    #TODO: Ibias_CP_PLL, PLL_Vcntrl


    def startAcquisition(self):

        self._spidr.resetTimers()
        self._device.t0Sync()
        # self._spidr.resetTimers()
        # if self.shutterTriggerMode == SpidrShutterMode.Auto:
        #     self._spidr.startAutoTrigger()
        # elif self._open_shutter:
        self._spidr.openShutter()
        self.resumeTimer()
        self._shared_acq.value = 1
        print('Starting acquisition')
    def stopAcquisition(self):
        self.pauseTimer()
        self._spidr.closeShutter()
        print('Stopping acqusition')
        self._shared_acq.value = 0
    def resetPixels(self):
        self._device.resetPixels()
    #
    def stopThreads(self):
        self._file_queue.put(('CLOSE'))
        self._packet_sampler.terminate()
        self._packet_processor.terminate()
        self._file_storage.terminate()
        self._data_queue.put(None)
        self._run_timer = False
        print('Joing data thread')
        self._data_thread.join()
        print('Joining timer thread')
        self._timer_thread.join()
def main():


    tpx = TimePixAcq(('192.168.1.10',50000))
    # print(tpx.deviceInfoString)
    # print(tpx.polarity)
    # print (tpx.operationMode)
    # tpx.operationMode = OperationMode.ToAandToT
    # tpx.ShutterTriggerMode = SpidrShutterMode.Open

    # print (tpx.operationMode)
    # print (tpx.grayCounter)
    # print (tpx.testPulse)
    # print (tpx.superPixel)
    # print (tpx.shutterTriggerMode)
    # print (tpx.shutterTriggerFreqMilliHz)
    # print (tpx.shutterTriggerExposureTime)

    # print (tpx.shutterNumOfTriggers)
    # print(tpx.Ibias_Preamp_ON)
    # print (tpx.Ibias_Ikrum)
    # print (tpx.Vfbk)
    tpx.startAcquisition()
    time.sleep(40)
    tpx.stopAcquisition()
    
    tpx.stopThreads()

if __name__=="__main__":
    main()