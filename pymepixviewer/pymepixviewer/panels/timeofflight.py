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
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
from pymepixviewer.panels.ui.timeofflightpanelui import Ui_Form
from pymepixviewer.panels.regionsofinterest import RoiModel, RoiItem
from pymepixviewer.panels.roidialog import RoiDialog
import traceback


class TimeOfFlightPanel(QtGui.QWidget, Ui_Form):
    roiUpdate = QtCore.pyqtSignal(str, float, float)
    roiRemoved = QtCore.pyqtSignal(str)
    displayRoi = QtCore.pyqtSignal(str, float, float)

    def __init__(self, parent=None):
        super(TimeOfFlightPanel, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self._roi_model = RoiModel(parent=self)

        self._histo_x = None
        self._histo_y = None
        self._tof_data = pg.PlotDataItem()
        self._gauss_data = pg.PlotCurveItem()
        self.tof_view.addItem(self._tof_data)
        self.tof_view.addItem(self._gauss_data)
        self.tof_view.setLabel('bottom', text='Time of Flight', units='s')
        self.tof_view.setLabel('left', text='Hits')
        self.roi_list.setModel(self._roi_model)

        self._legend = pg.TextItem('FWHM:')
        self.tof_view.addItem(self._legend)
        self._legend.setPos(0, 0)

        self._gaussFit = True

        self._blob_tof_mode = False
        self.setupTofConfig()

        self.connectSignals()

    def connectSignals(self):
        self.add_roi.clicked.connect(self.onAddRoi)
        self.remove_roi.clicked.connect(self.onRemoveRoi)
        self.display_roi.clicked.connect(self.onDisplayRoi)
        self.update_config.clicked.connect(self.onUpdateTofConfig)
        self._roi_model.roiUpdated.connect(self.onRoiUpdate)
        self.blob_tof.stateChanged.connect(self.onCentroidCheck)

    def clearTof(self):
        self._histo_x = None
        self._histo_y = None

    def onCentroidCheck(self, status):
        if status == 2:
            self._blob_tof_mode = True
            self.clearTof()
        else:
            self._blob_tof_mode = False
            self.clearTof()

    def onUpdateTofConfig(self):
        try:
            start = float(self.event_start.text()) * 1e-6
            end = float(self.event_end.text()) * 1E-6
            binning = int(self.bin_size.text())
        except Exception as e:
            print(str(e))
            traceback.print_exc()
            return

        if start > end:
            self._tof_start = end
            self._tof_end = start
            self.event_start.setText(str(end))
            self.event_end.setText(str(start))
        else:
            self._tof_start = start
            self._tof_end = end

        self._tof_bin = binning
        self.clearTof()

    def _updateTof(self, tof):

        y, x = np.histogram(tof, np.linspace(self._tof_start, self._tof_end, self._tof_bin, dtype=np.float))
        if self._histo_x is None:
            self._histo_x = x
            self._histo_y = y
        else:
            self._histo_y += y

    def displayTof(self):
        if self._histo_x is None:
            return
        else:
            self._tof_data.setData(x=self._histo_x, y=self._histo_y, stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
            if self._gaussFit and len(self._histo_y) > 0:
                from scipy.optimize import curve_fit
                fwhm = (2 * np.sqrt(2 * np.log(2)))
                gaussFun = lambda x, a, x0, s: a * np.exp(-0.5 * ((x - x0) / (s / fwhm)) ** 2)
                try:
                    p, cov = curve_fit(gaussFun, self._histo_x[:-1], self._histo_y,
                                       p0=[self._histo_y.max(),
                                           self._histo_x[self._histo_y.argmax()], 1e-6])
                    self._gauss_data.setData(x=self._histo_x, y=gaussFun(self._histo_x, *p))
                    self._legend.setText(f'FWHM: {1e9*np.abs(p[2]):.2f}ns')
                    self._legend.setPos(self._histo_x[0], 0.5*p[0])
                except:
                    return

    def onRoiUpdate(self, name, start, end):
        self.roiUpdate.emit(name, start, end)

    def onAddRoi(self):

        while True:
            create_roi = RoiDialog(self)

            if create_roi.exec_() == QtGui.QDialog.Accepted:
                name, start, end = create_roi.roiParams()
                if name == "":
                    QtGui.QMessageBox.warning(self, 'Invalid name', 'Please enter a name')
                    continue
                if self._roi_model.roiNameExists(name):
                    QtGui.QMessageBox.warning(self, 'Roi name', 'Roi name \'{}\' already exists'.format(name))
                    continue
                else:
                    try:
                        start = float(start)
                    except:
                        QtGui.QMessageBox.warning(self, 'Invalid start region', 'Please enter a valid start region')
                        continue

                    try:
                        end = float(end)
                    except:
                        QtGui.QMessageBox.warning(self, 'Invalid end region', 'Please enter a valid end region')
                        continue
                    print('Adding roi')
                    roi_item = self._roi_model.addRegionofInterest(name, start * 1e-6, end * 1E-6)

                    self.tof_view.addItem(roi_item.RoiPlotItem)

                    break
            else:
                break

    def onRemoveRoi(self):
        if self._roi_model.isEmpty():
            return
        modelIndex = self.roi_list.currentIndex()
        roi = modelIndex.internalPointer()

        ret = QtGui.QMessageBox.warning(self, 'Remove ROI',
                                        'Are you sure you want to remove\n the ROI  \'{}\' ??'.format(roi.columnName),
                                        QtGui.QMessageBox.Ok |
                                        QtGui.QMessageBox.Cancel,
                                        QtGui.QMessageBox.Cancel)
        if ret == QtGui.QMessageBox.Ok:
            self._roi_model.removeRegionofInterest(roi.columnName)
            self.tof_view.removeItem(roi.RoiPlotItem)
            self.roiRemoved.emit(roi.columnName)

    def onDisplayRoi(self):
        if self._roi_model.isEmpty():
            return
        modelIndex = self.roi_list.currentIndex()
        roi = modelIndex.internalPointer()
        if roi is None:
            QtGui.QMessageBox.warning(self, 'No Roi selected', 'Please select an ROI')
            return
        else:
            self.displayRoi.emit(roi.columnName, *roi.region)

    def onEvent(self, event):

        if not self._blob_tof_mode:
            tof = event[3]
            self._updateTof(tof)

    def onBlob(self, blob):
        if self._blob_tof_mode:
            tof = blob[3]
            self._updateTof(tof)

    def setupTofConfig(self):
        self.event_start.setValidator(QtGui.QDoubleValidator(self))
        self.event_end.setValidator(QtGui.QDoubleValidator(self))
        self.bin_size.setValidator(QtGui.QIntValidator(self))
        self.event_start.setText(str(0.0))
        self.event_end.setText(str(100.0))
        self.bin_size.setText(str(1000))

        self._tof_start = 0.0
        self._tof_end = 100.0
        self._tof_bin = 1000


def main():
    import sys
    app = QtGui.QApplication([])
    tof = TimeOfFlightPanel()

    # provide sample data
    np.random.seed(19680801)
    # example data
    mu = 40  # mean of distribution
    sigma = 15  # standard deviation of distribution
    x = mu + sigma * np.random.randn(43700)
    num_bins = 50
    tof._updateTof(x)
    tof.displayTof()


    tof.show()

    app.exec_()

if __name__ == "__main__":
    main()
