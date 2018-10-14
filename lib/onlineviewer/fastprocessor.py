

from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

class EventData(object):

    def __init__(self,trigger_counter,trigger_time,x,y,toa,tot):
        self._number = trigger_counter
        self.time = trigger_time
        self.x = x
        self.y = y
        self.toa = toa
        self.tot = tot
        self.tof = toa-trigger_time

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
        self._trigger_counter = 0

    
    def reset(self):
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
        self._trigger_counter = 0      
        
    
    def read_data(self,f,chunk_size=8192000):

        #self.skipheader(f)
        bytes_read = f.read(chunk_size)
        if bytes_read:
            return self.process_packets(bytes_read)
        else:
            return None



    def process_packets(self,packets):
        packet= np.frombuffer(packets,dtype='<u8')

        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

        pixels = packet[np.logical_or(header ==0xA,header==0xB)]
        triggers = packet[np.logical_and(np.logical_or(header==0x4,header==0x6),subheader == 0xF)]
        
        self.process_pixels(pixels)
        self.process_triggers(triggers)
        return self.find_events()

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
        FToA        = (data & 0xF)*1.5625E-9
        globalToA  =(ToA_coarse)*25.0E-9 - FToA + self._pixel_time


        ToT         = ((data & 0x00003FF0) >> 4)*25.0E-9
        

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
        self.correct_pixel_time()


    def find_events(self):
        events_found = []
        while self._triggers.size > 2:
            start = self._triggers[0]
            end = self._triggers[1]
            self._trigger_counter += 1

            evt_filter = (self._toa >= start) & (self._toa < end)
            x,y,toa,tot = self.getBuffers(evt_filter)
            if x.size > 0:
                
                event = EventData(self._trigger_counter,start,x,y,toa,tot)
                events_found.append(event)


                self.updateBuffers(~evt_filter)
            self._triggers = self._triggers[1:]
        
        return events_found

    


            


    def correct_pixel_time(self):
        
        #Take the current globalToA and roll it then compute the differenct



        OToA = np.roll(self._toa,1)
        #Make sure the first is the same
        OToA[0] = self._toa[0]
        diff = np.abs(self._toa - OToA)
        #print(diff.max())
        #print('MAX',diff.max())
        #Find where the difference is larger than 20 seconds
        diff = np.where(diff > 20.0)[0]
        #print(diff)
        while diff.size > 0:
            
            self._pixel_time += 1.5625E-9*(1<<34)
            #print(self._pixel_time)
            self._toa[diff[0]:] += 1.5625E-9*(1<<34)

            OToA = np.roll(self._toa,1)
            #Make sure the first is the same
            OToA[0] = self._toa[0]
            diff = np.abs(self._toa - OToA)
            #print('MAX',diff.max())
            #Find where the difference is larger than 20 seconds
            diff = np.where(diff > 20.0)[0]
            #print('INDEX',diff)


    def correct_trigger_time(self):
        
        #Take the current globalToA and roll it then compute the differenct

        OToA = np.roll(self._triggers,1)
        #Make sure the first is the same
        OToA[0] = self._triggers[0]
        diff = np.abs(self._triggers - OToA)
        #print(diff.max())
        #print('MAX',diff.max())
        #Find where the difference is larger than 20 seconds
        diff = np.where(diff > 20.0)[0]
        while diff.size > 0:
            
            self._trigger_time += 1.5625E-9*(1<<34)
            #print(self._pixel_time)
            self._triggers[diff[0]:] += 1.5625E-9*(1<<34)

            OToA = np.roll(self._triggers,1)
            #Make sure the first is the same
            OToA[0] = self._triggers[0]
            diff = np.abs(self._triggers - OToA)
            #Find where the difference is larger than 20 seconds
            diff = np.where(diff > 20.0)[0]

        
        #phase  = (col >> 1) & 15

    def updateBuffers(self,val_filter):
        self._col = self._col[val_filter]
        self._row = self._row[val_filter]
        self._toa = self._toa[val_filter]
        self._tot = self._tot[val_filter]

    def getBuffers(self,val_filter):
        return self._col[val_filter],self._row[val_filter],self._toa[val_filter],self._tot[val_filter]


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
        m_trigTime = (globaltime)*1.5625E-9 + trigtime_fine*time_unit*1E-9 +self._trigger_time

        if self._triggers is None:
            self._triggers = m_trigTime
        else:
            self._triggers = np.append(self._triggers,m_trigTime)
        
        while self.correct_trigger_time():
            continue
def main():
    import matplotlib.pyplot as plt
    pp = FastPacketProcessor()
    events = None
    with open('molbeam_000000.tpx3','rb') as f:
        #Gives a list of events or None if reached end of file
        events = pp.read_data(f,chunk_size=81920000)


if __name__=="__main__":
    main()