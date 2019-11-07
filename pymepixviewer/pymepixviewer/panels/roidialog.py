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
from .ui.roidialogui import Ui_Dialog


class RoiDialog(QtGui.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super(RoiDialog, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)
        self.roi_start.setValidator(QtGui.QDoubleValidator(self))
        self.roi_end.setValidator(QtGui.QDoubleValidator(self))

    def roiParams(self):
        return self.roi_name.text(), self.roi_start.text(), self.roi_end.text()


def main():
    import sys
    app = QtGui.QApplication([])
    tof = RoiDialog()
    if tof.exec_() == QtGui.QDialog.Accepted:
        print(tof.roiParams())


if __name__ == "__main__":
    main()
