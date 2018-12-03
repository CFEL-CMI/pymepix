import pymepix
from pymepix.processing import MessageType
import pyqtgraph as pg
import numpy as np
import time
from pyqtgraph.Qt import QtCore, QtGui
from .panels.timeofflight import TimeOfFlightPanel
from .panels.daqconfig import DaqConfigPanel
from .panels.blobview import BlobView
from .ui.mainui import Ui_MainWindow
from .core.datatypes import ViewerMode
import logging

logger = logging.getLogger(__name__)

class PymepixDAQ(QtGui.QMainWindow,Ui_MainWindow):

    displayNow = QtCore.pyqtSignal()
    onPixelToA = QtCore.pyqtSignal(object)
    onPixelToF = QtCore.pyqtSignal(object)
    onCentroid = QtCore.pyqtSignal(object)
    clearNow = QtCore.pyqtSignal()
    modeChange = QtCore.pyqtSignal(object)

    def __init__(self,parent=None):
        super(PymepixDAQ, self).__init__(parent)
        self.setupUi(self)
        self.setupWindow() 

        self._view_widgets= {}

        # self._event_max = -1
        # self._current_event_count = 0

        self.onModeChange(ViewerMode.TOA)

        self._display_rate = 1/5
        self._frame_time = -1.0
        self._last_frame = 0.0
        self._last_update = 0
        self.startupTimepix()
        self.connectSignals()
        # 
    def startupTimepix(self):

        self._timepix = pymepix.Pymepix(('192.168.1.10',50000))

        if len(self._timepix) == 0:
            logger.error('NO TIMEPIX DEVICES DETECTED')
            quit()

        logging.getLogger('pymepix').setLevel(logging.INFO)

        self._timepix[0].setupAcquisition(pymepix.processing.CentroidPipeline)

        # self._timepix.
        self._timepix.dataCallback = self.onData
        self._timepix[0].thresholdMask = np.zeros(shape=(256,256),dtype=np.uint8)
        self._timepix[0].pixelMask = np.zeros(shape=(256,256),dtype=np.uint8)
        self._timepix[0].uploadPixels()
        self._timepix.startAcq()        

    def closeTimepix(self):
        self._timepix.stopAcq()




    def connectSignals(self):
        self.actionSophy_spx.triggered.connect(self.getfile)
        self._config_panel.acqtab.updateRateChange.connect(self.onDisplayUpdate)
        self._config_panel.acqtab.eventCountChange.connect(self.onEventCountUpdate)
        self._config_panel.acqtab.frameTimeChange.connect(self.onFrameTimeUpdate)
        self._config_panel.acqtab.biasVoltageChange.connect(self.onBiasVoltageUpdate)
        self._config_panel.acqtab.modeChange.connect(self.onModeChange)
        # self.displayNow.connect(self._tof_panel.displayTof)
        # self.newEvent.connect(self._tof_panel.onEvent)
        # self.clearNow.connect(self._tof_panel.clearTof)
        # self._tof_panel.roiUpdate.connect(self.onRoiChange)
        # self._tof_panel.displayRoi.connect(self.addViewWidget)

        self.displayNow.connect(self._overview_panel.plotData)
        self.onPixelToA.connect(self._overview_panel.onToA)
        self.onPixelToF.connect(self._overview_panel.onEvent)
        self.onCentroid.connect(self._overview_panel.onCentroid)
        self.clearNow.connect(self._overview_panel.clearData)
        # self._config_panel.startAcquisition.connect(self.startAcquisition)
        # self._config_panel.stopAcquisition.connect(self.stopAcquisition)

        # self._config_panel.resetPlots.connect(self.clearNow.emit)



    def onBiasVoltageUpdate(self,value):
        logger.info('Bias Voltage changed to {} V'.format(value))
        self._timepix.biasVoltage = value

    def onDisplayUpdate(self,value):
        logger.info('Display rate changed to {} s'.format(value))
        self._display_rate = value
    def onEventCountUpdate(self,value):
        self._event_max = value
        self._current_event_count = 0

    def onFrameTimeUpdate(self,value):
        logger.info('Frame time set to {} s'.format(value))
        self._frame_time = value
    
    def onModeChange(self,value):
        logger.info('Viewer mode changed to {}'.format(value))
        self._current_mode = value
        if self._current_mode is ViewerMode.TOA:
            #Hide TOF panel
            self._dock_tof.hide()
        elif self._current_mode in (ViewerMode.TOF,ViewerMode.Centroid,):
            #Show it
            self._dock_tof.show()

        self.modeChange.emit(value)

    def onData(self,data_type,event):
        
        # if self._event_max != -1 and self._current_event_count > self._event_max:
        #     self.clearNow.emit()
        #     self._current_event_count = 0


        # event_shots = event[4]
        check_update = time.time()


        # if data_type in (MessageType.PixelData,):
        #     self.clearNow.emit()

    

        if self._current_mode is ViewerMode.TOA:
            if self._frame_time >=0 and (check_update-self._last_frame) > self._frame_time:
                
                self.clearNow.emit()
                self._last_frame = time.time()

        if self._current_mode in (ViewerMode.TOF,ViewerMode.Centroid,) and \
                data_type in (MessageType.EventData,MessageType.CentroidData, ):
            
            event_shots = event[0]

            if self._event_max != -1 and self._current_event_count > self._event_max:
                self.clearNow.emit()
                self._current_event_count = 0

            num_events = event_shots.max()-event_shots.min()+1
            self._current_event_count+= num_events

        
        if data_type is MessageType.PixelData:
            logger.debug('RAW: {}'.format(event))
            self.onPixelToA.emit(event)
        elif data_type is MessageType.EventData:
            self.onPixelToF.emit(event)
        elif data_type is MessageType.CentroidData:
            self.onCentroid.emit(event)

        

        # if data_type in (MessageType.PixelData,):
        #     self.displayNow.emit()


        if (check_update-self._last_update) > self._display_rate:
            self.displayNow.emit()
            #self.displayNow.emit()
            self._last_update = time.time()



    # def startAcquisition(self,pathname,prefixname,do_raw,do_blob,exposure,startindex):
    #     self._timepix.filePath=pathname
    #     self._timepix.filePrefix = prefixname
    #     self._timepix.eventWindowTime = exposure


    #     logger.debug('Do raw',do_raw,'Do_blob',do_blob)
    #     self._timepix.beginFileWrite(write_raw=do_raw,write_blob=do_blob,start_index=startindex)

    # def stopAcquisition(self):
    #     self._timepix.stopFileWrite()

    def addViewWidget(self,name,start,end):
        if name in self._view_widgets:
            QtGui.QMessageBox.warning(self,'Roi name','Roi display of name \'{}\' already exists'.format(name))
            return
        else:
            dock_view = QtGui.QDockWidget('Display {}'.format(name),self)
            blob_view = BlobView(start=start,end=end,parent=self)
            dock_view.setWidget(blob_view)
            self._view_widgets[name] = dock_view
            self.displayNow.connect(blob_view.plotData)
            self.newEvent.connect(blob_view.onNewEvent)
            self.clearNow.connect(blob_view.clearData)
            self.addDockWidget(QtCore.Qt.RightDockWidgetArea,dock_view)

    def getfile(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
            '/home',"SoPhy File (*.spx)")
        logger.debug(fname)

        self._timepix.stopAcq()

        self._timepix[0].loadSophyConfig(fname[0])

        self._timepix.startAcq()

        self.clearNow.emit()
    def onRoiChange(self,name,start,end):
        logger.debug('ROICHANGE',name,start,end)
        if name in self._view_widgets:
            logger.debug('FOUND WIDGET',name,start,end)
            self._view_widgets[name].widget().onRegionChange(start,end)
        else:
            logger.debug('Widget for {} does not exist',)

    def setupWindow(self):
        self._tof_panel = TimeOfFlightPanel()
        self._config_panel = DaqConfigPanel()
        self._overview_panel = BlobView()
        self._dock_tof = QtGui.QDockWidget('Time of Flight',self)
        self._dock_tof.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)
        self._dock_tof.setWidget(self._tof_panel)
        self._dock_config = QtGui.QDockWidget('Daq Configuration',self)
        self._dock_config.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)
        self._dock_config.setWidget(self._config_panel)
        self._dock_overview = QtGui.QDockWidget('Overview',self)
        self._dock_overview.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)
        self._dock_overview.setWidget(self._overview_panel)

        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self._dock_tof)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self._dock_config)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self._dock_overview)


def main():
    import sys
    import logging
    logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    app = QtGui.QApplication([])
    

    
    config = PymepixDAQ()
    app.lastWindowClosed.connect(config.closeTimepix)
    config.show()
    
    app.exec_()
if __name__=="__main__":
    main()