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

import pymepix
from pymepix.processing import MessageType
import pyqtgraph as pg
import numpy as np
import time
from pyqtgraph.Qt import QtCore, QtGui
from .panels.timeofflight import TimeOfFlightPanel
from .panels.daqconfig import DaqConfigPanel
from .panels.blobview import BlobView
from .ui.mainui import Ui_MainWindow
from .core.datatypes import ViewerMode
import logging

logger = logging.getLogger(__name__)


class PymepixDAQ(QtGui.QMainWindow, Ui_MainWindow):
    displayNow = QtCore.pyqtSignal()
    onRaw = QtCore.pyqtSignal(object)
    onPixelToA = QtCore.pyqtSignal(object)
    onPixelToF = QtCore.pyqtSignal(object)
    onCentroid = QtCore.pyqtSignal(object)
    clearNow = QtCore.pyqtSignal()
    modeChange = QtCore.pyqtSignal(object)

    fineThresholdUpdate = QtCore.pyqtSignal(float)
    coarseThresholdUpdate = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super(PymepixDAQ, self).__init__(parent)
        self.setupUi(self)

        self._current_mode = ViewerMode.TOA
        self.setupWindow()

        self._view_widgets = {}

        self._event_max = -1
        self._current_event_count = 0

        self.setCentralWidget(None)

        self._display_rate = 1 / 5
        self._frame_time = -1.0
        self._last_frame = 0.0
        self._last_update = 0
        self.connectSignals()
        self.startupTimepix()

        #
        time.sleep(1.0)
        self.onModeChange(ViewerMode.TOA)

    def switchToMode(self):
        self._timepix.stop()
        if self._current_mode is ViewerMode.TOA:
            # self._timepix[0].setupAcquisition(pymepix.processing.PixelPipeline)
            self._timepix[0].acquisition.enableEvents = False
            logger.info('Switch to TOA mode, {}'.format(self._timepix[0].acquisition.enableEvents))
        elif self._current_mode is ViewerMode.TOF:
            # self._timepix[0].setupAcquisition(pymepix.processing.PixelPipeline)
            self._timepix[0].acquisition.enableEvents = True
            logger.info('Switch to TOF mode, {}'.format(self._timepix[0].acquisition.enableEvents))
        elif self._current_mode is ViewerMode.Centroid:
            # self._timepix[0].setupAcquisition(pymepix.processing.CentroidPipeline)
            self._timepix[0].acquisition.enableEvents = True
            logger.info('Switch to Centroid mode, {}'.format(self._timepix[0].acquisition.enableEvents))

        time.sleep(2.0)
        self._timepix.start()

    def startupTimepix(self):

        self._timepix = pymepix.Pymepix(('192.168.1.10', 50000))

        if len(self._timepix) == 0:
            logger.error('NO TIMEPIX DEVICES DETECTED')
            quit()

        logging.getLogger('pymepix').setLevel(logging.INFO)

        self._timepix[0].setupAcquisition(pymepix.processing.CentroidPipeline)
        # self._timepix.
        self._timepix.dataCallback = self.onData
        self._timepix[0].pixelThreshold = np.zeros(shape=(256, 256), dtype=np.uint8)
        self._timepix[0].pixelMask = np.zeros(shape=(256, 256), dtype=np.uint8)
        self._timepix[0].uploadPixels()

        logger.info('Fine: {} Coarse: {}'.format(self._timepix[0].Vthreshold_fine, self._timepix[0].Vthreshold_coarse))

        self.coarseThresholdUpdate.emit(self._timepix[0].Vthreshold_coarse)
        self.fineThresholdUpdate.emit(self._timepix[0].Vthreshold_fine)

        self._timepix.start()

    def closeTimepix(self):
        self._timepix.stop()

    def setFineThreshold(self, value):
        self._timepix[0].Vthreshold_fine = value

    def setCoarseThreshold(self, value):
        self._timepix[0].Vthreshold_coarse = value

    def setEventWindow(self, min_v, max_v):
        logger.info('Setting Event window {} {}'.format(min_v, max_v))
        self._timepix[0].acquisition.eventWindow = (min_v, max_v)

    def setTotThreshold(self, tot):
        logger.info('Setting Tot threshold {}'.format(tot))
        self._timepix[0].acquisition.totThreshold = tot

    def setCentroidSkip(self, skip):
        logger.info('Setting centroid skip {}'.format(skip))
        self._timepix[0].acquisition.centroidSkip = skip

    def setBlobProccesses(self, blob):
        import time
        logger.info('Setting number of blob processes {}'.format(blob))
        self._timepix.stop()
        time.sleep(10)
        self._timepix[0].acquisition.numBlobProcesses = blob
        self._timepix.start()

    def setEpsilon(self, epsilon):
        logger.info('Setting epsilon {}'.format(epsilon))
        self._timepix[0].acquisition.epsilon = epsilon

    def setSamples(self, samples):
        logger.info('Setting samples {}'.format(samples))
        self._timepix[0].acquisition.samples = samples

    def connectSignals(self):
        self.actionSophy_spx.triggered.connect(self.getfile)
        self._config_panel.viewtab.updateRateChange.connect(self.onDisplayUpdate)
        self._config_panel.viewtab.eventCountChange.connect(self.onEventCountUpdate)
        self._config_panel.viewtab.frameTimeChange.connect(self.onFrameTimeUpdate)
        self._config_panel.acqtab.biasVoltageChange.connect(self.onBiasVoltageUpdate)

        self._config_panel.acqtab.fine_threshold.valueChanged.connect(self.setFineThreshold)
        self._config_panel.acqtab.coarse_threshold.valueChanged.connect(self.setCoarseThreshold)

        self.fineThresholdUpdate.connect(self._config_panel.acqtab.fine_threshold.setValue)
        self.coarseThresholdUpdate.connect(self._config_panel.acqtab.coarse_threshold.setValue)
        self._config_panel.viewtab.modeChange.connect(self.onModeChange)
        self.displayNow.connect(self._tof_panel.displayTof)
        self.onPixelToF.connect(self._tof_panel.onEvent)
        self.onCentroid.connect(self._tof_panel.onBlob)
        self.clearNow.connect(self._tof_panel.clearTof)
        self._tof_panel.roiUpdate.connect(self.onRoiChange)
        self._tof_panel.displayRoi.connect(self.addViewWidget)

        self.displayNow.connect(self._overview_panel.plotData)

        self.onPixelToA.connect(self._overview_panel.onToA)
        self.onPixelToF.connect(self._overview_panel.onEvent)
        self.onCentroid.connect(self._overview_panel.onCentroid)
        self.clearNow.connect(self._overview_panel.clearData)
        self.modeChange.connect(self._overview_panel.modeChange)

        # self._config_panel.startAcquisition.connect(self.startAcquisition)
        # self._config_panel.stopAcquisition.connect(self.stopAcquisition)

        self._config_panel.viewtab.resetPlots.connect(self.clearNow.emit)
        self._config_panel.proctab.eventWindowChanged.connect(self.setEventWindow)
        self._config_panel.proctab.totThresholdChanged.connect(self.setTotThreshold)
        self._config_panel.proctab.centroidSkipChanged.connect(self.setCentroidSkip)
        self._config_panel.proctab.blobNumberChanged.connect(self.setBlobProccesses)
        self._config_panel.proctab.epsilonChanged.connect(self.setEpsilon)
        self._config_panel.proctab.samplesChanged.connect(self.setSamples)

        self.onRaw.connect(self._config_panel.fileSaver.onRaw)
        self.onPixelToA.connect(self._config_panel.fileSaver.onToa)
        self.onPixelToF.connect(self._config_panel.fileSaver.onTof)
        self.onCentroid.connect(self._config_panel.fileSaver.onCentroid)

    def onBiasVoltageUpdate(self, value):
        logger.info('Bias Voltage changed to {} V'.format(value))
        self._timepix.biasVoltage = value

    def onDisplayUpdate(self, value):
        logger.info('Display rate changed to {} s'.format(value))
        self._display_rate = value

    def onEventCountUpdate(self, value):
        self._event_max = value
        self._current_event_count = 0

    def onFrameTimeUpdate(self, value):
        logger.info('Frame time set to {} s'.format(value))
        self._frame_time = value

    def onModeChange(self, value):
        logger.info('Viewer mode changed to {}'.format(value))
        self._current_mode = value
        if self._current_mode is ViewerMode.TOA:
            # Hide TOF panel
            self._dock_tof.hide()
            for k, view in self._view_widgets.items():
                view.hide()

        elif self._current_mode in (ViewerMode.TOF, ViewerMode.Centroid,):
            # Show it
            self._dock_tof.show()
            for k, view in self._view_widgets.items():
                view.show()
        self.switchToMode()

        self.modeChange.emit(value)

    def onData(self, data_type, event):

        # if self._event_max != -1 and self._current_event_count > self._event_max:
        #     self.clearNow.emit()
        #     self._current_event_count = 0

        # event_shots = event[4]
        check_update = time.time()

        # if data_type in (MessageType.PixelData,):
        #     self.clearNow.emit()

        if self._current_mode is ViewerMode.TOA:
            if self._frame_time >= 0 and (check_update - self._last_frame) > self._frame_time:
                self.clearNow.emit()
                self._last_frame = time.time()

        if self._current_mode in (ViewerMode.TOF, ViewerMode.Centroid,) and \
                data_type in (MessageType.EventData, MessageType.CentroidData,):

            event_shots = event[0]

            if self._event_max != -1 and self._current_event_count > self._event_max:
                self.clearNow.emit()
                self._current_event_count = 0

            try:
                num_events = event_shots.max() - event_shots.min() + 1
            except ValueError:
                logger.warning('Events has no identity {}'.format(event_shots))
                return
            self._current_event_count += num_events

        if data_type is MessageType.RawData:
            self.onRaw.emit(event)
        elif data_type is MessageType.PixelData:
            logger.debug('RAW: {}'.format(event))
            self.onPixelToA.emit(event)
        elif data_type is MessageType.EventData:
            logger.debug('TOF: {}'.format(event))
            self.onPixelToF.emit(event)
        elif data_type is MessageType.CentroidData:
            logger.debug('CENTROID: {}'.format(event))
            self.onCentroid.emit(event)

        # if data_type in (MessageType.PixelData,):
        #     self.displayNow.emit()

        if (check_update - self._last_update) > self._display_rate:
            self.displayNow.emit()
            # self.displayNow.emit()
            self._last_update = time.time()

    # def startAcquisition(self,pathname,prefixname,do_raw,do_blob,exposure,startindex):
    #     self._timepix.filePath=pathname
    #     self._timepix.filePrefix = prefixname
    #     self._timepix.eventWindowTime = exposure

    #     logger.debug('Do raw',do_raw,'Do_blob',do_blob)
    #     self._timepix.beginFileWrite(write_raw=do_raw,write_blob=do_blob,start_index=startindex)

    # def stopAcquisition(self):
    #     self._timepix.stopFileWrite()

    def addViewWidget(self, name, start, end):
        if name in self._view_widgets:
            QtGui.QMessageBox.warning(self, 'Roi name', 'Roi display of name \'{}\' already exists'.format(name))
            return
        else:
            dock_view = QtGui.QDockWidget('Display {}'.format(name), self)
            blob_view = BlobView(start=start, end=end, parent=self, current_mode=self._current_mode)
            dock_view.setWidget(blob_view)
            self._view_widgets[name] = dock_view
            self.displayNow.connect(blob_view.plotData)
            self.onPixelToA.connect(blob_view.onToA)
            self.onPixelToF.connect(blob_view.onEvent)
            self.onCentroid.connect(blob_view.onCentroid)
            self.clearNow.connect(blob_view.clearData)
            self.modeChange.connect(blob_view.modeChange)
            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_view)

    def getfile(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                  '/home', "SoPhy File (*.spx)")
        logger.debug(fname)

        if fname[0] == "":
            return

        self._timepix.stop()

        try:
            self._timepix[0].setConfigClass(pymepix.config.SophyConfig)
            self._timepix[0].loadConfig(fname[0])
        except FileNotFoundError:
            QtGui.QMessageBox.warning(None, 'File not found',
                                      'File with name {} not found'.format(fname[0]),
                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok);

        self.coarseThresholdUpdate.emit(self._timepix[0].Vthreshold_coarse)
        self.fineThresholdUpdate.emit(self._timepix[0].Vthreshold_fine)

        self._timepix.start()

        self.clearNow.emit()

    def onRoiChange(self, name, start, end):
        logger.debug('ROICHANGE', name, start, end)
        if name in self._view_widgets:
            logger.debug('FOUND WIDGET', name, start, end)
            self._view_widgets[name].widget().onRegionChange(start, end)
        else:
            logger.debug('Widget for {} does not exist', )

    def setupWindow(self):
        self._tof_panel = TimeOfFlightPanel()
        self._config_panel = DaqConfigPanel()
        self._overview_panel = BlobView()
        self._dock_tof = QtGui.QDockWidget('Time of Flight', self)
        self._dock_tof.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)
        self._dock_tof.setWidget(self._tof_panel)
        self._dock_config = QtGui.QDockWidget('Daq Configuration', self)
        self._dock_config.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)
        self._dock_config.setWidget(self._config_panel)
        self._dock_overview = QtGui.QDockWidget('Overview', self)
        self._dock_overview.setFeatures(QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)
        self._dock_overview.setWidget(self._overview_panel)

        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self._dock_tof)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self._dock_config)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_overview)


def main():
    import sys
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    app = QtGui.QApplication([])

    config = PymepixDAQ()
    app.lastWindowClosed.connect(config.closeTimepix)
    config.show()

    app.exec_()


if __name__ == "__main__":
    main()
