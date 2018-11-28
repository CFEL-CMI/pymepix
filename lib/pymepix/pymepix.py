"""Main module for pymepix"""

import numpy as np
from .SPIDR.spidrcontroller import SPIDRController
from.SPIDR.spidrdefs import SpidrReadoutSpeed
from pymepix.core.log import Logger
from .timepixdevice import TimepixDevice
from multiprocessing import Queue
from collections import deque
import threading
import time

class PollBufferEmpty(Exception):
    pass

class Pymepix(Logger):
    """This is the main class to work with timepix
    
    TODO: More docstrings here

    
    """

    def data_thread(self):
        self.info('Starting data thread')
        while True:
            value = self._data_queue.get()
            self.debug('Popped value {}'.format(value))
            if value is None:
                break
            
            data_type,data = value
            self._event_callback(data_type,data)



    def __init__(self,spidr_address,src_ip_port=('192.168.1.1',0)):
        Logger.__init__(self,'Pymepix')
        self._spidr = SPIDRController(spidr_address,src_ip_port)
        
        self._timepix_devices = []

        self._data_queue = Queue()
        self._createTimepix()
        self._spidr.setBiasSupplyEnable(True)
        self.biasVoltage = 50
        self.enablePolling()
        self._data_thread = threading.Thread(target=self.data_thread)
        self._data_thread.daemon = True
        self._data_thread.start()


    @property
    def biasVoltage(self):
        return self._bias_voltage
    
    @biasVoltage.setter
    def biasVoltage(self,value):
        self._bias_voltage = value
        self._spidr.biasVoltage = value
    

    def poll(self,block=False):
        if block:
            while True:
                try:
                    return self._poll_buffer.popleft()
                except IndexError:
                    time.sleep(0.5)
                    continue  
        else:
            try:
                return self._poll_buffer.popleft()
            except IndexError:
                raise PollBufferEmpty
        

    @property
    def pollBufferLength(self):
        return self._poll_buffer.maxlen

    @pollBufferLength.setter
    def pollBufferLength(self,value):
        self.warning('Clearing polling buffer')
        self._poll_buffer = deque(maxlen=value)

    @property
    def dataCallback(self):
        return self._event_callback

    @dataCallback.setter
    def dataCallback(self,value):
        self._event_callback = value
        self.warning('Clearing polling buffer')
        self._poll_buffer.clear()

    def enablePolling(self,maxlen=100):
        self.info('Enabling polling')

        self.pollBufferLength = maxlen
        self.dataCallback = self._pollCallback
    




    def _pollCallback(self,data_type,data):
        self._poll_buffer.append((data_type,data))



    def _createTimepix(self):

        for x in self._spidr:
            status,enabled,locked = x.linkStatus
            if enabled != 0 and locked == enabled:
                self._timepix_devices.append(TimepixDevice(x,self._data_queue)) 
        
        self._num_timepix = len(self._timepix_devices)
        self.info('Found {} Timepix/Medipix devices'.format(len(self._timepix_devices)))
        for idx,tpx in enumerate(self._timepix_devices):
            self.info('Device {} - {}'.format(idx,tpx.devIdToString()))


    def _prepare(self):
        self._spidr.disableExternalRefClock()
        TdcEnable = 0x0000
        self._spidr.setSpidrReg(0x2B8,TdcEnable)
        self._spidr.enableDecoders(True)
        self._spidr.datadrivenReadout()


    def startAcq(self):
        self.info('Starting acquisition')
        self._prepare()
        self._spidr.resetTimers()
        self._spidr.restartTimers()

        for t in self._timepix_devices:
            self.info('Setting up {}'.format(t.deviceName))
            t.setupDevice()

        self._spidr.openShutter()
        for t in self._timepix_devices:
            self.info('Starting {}'.format(t.deviceName))
            t.start()

    def stopAcq(self):
        self.info('Stopping acquisition')
        trig_mode = 0
        trig_length_us = 10000
        trig_freq_hz = 5
        nr_of_trigs = 1

        self._spidr.setShutterTriggerConfig(trig_mode, trig_length_us,
                                                 trig_freq_hz, nr_of_trigs,0)
        self._spidr.closeShutter()        
        self.debug('Closing shutter')
        for t in self._timepix_devices:
            self.debug('Stopping {}'.format(t.deviceName))
            t.stop()       


    @property
    def numDevices(self):
        return self._num_timepix

    
    def __getitem__(self, key):
        return self._timepix_devices[key]

    def __len__(self):
        return len(self._timepix_devices)

    def getDevice(self,num):
        return self._timepix_devices[num]
    




def main():
    import logging
    from .processing.datatypes import MessageType
    from .processing import CentroidPipeline

    logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    pymepix = Pymepix(('192.168.1.10',50000))
    num_devices = len(pymepix)

    pymepix[0].loadSophyConfig('/Users/alrefaie/Documents/repos/libtimepix/config/eq-norm-50V.spx')

    for p in pymepix:
        p.setupAcquisition(CentroidPipeline)
        p.acquisition.enableEvents = False
        p.acquisition.numBlobProcesses = 10

    
    pymepix.biasVoltage = 50

    pymepix.startAcq()
    time.sleep(2.0)
    pymepix.stopAcq()

    while True:
        try:
            value = pymepix.poll()
            data_type,data = value
            #print(value)
            if data_type == MessageType.RawData:
                header = ((data[0] & 0xF000000000000000) >> 60) & 0xF
                filt = (header == 0x6)
                subheader = ((data[0][filt] & 0x0F00000000000000) >> 56) & 0xF
                

                print('SUBHEADERS {}'.format(subheader))

            

        except PollBufferEmpty:
            print('EMPTY')
            break

    pymepix.startAcq()
    time.sleep(5.0)
    pymepix.stopAcq()
    while True:
        try:
            #print(pymepix.poll())
            value = pymepix.poll()
            data_type,data = value
            print(value)
            if data_type == MessageType.RawData:
                subheader = ((data[0] & 0x0F00000000000000) >> 56) & 0xF
                print('SUBHEADERS ',subheader)
        except PollBufferEmpty:
            print('EMPTY')
            break
    print('Done')
if __name__=="__main__":
    main()