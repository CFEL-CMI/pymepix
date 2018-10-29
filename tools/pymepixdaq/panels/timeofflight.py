import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from ui.timeofflightpanelui import Ui_Form
from regionsofinterest import RoiModel,RoiItem
from roidialog import RoiDialog

class TimeOfFlightPanel(QtGui.QWidget,Ui_Form):

    roiUpdate = QtCore.pyqtSignal(str,float,float)
    roiRemoved = QtCore.pyqtSignal(str)
    displayRoi = QtCore.pyqtSignal(str,float,float)



    clearPlots = QtCore.pyqtSignal()
    updatePlots = QtCore.pyqtSignal()

    eventUpdate = QtCore.pyqtSignal(object)


    def __init__(self):
        super(TimeOfFlightPanel, self).__init__()

        # Set up the user interface from Designer.
        self.setupUi(self)


        self._roi_model = RoiModel()

        self.roi_list.setModel(self._roi_model)
        self.setupTofConfig()

        self.connectSignals()

        
    def connectSignals(self):
        self.add_roi.clicked.connect(self.onAddRoi)
        self.remove_roi.clicked.connect(self.onRemoveRoi)


    def onRoiUpdate(self,name,start,end):
        self.roiUpdate.emit(name,start,end)

    def onAddRoi(self):
        

        while True:
            create_roi = RoiDialog(self)

            if create_roi.exec_() == QtGui.QDialog.Accepted:
                name,start,end = create_roi.roiParams()
                if name =="":
                    QtGui.QMessageBox.warning(self,'Invalid name','Please enter a name')
                    continue                    
                if self._roi_model.roiNameExists(name):
                    QtGui.QMessageBox.warning(self,'Roi name','Roi name \'{}\' already exists'.format(name))
                    continue
                else:
                    try:
                        start = float(start)
                    except:
                        QtGui.QMessageBox.warning(self,'Invalid start region','Please enter a valid start region')
                        continue                          

                    try:
                        end = float(end)
                    except:
                        QtGui.QMessageBox.warning(self,'Invalid end region','Please enter a valid end region')
                        continue     

                    roi_item = self._roi_model.addRegionofInterest(name,start*1e-6,end*1E-6)
                    self.tof_view.addItem(roi_item.RoiPlotItem)


                    break
            else:
                break




    def onRemoveRoi(self):
        modelIndex = self.roi_list.currentIndex()
        roi = modelIndex.internalPointer()


        ret = QtGui.QMessageBox.warning(self,'Remove ROI',
                                       'Are you sure you want to remove\n the ROI  \'{}\' ??'.format(roi.columnName),
                                       QtGui.QMessageBox.Ok |
                                        QtGui.QMessageBox.Cancel,
                                       QtGui.QMessageBox.Cancel)
        if ret == QtGui.QMessageBox.Ok:
            self._roi_model.removeRegionofInterest(roi.columnName)
            self.tof_view.removeItem(roi.RoiPlotItem)
            self.roiRemoved.emit(roi.columnName)




    def onEvent(self,event):
        pass



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
    tof.show()

    app.exec_()
if __name__=="__main__":
    main()