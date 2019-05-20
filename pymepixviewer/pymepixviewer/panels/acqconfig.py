import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.acqconfigui import Ui_Form
from ..core.datatypes import ViewerMode
import logging

logger = logging.getLogger(__name__)


class AcquisitionConfig(QtGui.QWidget,Ui_Form):
    biasVoltageChange = QtCore.pyqtSignal(int)
    

    def __init__(self,parent=None):
        super(AcquisitionConfig, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  

        self._current_mode = ViewerMode.TOA
        self.setupLines()
        self.connectSignals()


    def setupLines(self):
        self.acq_time.setValidator(QtGui.QDoubleValidator(self))


        
    def connectSignals(self):
        self.openpath.clicked.connect(self.openPath)
        self.bias_voltage.valueChanged[int].connect(self.biasVoltageChange.emit)
    def openPath(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",
                                             "/home",
                                             QtGui.QFileDialog.ShowDirsOnly
                                             | QtGui.QFileDialog.DontResolveSymlinks)

        self.path_name.setText(directory)
    
