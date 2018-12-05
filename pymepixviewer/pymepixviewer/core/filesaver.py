from pyqtgraph.Qt import QtCore, QtGui
from pymepix.util.storage import open_output_file,store_raw,store_toa,store_tof,store_centroid
from pymepix.processing import MessageType

import logging

logger = logging.getLogger(__name__)


class FileSaver(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)

        self._raw_file = None
        self._blob_file = None
        self._tof_file = None
        self._toa_file= None
        self._index = 0


    def openFiles(self,filename,index,raw,toa,tof,blob):
        self._index = index
        if raw: 
            self.openRaw(filename)
        if toa: 
            self.openToa(filename)
        if tof: 
            self.openTof(filename)
        if blob: 
            self.openBlob(filename)


    def openRaw(self,filename):
        if self._raw_file is not None:
            self._raw_file.close()
        logger.info('Opening raw file :{}'.format(filename))
        self._raw_file = open_output_file(filename,'raw',index=self._index)

    def openToa(self,filename):
        if self._toa_file is not None:
            self._toa_file.close()
        logger.info('Opening toa file :{}'.format(filename))
        self._toa_file = open_output_file(filename,'toa',index=self._index)


    def openTof(self,filename):
        if self._tof_file is not None:
            self._tof_file.close()
        logger.info('Opening tof file :{}'.format(filename))
        self._tof_file = open_output_file(filename,'tof',index=self._index)
    
    
    def openBlob(self,filename):
        if self._blob_file is not None:
            self._blob_file.close()
        logger.info('Opening blob file :{}'.format(filename))
        self._blob_file = open_output_file(filename,'blob',index=self._index)
    
    def setIndex(self,index):
        self._index = index

    def processData(self,data):
        data_type,result = data

        if data_type is MessageType.RawData:
            if self._raw_file is not None:
                store_raw(self._raw_file,data)

        elif data_type is MessageType.PixelData:
            if self._toa_file is not None:
                store_toa(self._toa_file,data)    

        elif data_type is MessageType.EventData:
            if self._tof_file is not None:
                store_tof(self._tof_file,data)       
        elif data_type is MessageType.CentroidData:
            if self._blob_file is not None:
                store_centroid(self._blob_file,data) 

    def closeFiles(self):
        if self._raw_file is not None:
            logger.info('Closing raw file')
            self._raw_file.close()
            self._raw_file = None
        if self._blob_file is not None:
            logger.info('Closing blob file')
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