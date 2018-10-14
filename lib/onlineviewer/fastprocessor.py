

from pyqtgraph.Qt import QtCore, QtGui
import numpy as np



class FastPacketProcessor(object):

    def __init__(self):

        self._longtime_lsb = 0
        self._longtime_msb = 0
        self._longtime = 0
        self._pixel_time = 0
        self._trigger_time = 0    

        self._col = None
        self._row = None
        self._tot = None
        self._toa = None

        self._triggers = None
    
    def run(self):
        #with open("molbeam_000002.tpx3",'rb') as f:
        with open("test_tof_000001.tpx3",'rb') as f:
            self.read_data(f)
        
    
    def read_data(self,f,chunk_size=819200):

        #self.skipheader(f)
        bytes_read = f.read(chunk_size)
        self.process_packets(bytes_read)



    def process_packets(self,packets):
        packet= np.frombuffer(packets,dtype='<u8')

        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

        pixels = packet[np.logical_or(header ==0xA,header==0xB)]
        triggers = packet[np.logical_and(np.logical_or(header==0x4,header==0x6),subheader == 0xF)]
        
        self.process_pixels(pixels)
        self.process_triggers(triggers)
    def process_pixels(self,pixdata):
        dcol        = ((pixdata & 0x0FE0000000000000) >> 52)
        spix        = ((pixdata & 0x001F800000000000) >> 45)
        pix         = ((pixdata & 0x0000700000000000) >> 44)
        col         = (dcol + pix//4)
        row         = (spix + (pix & 0x3))


        data        = ((pixdata & 0x00000FFFFFFF0000) >> 16)
        spidr_time  = (pixdata & 0x000000000000FFFF)
        ToA         = ((data & 0x0FFFC000) >> 14 )
        ToA_coarse  = (spidr_time << 14) | ToA
        FToA        = (data & 0xF)*1.5625
        globalToA  =(ToA_coarse)*25.0


        ToT         = (data & 0x00003FF0) >> 4
        globalToA -=FToA
        

        if self._col is None:
            self._col = col
            self._row = row
            self._toa = globalToA
            self._tot = ToT
        else:
            self._col = np.append(self._col,col)
            self._row = np.append(self._row,row)
            self._toa = np.append(self._toa,globalToA)
            self._tot = np.append(self._tot,ToT)
        
        #Correct the pixels global time
        while self.correct_pixel_time():
            continue

    def correct_pixel_time(self):
        
        #Take the current globalToA and roll it then compute the differenct

        OToA = np.roll(self._toa,1)
        #Make sure the first is the same
        OToA[0] = self._toa[0]

        OToA -= 1e9
        OToA[0] = self._toa[0]
        diff = np.where((self._toa - OToA) < 0)[0]
        if diff.size > 0:
            self._pixel_time += 1.5625*(1<<35)
            self._toa[diff] += 1.5625*(1<<35)
            OToA = np.roll(self._toa,1)
            #Make sure the first is the same
            OToA[0] = self._toa[0]

            OToA -= 1e9
            OToA[0] = self._toa[0]
            diff = np.where((self._toa - OToA) < 0)


        return diff.size != 0

    def correct_trigger_time(self):
        
        #Take the current globalToA and roll it then compute the differenct

        oldTriggers = np.roll(self._triggers,1)
        #Make sure the first is the same
        oldTriggers[0] = self._triggers[0]

        oldTriggers -= 1e9
        oldTriggers[0] = self._triggers[0]
        diff = np.where((self._triggers - oldTriggers) < 0)[0]
        if diff.size > 0:
            self._pixel_time += 1.5625*(1<<35)
            self._triggers[diff] += 1.5625*(1<<35)
            oldTriggers = np.roll(self._triggers,1)
            #Make sure the first is the same
            oldTriggers[0] = self._triggers[0]

            oldTriggers -= 1e9
            oldTriggers[0] = self._triggers[0]
            diff = np.where((self._triggers - oldTriggers) < 0)


        return diff.size != 0
        #phase  = (col >> 1) & 15

    def updateBuffers(self,val_filter):
        self._col = self._col[val_filter]
        self._row = self._row[val_filter]
        self._toa = self._toa[val_filter]
        self._tot = self._tot[val_filter]

    def getBuffers(self,val_filter):
        return self._col[val_filter],self._row[val_filter],self._globaltime[val_filter],self._ToT[val_filter]


    def process_triggers(self,pixdata):
        coarsetime = (pixdata >> 9) & 0x7FFFFFFFF
        tmpfine = (pixdata >> 5 ) & 0xF
        tmpfine = ((tmpfine-1) << 9) // 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF);
        #time_unit=25./4096.0
        # global_clock = (current_time & 0xFFFFC0000000)*1.5925E-9
        
        #print('RawTrigger TS: ',coarsetime*3.125E-9 )
        globaltime  = (coarsetime<<1) & np.uint64(~0xC00000000)
        time_unit=25./4096
        m_trigTime = (globaltime)*1.5625 + trigtime_fine*time_unit     

        if self._triggers is None:
            self._triggers = m_trigTime
        else:
            self._triggers = np.append(self._triggers,m_trigTime)
        
        while self.correct_trigger_time():
            continue
def main():
    pp = FastPacketProcessor()
    pp.run()

if __name__=="__main__":
    main()