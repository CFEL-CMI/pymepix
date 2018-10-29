import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np
from pymepix import *
import threading
from ui.dataview_designer_new import Ui_Form
import time

class DataVisualizer(QtGui.QWidget,Ui_Form):

    startAcqWrite = QtCore.pyqtSignal(str,str,float)
    stopAcqWrite = QtCore.pyqtSignal()

    startCamera = QtCore.pyqtSignal(str,str)
    stopCamera = QtCore.pyqtSignal()

    def __init__(self,parent=None):
        super(DataVisualizer,self).__init__(parent)
        self.setupUi(self)
        self._mode  = OperationMode.ToAandToT
        self._toa_roi = pg.LinearRegionItem([0e-6,20e-6])
        self._toa_max = 20E-6
        self._toa_min = 0
        self._toa_bins=1000
        #self._toa_roi = pg.LinearRegionItem([1.688e-3,1.698e-3])
        
        self.toa_view.addItem(self._toa_roi)
        toa = self.toa_view.getPlotItem()
        #toa.setXRange(0, 500e-6, padding=0)
        toa.setLabel('bottom',text='Trigger Offset',units='s')
        toa.setLabel('left',text='Hits')
        self._toa_data = pg.PlotDataItem()
        toa.addItem(self._toa_data)
        self._viewer_data = np.ndarray(shape=(256,256))
        self._live_viewer_data = np.ndarray(shape=(256,256))
        self.x = None
        self.y = None
        self._hist_x = None
        self._hist_y = None
        self.hit = None
        self.tot_diff = None
        self._num = 0
        self._viewer_data[...] = 0.0
        self._live_viewer_data[...] = 0.0
        self._toa_roi.sigRegionChangeFinished.connect(self.clearAndChange)

        self._tot_histo = None

        self._start_time = time.time()

        self.exposure.returnPressed.connect(self.onExposureSet)
        self.sexposure.returnPressed.connect(self.onSexposureSet)
        self.bins.returnPressed.connect(self.onBinSet)
        self.reset_toa.clicked.connect(self.onReset)
        self.openpath.clicked.connect(self.openPath)
        self.startAcq.stateChanged.connect(self.onCheck)

    def openPath(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",
                                             "/home",
                                             QtGui.QFileDialog.ShowDirsOnly
                                             | QtGui.QFileDialog.DontResolveSymlinks)

        self.path_name.setText(directory)
    
    def onCheck(self,status):
        if status == 2:
            self.onStartAcq()
        else:
            self.onStopAcq()

    def onStartAcq(self):

        print(self.path_name.text(),self.file_prefix.text())
        exposure = 10000.0
        if self.exposure_time.text() != "":
            exposure = float(self.exposure_time.text())*1e-6


        self.startAcqWrite.emit(self.path_name.text(),self.file_prefix.text(),exposure)
        if self.timeValue.text() != "":
            seconds_to_stop = float(self.timeValue.text())
            timer = threading.Timer(seconds_to_stop,lambda: self.startAcq.setChecked(False))
            timer.start()
    def onStopAcq(self):
        self.stopAcqWrite.emit()

    def clearAndChange(self):

        self._viewer_data[...]=0.0
        self._live_viewer_data[...] = 0.0
        self._tot_histo = None
        self.updateMainPlot()

    def onSexposureSet(self):
        self._toa_min = float(self.sexposure.text())*1E-6
        self.clearToa()
        self.clearAndChange()

    def onExposureSet(self):
        self._toa_max = float(self.exposure.text())*1E-6
        self.clearToa()
        self.clearAndChange()
    def onBinSet(self):
        self._toa_bins  =int(self.bins.text())
        self.clearToa()
    def onReset(self):
        self.clearToa()
        self.clearAndChange()

    def clearToa(self):
        self._hist_x = None
        self._hist_y = None

    def onModeChange(self,new_mode):
        self._mode = new_mode

    def updateToA(self,toa_diff):
        cov_diff = toa_diff
        
        #print('TOA DIFF:', cov_diff)
        #print('Bins', np.linspace(0.0,cov_diff.max(),100,dtype=np.float))
        #y,x = np.histogram(cov_diff,np.linspace(0.0,cov_diff.max(),10000,dtype=np.float))
        #y,x = np.histogram(cov_diff,np.linspace(2780e-6,2800e-6,1000,dtype=np.float))
        y,x = np.histogram(cov_diff,np.linspace(self._toa_min,self._toa_max,self._toa_bins,dtype=np.float))
        if self._hist_y is None:
            self._hist_y = y
            self._hist_x = x
        else:
            self._hist_y+= y
        
        
        return True

    def updateToT(self,filt):
        #print('TOT DIFF:', tot_diff)
        #compute the difference
        H, xedges, yedges = np.histogram2d(x=self.diff, y=self.tot, bins=100,range=[[self._toa_min,self._toa_max],[0,4000]])
        
        if self._tot_histo is None:
            self._tot_histo = H
        else:
            self._tot_histo += H
        #self._tot_data.setData(x=self.diff[filt],y=self.tot[filt],  pen=None, symbol='o', symbolPen=None, symbolSize=3, symbolBrush=(100, 100, 255, 50))


    def updatePlots(self):

        end = time.time()
        if end - self._start_time > 0.125:
            if self._hist_x is not None:
                self._toa_data.setData(x=self._hist_x,y=self._hist_y, stepMode=True, fillLevel=0, brush=(0,0,255,150))
            self.viewer.setImage(self._viewer_data,autoLevels=False,autoRange=False)
            if self._tot_histo is not None:
                self.tot_view.setImage(self._tot_histo,autoLevels=False)
            self.live_viewer.setImage(self._live_viewer_data,autoLevels=True,autoRange=False)
            self._start_time = end

    def onNewTriggerData(self,data):
        #Unpack
        # self._num+=1
        # if self._num % 10 != 0:
        #     return

        #print('Found event')
        x,y,tof,cluster_shot,cluster_x,cluster_y,cluster_area,cluster_integral,cluster_eig,cluster_vect = data
        #print('Trigger delta',triggers,np.ediff1d(triggers))

        self.x = x
        self.y = y
        #self.tot = tot
        self.diff = tof
        #print(self.diff)
        if self.updateToA(tof):
            
            self.updateMainPlot()
        self.updatePlots()
    def updateMainPlot(self):
        self._live_viewer_data[...]=0.0
        min_t,max_t = self._toa_roi.getRegion()
        #print(self._toa_roi.getRegion())
        view_filter = np.logical_and(self.diff >= min_t,self.diff <= max_t)
        
 
        x = self.x[view_filter]
        y=self.y[view_filter]
        diff=self.diff[view_filter]
        self.updateToT(view_filter)
        self._viewer_data[x,y] += 1.0
        self._live_viewer_data[x,y] = diff
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
