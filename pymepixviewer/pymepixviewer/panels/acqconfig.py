import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.acqconfigui import Ui_Form
from ..core.datatypes import ViewerMode
import logging

logger = logging.getLogger(__name__)


class AcquisitionConfig(QtGui.QWidget,Ui_Form):

    resetPlots = QtCore.pyqtSignal()
    updateRateChange = QtCore.pyqtSignal(float)
    eventCountChange = QtCore.pyqtSignal(int)   
    frameTimeChange = QtCore.pyqtSignal(float)
    biasVoltageChange = QtCore.pyqtSignal(int)

    modeChange = QtCore.pyqtSignal(object)

    def __init__(self,parent=None):
        super(AcquisitionConfig, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  

        self._current_mode = ViewerMode.TOA

        self.setupLines()
        self.connectSignals()
        self.handleMode()
    def setupLines(self):
        self.event_count.setValidator(QtGui.QIntValidator(self))
        self.acq_time.setValidator(QtGui.QDoubleValidator(self))
        self.frame_time.setValidator(QtGui.QDoubleValidator(self))

    def connectSignals(self):
        self.openpath.clicked.connect(self.openPath)
        self.display_rate.valueChanged.connect(self.displayRateChange)
        self.event_count.returnPressed.connect(self.eventCountChanged)
        self.frame_time.returnPressed.connect(self.frameTimeChanged)
        self.reset_plots.clicked.connect(self.resetPlots.emit)
        self.bias_voltage.valueChanged[int].connect(self.biasVoltageChange.emit)
        self.mode_box.currentIndexChanged[int].connect(self.modeChanged)
    def openPath(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",
                                             "/home",
                                             QtGui.QFileDialog.ShowDirsOnly
                                             | QtGui.QFileDialog.DontResolveSymlinks)

        self.path_name.setText(directory)

    def modeChanged(self,value):
        
        if value == 0:
            self.modeChange.emit(ViewerMode.TOA)
            self._current_mode = ViewerMode.TOA
        elif value == 1:
            self.modeChange.emit(ViewerMode.TOF)
            self._current_mode = ViewerMode.TOF
        elif value == 2:
            self.modeChange.emit(ViewerMode.Centroid)
            self._current_mode = ViewerMode.Centroid
        
        self.handleMode()
    def handleMode(self):


        if self._current_mode is ViewerMode.TOA:
            self.eventwidget.hide()
            self.framelayout.show()
        elif self._current_mode in (ViewerMode.TOF,ViewerMode.Centroid,):
            self.eventwidget.show()
            self.framelayout.hide()
        

    def displayRateChange(self,value):
        seconds = 1.0/value
        self.updateRateChange.emit(seconds)
    
    def eventCountChanged(self):

        self.eventCountChange.emit(int(self.event_count.text()))
    
    def frameTimeChanged(self):
        frame_time = float(self.frame_time.text())

        if self.time_multi.currentText() == "s":
            frame_time*=1
        elif self.time_multi.currentText()=="ms":
            frame_time*=1E-3
        
        logger.info('Frame time changed to {} s'.format(frame_time))

        self.frameTimeChange.emit(frame_time)        