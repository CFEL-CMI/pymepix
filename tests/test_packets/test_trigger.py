import socket
import numpy as np
import threading
import time
class TimepixUDPListener(object):

    def __init__(self,udpipport,print_triggers=True,print_pixels=True,queue=None):
        #threading.Thread.__init__(self)
        self._sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        self._sock.bind(udpipport)

        self.reset()
        self._run = True

        self._raw_bytes = np.ndarray(shape=(2048,),dtype='<u8')

        self._queue = queue

        self._in_acq = False
        self._total_time = 0
        self._calls = 0
        self._print_triggers = print_triggers
        self._print_pixels = print_pixels

    def reset(self):
        self.stopRunning()
        self._packets_collected = 0


    def startAcquisition(self):
        self._in_acq = True
        self._total_time = 0
        self._calls = 0
    def stopAcquisition(self):
        self._in_acq = False
        
        avg = self._total_time/self._calls
        print ('Total time taken {} s Calls {} Avg: {} Rate {} Hz'.format(self._total_time,self._calls,avg,1/avg))

    @property
    def packetsCollected(self):
        return self._packets_collected
    
    def stopRunning(self):
        self._run = False


    


    def processTriggers(self,trigger_data):
        #Get only the trigger
        subheader = ((trigger_data & 0x0F00000000000000) >> 56) & 0xF
        trigger_data = trigger_data[subheader == 0xF]
        if trigger_data.size == 0:
            return
        #reserved = trigger_data & 0x1F
        trigger_counter = ((trigger_data & 0x00FFF00000000000) >> 44) & 0xFFF
        timestamp = ((trigger_data & 0x00000FFFFFFFF000) >> 12) & 0xFFFFFFFF
        stamp = (trigger_data >> 5 ) & 0xF
        if self._print_triggers:
            print('Detected trigger')
            print('Counter: {} Timestamp: {} Stamp: {}'.format(trigger_counter,timestamp,stamp))

    def processPixels(self,pixdata):
        dcol = ((pixdata & 0x0FE0000000000000) >> 52)
        spix  = ((pixdata & 0x001F800000000000) >> 45)
        pix   = ((pixdata & 0x0000700000000000) >> 44)
        pdata = ((pixdata & 0x00000FFFFFFF0000) >> 16)
        toa = (pdata >>14) &0x3FFF
        tot = (pdata >>4) & 0x3FF
        hit = pdata &0xF
        ts = (pixdata & 0x000000000000FFFF)
        x = dcol + pix//4
        y = spix + (pix &0x3)
        if self._print_pixels:
            print('Pixel data: x {} y {} toa: {}'.format(x,y,toa))
        #print('TOA:',toa,(toa<<4).astype(np.float)*1.5625/1000.0)

    def run(self):

        while self._run:


            
            size = self._sock.recv_into(self._raw_bytes,16384) # buffer size is 1024 bytes
            start = time.time()
            raw_bytes = self._raw_bytes[0:size//8]
            self._packets_collected+=1

            
            header = ((raw_bytes & 0xF000000000000000) >> 60) & 0xF
            #Handle trigger packets
            trigger_data = raw_bytes[np.logical_or(header == 0x4,header==0x6)]
            if trigger_data.size !=0:
                self.processTriggers(trigger_data)

            #Handle pixel packets
            pixdata = raw_bytes[np.logical_or(header == 0xA,header==0xB)]
            if pixdata.size !=0:
                self.processPixels(pixdata)
            self._total_time+= time.time()-start
            self._calls +=1
def deviceInfoString(spidr):

    output_string = "-------------------SPIDR Board Info----------------------\n"
    output_string += "\tFW version: {:8X}\n SW Version: {:8X}\n".format(spidr.firmwareVersion,spidr.softwareVersion)
    output_string += "\tNumber of devices: {} \nDevice Ids: {}\n".format(len(spidr),spidr.deviceIds)
    output_string += "\tPressure: {} mbar\n Temperature {}".format(spidr.pressure,spidr.localTemperature)

    return output_string

if __name__=="__main__":
    from SPIDR.spidrcontroller import SPIDRController
    import time
    import numpy as np
    spidr = SPIDRController(('192.168.1.10',50000))
    print(deviceInfoString(spidr))

    UDP_IP = spidr[0].ipAddrDest
    UDP_PORT = spidr[0].serverPort



    spidr.resetPacketCounters()
    spidr.datadrivenReadout()



    spidr.openShutter()
    time_spent = 0
    calls = 0

    udp_thread = TimepixUDPListener((UDP_IP,UDP_PORT),print_pixels=False)
    print('Started acquisition')
    udp_thread.run()

