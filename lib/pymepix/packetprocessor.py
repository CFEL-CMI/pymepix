import multiprocessing
import traceback
from multiprocessing.sharedctypes import RawArray 
import numpy as np
import socket
import time
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

        self._find_time = 0
        self._process_trig_time = 0
        self._process_pix_time = 0
        self._find_event_time = 0

        self._decode_time = 0

        self._append_time = 0

        self._put_time = 0
        self._put_count = 0

        self._find_count= 0
        self._process_trig_count= 0
        self._process_pix_count= 0
        self._find_event_count= 0
        self._append_count = 0

    def reset(self):
        self._longtime_lsb = 0
        self._longtime_msb = 0
        self._longtime = 0

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
        start = time.time()

        dcol        = ((pixdata & 0x0FE0000000000000) >> 52)
        spix        = ((pixdata & 0x001F800000000000) >> 45)
        pix         = ((pixdata & 0x0000700000000000) >> 44)
        col         = (dcol + pix//4)
        row         = (spix + (pix & 0x3))


        data        = ((pixdata & 0x00000FFFFFFF0000) >> 16)
        spidr_time  = (pixdata & 0x000000000000FFFF)
        ToA         = ((data & 0x0FFFC000) >> 14 )
        FToA        = (data & 0xF)
        ToT         = ((data & 0x00003FF0) >> 4)*25 
        self._decode_time += time.time()- start
        ToA_coarse  = self.correct_global_time((spidr_time << 14) | ToA,longtime)
        



        ToT         = ((data & 0x00003FF0) >> 4)*25 #Convert to ns


        globalToA = (ToA_coarse << 12) - (FToA << 8)
        globalToA += ((col//2) %16 ) << 8
        globalToA[((col//2) %16)==0] += (16<<8)
        time_unit=25./4096
        finalToA = globalToA*time_unit*1E-9
        
        self._process_pix_time+= time.time() - start
        self._process_pix_count+=1
        start = time.time()
        #print('PIXEL',finalToA,longtime)
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
        self._append_time+= time.time()-start
        self._append_count += 1

    def correct_global_time(self,arr,ltime):
        pixelbits = ( arr >> 28 ) & 0x3
        ltimebits = ( ltime >> 28 ) & 0x3
        diff = ltimebits - pixelbits
        neg = (diff == 1) | (diff == -3)
        pos = (diff == -1) | (diff == 3)
        arr = ( (ltime) & 0xFFFFC0000000) | (arr & 0x3FFFFFFF)
        arr[neg] =   ( (ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg] & 0x3FFFFFFF)
        arr[pos] =   ( (ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos] & 0x3FFFFFFF)
        #arr[zero] =   ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)
        
        return arr

    def process_triggers(self,pixdata,longtime):
        start = time.time()
        coarsetime = pixdata >>12 & 0xFFFFFFFF
        coarsetime = self.correct_global_time(coarsetime,longtime)
        tmpfine = (pixdata  >> 5 ) & 0xF
        tmpfine = ((tmpfine-1) << 9) // 12
        trigtime_fine = (pixdata  & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        time_unit=25./4096
        tdc_time = (coarsetime*25E-9 + trigtime_fine*time_unit*1E-9)
        # coarsetime = (pixdata >> 9) & 0x7FFFFFFFF

        # coarsetime >>=3


        # tmpfine = (pixdata >> 5 ) & 0xF
        # tmpfine = ((tmpfine-1) << 9) // 12
        # trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)

        # globaltime = self.correct_global_time(coarsetime,longtime)
        # #time_unit=25./4096.0
        # # global_clock = (current_time & 0xFFFFC0000000)*1.5925E-9
        
        # #print('RawTrigger TS: ',coarsetime*3.125E-9 )
        # #Now shift the time to the proper position


        # time_unit=25./4096
        m_trigTime = tdc_time

        self._process_trig_time+= time.time() - start
        self._process_trig_count+=1
        #print('TRIGGERS',m_trigTime,longtime*25E-9)
        start = time.time()
        if self._triggers is None:
            self._triggers = m_trigTime
        else:
            self._triggers = np.append(self._triggers,m_trigTime)
        self._append_time += time.time()-start
        self._append_count+=1
    def updateBuffers(self,val_filter):
        self._col = self._col[val_filter]
        self._row = self._row[val_filter]
        self._toa = self._toa[val_filter]
        self._tot = self._tot[val_filter]

    def getBuffers(self,val_filter):
        return np.copy(self._col[val_filter]),np.copy(self._row[val_filter]),np.copy(self._toa[val_filter]),np.copy(self._tot[val_filter])


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
        return self.find_events_fast()

    def filterBadTriggers(self):
        # OToA = np.roll(self._triggers,1)
        # #Make sure the first is the same
        # OToA[0] = self._triggers[0]
        # diff = np.abs(self._triggers - OToA)
        # #print(diff.max())
        # #print('MAX',diff.max())
        # #Find where the difference is larger than 20 seconds
        # diff = np.where(diff > 20.0)[0]
        # if diff.size > 0:
        #     self._triggers = self._triggers[diff[0]:]
        self._triggers = self._triggers[np.argmin(self._triggers):]

    def find_events_fast(self):
        if self._triggers is None:
            return None
        self.filterBadTriggers()
        if self._triggers.size < 5:
            return None

        if self._toa is None:
            return None
        if self._toa.size == 0:
            #Clear out the triggers since they have nothing
            return None
        
        start_time = time.time()
        #Get our start/end triggers to get events
        start = self._triggers[0:-1:]
        if start.size ==0:
            return None
        # end = self._triggers[1:-1:]
        #Get the first and last triggers in pile
        first_trigger = start[0]
        last_trigger = start[-1]
        #Delete useless pixels beyond the trigger
        self.updateBuffers(self._toa  >= first_trigger)
        #grab only pixels we care about
        x,y,toa,tot = self.getBuffers(self._toa < last_trigger)
        self.updateBuffers(self._toa  < last_trigger)

        #print('toa min/max',toa.min(),toa.max())
        #Delete them from the rest of the array
        #self.updateBuffers(self._toa >= last_trigger)
        #Our event filters
        #evt_filter = (toa[None,:] >= start[:,None]) & (toa[None,:] < end[:,None])

        #Get the mapping
        event_mapping = np.digitize(toa,start)-1
        event_triggers = self._triggers[:-1:]
        
        self._triggers = self._triggers[-1:]

        self._find_event_time+= time.time() - start_time
        self._find_event_count+=1

        
        #print('Triggers',event_triggers,np.ediff1d(event_triggers))

        return event_triggers,x,y,toa,tot,event_mapping


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

                if events is not None and self._output_queue is not None:
                    #print('EVENT FOUND')
                    start = time.time()
                    self._output_queue.put(events)
                    self._put_time += time.time()-start
                    self._put_count+=1

        
            except Exception as e:
                print (str(e))
                traceback.print_exc()
                break

        fmt = "{} Total time: {}s calls {} Avg Time {}s"

        print(fmt.format('PIXEL',self._process_pix_time,self._process_pix_count,self._process_pix_time/max(self._process_pix_count,1)))
        print(fmt.format('::DECODE',self._decode_time,self._process_pix_count,self._decode_time/max(self._process_pix_count,1)))
        print(fmt.format('TRIGG',self._process_trig_time,self._process_trig_count,self._process_trig_time/max(self._process_trig_count,1)))
        print(fmt.format('FIND ',self._find_event_time,self._find_event_count,self._find_event_time/max(self._find_event_count,1)))
        print(fmt.format('APPND',self._append_time,self._append_count,self._append_time/max(self._append_count,1)))
        print(fmt.format('PUTQ ',self._put_time,self._put_count,self._put_time/max(self._put_count,1)))