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

        self._timepix.attachEventCallback(self.onNewTrigger)
        self.connectSignals()

        self._timepix.startAcquisition()
    
    def startWrite(self,path,prefix):
        self._timepix.filePath=path
        self._timepix.filePrefix = prefix
        self._timepix.beginFileWrite()
    
    def stopWrite(self):
        self._timepix.stopFileWrite()


    def onNewTrigger(self,trigger):

        self.newTriggerData.emit(trigger)

    def onNewPixel(self,pixel):

        self.newPixelData.emit(pixel)

    def connectSignals(self):

        self.newTriggerData.connect(self._viewer_widget.onNewTriggerData)
        self._viewer_widget.startAcqWrite.connect(self.startWrite)
        self._viewer_widget.stopAcqWrite.connect(self.stopWrite)
def main():
    import sys
    app = QtGui.QApplication([])
    daq = MainWindow()
    daq.show()
    app.exec_()
    daq._timepix.stopAcquisition()
    daq._timepix.stopThreads()
if __name__=="__main__":
    main()