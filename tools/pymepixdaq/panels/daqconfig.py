import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from ui.daqconfigui import Ui_Form
import threading


class DaqConfigPanel(QtGui.QWidget,Ui_Form):

    startAcquisition = QtCore.pyqtSignal(str,str,bool,bool,float)
    stopAcquisition = QtCore.pyqtSignal()

    updateRateChange = QtCore.pyqtSignal(float)
    eventCountChange = QtCore.pyqtSignal(int)

    def __init__(self,parent=None):
        super(DaqConfigPanel, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  

        self.setupLines()
        self.connectSignals()

    def setupLines(self):
        self.event_count.setValidator(QtGui.QIntValidator(self))
        self.exposure_time.setValidator(QtGui.QDoubleValidator(self))
        self.acq_time.setValidator(QtGui.QDoubleValidator(self))

    def connectSignals(self):
        self.openpath.clicked.connect(self.openPath)
        self.display_rate.valueChanged.connect(self.displayRateChange)
        self.event_count.returnPressed.connect(self.eventCountChanged)

        self.start_acq.clicked.connect(self.startAcqClicked)
        self.end_acq.clicked.connect(self.endAcqClicked)

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


    def startAcqClicked(self):

        print(self.path_name.text(),self.file_prefix.text())
        exposure = 10000.0
        if self.exposure_time.text() != "":
            exposure = float(self.exposure_time.text())*1e-6


        raw_checked = bool(self.raw_enable.isChecked())
        blob_checked = bool(self.blob_enable.isChecked())

        self.startAcquisition.emit(self.path_name.text(),self.file_prefix.text(),raw_checked,blob_checked,exposure)
        self.text_status.setText('Acquiring.....')

        if self.acq_time.text() != "":
            time_val = int(self.acq_time.text())
            if time_val != -1:
                seconds_to_stop = float(self.acq_time.text())
                timer = threading.Timer(seconds_to_stop,lambda: self.end_acq.click())
                timer.start()        

    def endAcqClicked(self):
        self.stopAcquisition.emit()
        self.text_status.setText('Live')
def main():
    import sys
    app = QtGui.QApplication([])
    config = DaqConfigPanel()
    config.show()

    app.exec_()
if __name__=="__main__":
    main()