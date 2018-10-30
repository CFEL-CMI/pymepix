import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from ui.blobviewui import Ui_Form
import threading
import numpy as np

class BlobView(QtGui.QWidget,Ui_Form):

    def __init__(self,parent=None,start=None,end=None):
        super(BlobView, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)  

        self._start_tof = start
        self._end_tof = end

        self._int_blob_count = 0

        self._matrix = np.ndarray(shape=(256,256),dtype=np.float)
        self._matrix[...]=0.0
    
    def getFilter(self,tof):
        

        if self._start_tof is not None:
            return (tof >= self._start_tof) & (tof < self._end_tof)
        else:
            return (tof>=0.0)



    def updateMatrix(self,x,y,tof,tot):
        tof_filter = self.getFilter(tof)

        self._matrix[x[tof_filter],y[tof_filter]] += 1.0


    def onRegionChange(self,start,end):
        self._start_tof = start
        self._end_tof = end


    def computeDirectionCosine(self,x,y,tof):
        pass



    def updateBlobData(self,cluster_shot,cluster_x,cluster_y,cluster_tof):
        tof_filter = self.getFilter(cluster_tof)
        
        x = cluster_x[tof_filter]
        y = cluster_y[tof_filter]
        tof = cluster_tof[tof_filter]
        shots = cluster_tof[tof_filter]

        uniq_shot,counts = np.unique(shots,return_counts=True)

        self._int_blob_count += np.sum(counts)

        avg_blobs = np.average(counts)

        self.rec_blobs.setText(str(int(avg_blobs)))
        
        self.int_blobs.setText(int(self._int_blob_count))

        self.computeDirectionCosine(x,y,tof)


    def onNewEvent(self,event):
        x,y,tof,tot,cluster_shot,cluster_x,cluster_y,cluster_area,cluster_integral,cluster_eig,cluster_vect,cluster_tof = event
        self.updateMatrix(x,y,tof,tot)
        self.updateBlobData(cluster_shot,cluster_x,cluster_y,cluster_tof )
        
        


        

    def plotData(self):
        self.image_view.setImage(self._matrix,autoLevels=True,autoRange=False)
    
    def clearData(self):
        self._matrix[...]=0.0
        self.plotData()


def main():
    import sys
    app = QtGui.QApplication([])
    config = BlobView()
    config.show()

    app.exec_()
if __name__=="__main__":
    main()