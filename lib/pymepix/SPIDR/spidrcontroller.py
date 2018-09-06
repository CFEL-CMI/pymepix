import socket
import numpy as np
from error import PymePixException
from spidrcmds import SpidrCmds
from spidrdevice import SpidrDevice
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
    def deviceCount(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_DEVICECOUNT,0)

    @property
    def deviceIds(self):
        device_count = self.deviceCount
        return self.requestGetInts(SpidrCmds.CMD_GET_DEVICEIDS,0,device_count)





    def getSpidrReg(self,addr):
        res = self.requestGetInts(SpidrCmds.CMD_GET_SPIDRREG,0,2,addr)
        if socket.ntohl(res[0]) != addr:
            raise Exception('Incorrect register address returned {} expected {}'.format(socket.ntohl(res[0]),addr))
        
        return socket.ntohl(res[1])


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

        self.request(cmd,dev_nr,msg_length,msg_length)


    def requestSetInts(self,cmd,dev_nr,value):
        num_ints = len(value)
        msg_length = (4+num_ints)*4

        self._req_buffer[4:4+num_ints] = self._vec_htonl(value)[:]

        self.request(cmd,dev_nr,msg_length,msg_length)

    def requestSetIntBytes(self,cmd,dev_nr,value_int,value_bytes):
        num_bytes = len(value_bytes)
        msg_length = (4+1)*4 + num_bytes
        self._req_buffer[4] = socket.htonl(value_int)

        self._req_buffer[5:].view(dtype=np.uint8)[:num_bytes] = value_bytes[:]

        self.request(cmd,dev_nr,msg_length,msg_length)
def main():
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
    spidr[0].pixelConfig
    #plt.matshow()
    #plt.show()

if __name__=="__main__":
    main()

