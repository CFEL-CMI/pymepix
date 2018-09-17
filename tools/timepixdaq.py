import pymepix
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import tempDaq
import time
import numpy as np
class DataProcessorThread(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)


class TimepixDaq(QtGui.QWidget,tempDaq.Ui_Form):


    def __init__(self,parent=None):
        super(TimepixDaq,self).__init__(parent)
        self.setupUi(self)

        self.imageview = pg.ImageView()
        self._data = np.ndarray(shape=(256,256),dtype=np.float)
        self.pyqtViewLayout.addWidget(self.imageview)

        

        self._timepix = pymepix.TimePixAcq(('192.168.1.10',50000))
        self._timepix.threshold = np.zeros(shape=(256,256),dtype=np.uint8)
        self._timepix.mask = np.ones(shape=(256,256),dtype=np.uint8)
        self._timepix.uploadPixels()
        self.startAcq.clicked.connect(self._timepix.startAcquisition)
        self.stopAcq.clicked.connect(self._timepix.stopAcquisition)

        self._start_time = time.time()
        self._timepix.attachPixelCallback(self.updatePlot)
        self._timepix.shutterTriggerCount = 0
        self._timepix.shutterTriggerExposure = 10000
        self._timepix.shutterTriggerDelay = 1

        self._timepix.operationMode = pymepix.OperationMode.ToAandToT
        self._timepix.shutterTriggerMode = pymepix.SpidrShutterMode.Auto

    def updatePlot(self,pixels):
        current_time = time.time()
        pixel = pixels[0]
        self._data[...]=0
        if (current_time - self._start_time) >0.5:
            self._data[pixel[0],pixel[1]] = pixel[3].astype(np.float)

            self.imageview.setImage(self._data)
            self._start_time = current_time

    def closeTimepix(self):
        self._timepix.stopAcquisition()
        self._timepix.stopThreads()

def main():
    import sys
    app = QtGui.QApplication([])
    daq = TimepixDaq()
    daq.show()

    app.exec_()

    daq.closeTimepix()
if __name__=="__main__":
    main()