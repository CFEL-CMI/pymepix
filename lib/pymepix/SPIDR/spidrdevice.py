import weakref
from spidrcmds import SpidrCmds
import numpy as np

class SpidrDevice(object):

    def __init__(self,spidr_ctrl,device_num):
        self._ctrl = weakref.proxy(spidr_ctrl)
        self._dev_num = device_num
        self._pixel_config = np.ndarray(shape=(256,256),dtype=np.uint8)
    @property
    def deviceId(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_DEVICEID,self._dev_num)

    def pixelConfig(self):

        for x in range(256):
            row,pixelcolumn = self._ctrl.requestGetIntBytes(SpidrCmds.CMD_GET_PIXCONF,self._dev_num,256,x)
            #print ('Column : {} Pixels: {}'.format(row,pixelcolumn))
            self._pixel_config[row,:] = pixelcolumn[:]