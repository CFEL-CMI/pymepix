from .SPIDR.spidrcontroller import SPIDRController
from .udplistener import TimepixUDPListener
import numpy as np
from .timepixdef import *

class TimePixAcq(object):


    def __init__(self,ip_port,device_num=0):
        self._spidr = SPIDRController(ip_port)

        self._device = self._spidr[device_num]
        self._device.reset()
        self._device.reinitDevice()

        self._device.getPixelConfig()

        UDP_IP = self._device.ipAddrDest
        UDP_PORT = self._device.serverPort

        self._udp_listener = TimepixUDPListener((UDP_IP,UDP_PORT))


    @property
    def deviceInfoString(self):

        output_string = "-------------------SPIDR Board Info----------------------\n"
        output_string += "\tFW version: {:8X} SW Version: {:8X}\n".format(self._spidr.firmwareVersion,self._spidr.softwareVersion)
        output_string += "\tNumber of devices: {} Device Ids: {}\n".format(len(self._spidr),self._spidr.deviceIds)
        output_string += "\tPressure: {} mbar".format(self._spidr.pressure)

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

    
    


    def startAcquisition(self):
        self._spidr.openShutter()
    
    def stopAcquisition(self):
        self._spidr.closeShutter()
    
    def resetPixels(self):
        self._device.resetPixels()
    #

def main():
    tpx = TimePixAcq(('192.168.1.10',50000))
    print(tpx.deviceInfoString)
    print (tpx.polarity)
    tpx.polarity = Polarity.Negative
    print(tpx.polarity)
    print (tpx.operationMode)
    tpx.operationMode = OperationMode.EventiTot
    print (tpx.operationMode)
    print (tpx.grayCounter)
    print (tpx.testPulse)
    print (tpx.superPixel)

    

if __name__=="__main__":
    main()