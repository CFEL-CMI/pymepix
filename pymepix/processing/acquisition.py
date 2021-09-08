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
from .baseacquisition import AcquisitionPipeline
from .pipeline_centroid_calculator import PipelineCentroidCalculator
from .pipeline_packet_processor import PipelinePacketProcessor
from .udpsampler import UdpSampler


class PixelPipeline(AcquisitionPipeline):
    """An acquisition pipeline that includes the udpsampler and pixel processor

    A pipeline that will read from a UDP address and decode the pixels a useable form.
    This class can be used as a base for all acqusition pipelines.
    """

    def __init__(self, data_queue, address, longtime, use_event=False, name="Pixel"):
        AcquisitionPipeline.__init__(self, name, data_queue)
        self.info("Initializing Pixel pipeline")
        self._use_events = use_event
        self._event_window = (0, 10000)

        self.addStage(0, UdpSampler, address, longtime)
        self.addStage(2, PipelinePacketProcessor, num_processes=2)
        self._reconfigureProcessor()

    def _reconfigureProcessor(self):
        self.debug(
            "Configuring packet processor handle_events={} event_window={}".format(
                self._use_events, self._event_window
            )
        )
        self.getStage(2).configureStage(
            PipelinePacketProcessor,
            packet_processor=PacketProcessor(self._use_events, self._event_window)
        )

    @property
    def enableEvents(self):
        """This either enables or disables TOF (Time of Flight) calculation

        Enabling this will ask the packet processor to process both triggers and pixels
        and compute time of flight rather than time of arrival. Changes take effect on the next
        acquisition

        Parameters
        ------------
        value : bool


        Returns
        ------------
        bool

        """
        return self._use_events

    @enableEvents.setter
    def enableEvents(self, value):
        self.info("Setting event to {}".format(value))
        self._use_events = value
        self._reconfigureProcessor()

    @property
    def eventWindow(self):
        """In TOF mode (useEvents is true) the time window in seconds to output further down the pipeline

        When in TOF mode, sets up the packet processor to only output events within a certain time window relative
        to a trigger. Changes happen immediately.
        For example to only consider events within a time window between 3 us and 8 us after the trigger do

        >>> pixelpipeline.eventWindow = (3E-6,8E-6)



        Parameters
        ------------
        value: :obj:`tuple` of 2 :obj:`float`
            A tuple of two floats that represents the (min,max) time of flight window in seconds
            This is useful to filter out a particular region


        Returns
        ----------
        :obj:`tuple` of 2 floats
            Currently set event window

        """
        return self._event_window

    @eventWindow.setter
    def eventWindow(self, value):
        self._event_window = value
        self._reconfigureProcessor()
        if self.isRunning:
            min_win, max_win = self._event_window
            for p in self.getStage(2).processes:
                p.minWindow = min_win
                p.maxWindow = max_win


class CentroidPipeline(PixelPipeline):
    """A Pixel pipeline that includes centroiding

    Same as the pixel pipeline but also includes centroid processing, note that this can be extremely slow
    when dealing with a huge number of objects


    """

    def __init__(self, data_queue, address, longtime):
        PixelPipeline.__init__(
            self, data_queue, address, longtime, use_event=True, name="Centroid"
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
