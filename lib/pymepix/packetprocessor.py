import multiprocessing

from multiprocessing.sharedctypes import RawArray 
import numpy as np
import socket
from multiprocessing import Queue
from .timepixdef import PacketType
class PacketProcessor(multiprocessing.Process):

    def __init__(self,input_queue,output_queue,exposure_length):

        self._input_queue = input_queue
        self._output_queue = output_queue
        self._trigtime_global_ext = 0
        self._recent_trigger = 0
        self._trigger_data = []
        self._exposure_length = exposure_length
        self._current_trigger = 0
    def processPixel(self,pixdata,current_time):
        if pixdata.size==0:
            return None,None,None,None
        dcol        = ((pixdata & 0x0FE0000000000000) >> 52)
        spix        = ((pixdata & 0x001F800000000000) >> 45)
        pix         = ((pixdata & 0x0000700000000000) >> 44)
        col         = (dcol + pix//4)
        row         = (spix + (pix & 0x3))


        data        = ((pixdata & 0x00000FFFFFFF0000) >> 16)
        spidr_time  = (pixdata & 0x000000000000FFFF)
        ToA         = ((data & 0x0FFFC000) >> 14 )
        ToA_coarse  = (spidr_time << 14) | ToA
        FToA        = (data & 0xF)
        globaltime  = (current_time & 0xFFFFC0000000) | (ToA_coarse & 0x3FFFFFFF)
    

        ToT         = ((data & 0x00003FF0) >> 4)*25 # ns

        pixelbits = ( ToA_coarse >> 28 ) & 0x3
        longtimebits = ( current_time >> 28 ) & 0x3
        diff = longtimebits - pixelbits     

        neg = np.logical_or(diff==1,diff==-3)
        pos = np.logical_or( diff == -1,diff == 3 )
        globaltime[neg] = ( (current_time - 0x10000000) & 0xFFFFC0000000) | (ToA_coarse & 0x3FFFFFFF)
        globaltime[pos] = ( (current_time + 0x10000000) & 0xFFFFC0000000) | (ToA_coarse & 0x3FFFFFFF)

        globaltime <<=12
        globaltime -= FToA<<8

        return col,row,globaltime,ToT


    def processTrigger(self,_pixdata,current_time):
        if _pixdata.size == 0:
            return None
        pixdata = _pixdata[0]
        m_trigCnt = ((pixdata & 0x00FFF00000000000) >> 44) & 0xFFF
        trigtime_coarse = ((pixdata & 0x00000FFFFFFFF000) >> 12) & 0xFFFFFFFF
        tmpfine = (pixdata >> 5 ) & 0xF
        tmpfine = ((tmpfine-1) << 9) / 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        trigtime_coarse  = (current_time & 0xFFFFC0000000) | (trigtime_coarse & 0x3FFFFFFF)
        
        m_trigTime = ((trigtime_coarse) << 12) | trigtime_fine

        return m_trigTime
    def run(self):
        while True:
            try:
                # get a new message
                packet = self._input_queue.get()
                # this is the 'TERM' signal
                if packet is None:
                    break
                data = packet[0]
                longtime = packet[1]
                
                header = data &  0xF000000000000000

                pixel_packets = data[np.logical_or.reduce(header == 0xB000000000000000,header == 0xA000000000000000)]
                trigger_packets = data[header == 0x6000000000000000]

                
                col,row,globaltime,ToT = self.processPixel(pixel_packets,longtime)

                trigger_time = self.processTrigger(trigger_packets[0],longtime)
                if trigger_time is not None:
                    print('Trigger',trigger_time)
                    self._recent_trigger = trigger_time
                if globaltime is not None:
                    print(globaltime)
                    evt_filter =  np.logical_and(globaltime >= self._current_trigger,globaltime<self._current_trigger+self._exposure_length.value)
                    t_col = col[evt_filter]
                    t_row = row[evt_filter]
                    t_globaltime = globaltime[evt_filter]
                    t_ToT = ToT[evt_filter]

                    if evt_filter.size ==0:
                        #We need a new trigger
                        self._output_queue.put((self._current_trigger,self._trigger_data))
                        self._current_trigger =self._recent_trigger
                        self._trigger_data = []
                    else:
                        self._trigger_data.append((t_col,t_row,t_globaltime,t_ToT,t_globaltime-self._current_trigger))


        
            except Exception as e:
                print (str(e))
