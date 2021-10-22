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
from abc import abstractmethod, ABC

from pymepix.core.log import Logger
from pymepix.processing.logic.processing_parameter import ProcessingParameter

class ProcessingStep(Logger, ABC):
    """Representation of one processing step in the pipeline for processing timepix raw data. 
    Implementations are provided by PacketProcessor and CentroidCalculator. To combine those (and possibly other) classes
    into a pipeline they have to implement this interface.
    Also provides pre- and post-process implementations which are required for integration in the online processing pipeline 
    (see PipelineCentroidCalculator and PipelinePacketProcessor).
    
    Currently the picture is the following:
     - For post processing the CentroidCalculator and the PacketProcessor are used directly
     - PipelineCentroidCalculator and PipelinePacketProcessor build on top of CentroidCalculator and PacketProcessor to provide an integration in the existing online processing pipeline for online analysis.
    """

    def __init__(self, name, parameter_wrapper_class=ProcessingParameter):
        super().__init__(name)
        self.parameter_wrapper_class = parameter_wrapper_class

    def pre_process(self):
        pass

    def post_process(self):
        pass

    @abstractmethod
    def process(self, data):
        pass
