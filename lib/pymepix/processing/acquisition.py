from .basepipeline import AcquisitionPipeline
from .packetprocessor import PacketProcessor
from .udpsampler import UdpSampler


class PixelPipeline(AcquisitionPipeline):
    """ An acquisition pipeline that includes the udpsampler and pixel processor """



    def __init__(self,data_queue,address,longtime):
        AcquisitionPipeline.__init__(self,'Pixel',data_queue)

        self._use_events = False

        self.addStage(0,UdpSampler,address,longtime,num_processes=1)
        self.addStage(2,PacketProcessor,num_processes=1)




