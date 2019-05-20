import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.processingconfigui import Ui_Form



class ProcessingConfig(QtGui.QWidget,Ui_Form):

    eventWindowChanged = QtCore.pyqtSignal(float,float)
    totThresholdChanged = QtCore.pyqtSignal(int)
    centroidSkipChanged = QtCore.pyqtSignal(int)
    blobNumberChanged = QtCore.pyqtSignal(int)
    samplesChanged = QtCore.pyqtSignal(int)
    epsilonChanged = QtCore.pyqtSignal(float)

    def __init__(self,parent=None):
        super(ProcessingConfig, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  

        self.setupLines()
        self.setupSignals()
    def setupLines(self):
        self.min_event_window.setValidator(QtGui.QIntValidator(self))
        self.max_event_window.setValidator(QtGui.QDoubleValidator(self))


    def tofEventWindow(self):
        min_value = float(self.min_event_window.text())*1E-6
        max_value = float(self.max_event_window.text())*1E-6
        self.eventWindowChanged.emit(min_value,max_value)
        self.tot_threshold.valueChanged[int].connect(self.totThresholdChanged.emit)
        self.centroid_skip.valueChanged[int].connect(self.centroidSkipChanged.emit)
        self.blob_num.valueChanged[int].connect(self.blobNumberChanged.emit)
        self.samples.valueChanged[int].connect(self.samplesChanged.emit)
        self.epsilon.valueChanged[float].connect(self.epsilonChanged.emit)
    def setupSignals(self):
        self.min_event_window.returnPressed.connect(self.tofEventWindow)
        self.max_event_window.returnPressed.connect(self.tofEventWindow)