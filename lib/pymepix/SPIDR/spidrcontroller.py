import socket
import numpy as np
from .error import PymePixException
from .spidrcmds import SpidrCmds
from .spidrdevice import SpidrDevice
from .spidrdefs import SpidrRegs,SpidrShutterMode
class SPIDRController(list):

    def __init__(self,ip_port):

        self._sock = socket.create_connection(ip_port,source_address=('192.168.1.1',0))

        self._req_buffer = np.ndarray(shape=(512,),dtype=np.uint32)
        self._reply_buffer = bytearray(4096)
        self._reply_view = memoryview(self._reply_buffer)

        self._vec_htonl = np.vectorize(self.convertHtonl)
        self._vec_ntohl = np.vectorize(self.convertNtohl)

        self._pixel_config = np.ndarray(shape=(256,256),dtype=np.uint8)

        self._initDevices()
    
    def _initDevices(self):
        
        count = self.deviceCount

        for x in range(count):
            self.append(SpidrDevice(self,x))
        
    def resetModule(self,readout_speed):
        self.requestGetInt(SpidrCmds.CMD_RESET_MODULE,0,readout_speed.value)

    #-----------------Registers-----------------------
    @property
    def CpuToTpx(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_CPU2TPX_WR_I)
    
    @CpuToTpx.setter
    def CpuToTpx(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_CPU2TPX_WR_I,value)
    
        #---------Shutter registers---------
    @property
    def ShutterTriggerCtrl(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_CTRL_I)
    
    @ShutterTriggerCtrl.setter
    def ShutterTriggerCtrl(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_CTRL_I,value)  

    @property
    def ShutterTriggerMode(self):
        return SpidrShutterMode(self.ShutterTriggerCtrl &0x7)
    
    @ShutterTriggerMode.setter
    def ShutterTriggerMode(self,mode):
        reg = self.ShutterTriggerCtrl
        reg &= ~0x7
        reg |= mode.value
        self.ShutterTriggerCtrl = reg



    @property
    def ShutterTriggerCount(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_CNT_I)
    
    @ShutterTriggerCount.setter
    def ShutterTriggerCount(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_CNT_I,value)  

    @property
    def ShutterTriggerFreq(self):
        freq = self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_FREQ_I)

        mhz = 40000000000.0/freq
        
        return int(mhz)
    
    @ShutterTriggerFreq.setter
    def ShutterTriggerFreq(self,mhz):


        freq = 40000000000.0/mhz
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_FREQ_I,freq)  

    @property
    def ShutterTriggerLength(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_LENGTH_I)*25
    
    @ShutterTriggerLength.setter
    def ShutterTriggerLength(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_LENGTH_I,value//25)  

    @property
    def ShutterTriggerDelay(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_DELAY_I)*25
    
    @ShutterTriggerDelay.setter
    def ShutterTriggerDelay(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_DELAY_I,value//25)  
    
    @property
    def DeviceAndPorts(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_DEVICES_AND_PORTS_I)
    
    @property
    def TdcTriggerCounter(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_TDC_TRIGGERCOUNTER_I)
    
    @property
    def UdpPacketCounter(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_UDP_PKTCOUNTER_I)

    @property
    def UdpMonPacketCounter(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_UDPMON_PKTCOUNTER_I)

    @property
    def UdpPausePacketCounter(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_UDPPAUSE_PKTCOUNTER_I)    

    @UdpPacketCounter.setter
    def UdpPacketCounter(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_UDP_PKTCOUNTER_I,0)

    @UdpMonPacketCounter.setter
    def UdpMonPacketCounter(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_UDPMON_PKTCOUNTER_I,0)

    @UdpPausePacketCounter.setter
    def UdpPausePacketCounter(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_UDPPAUSE_PKTCOUNTER_I,0)   

    #---------------------------------------------------

    @property
    def softwareVersion(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_SOFTWVERSION,0)

    @property
    def firmwareVersion(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_FIRMWVERSION,0)

    @property
    def localTemperature(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_LOCALTEMP,0)/1000

    @property
    def remoteTemperature(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_REMOTETEMP,0)/1000

    @property
    def fpgaTemperature(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_FPGATEMP,0)/1000


    @property
    def humidity(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_HUMIDITY,0)

    @property
    def pressure(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_PRESSURE,0)

    @property
    def chipboardFanSpeed(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_FANSPEED,0,0)

    @property
    def spidrFanSpeed(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_FANSPEED,0,1)


    @property
    def avdd(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_AVDD,0,3)/1000)

    @property
    def vdd(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_VDD,0,3)/1000)

    @property
    def dvdd(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_DVDD,0,3)/1000)


    @property
    def avddNow(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_AVDD_NOW,0,3)/1000)

    @property
    def vddNow(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_VDD_NOW,0,3)/1000)

    @property
    def dvddNow(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_DVDD_NOW,0,3)/1000)

    @property
    def deviceCount(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_DEVICECOUNT,0)

    @property
    def deviceIds(self):
        device_count = self.deviceCount
        return self.requestGetInts(SpidrCmds.CMD_GET_DEVICEIDS,0,device_count)


    @property
    def linkCounts(self):
        links = self.DeviceAndPorts

        return ((links &0xF00) >> 8) + 1




    @property
    def chipboardId(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_CHIPBOARDID,0)

    def setBusy(self):
        return self.requestSetInt(SpidrCmds.CMD_SET_BUSY,0,0)

    def clearBusy(self):
        return self.requestSetInt(SpidrCmds.CMD_CLEAR_BUSY,0,0)

    def resetDevices(self):
        self.requestSetInt(SpidrCmds.CMD_RESET_DEVICES,0,0)
    
    def reinitDevices(self):
        self.requestSetInt(SpidrCmds.CMD_REINIT_DEVICES,0,0)


    def setPowerPulseEnable(self,enable):
        self.requestSetInt(SpidrCmds.CMD_PWRPULSE_ENA,0,int(enable))
    
    def setTpxPowerPulseEnable(self,enable):
        self.requestSetInt(SpidrCmds.CMD_TPX_POWER_ENA,0,int(enable))

    def setBiasSupplyEnable(self,enable):
        self.requestSetInt(SpidrCmds.CMD_BIAS_SUPPLY_ENA,0,int(enable))



    @property
    def biasVoltage(self):
        adc_data = self.requestGetInt(SpidrCmds.CMD_GET_SPIDR_ADC,0,1)
        return (((adc_data & 0xFFF)*1500 + 4095) / 4096) / 10
    @biasVoltage.setter
    def biasVoltage(self,volts):
        if volts < 12: volts = 12
        if volts > 104: volts = 104
        
        dac_value = ((volts-12)*4095)/(104-12)
        self.requestSetInt(SpidrCmds.CMD_SET_BIAS_ADJUST,0,dac_value)


    def enableDecoders(self,enable):
        self.requestSetInt(SpidrCmds.CMD_DECODERS_ENA,0,enable)

    def enablePeriphClk80Mhz(self):
        self.CpuToTpx |= ( 1<<24)

    def disablePeriphClk80Mhz(self):
        self.CpuToTpx &= ~(1<<24)
    
    def enableExternalRefClock(self):
        self.CpuToTpx |= ( 1<<25)

    def disableExternalRefClock(self):
        self.CpuToTpx &= ~(1<<25)


    def sequentialReadout(self,tokens,now ):

        if( now ): tokens |= 0x80000000
        self.requestSetInt( SpidrCmds.CMD_SEQ_READOUT, 0, tokens )




    def datadrivenReadout(self):

        self.requestSetInt( SpidrCmds.CMD_DDRIVEN_READOUT, 0, 0 )




    def pauseReadout(self):

        self.requestSetInt( SpidrCmds.CMD_PAUSE_READOUT, 0, 0 )



    def setShutterTriggerConfig(self,mode,length_us,freq_hz,count,delay_ns):

        data =  [mode,length_us,freq_hz,count,delay_ns]

        if delay_ns == 0:
            data.pop()
        
        self.requestSetInts(SpidrCmds.CMD_SET_TRIGCONFIG,0,data)

    @property
    def shutterTriggerConfig(self):
        config = self.requestGetInts(SpidrCmds.CMD_GET_TRIGCONFIG,0,5)

        return tuple(config)

    def startAutoTrigger(self):
        self.requestSetInt(SpidrCmds.CMD_AUTOTRIG_START,0,0)

    def stopAutoTrigger(self):
        self.requestSetInt(SpidrCmds.CMD_AUTOTRIG_STOP,0,0)


    def openShutter(self):
        self.ShutterTriggerMode = SpidrShutterMode.SHUTTERMODE_AUTO
        self.ShutterTriggerCount = 0
        self.ShutterTriggerLength = 10000
        self.ShutterTriggerDelay = 1
        self.startAutoTrigger()
    
    def closeShutter(self):
        self.stopAutoTrigger()

    @property
    def externalShutterCounter(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_EXTSHUTTERCNTR,0)
    
    @property
    def shutterCounter(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_SHUTTERCNTR,0)

    def resetCounters(self):
        self.requestSetInt(SpidrCmds.CMD_RESET_COUNTERS,0,0)

    def resetTimers(self):
        self.requestSetInt(SpidrCmds.CMD_RESET_TIMER,0,0)

    def getAdc(self,channel,nr_of_samples):
        args = (channel & 0xFFFF) | ((nr_of_samples & 0xFFFF) << 16)
        self.requestGetInt(SpidrCmds.CMD_GET_SPIDR_ADC,0,args)





    def resetPacketCounters(self):
        self.UdpPacketCounter = 0
        self.UdpMonPacketCounter = 0
        self.UdpPausePackerCounter = 0
        for idx,dev in enumerate(self):
            self.setSpidrReg(SpidrRegs.SPIDR_PIXEL_PKTCOUNTER_I,idx)


    
    def getSpidrReg(self,addr):
        res = self.requestGetInts(SpidrCmds.CMD_GET_SPIDRREG,0,2,addr)
        if res[0] != addr:
            raise Exception('Incorrect register address returned {} expected {}'.format(res[0],addr))
        
        return res[1]


    def setSpidrReg(self,addr,value):
        self.requestSetInts(SpidrCmds.CMD_SET_SPIDRREG,0,[addr,value])


    def request(self,cmd,dev_nr,message_length,expected_bytes):

        self._req_buffer[0] = socket.htonl(cmd)
        self._req_buffer[1] = socket.htonl(message_length)
        self._req_buffer[2] = 0
        self._req_buffer[3] = socket.htonl(dev_nr)

        self._sock.send(self._req_buffer.tobytes()[0:message_length])

        if cmd & SpidrCmds.CMD_NOREPLY: return
        
        bytes_returned = self._sock.recv_into(self._reply_view,4096)

        if bytes_returned < 0:
            raise Exception('Failed to get reply')
        
        if bytes_returned < expected_bytes:
            raise Exception("Unexpected reply length, got {} expected at least {}".format(bytes_returned,expected_bytes))


        _replyMsg = np.frombuffer(self._reply_buffer,dtype=np.uint32)
        error = socket.ntohl(int(_replyMsg[2]))
        if error != 0:
            raise PymePixException(error)


        reply = socket.ntohl(int(_replyMsg[0]))

        if reply != cmd | SpidrCmds.CMD_REPLY:
            raise Exception('Unexpected Reply {}'.format(reply))

        if socket.ntohl(int(_replyMsg[3])) != dev_nr:
            raise Exception('Unexpected device {}'.format(dev_nr))
        
        return _replyMsg


    def customRequest(self,request,total_bytes):
        self._sock.send(self._req_buffer.tobytes()[0:total_bytes])
        sock_recv= self._sock.recv(4096)
        missing_bytes = ((len(sock_recv)//32) + 1)*32
        buffer = sock_recv + b" "*missing_bytes

        arr = np.frombuffer(buffer,dtype=np.uint32)
        print(self._vec_ntohl(arr))
    def convertNtohl(self,x):
        return socket.ntohl(int(x))

    def convertHtonl(self,x):
        return socket.htonl(int(x))

    def requestGetInt(self,cmd,dev_nr,arg=0):
        msg_length = 20
        self._req_buffer[4] = socket.htonl(arg)

        reply = self.request(cmd,dev_nr,msg_length,msg_length)

        return socket.ntohl(int(reply[4]))

    def requestGetInts(self,cmd,dev_nr,num_ints,args=0):
        msg_length = 20
        self._req_buffer[4] = socket.htonl(args)
        expected_len = (4 + num_ints)*4

        reply = self.request(cmd,dev_nr,msg_length,expected_len)

        return self._vec_ntohl(reply[4:4+num_ints])

    def requestGetBytes(self,cmd,dev_nr,expected_bytes,args=0):
        msg_length = (4+1)*4
        self._req_buffer[4]=0
        expected_len = 16 + expected_bytes
        #Cast reply as an uint8
        reply = self.request(cmd,dev_nr,msg_length,expected_len)
        return np.copy(reply[4:].view(dtype=np.uint8)[:expected_bytes])

    def requestGetIntBytes(self,cmd,dev_nr,expected_bytes,args=0):
        msg_length = (4+1)*4
        self._req_buffer[4]=socket.htonl(args)
        expected_len = 20 + expected_bytes
        #Cast reply as an uint8
        int_total = expected_bytes + ((expected_bytes) & 5)
        reply = self.request(cmd,dev_nr,msg_length,expected_len)
        int_val = socket.ntohl(int(reply[4]))

        byte_val = np.copy(reply[5:].view(dtype=np.uint8)[:expected_bytes])

        return int_val,byte_val
    
    def requestSetInt(self,cmd,dev_nr,value):
        msg_length = (4+1)*4
        self._req_buffer[4] = socket.htonl(value)

        self.request(cmd,dev_nr,msg_length,20)


    def requestSetInts(self,cmd,dev_nr,value):
        num_ints = len(value)
        msg_length = (4+num_ints)*4

        self._req_buffer[4:4+num_ints] = self._vec_htonl(value)[:]

        self.request(cmd,dev_nr,msg_length,20)

    def requestSetIntBytes(self,cmd,dev_nr,value_int,value_bytes):
        num_bytes = len(value_bytes)
        msg_length = (4+1)*4 + num_bytes
        self._req_buffer[4] = socket.htonl(value_int)

        self._req_buffer[5:].view(dtype=np.uint8)[:num_bytes] = value_bytes[:]

        self.request(cmd,dev_nr,msg_length,20)

    


def main():
    import cv2
    import matplotlib.pyplot as plt
    spidr = SPIDRController(('192.168.1.10',50000))
    print('Local temp: {} C'.format(spidr.localTemperature))

    print ('FW: {:8X}'.format(spidr.firmwareVersion))
    print ('SW: {:8X}'.format(spidr.softwareVersion))
    print ('Device Ids {}'.format(spidr.deviceIds))
    for idx,dev in enumerate(spidr):
        print ("Device {}: {}".format(idx,dev.deviceId))
    
    print ('CHIP Fanspeed: ',spidr.chipboardFanSpeed)
    print ('SPIDR Fanspeed: ',spidr.spidrFanSpeed)
    print ('Pressure: ',spidr.pressure, 'mbar')
    print ('Humidity: ',spidr.humidity,'%')
    print ('Temperature: ',spidr.localTemperature,' C')
    print (spidr[0].ipAddrSrc)
    print (spidr[0].ipAddrDest)
    print (spidr[0].devicePort)
    print(spidr[0].serverPort)
    print (spidr[0].headerFilter)
    # print ('Link COunts : ',spidr.linkCounts)
    # spidr[0].reset()
    # spidr[0].reinitDevice()
    # spidr[0].resetPixels()


    # image = cv2.imread('images.png', cv2.IMREAD_GRAYSCALE)
    # res_im = cv2.resize(image,(256,256))
    # res_im = res_im/256
    # res_im *= 16

    # spidr[0].setPixelThreshold(res_im.astype(np.uint8))
    # spidr[0].uploadPixelConfig(True,1)
    spidr[0].getPixelConfig()
    # print(spidr.vddNow)
    plt.matshow(spidr[0].currentPixelConfig)
    plt.show()

if __name__=="__main__":
    main()

