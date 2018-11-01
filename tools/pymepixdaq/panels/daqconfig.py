import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.daqconfigui import Ui_Form
import threading
from threading import Thread
import time
class RepeatFunction(Thread):
    """Call a function after a specified number of seconds:

            t = Timer(30.0, f, args=[], kwargs={})
            t.start()
            t.cancel()     # stop the timer's action if it's still waiting

    """

    def __init__(self, n_repeats, function, args=[], kwargs={}):
        Thread.__init__(self)
        self.repeats = n_repeats
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = threading.Event()

    def cancel(self):
        """Stop the timer if it hasn't finished yet"""
        self.finished.set()

    def run(self):
        repeats = 0
        while not self.finished.is_set() and repeats < self.repeats:
            self.function(*self.args, **self.kwargs)
            repeats+=1
        self.finished.set()

class DaqConfigPanel(QtGui.QWidget,Ui_Form):

    startAcquisition = QtCore.pyqtSignal(str,str,bool,bool,float)
    stopAcquisition = QtCore.pyqtSignal()

    resetPlots = QtCore.pyqtSignal()
    updateRateChange = QtCore.pyqtSignal(float)
    eventCountChange = QtCore.pyqtSignal(int)


    def run_acquisition(self,path_name,prefix,raw_checked,blob_checked,exposure):

        self.startAcquisition.emit(path_name,prefix,raw_checked,blob_checked,exposure)
        self.text_status.setText('Acquiring.....')        
        print('STARTING')
        if self.acq_time.text() != "":
            time_val = int(self.acq_time.text())
            if time_val != -1:
                time.sleep(time_val)
        print('ENDING')
        self.endAcquisition()


    def __init__(self,parent=None):
        super(DaqConfigPanel, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  

        self.setupLines()
        self.connectSignals()

        self._acq_thread = None

        self._repeating_thread = None


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


    def startAcqClicked(self):

        print(self.path_name.text(),self.file_prefix.text())
        exposure = 10000.0
        if self.exposure_time.text() != "":
            exposure = float(self.exposure_time.text())*1e-6


        raw_checked = bool(self.raw_enable.isChecked())
        blob_checked = bool(self.blob_enable.isChecked())

        if self._repeating_thread is not None:
            self._repeating_thread.cancel()
            self._repeating_thread = None
        repeats = int(self.repeat_value.text())
        self._repeating_thread = RepeatFunction(repeats,self.run_acquisition,(self.path_name.text(),self.file_prefix.text(),raw_checked,blob_checked,exposure,))
        self._repeating_thread.start()

        # self.startAcquisition.emit(self.path_name.text(),self.file_prefix.text(),raw_checked,blob_checked,exposure)
        # self.text_status.setText('Acquiring.....')

        # if self.acq_time.text() != "":
        #     time_val = int(self.acq_time.text())
        #     if time_val != -1:
        #         seconds_to_stop = float(self.acq_time.text())
        #         timer = threading.Timer(seconds_to_stop,lambda: self.end_acq.click())
        #         timer.start()        

    def endAcquisition(self):
        self.stopAcquisition.emit()
        self.text_status.setText('Live')

    def endAcqClicked(self):
        self.endAcquisition()
        if self._repeating_thread is not None:
            self._repeating_thread.cancel()
            self._repeating_thread = None
def main():
    import sys
    app = QtGui.QApplication([])
    config = DaqConfigPanel()
    config.show()

    app.exec_()
if __name__=="__main__":
    main()