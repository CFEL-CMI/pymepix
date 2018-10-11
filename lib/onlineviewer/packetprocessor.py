
import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np

class EventData(object):

    def __init__(self,trigger_num,x,y,toa,tot):
        self.no = trigger_num
        self.x = np.array(x)
        self.y = np.array(y)
        self.toa = np.array(toa)
        self.tot = np.array(tot)
        # self.diff = np.array(diff)
        #Fix timestamping issues
        #self.diff += abs(self.diff.min())
class PacketProcessor(object):
    #onNewEvent = QtCore.pyqtSignal(object)
    def __init__(self):

        #QtCore.QThread.__init__(self)
        self._longtime_lsb = 0
        self._longtime_msb = 0
        self._longtime = 0
        self._global_trig_time = 0
    
    def run(self):
        with open('/Users/alrefaie/Documents/repos/libtimepix/lib/onlineviewer/molbeam_000002.tpx3','rb') as f:
            self.read_data(f)
        #evt = EventData(0,self.col,self.row,self.globaltime,self.ToT)
        #self.onNewEvent.emit(evt)
    def processPixelArray(self,pixdata,current_time):
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
        if neg.size > 0:
            globaltime[neg] = ( (current_time - 0x10000000) & 0xFFFFC0000000) | (ToA_coarse[neg] & 0x3FFFFFFF)
        if pos.size > 0:
            globaltime[pos] = ( (current_time + 0x10000000) & 0xFFFFC0000000) | (ToA_coarse[neg] & 0x3FFFFFFF)

        globaltime <<=12
        globaltime -= FToA<<8

        return col,row,globaltime,ToT

    def processPixelSingle(self,pixdata,current_time):
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
        globaltime  = ToA_coarse
    

        ToT         = (data & 0x00003FF0) >> 4

        # pixelbits = ( ToA_coarse >> 28 ) & 0x3
        # longtimebits = ( current_time >> 28 ) & 0x3
        # diff = longtimebits - pixelbits
        # if( diff == 1  or diff == -3):
        #     globaltime = ( (current_time - 0x10000000) & 0xFFFFC0000000) | (ToA_coarse & 0x3FFFFFFF);
        # if( diff == -1 or diff == 3 ):  
        #     globaltime = ( (current_time + 0x10000000) & 0xFFFFC0000000) | (ToA_coarse & 0x3FFFFFFF)

        ToAs = (globaltime << 12) - (FToA<<8)
        ToAs += ( ( (col//2) %16 ) << 8 )
        if (((col//2)%16) == 0):
             ToAs += ( 16 << 8 )

        return col,row,ToAs,ToT
        
    def processTrigger(self,pixdata,current_time):
        m_trigCnt = ((pixdata & 0x00FFF00000000000) >> 44) & 0xFFF

        trigtime_coarse = ((pixdata & 0x00000FFFFFFFF000) >> 12) & 0xFFFFFFFF
        tmpfine = (pixdata >> 5 ) & 0xF
        tmpfine = ((tmpfine-1) << 9) // 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        #trigtime_coarse  = (current_time & 0xFFFFC0000000) | (trigtime_coarse & 0x3FFFFFFF)
        
        m_trigTime = ((trigtime_coarse) << 12) | trigtime_fine

        return m_trigCnt,m_trigTime

    def read_data(self,f):
        self.triggers = None
        self.col = []
        self.row = []
        self.globaltime = []
        self.rel_global = []
        self.tof = []
        self.ToT = []
        self.updateTrigger = False
        self.triggers = None
        self._first_toa = None
        self._first_trigger = None
        self._last_global_time = None
        self._last_trigger = None
        self._global_time_ext = 0
        self._trigger_time_ext = 0
        #self.skipheader(f)
        bytes_read = f.read(8)
        while bytes_read:
            self.loopPackets(bytes_read)
            bytes_read = f.read(8)
        print('Finished')
    def loopPackets(self,_packet):
        

        packet = int.from_bytes(_packet,byteorder='little')
        header = ((int(packet) & 0xF000000000000000) >> 60) & 0xF
        if (header == 0xA or header == 0xB):
            _col,_row,_globaltime,_ToT = self.processPixelSingle(int(packet),self._longtime)
            #print('Pixel: col: {} row : {} globaltime: {} ToT: {}'.format(col,row,globaltime,ToT))
            #print('Pixeltime: {}'.format(_globaltime))
            # if self.updateTrigger:
            #     if len(self.col) > 0:
            #         evt = EventData(0,self.col,self.row,self.globaltime,self.ToT,self.diff)
            #         self.onNewEvent.emit(evt)
            #     self.triggers = _globaltime
            #     self.col = []
            #     self.row = []
            #     self.globaltime = []
            #     self.diff = []
            #     self.ToT = []
            #     self.updateTrigger = False

            if self._first_toa is None:
                self._first_toa = _globaltime
                self._last_global_time = _globaltime

            tmp_globaltime = _globaltime + self._global_time_ext
            print('Compare: ',tmp_globaltime,self._last_global_time)
            if tmp_globaltime < self._last_global_time:
                self._global_time_ext += (1<<35)
                quit()
            tmp_globaltime = _globaltime + self._global_time_ext
            self.col.append(_col)
            self.row.append(_row)
            self.globaltime.append(tmp_globaltime)
            self.ToT.append(_ToT)
            self._last_global_time = tmp_globaltime
            print('Pixeltime: {} {}'.format(tmp_globaltime-self._first_toa,self._global_time_ext))
                #An overflow occured so lets increase the 
            #self.diff.append(_globaltime-self.triggers)
            #print('Diff ',_globaltime-self.triggers)
            self.ToT.append(_ToT)
        elif ( header == 0x4  or header == 0x6 ):
            subheader = ((int(packet) & 0x0F00000000000000) >> 56) & 0xF
            if subheader == 0xF:
                trigger_count,trigger_time = self.processTrigger(int(packet),self._longtime)
                if self._first_trigger is None:
                    self._first_trigger = trigger_time
                    self._last_trigger = trigger_time
                
                tmp_trigger_time = trigger_time

                if trigger_time < self._last_trigger:
                    self._global_time_ext += (1<<35)
                self._last_trigger = trigger_time
                #print('Trigger count:{}, Trigger time: {}'.format(trigger_count,trigger_time))
                print('Trigetime: {} {}'.format(trigger_time-self._first_trigger,self._first_trigger))
            elif ( subheader == 0x4 ):
                self._longtime_lsb = (packet & 0x0000FFFFFFFF0000) >> 16
            elif (subheader == 0x5 ):
                self._longtime_msb = (packet & 0x00000000FFFF0000) << 16
                tmplongtime = self._longtime_msb | self._longtime_lsb
                if ( (tmplongtime > ( self._longtime + 0x10000000)) and (self._longtime > 0) ):
                
                    #print("Large forward time jump")
                    self._longtime = (self._longtime_msb - 0x10000000) | self._longtime_lsb
                
                else: 
                    self._longtime = tmplongtime
                #print('Longtime: {}',self._longtime)
        
    def skipheader(self,f):
        #Create uint32 view
        
        print('{}'.format(f.read(4)))
        sphdr_size = int.from_bytes(f.read(4),byteorder='little')
        print('header_size: {}'.format(sphdr_size))
        if (sphdr_size > 66304):
            sphdr_size = 66304
        
        header_length = sphdr_size
        f.read(sphdr_size-2)





def main():
    import matplotlib.pyplot as plt
    analysis = PacketProcessor()
    matrix = np.zeros(shape=(256,256))
    with open('/Users/alrefaie/Documents/repos/libtimepix/lib/onlineviewer/molbeam_000000.tpx3','rb') as f:

        analysis.read_data(f)


if __name__=="__main__":
    main()