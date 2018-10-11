import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np
from pymepix import *
from dataviewer_designer import Ui_Form
from packetprocessor import PacketProcessor


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
        self._num = 0
        self._toa_roi.sigRegionChangeFinished.connect(self.updateMainPlot)
        self._tot_roi.sigRegionChangeFinished.connect(self.updateMainPlot)
    def onModeChange(self,new_mode):
        self._mode = new_mode

    def updateToA(self,toa_diff):
        cov_diff = toa_diff
        
        #print('TOA DIFF:', cov_diff)
        y,x = np.histogram(cov_diff,np.linspace(0.0,cov_diff.max(),100,dtype=np.float))
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
        self._num +=1
        self.x = data.x
        self.y = data.y
        self.toa = data.toa
        self.tot = data.tot
        self.diff = data.toa   
        self.updateToA(self.diff)
        print(self.x)
        self.updateMainPlot()
    def updateMainPlot(self):
        self._viewer_data[...] = 0.0
        min_t,max_t = self._toa_roi.getRegion()

        print(min_t,max_t)
        view_filter = np.logical_and(self.diff >= min_t,self.diff <= max_t)
        
 
        x = self.x[view_filter]
        y=self.y[view_filter]
        diff=self.diff[view_filter]
        self._viewer_data[x,y] = diff
        print(np.where(self._viewer_data != 0))
        self.viewer.setImage(self._viewer_data)
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