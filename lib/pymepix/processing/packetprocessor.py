from .basepipeline import BasePipelineObject
import socket
from .datatypes import MessageType
import time
import numpy as np
from enum import IntEnum
class PixelOrientation(IntEnum):
    """Defines how row and col are intepreted in the output"""
    Up=0
    """Up is the default, x=column,y=row"""
    Left=1
    """x=row, y=-column"""
    Down=2
    """x=-column, y = -row """
    Right=3
    """x=-row, y=column"""

class PacketProcessor(BasePipelineObject):
    """Processes Pixel packets for ToA, ToT,triggers and events

    This class, creates a UDP socket connection to SPIDR and recivies the UDP packets from Timepix
    It them pre-processes them and sends them off for more processing

    """

    def __init__(self,
                    handle_events=False, position_offset=(0,0), orientation=PixelOrientation.Up,input_queue=None,create_output=True,num_outputs=1,shared_output=None):
        BasePipelineObject.__init__(self,PacketProcessor.__name__,input_queue=input_queue,create_output=create_output,num_outputs=num_outputs,shared_output=shared_output)

        self.clearBuffers()
        self._orientation = orientation
        self._x_offset,self._y_offset = position_offset


        self._trigger_counter = 0        

        self._handle_events= False



    def updateBuffers(self,val_filter):
        self._x = self._x[val_filter]
        self._y = self._y[val_filter]
        self._toa = self._toa[val_filter]
        self._tot = self._tot[val_filter]

    def getBuffers(self,val_filter=None):
        if val_filter is None:
            return np.copy(self._x),np.copy(self._y),np.copy(self._toa),np.copy(self._tot)
        else:
            return np.copy(self._x[val_filter]),np.copy(self._y[val_filter]),np.copy(self._toa[val_filter]),np.copy(self._tot[val_filter])

    def clearBuffers(self):
        self._x = None
        self._y = None
        self._tot = None
        self._toa = None
        self._triggers = None



    def process(self,data_type,data):
        if data_type is not MessageType.RawData:
            return None,None

        packets,longtime = data

        packet = packets

        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

        pixels = packet[np.logical_or(header ==0xA,header==0xB)]
        triggers = packet[np.logical_and(np.logical_or(header==0x4,header==0x6),subheader == 0xF)]

        if pixels.size > 0:
            self.process_pixels(pixels,longtime)
        
        if self._handle_events:
            if triggers.size > 0:
                self.process_triggers(triggers,longtime)

            events = self.find_events_fast()

            if events is not None:
                return MessageType.EventData,events
            else:
                return None,None
        else:
            if self._x is not None:
                pixel_data = self.getBuffers()
                self.clearBuffers()
                #self.debug('Putting pixel, {}'.format(pixel_data))
                return MessageType.PixelData,pixel_data
            else:
                return None,None

    def filterBadTriggers(self):
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
        
        #Get our start/end triggers to get events
        start = self._triggers[0:-1:]
        if start.size ==0:
            return None

        trigger_counter= np.arange(self._trigger_counter,self._trigger_counter+start.size,dtype=np.int)

        self._trigger_counter = trigger_counter[-1]+1

        # end = self._triggers[1:-1:]
        #Get the first and last triggers in pile
        first_trigger = start[0]
        last_trigger = start[-1]
        #Delete useless pixels beyond the trigger
        self.updateBuffers(self._toa  >= first_trigger)
        #grab only pixels we care about
        x,y,toa,tot = self.getBuffers(self._toa < last_trigger)
        self.updateBuffers(self._toa  >= last_trigger)

        event_mapping = np.digitize(toa,start)-1
        event_triggers = self._triggers[:-1:]   
        self._triggers = self._triggers[-1:]

        #print('Trigger delta',triggers,np.ediff1d(triggers))

        tof = toa-event_triggers[event_mapping]
        event_number = trigger_counter[event_mapping]

        return event_number,x,y,tof,tot



    def correct_global_time(self,arr,ltime):
        pixelbits = ( arr >> 28 ) & 0x3
        ltimebits = ( ltime >> 28 ) & 0x3
        diff = ltimebits - pixelbits
        neg = (diff == 1) | (diff == -3)
        pos = (diff == -1) | (diff == 3)
        zero = (diff == 0) | (diff == 2)
        arr[neg] =   ( (ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg] & 0x3FFFFFFF)
        arr[pos] =   ( (ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos] & 0x3FFFFFFF)
        arr[zero] = ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)
        #arr[zero] =   ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)
        
        return arr

    def process_triggers(self,pixdata,longtime):
        coarsetime = pixdata >>12 & 0xFFFFFFFF
        coarsetime = self.correct_global_time(coarsetime,longtime)
        tmpfine = (pixdata  >> 5 ) & 0xF
        tmpfine = ((tmpfine-1) << 9) // 12
        trigtime_fine = (pixdata  & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        time_unit=25./4096
        tdc_time = (coarsetime*25E-9 + trigtime_fine*time_unit*1E-9)

        m_trigTime = tdc_time

        if self._triggers is None:
            self._triggers = m_trigTime
        else:
            self._triggers = np.append(self._triggers,m_trigTime)

    def orientPixels(self,col,row):
        if self._orientation is PixelOrientation.Up:
            return col,row
        elif self._orientation is PixelOrientation.Left:
            return row,255-col
        elif self._orientation is PixelOrientation.Down:
            return 255-col,255-row
        elif self._orientation is PixelOrientation.Right:
            return 255-row,col            

    def process_pixels(self,pixdata,longtime):

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

        ToA_coarse  = self.correct_global_time((spidr_time << 14) | ToA,longtime)
        
        globalToA = (ToA_coarse << 12) - (FToA << 8)
        globalToA += ((col//2) %16 ) << 8
        globalToA[((col//2) %16)==0] += (16<<8)
        time_unit=25./4096
        finalToA = globalToA*time_unit*1E-9


        #Orient the pixels based on Timepix orientation
        x,y = self.orientPixels(col,row)

        #
        x+= self._x_offset 
        y+= self._y_offset

        #print('PIXEL',finalToA,longtime)
        if self._x is None:
            self._x = x
            self._y = y
            self._toa = finalToA
            self._tot = ToT
        else:
            self._x = np.append(self._x,x)
            self._y = np.append(self._y,y)
            self._toa = np.append(self._toa,finalToA)
            self._tot = np.append(self._tot,ToT)
        


