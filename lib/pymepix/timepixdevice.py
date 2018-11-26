import numpy as np
from .SPIDR.spidrdevice import SpidrDevice
from.timepixdef import *
from .config.sophyconfig import SophyConfig
from .core.log import Logger
class TimepixDevice(Logger):
    """ Provides high level control of a timepix/medipix object



    """


    def __init__(self,spidr_device,data_queue):
        
        self._device = spidr_device
        Logger.__init__(self,'Timepix '+self.devIdToString())
        self._data_queue = data_queue
        self._udp_address = (self._device.ipAddrDest,self._device.serverPort)
        self.info('UDP Address is {}:{}'.format(*self._udp_address))
        self._pixel_offset_coords = (0,0)


    def loadSophyConfig(self,sophyFile):
        sophyconfig = SophyConfig(sophyFile)
        for code,value in sophyconfig.dacCodes():
            self._device.setDac(code,value)
            
    
    def devIdToString(self):
        devId = self._device.deviceId
        waferno = (devId >> 8) & 0xFFF
        id_y = (devId >> 4) & 0xF
        id_x = (devId >> 0) & 0xF
        return "W{:04d}_{}{:02d}".format(waferno,chr(ord('A')+id_x-1),id_y)


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

def main():
    import logging
    from .SPIDR.spidrcontroller import SPIDRController
    logging.basicConfig(level=logging.INFO)

    spidr = SPIDRController(('192.168.1.10',50000))

    timepix = TimepixDevice(spidr[0],None)
    print(timepix.devIdToString())


if __name__=="__main__":
    main()