from .SPIDR.spidrcontroller import SPIDRController
from .udplistener import TimepixUDPListener
import numpy as np
from .timepixdef import *
from .SPIDR.spidrdefs import SpidrShutterMode
import time
import queue
import threading
class TimePixAcq(object):


    def updateTimer(self):

        while self._run_timer:
            self._timer = self._device.timer
            time.sleep(1.0)
    
    def dataThread(self):

        while True:
            value = self._data_queue.get()
            if value is None:
                break
            if value[0]==PacketType.Trigger:
                self.onTrigger(value[1])
            elif value[0]==PacketType.Pixel:
                self.onPixel(value[1])


    def __init__(self,ip_port,device_num=0):
        self._spidr = SPIDRController(ip_port)

        self._device = self._spidr[device_num]
        self._device.reset()
        self._device.reinitDevice()

        self._device.getPixelConfig()

        UDP_IP = self._device.ipAddrDest
        UDP_PORT = self._device.serverPort

        self._data_queue = queue.Queue()

        self._udp_listener = TimepixUDPListener((UDP_IP,UDP_PORT),self._data_queue)
        self._udp_listener.start()

        self._run_timer = True

        self._timer = 0
        self._timer_thread = threading.Thread(target = self.updateTimer)
        self._timer_thread.start()

        self._data_thread = threading.Thread(target=self.dataThread)
        self._data_thread.start()


    @property
    def deviceInfoString(self):

        output_string = "-------------------SPIDR Board Info----------------------\n"
        output_string += "\tFW version: {:8X}\n SW Version: {:8X}\n".format(self._spidr.firmwareVersion,self._spidr.softwareVersion)
        output_string += "\tNumber of devices: {} \nDevice Ids: {}\n".format(len(self._spidr),self._spidr.deviceIds)
        output_string += "\tPressure: {} mbar\n Temperature {}".format(self._spidr.pressure,self._spidr.localTemperature)

        return output_string





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
        self._device.setPixelThreshold(threshold)
    
    @property
    def pixelMask(self):
        #self._device.getPixelConfig()
        pixel_config = self._device.currentPixelConfig
        return pixel_config&0x1

    @pixelMask.setter
    def pixelMask(self,mask):
        self._device.setPixelMask(mask)
    

    def uploadPixels(self):
        self._device.uploadPixels()
    
    def refreshPixels(self):
        self._device.getPixelConfig()

    
    @property
    def shutterTriggerMode(self):
        return self._spidr.ShutterTriggerMode
    @shutterTriggerMode.setter
    def shutterTriggerMode(self,value):
        self._spidr.ShutterTriggerMode = value

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
    def shutterCount(self):
        pass


    def startAcquisition(self):
        self._spidr.datadrivenReadout()
        if self.shutterTriggerMode == SpidrShutterMode.Auto:
            self._spidr.startAutoTrigger()
        self._udp_listener.startAcquisition()
    def stopAcquisition(self):

        if self.shutterTriggerMode == SpidrShutterMode.Auto:
            self._spidr.stopAutoTrigger()

        self._udp_listener.stopAcquisition()
    def resetPixels(self):
        self._device.resetPixels()
    #
    def stopThreads(self):
        self._udp_listener.stopRunning()
        self._udp_listener.join()
        self._run_timer = False
        self._data_queue.put(None)
        self._timer_thread.join()
        self._data_thread.join()

def main():

    try:
        tpx = TimePixAcq(('192.168.1.10',50000))
        print(tpx.deviceInfoString)
        print(tpx.polarity)
        print (tpx.operationMode)
        #tpx.operationMode = OperationMode.ToAandToT
        print (tpx.operationMode)
        print (tpx.grayCounter)
        print (tpx.testPulse)
        print (tpx.superPixel)
        tpx.shutterTriggerMode=SpidrShutterMode.Auto
        tpx.shutterTriggerFreqMilliHz = 10000000
        print (tpx.shutterTriggerMode)
        print (tpx.shutterTriggerFreqMilliHz)
        print (tpx.shutterTriggerExposureTime)
        print (tpx.shutterNumOfTriggers)

        tpx.startAcquisition()
        while True:
            continue

    except Exception as e:
        print(str(e))
    finally:
        tpx.stopAcquisition()
        tpx.stopThreads()


    

if __name__=="__main__":
    main()