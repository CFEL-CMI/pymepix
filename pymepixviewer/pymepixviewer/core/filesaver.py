from pyqtgraph.Qt import QtCore, QtGui
from pymepix.util.storage import open_output_file
class FileSaver(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)

        self._raw_file = None
        self._blob_file = None
        self._tof_file = None
        self._index = 0

    def openRaw(self,filename):
        if self._raw_file is not None:
            self._raw_file.close()
        
        self._raw_file = open_output_file(filename,'.raw',index=index)
    
    def openTof(self,filename):
        if self._tof_file is not None:
            self._tof_file.close()
        
        self._tof_file = open_output_file(filename,'.tof',index=index)
    
    
    def openBlob(self,filename):
        if self._blob_file is not None:
            self._blob_file.close()
        
        self._blob_file = open_output_file(filename,'.blob',index=index)
    

    def close(self):
        if self._raw_file is not None:
            self._raw_file.close()
            self._raw_file = None
        if self._blob_file is not None:
            self._blob_file.close()
            self._blob_file = None
        if self._tof_file is not None:
            self._tof_file.close()
            self._tof_file = None