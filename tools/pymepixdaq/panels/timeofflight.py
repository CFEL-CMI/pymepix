import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
from ui.timeofflightpanelui import Ui_Form
from regionsofinterest import RoiModel,RoiItem
from roidialog import RoiDialog
import traceback
class TimeOfFlightPanel(QtGui.QWidget,Ui_Form):

    roiUpdate = QtCore.pyqtSignal(str,float,float)
    roiRemoved = QtCore.pyqtSignal(str)
    displayRoi = QtCore.pyqtSignal(str,float,float)

    def __init__(self,parent=None):
        super(TimeOfFlightPanel, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)


        self._roi_model = RoiModel()


        self._histo_x = None
        self._histo_y = None
        self._tof_data = pg.PlotDataItem()
        self.tof_view.addItem(self._tof_data)

        self.roi_list.setModel(self._roi_model)
        self.setupTofConfig()

        self.connectSignals()

        
    def connectSignals(self):
        self.add_roi.clicked.connect(self.onAddRoi)
        self.remove_roi.clicked.connect(self.onRemoveRoi)
        self.display_roi.clicked.connect(self.onDisplayRoi)
        self.update_config.clicked.connect(self.onUpdateTofConfig)

    def clearTof(self):
        self._histo_x = None
        self._histo_y = None
    
    def onUpdateTofConfig(self):

        try:
            start = float(self.event_start.text())
            end = float(self.event_end.text())
            bin = int(self.bin_size.text())
        except Exception as e:
            print(str(e))
            traceback.print_exc()
            return

        if start > end:
            self._tof_start = end
            self._tof_end = start
            self.event_start.setText(str(end))
            self.event_end.setText(str(start))
        else:
            self._tof_start = start
            self._tof_end = end


        self._tof_bin = bin 

                   
    def _updateTof(self,tof):

        y,x = np.histogram(tof,np.linspace(self._tof_start,self._tof_end,self._tof_bin,dtype=np.float))
        if self._histo_x is None:
            self._histo_x = x
            self._histo_y = y
        else:
            self._histo_y += y



    def displayTof(self):
        if self._histo_x is None:
            return
        else:
            self._tof_data.setData(x=self._hist_x,y=self._hist_y, stepMode=True, fillLevel=0, brush=(0,0,255,150))


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
        if self._roi_model.isEmpty():
            return
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

    def onDisplayRoi(self):
        if self._roi_model.isEmpty():
            return
        modelIndex = self.roi_list.currentIndex()
        roi = modelIndex.internalPointer()
        self.displayRoi.emit(roi.columnName,*self.roi.region)



    def onEvent(self,event):
        tof = event[2]

        self._updateTof(tof)



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