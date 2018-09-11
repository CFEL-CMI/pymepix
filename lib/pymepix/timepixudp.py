import socket
import numpy as np
import threading
class TimepixUDPListener(threading.Thread):

    def __init__(self,udpipport):
        threading.Thread.__init__(self)
        self._sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        self._sock.bind(udpipport)

        self.reset()
        self._run = True

        self.attachCallback(None)
    def reset(self):
        self.stop()
        self._packets_collected = 0


    def attachCallback(self,callback):
        self._callback = callback

    @property
    def packetsCollected(self):
        return self._packets_collected
    
    def stop(self):
        self._run = False


    def run(self):

        while self._run:
            data, addr = self._sock.recvfrom(2*16384) # buffer size is 1024 bytes
            raw_bytes =  np.frombuffer(data,dtype='u8')
            self._packets_collected+=1
            #print (np.unpackbits(raw_bytes.view(dtype=np.uint8))[0:64])
            #arr= raw_bytes.view(dtype='<I')
            #print (raw_bytes)
            #Numpyize it!!!
            header = raw_bytes &  0xF000000000000000

            pixdata = raw_bytes[np.logical_or(header == 0xB000000000000000,header == 0xA000000000000000)]
            if pixdata.size ==0:
                continue
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

            if self._callback is not None:
                self._callback(x,y,toa,tot,hit,ts)

def print_data(x,y,toa,tot,hit,ts):
    print(x,y,toa,tot,hit,ts)



if __name__=="__main__":
    from SPIDR.spidrcontroller import SPIDRController
    import time
    from pyqtgraph.Qt import QtGui, QtCore
    import numpy as np
    import pyqtgraph as pg
    app = QtGui.QApplication([])
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

    spidr.datadrivenReadout()
    #print(spidr.chipboardId)
    #spidr[0].getPixelConfig()
    #print (spidr[0].currentPixelConfig)
    #plt.matshow(spidr[0].currentPixelConfig)
    #plt.show()
    #spidr.startAutoTrigger()

    win = QtGui.QMainWindow()
    win.resize(256,256)
    imv = pg.ImageView()
    win.setCentralWidget(imv)
    win.show()
    win.setWindowTitle('pyqtgraph example: ImageView')

    def imageViewData(x,y,toa,tot,hit,ts):
        mat = np.zeros(shape=(256,256))
        mat[x,y]=1.0
        imv.setImage(mat,xvals=x)

    spidr.openShutter()
    time_spent = 0
    calls = 0

    udp_thread = TimepixUDPListener((UDP_IP,UDP_PORT))
    udp_thread.attachCallback(imageViewData)
    udp_thread.start()
    try:
        QtGui.QApplication.instance().exec_()
    except:
        pass
    finally:
        udp_thread.stop()
        print('Packets Collected: {}'.format(udp_thread.packetsCollected))
        udp_thread.join()

