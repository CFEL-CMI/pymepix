import multiprocessing

from multiprocessing.sharedctypes import RawArray 
import numpy as np
import socket
from multiprocessing import Queue
from .timepixdef import PacketType
class PacketProcessor(multiprocessing.Process):

    def __init__(self,input_queue,output_queue,exposure_length):
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


    def process_pixels(self,pixdata,longtime):
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



        ToT         = ((data & 0x00003FF0) >> 4)*25.0E-9 #Convert to ns



        globalToA  =((ToA_coarse<<4) | ~FToA) + ((col//2) %16)
        check = ((col//2) %16 ) == 0)
        globalToA[check] += 16
        
        finalToA = globalToA*1.5625E-9

        if self._col is None:
            self._col = col
            self._row = row
            self._toa = globalToA
            self._tot = ToT
        else:
            self._col = np.append(self._col,col)
            self._row = np.append(self._row,row)
            self._toa = np.append(self._toa,finalToA)
            self._tot = np.append(self._tot,ToT)


    def correct_global_time(self,arr,ltime):
        pixelbits = ( arr >> 28 ) & 0x3
        ltimebits = ( ltime >> 28 ) & 0x3
        diff = ltimebits - pixelbits
        neg = diff == 1 | diff == -3
        pos = diff == -1 | diff == 3
        zero = diff == 0
        arr[neg] =   ( (ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg] & 0x3FFFFFFF)
        arr[pos] =   ( (ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos] & 0x3FFFFFFF)
        arr[zero] =   ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)
        
        return arr

    def process_triggers(self,pixdata,longtime):
        coarsetime = (pixdata >> 9) & 0x7FFFFFFFF

        coarsetime >>=3


        tmpfine = (pixdata >> 5 ) & 0xF
        tmpfine = ((tmpfine-1) << 9) // 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)

        globaltime = self.correct_global_time(coarsetime,longtime)
        time_unit=25./4096.0
        # global_clock = (current_time & 0xFFFFC0000000)*1.5925E-9
        
        #print('RawTrigger TS: ',coarsetime*3.125E-9 )
        #Now shift the time to the proper position


        time_unit=25./4096
        m_trigTime = (globaltime)*25E-9 + trigtime_fine*time_unit*1E-9

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
        packet= np.frombuffer(packets,dtype=np.uint64)

        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

        pixels = packet[np.logical_or(header ==0xA,header==0xB)]
        triggers = packet[np.logical_and(np.logical_or(header==0x4,header==0x6),subheader == 0xF)]
        
        self.process_pixels(pixels,longtime)
        self.process_triggers(triggers,longtime)

    def find_events(self):
        events_found = []
        while self._triggers.size > 2:
            start = self._triggers[0]
            end = self._triggers[1]
            self._trigger_counter += 1

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
                    break
                elif packet[0] == 'RESET':
                    self.reset()
                    continue
                data = packet[0]
                longtime = packet[1]
                
                events = self.process_packets(data,longtime)

                if len(events)> 0:
                    self.output_queue.put(events)

        
            except Exception as e:
                print (str(e))
