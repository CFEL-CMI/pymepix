import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np
from pymepix import *
from ui.dataviewer_designer import Ui_Form



class DataVisualizer(QtGui.QWidget,Ui_Form):


    def __init__(self,parent=None):
        super(DataVisualizer,self).__init__(parent)
        self.setupUi(self)
        self._mode  = OperationMode.ToAandToT

        self._toa_roi = pg.LinearRegionItem([0,0.001])
        self._tot_roi = pg.LinearRegionItem([0,0.001])
        self.toa_view.addItem(self._toa_roi)
        self.tot_view.addItem(self._tot_roi)
        toa = self.toa_view.getPlotItem()
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
        self.hit = None
        self.tot_diff = None

        self._toa_roi.sigRegionChangeFinished.connect(self.updateMainPlot)
        self._tot_roi.sigRegionChangeFinished.connect(self.updateMainPlot)
    def onModeChange(self,new_mode):
        self._mode = new_mode

    def updateToA(self,trigger,toa_diff):
        print('TOA DIFF:', toa_diff)
        if toa_diff.size==0:
            return
        try:
            y,x = np.histogram(toa_diff,np.linspace(0.0,toa_diff.max(),100,dtype=np.float))
        except:
            return
        self._toa_data.setData(x=x,y=y, stepMode=True, fillLevel=0, brush=(0,0,255,150))

    def updateToT(self,trigger,tot_diff):
        print('TOT DIFF:', tot_diff)
        if tot_diff.size == 0:
            return
        #compute the difference
        try:
            y,x = np.histogram(tot_diff,np.linspace(0.0,tot_diff.max(),100,dtype=np.float))
        except:
            return
        self._tot_data.setData(x=x,y=y, stepMode=True, fillLevel=0, brush=(0,0,255,150))

    def onNewTriggerData(self,data):
        #Unpack
        print('TRIGGERDATA',data)
        trigger,x,y,toa,tot,hit = data
        self.x = x
        self.y = y
        self.hit = hit
        self.tot_diff = None
        if tot is not None:
            self.tot_diff=tot.astype(np.float)-trigger
            
            self.tot_diff *=1.56e-9     
            self.updateToT(trigger,self.tot_diff)    
        self.toa_diff=toa.astype(np.float)-trigger
        self.toa_diff *=1.56e-9    
        self.updateToA(trigger,self.toa_diff)
           
        self.updateMainPlot()
    def updateMainPlot(self):
        self._viewer_data[...] = 0.0
        view_filter = None
        if self.x is None:
            return
        if self.toa_diff is not None:
            min_t,max_t = self._toa_roi.getRegion()


            view_filter = np.logical_and(self.toa_diff >= min_t,self.toa_diff <= max_t)
        if self.tot_diff is not None:
            min_t,max_t = self._tot_roi.getRegion()
            tot_filter = np.logical_and(self.tot_diff >= min_t,self.tot_diff <= max_t)  
            if view_filter is None:
                view_filter = tot_filter         
            else:
                view_filter = np.logical_and(view_filter,tot_filter)
        
        if view_filter is None:
            x = self.x
            y=self.y
            hit=self.hit
        else:
            x = self.x[view_filter]
            y=self.y[view_filter]
            hit=self.hit[view_filter]
        self._viewer_data[x,y] = hit.astype(np.float)
        print(self._viewer_data[x,y])
        self.viewer.setImage(self._viewer_data)
def main():
    import sys
    app = QtGui.QApplication([])
    daq = DataVisualizer()
    daq.show()

    x = (np.random.rand(1000)*256).astype(np.int)
    y = (np.random.rand(1000)*256).astype(np.int)
    hit=np.ones(1000)
    toa = np.random.rand(1000)*1000.0
    tot = np.random.rand(1000)*1000.0
    daq.onNewTriggerData((0.0,x,y,toa,tot,hit))
    app.exec_()
if __name__=="__main__":
    main()