import pymepix
import pyqtgraph as pg
import numpy as np
import time
from pyqtgraph.Qt import QtCore, QtGui
from panels.timeofflight import TimeOfFlightPanel
from panels.daqconfig import DaqConfigPanel
from panels.blobview import BlobView

class PymepixDAQ(QtGui.QMainWindow):

    displayNow = QtCore.pyqtSignal()
    newEvent = QtCore.pyqtSignal(object)
    clearNow = QtCore.pyqtSignal()


    def __init__(self,parent=None):
        super(PymepixDAQ, self).__init__(parent)
        self.setupWindow() 

        self._view_widgets= {}

        self._event_max = -1
        self._current_event_count = 0
        self._display_rate = 1/5

        self._last_update = 0

        self.connectSignals()
        self.startupTimepix()
    def startupTimepix(self):
        self._timepix = pymepix.TimePixAcq(('192.168.1.10',50000))

        self._timepix.attachEventCallback(self.onEvent)

        self._timepix.startAcquisition()        

    def connectSignals(self):
        self._config_panel.updateRateChange.connect(self.onDisplayUpdate)
        self._config_panel.eventCountChange.connect(self.onEventCountUpdate)

        self.displayNow.connect(self._tof_panel.displayTof)
        self.newEvent.connect(self._tof_panel.onEvent)
        self.clearNow.connect(self._tof_panel.clearTof)
        self._tof_panel.roiUpdate.connect(self.onRoiChange)
        self._tof_panel.displayRoi.connect(self.addViewWidget)

        self.displayNow.connect(self._overview_panel.plotData)
        self.newEvent.connect(self._overview_panel.onNewEvent)
        self.clearNow.connect(self._overview_panel.clearData)
        self._config_panel.startAcquisition.connect(self.startAcquisition)
        self._config_panel.stopAcquisition.connect(self.stopAcquisition)

        self._config_panel.resetPlots.connect(self.clearNow.emit)

    def onDisplayUpdate(self,value):
        self._display_rate = value
    def onEventCountUpdate(self,value):
        self._event_max = value
        self._current_event_count = 0

    
    def onEvent(self,event):
        
        if self._event_max != -1 and self._current_event_count > self._event_max:
            self.clearNow.emit()
            self._current_event_count = 0


        event_shots = event[4]



        num_events = event_shots.max()-event_shots.min()+1
        self._current_event_count+= num_events


        self.newEvent.emit(event)

        check_update = time.time()

        if (check_update-self._last_update) > self._display_rate:
            self.displayNow.emit()
            self._last_update = time.time()



    def startAcquisition(self,pathname,prefixname,do_raw,do_blob,exposure):
        self._timepix.filePath=pathname
        self._timepix.filePrefix = prefixname
        self._timepix.eventWindowTime = exposure


        print('Do raw',do_raw,'Do_blob',do_blob)
        self._timepix.beginFileWrite(write_raw=do_raw,write_blob=do_blob)

    def stopAcquisition(self):
        self._timepix.stopFileWrite()

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


    
    def onRoiChange(self,name,start,end):
        print('ROICHANGE',name,start,end)
        if name in self._view_widgets:
            print('FOUND WIDGET',name,start,end)
            self._view_widgets[name].widget().onRegionChange(start,end)
        else:
            print('Widget for {} does not exist',)

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


    def cleanupTpx(self):
        self._timepix.stopThreads()


def main():
    import sys
    app = QtGui.QApplication([])
    config = PymepixDAQ()
    config.show()

    app.exec_()
    config.cleanupTpx()
if __name__=="__main__":
    main()