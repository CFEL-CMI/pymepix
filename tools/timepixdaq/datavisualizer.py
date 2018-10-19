import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np
from pymepix import *
from ui.dataviewer_designer import Ui_Form
import time

class DataVisualizer(QtGui.QWidget,Ui_Form):


    def __init__(self,parent=None):
        super(DataVisualizer,self).__init__(parent)
        self.setupUi(self)
        self._mode  = OperationMode.ToAandToT
        self._toa_roi = pg.LinearRegionItem([2780e-6,2800e-6])
        #self._toa_roi = pg.LinearRegionItem([1.688e-3,1.698e-3])
        self._tot_roi = pg.LinearRegionItem([0,0.001])
        
        self.toa_view.addItem(self._toa_roi)
        self.tot_view.addItem(self._tot_roi)
        toa = self.toa_view.getPlotItem()
        #toa.setXRange(0, 500e-6, padding=0)
        toa.setLabel('bottom',text='Trigger Offset',units='s')
        toa.setLabel('left',text='Hits')
        self._toa_data = pg.PlotDataItem()
        toa.addItem(self._toa_data)

        tot = self.tot_view.getPlotItem()
        tot.setLabel('bottom',text='Trigger Offset',units='s')
        tot.setLabel('left',text='Hits')
        self._tot_data = pg.PlotDataItem()
        tot.addItem(self._tot_data)
        self._viewer_data = np.ndarray(shape=(256,256))
        self.x = None
        self.y = None
        self._hist_x = None
        self._hist_y = None
        self.hit = None
        self.tot_diff = None
        self._num = 0
        self._viewer_data[...] = 0.0
        self._toa_roi.sigRegionChangeFinished.connect(self.clearAndChange)

        self._start_time = time.time()
    
    def clearAndChange(self):

        self._viewer_data[...]=0.0
        self.updateMainPlot()

    def onModeChange(self,new_mode):
        self._mode = new_mode

    def updateToA(self,toa_diff):
        cov_diff = toa_diff
        
        #print('TOA DIFF:', cov_diff)
        #print('Bins', np.linspace(0.0,cov_diff.max(),100,dtype=np.float))
        #y,x = np.histogram(cov_diff,np.linspace(0.0,cov_diff.max(),10000,dtype=np.float))
        #y,x = np.histogram(cov_diff,np.linspace(2780e-6,2800e-6,1000,dtype=np.float))
        y,x = np.histogram(cov_diff,np.linspace(0,3e-3,1000,dtype=np.float))
        if self._hist_y is None:
            self._hist_y = y
            self._hist_x = x
        else:
            self._hist_y+= y
        
        
        return True

    def updateToT(self,tot_diff):
        #print('TOT DIFF:', tot_diff)
        if tot_diff.size == 0:
            return
        #compute the difference
        try:
            y,x = np.histogram(tot_diff,np.linspace(0.0,tot_diff.max(),100,dtype=np.float))
        except:
            return
        self._tot_data.setData(x=x,y=y, stepMode=True, fillLevel=0, brush=(0,0,255,150))


    def updatePlots(self):

        end = time.time()
        if end - self._start_time > 0.5:
            if self._hist_x is not None:
                self._toa_data.setData(x=self._hist_x,y=self._hist_y, stepMode=True, fillLevel=0, brush=(0,0,255,150))
            self.viewer.setImage(self._viewer_data,autoLevels=False)
            self._start_time = end

    def onNewTriggerData(self,data):
        #Unpack
        
        #print('Found event')
        triggers,x,y,toa,tot,mapping = data

        tof = toa-triggers[mapping]
        self.x = x
        self.y = y
        self.toa = toa
        self.tot = tot
        self.diff = tof
        #print(self.diff)
        if self.updateToA(tof):
            #self.updateToT(self.tot)
            self.updateMainPlot()
        self.updatePlots()
    def updateMainPlot(self):
        
        min_t,max_t = self._toa_roi.getRegion()
        print(self._toa_roi.getRegion())
        view_filter = np.logical_and(self.diff >= min_t,self.diff <= max_t)
        
 
        x = self.x[view_filter]
        y=self.y[view_filter]
        diff=self.diff[view_filter]

        self._viewer_data[x,y] += 1.0
        #print(np.where(self._viewer_data != 0))
        
def main():
    import sys
    app = QtGui.QApplication([])
    pp = PacketProcessor()
    daq = DataVisualizer()
    pp.onNewEvent.connect(daq.onNewTriggerData)
    daq.show()
    pp.start()

    app.exec_()
if __name__=="__main__":
    main()
