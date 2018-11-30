import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.roidialogui import Ui_Dialog



class RoiDialog(QtGui.QDialog,Ui_Dialog):

    def __init__(self,parent=None):
        super(RoiDialog, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)
        self.roi_start.setValidator(QtGui.QDoubleValidator(self))
        self.roi_end.setValidator(QtGui.QDoubleValidator(self))
    

    def roiParams(self):
        return self.roi_name.text(),self.roi_start.text(),self.roi_end.text()


def main():
    import sys
    app = QtGui.QApplication([])
    tof = RoiDialog()
    if tof.exec_() == QtGui.QDialog.Accepted:
        print(tof.roiParams())
if __name__=="__main__":
    main()




    