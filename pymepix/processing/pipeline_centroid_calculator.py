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

"""Processors relating to centroiding"""
from pymepix.processing.datatypes import MessageType
from pymepix.processing.logic.centroid_calculator import CentroidCalculator
from pymepix.processing.logic.shared_processing_parameter import SharedProcessingParameter

from .basepipeline import BasePipelineObject


class PipelineCentroidCalculator(BasePipelineObject):
    """Performs centroiding on EventData recieved from Packet processor"""

    def __init__(
        self,
        centroid_calculator: CentroidCalculator = CentroidCalculator(parameter_wrapper_class=SharedProcessingParameter),
        input_queue=None,
        create_output=True,
        num_outputs=1,
        shared_output=None,
    ):
        super().__init__(
            PipelineCentroidCalculator.__name__,
            input_queue=input_queue,
            create_output=create_output,
            num_outputs=num_outputs,
            shared_output=shared_output
        )
        self.centroid_calculator = centroid_calculator

    def process(self, data_type=None, data=None):
        if data_type == MessageType.EventData:
            return MessageType.CentroidData, self.centroid_calculator.process(data)

        return None, None
