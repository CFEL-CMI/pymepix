from .baseacquisition import AcquisitionPipeline
from .packetprocessor import PacketProcessor
from .centroiding import TOFCentroiding
from .udpsampler import UdpSampler


class PixelPipeline(AcquisitionPipeline):
    """ An acquisition pipeline that includes the udpsampler and pixel processor """



    def __init__(self,data_queue,address,longtime,use_event=False,name='Pixel'):
        AcquisitionPipeline.__init__(self,name,data_queue)

        self._use_events = use_event
        self._event_window = (0,10000)

        self.addStage(0,UdpSampler,address,longtime)
        self.addStage(2,PacketProcessor)
        self._reconfigureProcessor()

    def _reconfigureProcessor(self):
        self.getStage(2).configureStage(PacketProcessor,handle_events=self._use_events,event_window=self._event_window)

    @property
    def enableEvents(self):
        return self._use_events

    
    @enableEvents.setter
    def enableEvents(self,value):
        self._use_events = True


    @property
    def eventWindow(self):
        return self._event_window
    
    @eventWindow.setter
    def eventWindow(self,value):
        self._event_window = value
        self._reconfigureProcessor()
        if self.isRunning:
            min_win,max_win = self._event_window
            for p in self.getStage(2).processes:
                p.minWindow = min_win
                p.maxWindow = max_win
    


class CentroidPipeline(PixelPipeline):

    def __init__(self,data_queue,address,longtime):
        PixelPipeline.__init__(self,data_queue,address,longtime,use_event=True,name='Centroid') 

        self._skip_centroid = 1
        self._tot_threshold = 0
    
        self.addStage(4,TOFCentroiding)

        self._reconfigureCentroid()

    def _reconfigureCentroid(self):
        p = self.getStage(4).configureStage(TOFCentroiding,skip_data=self._skip_centroid,tot_filter=self._tot_threshold)

    @property
    def centroidSkip(self):
        return self._skip_centroid
    
    @centroidSkip.setter
    def centroidSkip(self,value):
        self._skip_centroid = value
        self._reconfigureCentroid()
        if self.isRunning:
            skip = self._skip_centroid
            for p in self.getStage(4).processes:
                p.centroidSkip = skip
    
    @property
    def totThreshold(self):
        return self._tot_threshold
    
    @totThreshold.setter
    def totThreshold(self,value):
        self._tot_threshold = value
        self._reconfigureCentroid()
        if self.isRunning:
            skip = self._tot_threshold
            for p in self.getStage(4).processes:
                p.totThreshold = skip    
    

    @property
    def numBlobProcesses(self):
        return self.getStage(4).numProcess

    @numBlobProcesses.setter
    def numBlobProcesses(self,value):
        self.getStage(4).numProcess = max(1,value)
    
