
import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np

class EventData(object):

    def __init__(self,trigger_time,x,y,toa,tot,reltoa):
        self.time = trigger_time
        self.x = x
        self.y = y
        self.toa = toa
        self.tot = tot
        self.tof = toa-trigger_time
        print('Event', trigger_time,self.toa)
        print('TOF',trigger_time, self.tof*1E6)
        # self.diff = np.array(diff)
        #Fix timestamping issues
        #self.diff += abs(self.diff.min())
class PacketProcessor(QtCore.QThread):
    onNewEvent = QtCore.pyqtSignal(object)
    def __init__(self):

        QtCore.QThread.__init__(self)
        self._longtime_lsb = 0
        self._longtime_msb = 0
        self._longtime = 0
        self._global_trig_time = 0
     
    def run(self):
        #with open("molbeam_000002.tpx3",'rb') as f:
        with open("test_tof_000000.tpx3",'rb') as f:
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
    

        ToT         = ((data & 0x00003FF0) >> 4)*25E-9 # ns
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
        globaltime  =(ToA_coarse)


        ToT         = (data & 0x00003FF0) >> 4
        globaltime = (globaltime << 4) | FToA
        if current_time != 0:
            pixelbits = ( ToA_coarse >> 28 ) & 0x3
            current_timebits = ( current_time >> 28 ) & 0x3
            diff = current_timebits - pixelbits

        #globaltime  = (globaltime) & (0x0FFFFFFFF)
        #print('Pixel spidr time', (spidr_time*(2**14)*25E-9))
            #print('Diff',diff)
        #global_clock = (current_time & 0xFFFFC0000000)*1.5925E-9
        # ToAs += ( ( (col//2) %16 ) << 8 )
        # if (((col//2)%16) == 0):
        #      ToAs += ( 16 << 8 )
        return col,row,(globaltime*1.5625E-9),ToT
        
    def processTrigger(self,pixdata,current_time):
        coarsetime = (pixdata >> 9) & 0x7FFFFFFFF
        # tmpfine = (pixdata >> 5 ) & 0xF
        # tmpfine = ((tmpfine-1) << 9) // 12
        # trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF);
        #time_unit=25./4096.0
        global_clock = (current_time & 0xFFFFC0000000)*1.5925E-9
        time_unit=25./4096
        #print('RawTrigger TS: ',coarsetime*3.125E-9 )
        globaltime  = (coarsetime<<1) &(~0xC00000000)
        m_trigTime = (globaltime)*1.5625E-9 #+ trigtime_fine*time_unit*1E-9
        print('Trigger ',m_trigTime)
        return 0,m_trigTime

    def addPixel(self,col,row,toa,tot,reltoa):

        if self.col is None:
            self.col = np.array([col])
            self.row = np.array([row])
            self.globaltime = np.array([toa])
            self.ToT = np.array([tot])        
            self.rel_global = np.array([reltoa])  
        else:
            self.col = np.append(self.col,[col])
            self.row = np.append(self.row,[row])
            self.globaltime = np.append(self.globaltime,[toa])
            self.ToT = np.append(self.ToT,[tot])
            self.rel_global = np.append(self.rel_global,[reltoa])
        #print(self.rel_global)
    def updateBuffers(self,val_filter):
        self.col = self.col[val_filter]
        self.row = self.row[val_filter]
        self.globaltime = self.globaltime[val_filter]
        self.ToT = self.ToT[val_filter]
        self.rel_global = self.rel_global[val_filter]

    def getBuffers(self,val_filter):
        return self.col[val_filter],self.row[val_filter],self.globaltime[val_filter],self.ToT[val_filter],self.rel_global[val_filter]
    def handleTriggers(self,trigger):

        if self.trigger_buffer is None:
            #print('EMPTY')
            self.trigger_buffer = np.array([trigger])
        elif self.trigger_buffer.size < 3:
            #print('EXPANDING')
            self.trigger_buffer = np.append(self.trigger_buffer,[trigger])
        else:
            #print('CHECKING')
            #print(self.trigger_buffer)
            #Take the first element:
            to_check = self.trigger_buffer[0]
            center_point = self.trigger_buffer[1]
            #Check if we have any negative values from noise
            if self.rel_global is not None:
                toa = self.rel_global
                # neg_Tof = (to_check-toa) < 0
                # #Update arrays
                # self.updateBuffers(neg_Tof)
                print(self.trigger_buffer)
                #toa = self.rel_global
                #print('Global: ', toa)
                #Now we check for pixels that lie between the first and second
                trig_filter = np.logical_and(toa >= to_check, toa < center_point)
                col,row,toa,tot,reltoa = self.getBuffers(trig_filter)
                new_Tof = np.logical_not(trig_filter)
                self.updateBuffers(new_Tof)
                if col.size > 0:
                    evt = EventData(to_check,col,row,toa,tot,reltoa)
                    self.onNewEvent.emit(evt)
               # print('Values: ',toa)
            self.trigger_buffer = np.roll(self.trigger_buffer,-1)
            self.trigger_buffer[2] = trigger
            #Create event here

            

    def read_data(self,f):
        self.triggers = None
        self.col = None
        self.row = None
        self.globaltime = None
        self.rel_global = None
        self.tof = None
        self.ToT = None
        self.updateTrigger = False
        self.trigger_buffer = None
        self._first_toa = None
        self._first_trigger = None
        self._last_global_time = None
        self._last_trigger = None
        self._trigger_buffer = None
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
            #print('Pixelss ',_globaltime)
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

            tmp_globaltime = _globaltime
            #print('Pixel ',_globaltime )
            #print('PixelDiff:',tmp_globaltime-self._first_toa)
            self.addPixel(_col,_row,tmp_globaltime,_ToT,tmp_globaltime)

            self._last_global_time = tmp_globaltime
                #An overflow occured so lets increase the 
            #self.diff.append(_globaltime-self.triggers)
            #print('Diff ',_globaltime-self.triggers)
        elif ( header == 0x4  or header == 0x6 ):
            subheader = ((int(packet) & 0x0F00000000000000) >> 56) & 0xF
            if subheader == 0xF:
                trigger_count,trigger_time = self.processTrigger(int(packet),self._longtime)
                if self._first_trigger is None:
                    self._first_trigger = trigger_time
                    self._last_trigger = trigger_time
                
                tmp_trigger_time = trigger_time
                self._last_trigger = trigger_time
                #print('Trigg ',trigger_time )
                #print('Trigger count:{}, Trigger time: {}'.format(trigger_count,trigger_time))
                self.handleTriggers(trigger_time)
                #print('TriggDiff:',trigger_time-self._first_trigger,trigger_time,self._first_trigger)
            elif ( subheader == 0x4 ):
            
                self._longtime_lsb = (packet & 0x0000FFFFFFFF0000) >> 16
            elif (subheader == 0x5 ):
                self._longtime_msb = (packet & 0x00000000FFFF0000) << 16
                tmplongtime = self._longtime_msb | self._longtime_lsb

                self._longtime = tmplongtime
        #print('Longtime: {}',self._longtime*1.5625E-9)
        
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