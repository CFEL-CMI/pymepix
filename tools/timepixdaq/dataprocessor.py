import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np
from pymepix import *


class DataProcessor(QtCore.QThread):

    newData = QtCore.pyqtSignal(object)
    triggerRegionData = QtCore.pyqtSignal(object)


    def __init__(self):
        QtCore.QThread.__init__(self)

        self._mode = OperationMode.ToAandToT
        self._use_super_pixl = False
    
        self._last_trigger = None
        self._next_trigger = None

        self._pixel_data_to_process = []
        
        self._x_data = None
        self._y_data = None
        self._toa_data = None
        self._tot_data = None
        self._hit_data = None

        self._run_thread = True
        self._is_in_acq= False
    def resetAcq(self):
        self._last_trigger = None
        self._next_trigger = None

        self._pixel_data_to_process = []
        self._trigger_data_to_process = []
        self._x_data = None
        self._y_data = None
        self._toa_data = None
        self._tot_data = None
        self._hit_data = None        


    def onNewTrigger(self,trigger_data):
        self._trigger_data_to_process.append(trigger_data)
    def processTrigger(self,trigger_data):
        #Should only be one
        #Take the trigger timestamps
        trigger = trigger_data[0][1][0]
        print('RawTrigger: ',trigger,trigger.dtype)
        time_stamps = trigger_data[0][1][0]<<np.uint64(1)
        heartbeat = trigger_data[1]<<4
        #Convert it to the same format 1.5ns as fToA
        #Remove
        abs_timestamp = np.uint64(heartbeat)& np.uint64(~(0x3FFFFFFFF))
        #Now take the heartbeat and shift it by 4
        abs_timestamp|=time_stamps
        
        

        #Now store it
        if self._last_trigger is None:
            self._last_trigger  =  abs_timestamp
        else:
            self._next_trigger =  abs_timestamp
            self.sortPixels()
    def onModeChange(self,new_mode):
        self._mode = new_mode
        self.resetAcq()
    def onSuperPixelMode(self,superPixel):
        self._use_super_pixl = superPixel
        self.resetAcq()
    def grayToBinary32(self,num):
    
        num = num ^ (num >> 16)
        num = num ^ (num >> 8)
        num = num ^ (num >> 4)
        num = num ^ (num >> 2)
        num = num ^ (num >> 1)
        return num

    def sortPixels(self):
        """Here, once we have a trigger (during open shutter mode)
        We check whether the pixel hit either before or after the latest trigger"""
        print('NEXT TRIGGER ',self._next_trigger,' LAST TRIGGER: ',self._last_trigger)
        if self._toa_data is not None:
            toa_diff = self._toa_data.astype(np.int64) - np.int64(self._next_trigger)
            
            print('CHECKING TOA DIFFERENCE, ')
            last_loc = toa_diff < 0
            next_loc = toa_diff >= 0
            print('ASSINGING')
            #print('LOCATION',last_loc,next_loc)
            try:
                x =  self._x_data[last_loc]
                y = self._y_data[last_loc]
                z = self._toa_data[last_loc]
                if self._tot_data is not None:
                    tot = self._tot_data[last_loc]
                else:
                    tot= None
                hit = self._hit_data[last_loc]
            except Exception as e:
                print(str(e))
            print('XYZ HERE: ',x,y,z)
            #print('Selected_Z = ',z)

            self._x_data = self._x_data[next_loc]
            self._y_data = self._y_data[next_loc]
            self._toa_data = self._toa_data[next_loc]
            if self._tot_data is not None:
                self._tot_data = self._tot_data[next_loc]
            self._hit_data = self._hit_data[next_loc]
            #print('Leftover_Z = ',self._toa_data)
            if x.size > 0:
                self.triggerRegionData.emit((self._last_trigger,x,y,z,tot,hit))

        self._last_trigger = self._next_trigger

        self._next_trigger = None


    def onNewPixelData(self,pixelData):
        self._pixel_data_to_process.append(pixelData)


    def acquisitionStart(self):
        self.resetAcq()
        self._is_in_acq = True
    def acquisitionStop(self):
        self.sortPixels()
        self._is_in_acq = False
    def windDownThread(self):
        self._run_thread = False


    def run(self):

        while self._run_thread:
            if self._is_in_acq is False:
                continue

            try:
                data = self._pixel_data_to_process.pop(0)
                self.processPixels(data)
            except IndexError:
                pass
            try:
                data = self._trigger_data_to_process.pop(0)
                self.processTrigger(data)
            except IndexError:
                pass

    def processToE(self,toa,spidr_ts,heartbeat):
        
        #shift toa by 4 to accomodate possible ftoa
        toa<<=4
        abs_toa_timestamp = heartbeat & ~(0x3FFFFFFFF)
        #shift spidr timestamp
        abs_toa_timestamp |= (spidr_ts << 18)  
        abs_toa_timestamp |= toa  
        return abs_toa_timestamp    


    def processPixels(self,pixeldata):
        print(pixeldata)
        x,y,toa,tot,hits = self._processPixel(pixeldata)

        if self._x_data is None:
            self._x_data = x
            self._y_data = y
            self._toa_data = toa
            self._tot_data = tot
            self._hit_data = hits
        else:
            
            #Append it
            self._x_data = np.append(self._x_data,x)
            self._y_data = np.append(self._y_data,y)
            self._toa_data = np.append(self._toa_data,toa)
            if tot is not None:
                self._tot_data = np.append(self._tot_data,tot)
            self._hit_data = np.append(self._hit_data,hits)

    def _processPixel(self,pixeldata):

        #Grab pixel data
        pixels = pixeldata[0]
        heartbeat = pixeldata[1]<<4

        x,y,f1,f2,f3,spidr_ts = pixels
        toa = None
        tot = None
        hits = None
        if self._mode == OperationMode.ToAandToT:
            #Do toa processing
            #f1 is toa,f2 is tot, f3 is either ftoa or hit process that
            #Decode toa from gray to binary
            toa = f1
            toa = self.processToE(toa,spidr_ts,heartbeat)
            print('Original',f1)
            print('TOA',toa)
            print('HEartBeat',heartbeat& ~(0x3FFFFFFFF))




            #do the same for tot which is f2
            tot = self.processToE(f2,spidr_ts,heartbeat)

            if self._use_super_pixl: 
                toa += f3    
                hits = np.ones(shape=toa.shape)
            else:
                hits = f3
            #print('TOA ',toa.astype(np.float)*1.56e-9,' TOT ',tot)
            
        elif self._mode == OperationMode.ToA:
            toa = self.processToE(f1,spidr_ts,heartbeat)
            if self._use_super_pixl: 
                toa += f3    
                hits = np.ones(shape=toa.shape)
            else:
                hits = f3 

        #self.newData.emit((x,y,toa,tot,hits))
        return x,y,toa,tot,hits        


