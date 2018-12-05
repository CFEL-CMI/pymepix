from pyqtgraph.Qt import QtCore, QtGui
from pymepix.util.storage import open_output_file,store_raw,store_toa,store_tof,store_centroid
from pymepix.processing import MessageType
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
        
        self._raw_file = open_output_file(filename,'.raw',index=self._index)
    
    def openTof(self,filename):
        if self._tof_file is not None:
            self._tof_file.close()
        
        self._tof_file = open_output_file(filename,'.tof',index=self._index)
    
    
    def openBlob(self,filename):
        if self._blob_file is not None:
            self._blob_file.close()
        
        self._blob_file = open_output_file(filename,'.blob',index=self._index)
    
    def setIndex(self,index):
        self._index = index

    def processData(self,data):
        data_type,result = data

        if data_type is MessageType.RawData:
            if self._raw_file is not None:
                store_raw(self._raw_file,data)

        elif data_type is MessageType.EventData:
            if self._tof_file is not None:
                store_tof(self._tof_file,data)       
        elif data_type is MessageType.CentroidData:
            if self._blob_file is not None:
                store_centroid(self._blob_file,data) 

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