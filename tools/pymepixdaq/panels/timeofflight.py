import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from ui.timeofflightpanelui import Ui_Form

class RoiItem(object):
    pass

class TimeOfFlightPanel(QtGui.QWidget,Ui_Form):

    roiUpdate = QtCore.pyqtSignal(object)
    clearPlots = QtCore.pyqtSignal()


    def __init__(self):
        super(TimeOfFlightPanel, self).__init__()

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.setupTofConfig()
    

    def onEvent(self,event):
        pass



    def setupTofConfig(self):
        self.event_start.setValidator(QtGui.QDoubleValidator(self))
        self.event_end.setValidator(QtGui.QDoubleValidator(self))
        self.bin_size.setValidator(QtGui.QIntValidator(self))
        self.event_start.setText(str(0.0))
        self.event_end.setText(str(100.0))
        self.bin_size.setText(str(1000))

def main():
    import sys
    app = QtGui.QApplication([])
    tof = TimeOfFlightPanel()
    tof.show()

    app.exec_()
if __name__=="__main__":
    main()