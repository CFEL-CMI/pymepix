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
from .ui.viewerconfigui import Ui_Form
from ..core.datatypes import ViewerMode
import logging

logger = logging.getLogger(__name__)


class ViewerConfig(QtGui.QWidget, Ui_Form):
    resetPlots = QtCore.pyqtSignal()
    updateRateChange = QtCore.pyqtSignal(float)
    eventCountChange = QtCore.pyqtSignal(int)
    frameTimeChange = QtCore.pyqtSignal(float)

    modeChange = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(ViewerConfig, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self._current_mode = ViewerMode.TOA

        self.setupLines()
        self.connectSignals()
        self.handleMode()

    def setupLines(self):
        self.event_count.setValidator(QtGui.QIntValidator(self))
        self.frame_time.setValidator(QtGui.QDoubleValidator(self))

    def connectSignals(self):
        self.display_rate.valueChanged.connect(self.displayRateChange)
        self.event_count.returnPressed.connect(self.eventCountChanged)
        self.frame_time.returnPressed.connect(self.frameTimeChanged)
        self.reset_plots.clicked.connect(self.resetPlots.emit)
        self.mode_box.currentIndexChanged[int].connect(self.modeChanged)

    def modeChanged(self, value):

        if value == 0:
            self.modeChange.emit(ViewerMode.TOA)
            self._current_mode = ViewerMode.TOA
        elif value == 1:
            self.modeChange.emit(ViewerMode.TOF)
            self._current_mode = ViewerMode.TOF
        elif value == 2:
            self.modeChange.emit(ViewerMode.Centroid)
            self._current_mode = ViewerMode.Centroid

        self.handleMode()

    def handleMode(self):

        if self._current_mode is ViewerMode.TOA:
            self.eventwidget.hide()
            self.framelayout.show()
        elif self._current_mode in (ViewerMode.TOF, ViewerMode.Centroid,):
            self.eventwidget.show()
            self.framelayout.hide()

    def displayRateChange(self, value):
        seconds = 1.0 / value
        self.updateRateChange.emit(seconds)

    def eventCountChanged(self):

        self.eventCountChange.emit(int(self.event_count.text()))

    def frameTimeChanged(self):
        frame_time = float(self.frame_time.text())

        if self.time_multi.currentText() == "s":
            frame_time *= 1
        elif self.time_multi.currentText() == "ms":
            frame_time *= 1E-3

        logger.info('Frame time changed to {} s'.format(frame_time))

        self.frameTimeChange.emit(frame_time)
