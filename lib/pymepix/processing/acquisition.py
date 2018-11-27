from .baseacquisition import AcquisitionPipeline
from .packetprocessor import PacketProcessor
from .udpsampler import UdpSampler


class PixelPipeline(AcquisitionPipeline):
    """ An acquisition pipeline that includes the udpsampler and pixel processor """



    def __init__(self,data_queue,address,longtime):
        AcquisitionPipeline.__init__(self,'Pixel',data_queue)

        self._use_events = False
        self._event_window = (0,10000)

        self.addStage(0,UdpSampler,address,longtime)

        self.addStage(2,PacketProcessor,handle_events=False,event_window=self._event_window)


    @property
    def eventWindow(self):
        return self._event_window
    
    @eventWindow.setter
    def eventWindow(self,value):
        self._event_window = value
        if self.isRunning:
            min_win,max_win = self._event_window
            self.getStage(2).processes[-1].minWindow = min_win
            self.getStage(2).processes[-1].maxWindow = max_win