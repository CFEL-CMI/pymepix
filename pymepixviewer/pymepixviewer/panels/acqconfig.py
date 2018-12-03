import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.acqconfigui import Ui_Form
import logging

logger = logging.getLogger(__name__)


class AcquisitionConfig(QtGui.QWidget,Ui_Form):

    resetPlots = QtCore.pyqtSignal()
    updateRateChange = QtCore.pyqtSignal(float)
    eventCountChange = QtCore.pyqtSignal(int)   
    frameTimeChange = QtCore.pyqtSignal(float)

    def __init__(self,parent=None):
        super(AcquisitionConfig, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  

        self.setupLines()
        self.connectSignals()

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

    def openPath(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",
                                             "/home",
                                             QtGui.QFileDialog.ShowDirsOnly
                                             | QtGui.QFileDialog.DontResolveSymlinks)

        self.path_name.setText(directory)

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

        self.updateRateChange.emit(frame_time)        