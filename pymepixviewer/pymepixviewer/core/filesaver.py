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

from pyqtgraph.Qt import QtCore, QtGui
from pymepix.util.storage import open_output_file, store_raw, store_toa, store_tof, store_centroid
from pymepix.processing import MessageType
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FileSaver(QtCore.QThread):

    def __init__(self):
        QtCore.QObject.__init__(self)

        self._raw_file = None
        self._blob_file = None
        self._tof_file = None
        self._toa_file = None
        self._index = 0

    def openFiles(self, filename, index, raw, toa, tof, blob):
        self._index = index
        if raw:
            self.openRaw(filename)
        if toa:
            self.openToa(filename)
        if tof:
            self.openTof(filename)
        if blob:
            self.openBlob(filename)

    def openRaw(self, filename):
        if self._raw_file is not None:
            self._raw_file.close()
        logger.info('Opening raw file :{}'.format(filename))
        self._raw_file = open_output_file(filename, 'raw', index=self._index)

    def openToa(self, filename):
        if self._toa_file is not None:
            self._toa_file.close()
        logger.info('Opening toa file :{}'.format(filename))
        self._toa_file = open_output_file(filename, 'toa', index=self._index)

    def openTof(self, filename):
        if self._tof_file is not None:
            self._tof_file.close()
        logger.info('Opening tof file :{}'.format(filename))
        self._tof_file = open_output_file(filename, 'tof', index=self._index)

    def openBlob(self, filename):
        if self._blob_file is not None:
            self._blob_file.close()
        logger.info('Opening blob file :{}'.format(filename))
        self._blob_file = open_output_file(filename, 'blob', index=self._index)
        self._blob_x = []
        self._blob_shot = []
        self._blob_y = []
        self._blob_tof = []
        self._blob_tot = []

    def setIndex(self, index):
        self._index = index

    def onRaw(self, data):
        if self._raw_file is not None:
            store_raw(self._raw_file, data)

    def onToa(self, data):
        if self._toa_file is not None:
            store_toa(self._toa_file, data)

    def onTof(self, data):
        if self._tof_file is not None:
            store_tof(self._tof_file, data)

    def convertBlobs(self):
        shot = np.concatenate(self._blob_shot)
        x = np.concatenate(self._blob_x)
        y = np.concatenate(self._blob_y)
        tof = np.concatenate(self._blob_tof)
        tot = np.concatenate(self._blob_tot)
        self._blob_x = []
        self._blob_shot = []
        self._blob_y = []
        self._blob_tof = []
        self._blob_tot = []
        return shot, x, y, tof, tot

    def onCentroid(self, data):
        if self._blob_file is not None and not self._blob_file.closed:
            shot, x, y, tof, tot = data
            self._blob_shot.append(shot)
            self._blob_x.append(x)
            self._blob_y.append(y)
            self._blob_tof.append(tof)
            self._blob_tot.append(tot)
            if len(self._blob_shot) > 1000:
                store_centroid(self._blob_file, self.convertBlobs())

    def closeFiles(self):
        if self._raw_file is not None:
            logger.info('Closing raw file')
            self._raw_file.close()
            self._raw_file = None
        if self._blob_file is not None:
            logger.info('Closing blob file')
            if len(self._blob_shot) > 0:
                store_centroid(self._blob_file, self.convertBlobs())
            self._blob_file.close()
            self._blob_file = None
        if self._tof_file is not None:
            logger.info('Closing tof file')
            self._tof_file.close()
            self._tof_file = None
        if self._toa_file is not None:
            logger.info('Closing toa file')
            self._toa_file.close()
            self._toa_file = None
