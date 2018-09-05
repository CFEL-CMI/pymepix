import socket
import numpy as np
from error import PymePixException
from spidrcmds import SpidrCmds
class SPIDRController(object):

    def __init__(self,ip_port):

        self._sock = socket.create_connection(ip_port,source_address=('192.168.1.1',0))

        self._req_buffer = np.ndarray(shape=(512,),dtype=np.uint32)
        self._reply_buffer = bytearray(4096)
        self._reply_view = memoryview(self._reply_buffer)

        self._vec_htonl = np.vectorize(self.convertHtonl)
        self._vec_ntohl = np.vectorize(self.convertNtohl)
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
    def deviceCount(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_DEVICECOUNT,0)

    @property
    def deviceIds(self):
        device_count = self.deviceCount
        return self.requestGetInts(SpidrCmds.CMD_GET_DEVICEIDS,0,device_count)


    def getDeviceId(self,device_nr):
        return self.requestGetInt(SpidrCmds.CMD_GET_DEVICEID,device_nr)

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



def main():
    spidr = SPIDRController(('192.168.1.10',50000))
    print('Local temp: {} C'.format(spidr.localTemperature))

    print ('FW: {:8X}'.format(spidr.firmwareVersion))
    print ('SW: {:8X}'.format(spidr.softwareVersion))
    print ('Device Ids {}'.format(spidr.deviceIds))
    for x in range(spidr.deviceCount):
        print ("Device {}: {}".format(x,spidr.getDeviceId(x)))
if __name__=="__main__":
    main()

