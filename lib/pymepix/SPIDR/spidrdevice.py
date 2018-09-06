import weakref
from spidrcmds import SpidrCmds
import numpy as np
from spidrdefs import SpidrRegs
class SpidrDevice(object):

    def __init__(self,spidr_ctrl,device_num):
        self._ctrl = weakref.proxy(spidr_ctrl)
        self._dev_num = device_num
        self._pixel_config = np.ndarray(shape=(256,256),dtype=np.uint8)

        self._cptr = self.cptr
    @property
    def deviceId(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_DEVICEID,self._dev_num)

    def pixelConfig(self):

        for x in range(256):
            row,pixelcolumn = self._ctrl.requestGetIntBytes(SpidrCmds.CMD_GET_PIXCONF,self._dev_num,256,x)
            #print ('Column : {} Pixels: {}'.format(row,pixelcolumn))
            self._pixel_config[row,:] = pixelcolumn[:]
    

    @property
    def headerFilter(self):
        mask = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_HEADERFILTER,self._dev_num)

        eth_mask = mask &0xFFFF
        cpu_mask = (mask>>16) &0xFFFF

        return eth_mask,cpu_mask
    
    def setHeaderFilter(self,eth_mask,cpu_mask):
        to_write = (eth_mask &0xFFFF) | ((cpu_mask & 0xFFFF)<<16)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_HEADERFILTER,self._dev_num,to_write)

    
    def reset(self):
        self._ctrl.requestSetInt(SpidrCmds.CMD_RESET_DEVICE,self._dev_num,0)
    
    def reinitDevice(self):
        self._ctrl.requestSetInt(SpidrCmds.CMD_REINIT_DEVICE,self._dev_num,0)

    def setSenseDac(self,dac_code):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_SENSEDAC,self._dev_num,dac_code)
    
    def setExternalDac(self,dac_code,dac_val):
        dac_data = ((dac_code &0xFFFF) << 16) | (dac_val & 0xFFFF)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_EXTDAC,self._dev_num,dac_data)
    
    def getDac(self,dac_code):
        
        dac_data = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_DAC,self._dev_num,dac_code)

        if (dac_data >> 16)&0xFFFF != dac_code:
            raise Exception('DAC code mismatch')
        
        return dac_data & 0xFFFF
    
    def setDac(self,dac_code,dac_val):
        dac_data = ((dac_code &0xFFFF) << 16) | (dac_val & 0xFFFF)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_DAC,self._dev_num,dac_data)
    
    def setDacDefault(self):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_DACS_DFLT,self._dev_num)
    
    @property
    def genConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_GENCONFIG,self._dev_num)
    
    @genConfig.setter
    def genConfig(self,value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_GENCONFIG,self._dev_num,value)

    
    @property
    def pllConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_PLLCONFIG,self._dev_num)

    @pllConfig.setter
    def pllConfig(self,value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_PLLCONFIG,self._dev_num,value)


    @property
    def outBlockConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_OUTBLOCKCONFIG,self._dev_num)

    @outBlockConfig.setter
    def outBlockConfig(self,value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_OUTBLOCKCONFIG,self._dev_num,value)

    
    def setOutputMask(self,value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_OUTPUTMASK,self._dev_num,value)
    
    @property
    def readoutSpeed(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_READOUTSPEED,self._dev_num)
    
    @readoutSpeed.setter
    def readoutSpeed(self,mbits):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_READOUTSPEED,self._dev_num,mbits)
    
    @property
    def linkStatus(self):
        reg_addr = SpidrRegs.SPIDR_FE_GTX_CTRL_STAT_I + (self._dev_num<<2)
        status = self._ctrl.getSpidrReg(reg_addr)

        enabled = (~status) & 0xFF
        locked = (status & 0xFF0000) >> 16

        return status,enabled,locked
    

    @property
    def slaveConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_SLVSCONFIG,self._dev_num)
    
    @slaveConfig.setter
    def slaveConfig(self,value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_GET_SLVSCONFIG,self._dev_num,value)


    @property
    def powerPulseConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_PWRPULSECONFIG,self._dev_num)
    
    @powerPulseConfig.setter
    def powerPulseConfig(self,value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_GET_PWRPULSECONFIG,self._dev_num,value)
    

    def uploadPacket(self,packet):
        self._ctrl.requestSetIntBytes(SpidrCmds.CMD_UPLOAD_PACKET,self._dev_num,len(packet),packet)

    
    @property
    def TpPeriodPhase(self):
        tp_data = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_TPPERIODPHASE,self._dev_num)

        return tp_data&0xFFFF,(tp_data>>16)&0xFFFF
    
    def setTpPeriodPhase(self,period,phase):
        tp_data = ((phase & 0xFFFF) << 16) | (period & 0xFFFF)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_TPPERIODPHASE,self._dev_num,tp_data)
    
    @property
    def tpNumber(self):
       tp_data = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_TPNUMBER,self._dev_num) 
    
    @tpNumber.setter
    def tpNumber(self,value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_TPNUMBER,self._dev_num,value)

    @property
    def cptr(self):
        _cptr = self._ctrl.requestGetBytes(SpidrCmds.CMD_GET_CTPR,self._dev_num,256//8)
        #Store it locally for use
        self._cptr = _cptr
        return _cptr
    
    @cptr.setter
    def cptr(self,_cptr):
        self._ctrl.requestSetIntBytes(SpidrCmds.CMD_SET_CTPR,self._dev_num,0,_cptr)
        self._cptr = self.cptr
