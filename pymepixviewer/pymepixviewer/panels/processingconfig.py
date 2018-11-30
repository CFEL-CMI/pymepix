import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.processingconfigui import Ui_Form



class ProcessingConfig(QtGui.QWidget,Ui_Form):



    def __init__(self,parent=None):
        super(ProcessingConfig, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  