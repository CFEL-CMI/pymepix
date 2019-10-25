##############################################################################
##
# This file is part of Pymepix
#
# https://arxiv.org/abs/1905.07999
#
#
# Pymepix is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pymepix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pymepix.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""Module that contains predefined acquisition pipelines for the user to use"""

from .baseacquisition import AcquisitionPipeline
from .packetprocessor import PacketProcessor
from .centroiding import Centroiding
from .udpsampler import UdpSampler


class PixelPipeline(AcquisitionPipeline):
    """ An acquisition pipeline that includes the udpsampler and pixel processor

        A pipeline that will read from a UDP address and decode the pixels a useable form.
        This class can be used as a base for all acqusition pipelines.
    """



    def __init__(self,data_queue,address,longtime,use_event=False,name='Pixel'):
        AcquisitionPipeline.__init__(self,name,data_queue)
        self.info('Initializing Pixel pipeline')
        self._use_events = use_event
        self._event_window = (0,10000)

        self.addStage(0,UdpSampler,address,longtime)
        self.addStage(2,PacketProcessor)
        self._reconfigureProcessor()

    def _reconfigureProcessor(self):
        self.debug('Configuring packet processor handle_events={} event_window={}'.format(self._use_events,self._event_window))
        self.getStage(2).configureStage(PacketProcessor,handle_events=self._use_events,event_window=self._event_window)

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
    def enableEvents(self,value):
        self.info('Setting event to {}'.format(value))
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
    def eventWindow(self,value):
        self._event_window = value
        self._reconfigureProcessor()
        if self.isRunning:
            min_win,max_win = self._event_window
            for p in self.getStage(2).processes:
                p.minWindow = min_win
                p.maxWindow = max_win



class CentroidPipeline(PixelPipeline):
    """A Pixel pipeline that includes centroiding

    Same as the pixel pipeline but also includes centroid processing, note that this can be extremely slow
    when dealing with a huge number of objects


    """

    def __init__(self,data_queue,address,longtime):
        PixelPipeline.__init__(self,data_queue,address,longtime,use_event=True,name='Centroid')
        self.info('Initializing Centroid pipeline')
        self._skip_centroid = 1
        self._tot_threshold = 0
        self._samples = 3
        self._epsilon = 3.0

        self.addStage(4,Centroiding)

        self._reconfigureCentroid()

    def _reconfigureCentroid(self):
        self._reconfigureProcessor()
        p = self.getStage(4).configureStage(Centroiding,skip_data=self._skip_centroid,tot_filter=self._tot_threshold,epsilon=self._epsilon,samples=self._samples)

    @property
    def centroidSkip(self):
        """Perform centroiding on every nth packet

        Parameters
        -----------
        value: int


        """
        return self._skip_centroid

    @centroidSkip.setter
    def centroidSkip(self,value):
        self.info('Setting Centroid skip to {}'.format(value))
        self._skip_centroid = value
        self._reconfigureCentroid()
        if self.isRunning:
            skip = self._skip_centroid
            for p in self.getStage(4).processes:
                p.centroidSkip = skip

    @property
    def epsilon(self):
        """Perform centroiding on every nth packet

        Parameters
        -----------
        value: int


        """
        return self._epsilon

    @epsilon.setter
    def epsilon(self,value):
        self._epsilon = value
        self._reconfigureCentroid()
        self.info('Setting epsilon skip to {}'.format(value))
        if self.isRunning:
            skip = self._epsilon
            for p in self.getStage(4).processes:
                p.epsilon = skip

    @property
    def samples(self):
        """Perform centroiding on every nth packet

        Parameters
        -----------
        value: int


        """
        return self._samples

    @samples.setter
    def samples(self,value):
        self._samples = value
        self._reconfigureCentroid()
        if self.isRunning:
            skip = self._samples
            for p in self.getStage(4).processes:
                p.samples = skip



    @property
    def totThreshold(self):
        """Determines which time over threhsold values to filter before centroiding

        This is useful in reducing the computational time in centroiding and can filter out
        noise. Changes take effect immediately

        Parameters
        -----------
        value: int


        Returns
        -----------
        int

        """
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
        """Number of python processes to spawn for centroiding

        Setting this will spawn the appropriate number of processes to perform centroiding.
        Changes take effect on next acquisition.


        """
        return self.getStage(4).numProcess

    @numBlobProcesses.setter
    def numBlobProcesses(self,value):
        self.getStage(4).numProcess = max(1,value)
