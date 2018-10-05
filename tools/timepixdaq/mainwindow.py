import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np
from pymepix import *
from ui.mainwindow_designer import Ui_MainWindow
from timepixconfig import TimepixConfiguration
from datavisualizer import DataVisualizer
from dataprocessor import DataProcessor
class MainWindow(QtGui.QMainWindow,Ui_MainWindow):


    newPixelData = QtCore.pyqtSignal(object)
    newTriggerData = QtCore.pyqtSignal(object)
    acquisitionStart = QtCore.pyqtSignal()
    def __init__(self,parent=None):
        super(MainWindow,self).__init__(parent)
        self.setupUi(self)
        self._viewer_widget = DataVisualizer(parent=self)
        self.setCentralWidget(self._viewer_widget)
        self._timepix = TimePixAcq(('192.168.1.10',50000))

        tabwidget = QtGui.QTabWidget(parent=self)
        

        self._dock_tab_widget = QtGui.QDockWidget(parent=self)
        self._config_widget = TimepixConfiguration(self._timepix)
        tabwidget.addTab(self._config_widget,'Configuration')
        self._dock_tab_widget.setWidget(tabwidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self._dock_tab_widget)

        self._data_processor = DataProcessor()
        self._timepix.attachPixelCallback(self.onNewPixel)
        self._timepix.attachTriggerCallback(self.onNewTrigger)
        self.connectSignals()

        self._data_processor.start()
        self.startAcquisiton()
    
    def onNewTrigger(self,trigger):

        self.newTriggerData.emit(trigger)

    def onNewPixel(self,pixel):

        self.newPixelData.emit(pixel)

    def connectSignals(self):
        self.newPixelData.connect(self._data_processor.onNewPixelData)
        self.newTriggerData.connect(self._data_processor.onNewTrigger)

        self._data_processor.triggerRegionData.connect(self._viewer_widget.onNewTriggerData)
        self.acquisitionStart.connect(self._data_processor.acquisitionStart)
        self.acquisitionStart.connect(self._timepix.startAcquisition)
    def startAcquisiton(self):
        self.acquisitionStart.emit()

def main():
    import sys
    app = QtGui.QApplication([])
    daq = MainWindow()
    daq.show()
    app.exec_()
if __name__=="__main__":
    main()