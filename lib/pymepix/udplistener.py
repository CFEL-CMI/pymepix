import socket
import numpy as np
import threading
from .timepixdef import PacketType
import time
class TimepixUDPListener(threading.Thread):

    def __init__(self,udpipport,queue=None):
        threading.Thread.__init__(self)
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
        #reserved = trigger_data & 0x1F
        stamp = (trigger_data >> 5) &0xF
        timestamp = (trigger_data >> 9) & 0x7FFFFFFFF
        trigger_counter = (trigger_data>>44) &0xFFF
        if self._queue is not None:
            self._queue.put((PacketType.Trigger,(trigger_counter,timestamp,stamp)))
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
        print('TOA:',toa,(toa<<4).astype(np.float)*1.5625/1000.0)
        if self._queue is not None:
            self._queue.put((PacketType.Pixel,(x,y,toa,tot,hit,ts)))

    def run(self):

        while self._run:
            if not self._in_acq:
                
                continue


            
            size = self._sock.recv_into(self._raw_bytes,16384) # buffer size is 1024 bytes
            start = time.time()
            raw_bytes = self._raw_bytes[0:size//8]
            self._packets_collected+=1

            # #print (np.unpackbits(raw_bytes.view(dtype=np.uint8))[0:64])
            # #arr= raw_bytes.view(dtype='<I')
            # #print (raw_bytes)
            #Numpyize it!!!
            
            trigger_header = raw_bytes &  0x6F00000000000000
            trigger_data = raw_bytes[trigger_header!= 0]
            if trigger_data.size !=0:
                self.processTriggers(trigger_data)

            header = raw_bytes &  0xF000000000000000

            pixdata = raw_bytes[np.logical_or(header == 0xB000000000000000,header == 0xA000000000000000)]
            if pixdata.size !=0:
                self.processPixels(pixdata)
            self._total_time+= time.time()-start
            self._calls +=1


if __name__=="__main__":
    from .SPIDR.spidrcontroller import SPIDRController
    import time
    from pyqtgraph.Qt import QtGui, QtCore
    import numpy as np
    import pyqtgraph as pg
    spidr = SPIDRController(('192.168.1.10',50000))
    print('Local temp: {} C'.format(spidr.localTemperature))

    UDP_IP = spidr[0].ipAddrDest
    UDP_PORT = spidr[0].serverPort

    print(UDP_IP,UDP_PORT)

    # spidr[0].reset()
    #spidr[0].reinitDevice()
    # spidr.resetTimers()
    # eth,cpu = spidr[0].headerFilter
    # #spidr[0].setHeaderFilter(0xFFFF,cpu)
    # eth,cpu = spidr[0].headerFilter
    #print ('{:4X}'.format(eth))
    spidr.resetPacketCounters()
    spidr.datadrivenReadout()
    #print(spidr.chipboardId)
    #spidr[0].getPixelConfig()
    #print (spidr[0].currentPixelConfig)
    #plt.matshow(spidr[0].currentPixelConfig)
    #plt.show()
    #spidr.startAutoTrigger()


    def print_data(x,y,toa,tot,hit,ts):
        print('X:',x,'Y:',y,'TOA:',toa,'TOT:',tot,'HIT',hit,'TS:',ts)

    spidr.openShutter()
    time_spent = 0
    calls = 0

    udp_thread = TimepixUDPListener((UDP_IP,UDP_PORT))
    udp_thread.startAcquisition()
    try:
        while True:
            udp_thread.run()
    except:
        pass
    finally:
        udp_thread.stopRunning()
        print('Packets Collected: {}'.format(udp_thread.packetsCollected))
        print('Packet Counters: {} {} {} PIXEL: {} '.format(spidr.UdpPacketCounter,spidr.UdpMonPacketCounter,spidr.UdpPausePacketCounter,spidr[0].pixelPacketCounter))
        #spidr.closeShutter()

