import multiprocessing
import traceback
from multiprocessing.sharedctypes import RawArray 
import numpy as np
import socket
from multiprocessing import Queue
from .timepixdef import PacketType
class PacketProcessor(multiprocessing.Process):

    def __init__(self,input_queue,output_queue):
        multiprocessing.Process.__init__(self)
        self._input_queue = input_queue
        self._output_queue = output_queue
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

    # def process_pixels(self,pixdata,longtime):
    #     dcol        = ((pixdata & 0x0FE0000000000000) >> 52)
    #     spix        = ((pixdata & 0x001F800000000000) >> 45)
    #     pix         = ((pixdata & 0x0000700000000000) >> 44)
    #     col         = (dcol + pix//4)
    #     row         = (spix + (pix & 0x3))


    #     data        = ((pixdata & 0x00000FFFFFFF0000) >> 16)
    #     spidr_time  = (pixdata & 0x000000000000FFFF)
    #     ToA         = ((data & 0x0FFFC000) >> 14 )
    #     ToA_coarse  = (spidr_time << 14) | ToA
    #     FToA        = (data & 0xF)*1.5625E-9
    #     globalToA  =(ToA_coarse)*25.0E-9 - FToA + self._pixel_time


    #     ToT         = ((data & 0x00003FF0) >> 4)*25.0E-9
        

    #     if self._col is None:
    #         self._col = col
    #         self._row = row
    #         self._toa = globalToA
    #         self._tot = ToT
    #     else:
    #         self._col = np.append(self._col,col)
    #         self._row = np.append(self._row,row)
    #         self._toa = np.append(self._toa,globalToA)
    #         self._tot = np.append(self._tot,ToT)

    def process_pixels(self,pixdata,longtime):
        if pixdata.size == 0:
            return
        dcol        = ((pixdata & 0x0FE0000000000000) >> 52)
        spix        = ((pixdata & 0x001F800000000000) >> 45)
        pix         = ((pixdata & 0x0000700000000000) >> 44)
        col         = (dcol + pix//4)
        row         = (spix + (pix & 0x3))


        data        = ((pixdata & 0x00000FFFFFFF0000) >> 16)
        spidr_time  = (pixdata & 0x000000000000FFFF)
        ToA         = ((data & 0x0FFFC000) >> 14 )
        ToA_coarse  = self.correct_global_time((spidr_time << 14) | ToA,longtime)
        FToA        = (data & 0xF)



        ToT         = ((data & 0x00003FF0) >> 4)*25 #Convert to ns


        globalToA = (ToA_coarse << 12) - (FToA << 8)
        globalToA += ((col//2) %16 ) << 8
        globalToA[((col//2) %16)==0] += (16<<8)
        time_unit=25./4096
        finalToA = globalToA*np.float64(time_unit*1E-9)

        if self._col is None:
            self._col = col
            self._row = row
            self._toa = finalToA
            self._tot = ToT
        else:
            self._col = np.append(self._col,col)
            self._row = np.append(self._row,row)
            self._toa = np.append(self._toa,finalToA)
            self._tot = np.append(self._tot,ToT)


    def correct_global_time(self,arr,ltime):

        pixelbits = (( arr >> 28 ) & 0x3).astype(np.int8)
        ltimebits = int(( ltime >> 28 ) & 0x3)
        
        diff = ltimebits - pixelbits.astype(np.int64)
        neg = (diff == 1) | (diff == -3)
        pos = (diff == -1) | (diff == 3)
        arr=   ( (ltime) & 0xFFFFC0000000) | (arr & 0x3FFFFFFF)
        arr[neg] =   ( (ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg] & 0x3FFFFFFF)
        arr[pos] =   ( (ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos] & 0x3FFFFFFF)
        #print(( (ltime - 0x10000000) & 0xFFFFC0000000))
        return arr

    # def process_triggers(self,pixdata,longtime):
    #     coarsetime = (pixdata >> 9) & 0x7FFFFFFFF
    #     tmpfine = (pixdata >> 5 ) & 0xF
    #     tmpfine = ((tmpfine-1) << 9) // 12
    #     trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF);
    #     #time_unit=25./4096.0
    #     # global_clock = (current_time & 0xFFFFC0000000)*1.5925E-9
        
    #     #print('RawTrigger TS: ',coarsetime*3.125E-9 )
    #     globaltime  = (coarsetime<<1) & np.uint64(~0xC00000000)
    #     time_unit=25./4096
    #     m_trigTime = (globaltime)*1.5625E-9 + trigtime_fine*time_unit*1E-9 +self._trigger_time

    #     if self._triggers is None:
    #         self._triggers = m_trigTime
    #     else:
    #         self._triggers = np.append(self._triggers,m_trigTime)


    def process_triggers(self,pixdata,longtime):
        trigtime_coarse = ((pixdata & 0x00000FFFFFFFF000) >> 12) & 0xFFFFFFFF
        tmpfine = (pixdata >> 5 ) & 0xF
        tmpfine = ((tmpfine-1) << 9) // 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)

        globaltime = self.correct_global_time(trigtime_coarse,longtime)
        #time_unit=25./4096.0
        # global_clock = (current_time & 0xFFFFC0000000)*1.5925E-9
        
        #print('RawTrigger TS: ',coarsetime*3.125E-9 )
        #Now shift the time to the proper position


        time_unit=25./4096
        m_trigTime = (globaltime)*np.float64(25E-9) 
        if self._triggers is None:
            self._triggers = m_trigTime
        else:
            self._triggers = np.append(self._triggers,m_trigTime)
        
    def updateBuffers(self,val_filter):
        self._col = self._col[val_filter]
        self._row = self._row[val_filter]
        self._toa = self._toa[val_filter]
        self._tot = self._tot[val_filter]

    def getBuffers(self,val_filter):
        return self._col[val_filter],self._row[val_filter],self._toa[val_filter],self._tot[val_filter]


    def process_packets(self,packets,longtime):
        packet = packets

        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

        pixels = packet[np.logical_or(header ==0xA,header==0xB)]
        triggers = packet[np.logical_and(np.logical_or(header==0x4,header==0x6),subheader == 0xF)]

        if pixels.size > 0:
            self.process_pixels(pixels,longtime)
        if triggers.size > 0:
            self.process_triggers(triggers,longtime)
        if self._triggers is not None:
            return self.find_events()
        else:
            return []
    def find_events(self):
        events_found = []
        while self._triggers.size > 2:
            start = self._triggers[0]
            end = self._triggers[1]
            self._trigger_counter += 1
            if self._toa is not None:
                evt_filter = (self._toa >= start) & (self._toa < end)
                x,y,toa,tot = self.getBuffers(evt_filter)
                if x.size > 0:
                    
                    event = (self._trigger_counter,start,x,y,toa,tot)
                    events_found.append(event)


                    self.updateBuffers(~evt_filter)
            self._triggers = self._triggers[1:]
        
        return events_found

    def run(self):
        while True:
            try:
                # get a new message
                packet = self._input_queue.get()
                # this is the 'TERM' signal
                if packet is None:

                    if self._output_queue is not None:
                        self._output_queue.put(None)
                        break
                data = packet[0]
                longtime = packet[1]
                #print('GOT DATA')
                events = self.process_packets(data,longtime)

                if len(events)> 0 and self._output_queue is not None:
                    #print('EVENT FOUND')
                    self._output_queue.put(events)

        
            except Exception as e:
                print (str(e))
                traceback.print_exc()

