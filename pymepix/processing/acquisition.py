# This file is part of Pymepix
#
# In all scientific work using Pymepix, please reference it as
#
# A. F. Al-Refaie, M. Johny, J. Correa, D. Pennicard, P. Svihra, A. Nomerotski, S. Trippel, and J. Küpper:
# "PymePix: a python library for SPIDR readout of Timepix3", J. Inst. 14, P10003 (2019)
# https://doi.org/10.1088/1748-0221/14/10/P10003
# https://arxiv.org/abs/1905.07999
#
# Pymepix is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <https://www.gnu.org/licenses/>.

"""Module that contains predefined acquisition pipelines for the user to use"""

from pymepix.processing.logic.centroid_calculator import CentroidCalculator
from pymepix.processing.logic.packet_processor import PacketProcessor
from pymepix.processing.logic.packet_processor_tpx4 import PacketProcessor_tpx4
from .baseacquisition import AcquisitionPipeline
from .pipeline_centroid_calculator import PipelineCentroidCalculator
from .pipeline_packet_processor import PipelinePacketProcessor
from .logic.packet_processor_factory import packet_processor_factory
from .udpsampler import UdpSampler


class PixelPipeline(AcquisitionPipeline):
    """An acquisition pipeline that includes the udpsampler and pixel processor

    A pipeline that will read from a UDP address and decode the pixels a useable form.
    This class can be used as a base for all acqusition pipelines.
    """

    def __init__(self, data_queue, address, longtime, use_event=False, name="Pixel", event_window=(0, 1E-3),
                 camera_generation=3):
        """ 
        Parameters:
        use_event (boolean): If packets are forwarded to the centroiding. If True centroids are calculated."""
        AcquisitionPipeline.__init__(self, name, data_queue)
        self.info("Initializing Pixel pipeline")

        PacketProcessorClass = packet_processor_factory(camera_generation)
        self.packet_processor = PacketProcessorClass(handle_events=use_event, event_window=event_window)

        self.addStage(0, UdpSampler, address, longtime)
        self.addStage(2, PipelinePacketProcessor, num_processes=2)
        self._reconfigureProcessor()

    def _reconfigureProcessor(self):
        self.getStage(2).configureStage(
            PipelinePacketProcessor,
            packet_processor=self.packet_processor
        )



class CentroidPipeline(PixelPipeline):
    """A Pixel pipeline that includes centroiding

    Same as the pixel pipeline but also includes centroid processing, note that this can be extremely slow
    when dealing with a huge number of objects
    """

    def __init__(self, data_queue, address, longtime, camera_generation=3):
        PixelPipeline.__init__(
            self, data_queue, address, longtime, use_event=True, name="Centroid",
            camera_generation=camera_generation
        )
        self.info("Initializing Centroid pipeline")
        self.centroid_calculator=CentroidCalculator()

        self.addStage(4, PipelineCentroidCalculator, num_processes=6)

        self._reconfigureCentroid()

    def _reconfigureCentroid(self):
        self._reconfigureProcessor()
        self.getStage(4).configureStage(
            PipelineCentroidCalculator,
            centroid_calculator=self.centroid_calculator
        )

    @property
    def numBlobProcesses(self):
        """Number of python processes to spawn for centroiding

        Setting this will spawn the appropriate number of processes to perform centroiding.
        Changes take effect on next acquisition.
        """
        return self.getStage(4).numProcess

    @numBlobProcesses.setter
    def numBlobProcesses(self, value):
        self.getStage(4).numProcess = max(1, value)
