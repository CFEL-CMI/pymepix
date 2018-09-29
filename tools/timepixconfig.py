import pymepix
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import weakref
from pymepix import *


class TimepixConfiguration(QtGui.QWidget):

    def __init__(self,timepix,parent=None):
        self._ctrl = None
        #self._ctrl = weakref.proxy(timepix)
        QtGui.QWidget.__init__(self,parent)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)


        
        self.param_tree = ParameterTree(parent=self)
        
        self.layout.addWidget(self.param_tree)

        self.setupParameterTree()

        

    def setupParameterTree(self):
        dac_params = self._setupDACParameters()
        acq_params = self._setupAcquisitionParameters()

        
        acq = Parameter.create(name='Acquisition Configuration',type='group',children=acq_params)
        self.timepix_config = Parameter.create(name='TimePix',type='group',children=[acq,dac_params])
        self.param_tree.setParameters(self.timepix_config)
    def _setupDACParameters(self):
        


        dac_params = [ {'name': 'Bias Current Preamp ON','type' : 'float', 'value': 2.5e-6, 'step': 20e-9, 'siPrefix': True,  'limits': (0, 5.1e-6),'suffix': 'A'},
        {'name': 'Bias Current Preamp OFF','type' : 'float', 'value': 150e-9, 'step': 20e-9, 'siPrefix': True, 'limits': (0, 300e-9),'suffix': 'A'},

        {'name': 'VPreamp NCAS','type' : 'float', 'value': 0.634, 'step': 5e-3, 'siPrefix': True, 'limits': (0,1.275),'suffix': 'V'},

        {'name': 'Ibias Ikrum','type' : 'float', 'value': 30e-9, 'step': 240e-9, 'siPrefix': True, 'limits': (0, 60e-9),'suffix': 'A'},

        {'name': 'Voltage feedback','type' : 'float', 'value': 0.634, 'step': 5e-3, 'siPrefix': True, 'limits': (0, 1.275),'suffix': 'V'},

        {'name': 'Voltage Threshold Fine','type' : 'float', 'value': 127e-3, 'step': 0.5e-3, 'siPrefix': True, 'limits': (0, 255e-3),'suffix': 'V'},
        {'name': 'Voltage Threshold Coarse','type' : 'float', 'value': 0.560, 'step': 80e-3, 'siPrefix': True, 'limits': (0, 1.19),'suffix': 'V'},
        {'name': 'Voltage Test Pulse Coarse','type' : 'float', 'value': 634e-3, 'step': 5e-3, 'siPrefix': True, 'limits': (0, 1.275),'suffix': 'V'},
        {'name': 'Voltage Test Pulse Fine','type' : 'float', 'value': 634e-3, 'step': 2.5e-3, 'siPrefix': True, 'limits': (0, 1.275),'suffix': 'V'},
        {'name': 'PLL Voltage Control','type' : 'float', 'value': 724e-3, 'step': 5.7e-3, 'siPrefix': True, 'limits': (0, 1.35),'suffix': 'V'},
           
           
           ]
        dac = Parameter.create(name='DAC Configuration', type='group', children=dac_params)
        children = dac.children()
        #Connect the signals
        children[0].sigValueChanged.connect(self.setBiasCurrentPreampON)
        children[1].sigValueChanged.connect(self.setBiasCurrentPreampOFF)
        return dac

    def setBiasCurrentPreampON(self,param,value):
        value /= 1e-9
        print(value)
        if self._ctrl is not None:
            self._ctrl.Ibias_Preamp_ON = value
    
    def setBiasCurrentPreampOFF(self,param,value):
        value /= 1e-9
        if self._ctrl is not None:
            self._ctrl.Ibias_Preamp_OFF = value        

    def _setupAcquisitionParameters(self):
        return[ {'name': 'Operation Mode','type' : 'list', 'limits': ('ToA + ToT', 'ToA Only','Event Counting and integrated ToT')},
                {'name': 'Polarity','type' : 'list', 'limits': ('h+ collection (positive)', 'e- collection (negative)')},
                {'name': 'Gray counter (ToA only)','type' : 'list', 'limits': ('Disable', 'Enable')},
                {'name': 'Fast ToA','type' : 'list', 'limits': ('Disable', 'Enable')},
                {'name': 'Timer Overflow','type' : 'list', 'limits': ('Cycle', 'Stop')},
                
                
                ]





def main():
    tpx = None#pymepix.TimePixAcq(('192.168.1.10',50000))
    app = QtGui.QApplication([])
    daq = TimepixConfiguration(tpx)
    daq.show()

    app.exec_()
    tpx.stopThreads()

if __name__=="__main__":
    main()

