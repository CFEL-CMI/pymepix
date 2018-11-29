import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.acqconfigui import Ui_Form



class AcquisitionConfig(QtGui.QWidget,Ui_Form):



    def __init__(self,parent=None):
        super(AcquisitionConfig, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  