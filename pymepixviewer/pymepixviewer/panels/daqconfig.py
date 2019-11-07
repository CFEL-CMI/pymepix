##############################################################################
##
# This file is part of pymepixviewer
#
# https://arxiv.org/abs/1905.07999
#
#
# pymepixviewer is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pymepixviewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with pymepixviewer.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from .ui.daqconfigui import Ui_Form
from ..core.filesaver import FileSaver
import threading
from threading import Thread
import time, os
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
            repeats += 1
        self.finished.set()


class DaqConfigPanel(QtGui.QWidget, Ui_Form):
    resetPlots = QtCore.pyqtSignal()
    closeFile = QtCore.pyqtSignal()

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
    def run_acquisition(self, acq_time, filename, index, raw, toa, tof, blob):
        try:
            self._in_acq = True
            self._filesaver.openFiles(filename, index, raw, toa, tof, blob)
            self.text_status.setText('Acquiring.....')
            logger.info('Starting Acquisition')
            start = time.time()
            time_val = acq_time
            if time_val != -1:
                start = time.time()
                while time.time() - start < time_val and self._in_acq:
                    time.sleep(0.5)

            tot_time = time.time() - start
            logger.info('ENDING, time taken {}s or {} minutes'.format(tot_time, tot_time / 60.0))
            self.endAcquisition()
        except Exception as e:
            logger.error(str(e))
            return

    def __init__(self, parent=None):
        super(DaqConfigPanel, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self._in_acq = False
        self.connectSignals()

        self._repeating_thread = None
        self._filesaver = FileSaver()
        self.closeFile.connect(self._filesaver.closeFiles)
        self._filesaver.start()

        self._elapsed_time_thread = QtCore.QTimer()
        self._elapsed_time = QtCore.QElapsedTimer()
        self._elapsed_time_thread.timeout.connect(self.updateTimer)
        self._elapsed_time_thread.start(1000)

    @property
    def fileSaver(self):
        return self._filesaver

    def connectSignals(self):
        # self.openpath.clicked.connect(self.openPath)
        # self.display_rate.valueChanged.connect(self.displayRateChange)
        # self.event_count.returnPressed.connect(self.eventCountChanged)

        self.start_acq.clicked.connect(self.startAcqClicked)
        self.end_acq.clicked.connect(self.endAcqClicked)
        self.viewtab.reset_plots.clicked.connect(self.resetPlots.emit)

    def openPath(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",
                                                           "/home",
                                                           QtGui.QFileDialog.ShowDirsOnly
                                                           | QtGui.QFileDialog.DontResolveSymlinks)

        self.path_name.setText(directory)

    def displayRateChange(self, value):
        seconds = 1.0 / value
        self.updateRateChange.emit(seconds)

    def eventCountChanged(self):

        self.eventCountChange.emit(int(self.event_count.text()))

    def _collectAcquisitionSettings(self):
        acq = self.acqtab

        filename = os.path.join(acq.path_name.text(), acq.file_prefix.text())
        logger.info('Filename to store to: {}'.format(filename))
        index = acq.startindex.value()
        logger.info('Start index is {}'.format(index))
        raw_checked = bool(acq.write_raw.isChecked())
        pixels_checked = bool(acq.write_pixels.isChecked())
        tof_checked = bool(acq.write_tof.isChecked())
        blob_checked = bool(acq.write_blob.isChecked())

        logger.info('File settings: raw:{} toa:{} tof:{} blob:{}'.format(raw_checked, pixels_checked, tof_checked,
                                                                         blob_checked))

        acq_time = float(acq.acq_time.text())
        logger.info('Acq time is {} s'.format(acq_time))

        repeats = int(acq.repeat_value.value())
        logger.info('Will repeat this {} times'.format(repeats))

        return filename, index, raw_checked, pixels_checked, tof_checked, blob_checked, acq_time, repeats

    def updateTimer(self):
        if self._in_acq:
            seconds = self._elapsed_time.elapsed() / 1000
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)

            self.elapsed_time_s.display(int(round(s)))
            self.elapsed_time_m.display(int(round(m)))
            self.elapsed_time_h.display(h)

    def startAcqClicked(self):

        filename, index, raw, toa, tof, blob, acq_time, repeats = self._collectAcquisitionSettings()

        if self._repeating_thread is not None:
            self._repeating_thread.cancel()
            self._repeating_thread = None

        logger.info('Staring acquisition thread')
        self._repeating_thread = RepeatFunction(repeats, self.run_acquisition,
                                                (acq_time, filename, index, raw, toa, tof, blob,))
        self._repeating_thread.start()
        self._elapsed_time.restart()

    def endAcquisition(self):
        self.text_status.setText('Live')
        self._in_acq = False
        self.closeFile.emit()
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


if __name__ == "__main__":
    main()
