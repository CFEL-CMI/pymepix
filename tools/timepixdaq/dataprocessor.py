import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
import numpy as np
from pymepix import *
import time

class DataProcessor(QtCore.QThread):

    tofHistogram = pyqtSignal(object,object)
    totHistogram = pyqtSignal(object,object)
    integratedFrame = pyqtSignal(object)

    def __init__(self):
        QtCore.QThread.__init__(self)  

        self._updateTime = 1/30
        self._numFrames = 1000

        self.toaHistogram = None
        self.totHistogram = None

        self.integratedFrame = np.ndarray((256,256),dtype=np.float)
        self.integratedFrame[...] = 0

        self._tof_filters = None
        self._tof_host_x= None 
        self._tof_hist_y=None
        self._default_exposure_bin = np.linspace(0,300E-6,1000)
    def reset(self):
        self.toaHistogram = None
        self.totHistogram = None        
        self.integratedFrame[...] = 0

    def computeTofHistogram(self,tof):
        y,x = np.histogram(tof,self._default_exposure_bin)
        self.


    def onNewEvents(self,events):





