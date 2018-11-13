from .packetprocessor import PacketProcessor
import numpy as np


class FakePacket(object):



    def __init__(self,filename,output_queue=None,file_queue=None):

        self._filename = filename
        self._current_time = 0
        self._output_queue = output_queue
        #print('QUEUE',self._output_queue)
        self._file_queue = file_queue

        self.openFile()
    def openFile(self):

        self._file = open(self._filename,'rb')
        #Find longtime
        #Read about 8 mb
        buffer = self._file.read(8192*100)
        packet = np.frombuffer(buffer,dtype=np.uint64)
        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF
    


        trigger_header = (header==0x4)|(header==0x6)
        lsb_time_filter =trigger_header & (subheader == 0x4)
        msb_time_filter = trigger_header & (subheader == 0x5)
        lsb = int(packet[lsb_time_filter][0])
        msb = int(packet[msb_time_filter][0])


        #Move it back by one second
        self._current_time = int(self.compute_new_time(lsb,msb)- (1E9//25))
        print(self._current_time*25E-9)

        self._file.seek(0)
        


    def run(self):


        buffer = self._file.read(8192*10000) # buffer size is 1024 bytes
        
        while buffer:
            packet = np.frombuffer(buffer,dtype=np.uint64)
            #self._file_queue.put(('WRITE',raw_packet))
            header = ((packet & 0xF000000000000000) >> 60) & 0xF
            subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

            trigger_header = (header==0x4)|(header==0x6)
            lsb_time_filter =np.where(trigger_header & (subheader == 0x4))[0]
            msb_time_filter = np.where(trigger_header & (subheader == 0x5))[0]
            #print(msb_time_filter)
            start_index = 0

            if lsb_time_filter.size > 0 and msb_time_filter.size > 0:
                
                for x in range(min(lsb_time_filter.size,msb_time_filter.size)):
                    
                    end_index = msb_time_filter[x]
                    _packet = packet[start_index:end_index]
                    self.upload_packet(_packet)

                    lsb = packet[lsb_time_filter[x]]
                    msb = packet[msb_time_filter[x]]
                    self._current_time = self.compute_new_time(lsb,msb)
                    start_index = end_index
                    #print(self._current_time*25E-9)
                self.upload_packet(packet[start_index:])

            else:
                self.upload_packet(packet)               
            buffer = self._file.read(8192*10000)
        # self._output_queue.put(None)
    
    def upload_packet(self,packet):
        #Get the header
        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF
        pix_filter = (header ==0xA) |(header==0xB) 
        trig_filter =  ((header==0x4)|(header==0x6) & (subheader == 0xF))
        tpx_filter = pix_filter | trig_filter
        tpx_packets = packet[tpx_filter]
        #print(tpx_packets)
        if tpx_packets.size > 0 and self._output_queue is not None:
            #print('UPLOADING')
            self._output_queue.put((tpx_packets,self._current_time))

    def compute_new_time(self,lsb,msb):
        pixdata = int(lsb)
        longtime_lsb = (pixdata & 0x0000FFFFFFFF0000) >> 16
        pixdata = int(msb)
        longtime_msb = (pixdata & 0x00000000FFFF0000) << 16
        tmplongtime = (longtime_msb | longtime_lsb)
        return tmplongtime

def goodPart(queue,plt2):
    import time
    hy = None
    hx = None

    start = time.time()
    print('HISTO')
    for event in iter(queue.get, None):
        #print('Found event')
        triggers,x,y,toa,tot,mapping = event
        trg_idx,toa_idx = mapping

        tof = toa[toa_idx]-triggers[trg_idx]
        _y,_x = np.histogram(tof.flatten(),np.linspace(52E-6,58E-6,1000))
        if hy is None:
            hy = _y
            hx = _x
        else:
            hy+=_y
        
        end = time.time()
        if (end-start) > 2:
            print('Event ')
            plt2.setData(x=hx, y=hy, stepMode=True, fillLevel=0, brush=(0,0,255,150))
            start = end
    plt2.setData(x=hx, y=hy, stepMode=True, fillLevel=0, brush=(0,0,255,150))
    print('DONE')

def main():
    from multiprocessing import Queue
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore, QtGui
    import threading
    # win = pg.GraphicsWindow()
    # win.resize(800,350)
    # win.setWindowTitle('pyqtgraph example: Histogram')
    # plt1 = win.addPlot()    
    # plt1.setLabel('bottom',text='Time of Flight',units='s')
    # plt1.setLabel('left',text='Hits')
    # tof_data = pg.PlotDataItem()
    # plt1.addItem(tof_data)
    pixq = Queue()
    evnt = None
    pp=PacketProcessor(pixq,evnt)
    pp.start()
    fp = FakePacket('/Users/alrefaie/Documents/repos/libtimepix/lib/onlineviewer/coin4-1.dat',pixq)
    fp.run()
    pixq.put(None)
    # t = threading.Thread(target=goodPart,args=(evnt,tof_data,))
    # t.start()

    
    
    # QtGui.QApplication.instance().exec_()
    # t.join()
    pp.join()

    # 

if __name__=='__main__':
    main()