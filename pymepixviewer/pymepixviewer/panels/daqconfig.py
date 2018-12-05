import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.daqconfigui import Ui_Form
from ..core.filesaver import FileSaver
import threading
from threading import Thread
import time,os
import logging

logger = logging.getLogger(__name__)

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


    resetPlots = QtCore.pyqtSignal()
    # updateRateChange = QtCore.pyqtSignal(float)
    # eventCountChange = QtCore.pyqtSignal(int)


    # def run_acquisition(self,path_name,prefix,raw_checked,blob_checked,exposure,startindex):

    #     self.startAcquisition.emit(path_name,prefix,raw_checked,blob_checked,exposure,startindex)
    #     self.text_status.setText('Acquiring.....')        
    #     print('STARTING')
    #     if self.acq_time.text() != "":
    #         time_val = int(self.acq_time.text())
    #         if time_val != -1:
    #             time.sleep(time_val)
    #     print('ENDING')
    #     self.endAcquisition()
    def run_acquisition(self,path_name,prefix,raw_checked,blob_checked,exposure,startindex):
        self._in_acq = True
        self.startAcquisition.emit(path_name,prefix,raw_checked,blob_checked,exposure,startindex)
        self.text_status.setText('Acquiring.....')        
        print('STARTING')
        start = time.time()
        if self.acq_time.text() != "":
            time_val = float(self.acq_time.text())
            if time_val != -1:
                start = time.time()
                while time.time() - start < time_val and self._in_acq:
                    time.sleep(0.5)

        tot_time = time.time()-start
        print('ENDING, time taken {}s or {} minutes'.format(tot_time,tot_time/60.0))
        self.endAcquisition()



    def __init__(self,parent=None):
        super(DaqConfigPanel, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  


        self.connectSignals()

        self._repeating_thread = None





    def connectSignals(self):
        # self.openpath.clicked.connect(self.openPath)
        # self.display_rate.valueChanged.connect(self.displayRateChange)
        #self.event_count.returnPressed.connect(self.eventCountChanged)

        self.start_acq.clicked.connect(self.startAcqClicked)
        self.end_acq.clicked.connect(self.endAcqClicked)
        self.acqtab.reset_plots.clicked.connect(self.resetPlots.emit)

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


    def _collectAcquisitionSettings(self):
        acq = self.acqtab

        filename = os.path.join(acq.path_name.text(),acq.file_prefix.text())
        logger.info('Filename to store to: {}'.format(filename))
        index = acq.startindex.value()
        logger.info('Start index is {}'.format(index))
        raw_checked = bool(acq.write_raw.isChecked())
        pixels_checked = bool(acq.write_pixels.isChecked())
        tof_checked = bool(acq.write_tof.isChecked())
        blob_checked = bool(acq.write_blob.isChecked())

        logger.info('File settings: raw:{} toa:{} tof:{} blob:{}'.format(raw_checked,pixels_checked,tof_checked,blob_checked))

        acq_time = float(acq.acq_time.text())
        logger.info('Acq time is {} s'.format(acq_time))

        repeats = int(acq.repeat_value.value())
        logger.info('Will repeat this {} times'.format(repeats))

    def startAcqClicked(self):

        self._collectAcquisitionSettings()
    #     exposure = 10000.0
    #     if self.exposure_time.text() != "":
    #         exposure = float(self.exposure_time.text())*1e-6


    #     raw_checked = bool(self.raw_enable.isChecked())
    #     blob_checked = bool(self.blob_enable.isChecked())

    #     start_index = int(self.startindex.text())

    #     if self._repeating_thread is not None:
    #         self._repeating_thread.cancel()
    #         self._repeating_thread = None
    #     repeats = int(self.repeat_value.text())
    #     self._repeating_thread = RepeatFunction(repeats,self.run_acquisition,(self.path_name.text(),self.file_prefix.text(),raw_checked,blob_checked,exposure,start_index,))
    #     self._repeating_thread.start()

    #     # self.startAcquisition.emit(self.path_name.text(),self.file_prefix.text(),raw_checked,blob_checked,exposure)
    #     # self.text_status.setText('Acquiring.....')

    #     # if self.acq_time.text() != "":
    #     #     time_val = int(self.acq_time.text())
    #     #     if time_val != -1:
    #     #         seconds_to_stop = float(self.acq_time.text())
    #     #         timer = threading.Timer(seconds_to_stop,lambda: self.end_acq.click())
    #     #         timer.start()        

    def endAcquisition(self):
        self.stopAcquisition.emit()
        self.text_status.setText('Live')
        self._in_acq = False
        self._elapsed_time.restart()
    
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