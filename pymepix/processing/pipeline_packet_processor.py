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

from enum import IntEnum
from pymepix.processing.datatypes import MessageType
from pymepix.processing.logic.shared_processing_parameter import SharedProcessingParameter

import zmq

from .basepipeline import BasePipelineObject
from .logic.packet_processor import PacketProcessor
import pymepix.config.load_config as cfg

class PipelinePacketProcessor(BasePipelineObject):
    """Processes Pixel packets for ToA, ToT, triggers and events

    This class, creates a UDP socket connection to SPIDR and recivies the UDP packets from Timepix
    It then pre-processes them and sends them off for more processing
    """

    def __init__(
        self,
        packet_processor: PacketProcessor = PacketProcessor(parameter_wrapper_class=SharedProcessingParameter),
        input_queue=None,
        create_output=True,
        num_outputs=1,
        shared_output=None
    ):
        # set input_queue to None for now, or baseaqusition.build would have to be modified
        # input_queue is replace by zmq
        super().__init__(
            PipelinePacketProcessor.__name__,
            input_queue=None,
            create_output=create_output,
            num_outputs=num_outputs,
            shared_output=shared_output,
        )
        self.packet_processor = packet_processor

    def init_new_process(self):
        self.debug("create ZMQ socket")
        ctx = zmq.Context.instance()
        self._packet_sock = ctx.socket(zmq.PULL)
        self._packet_sock.connect(f"ipc:///tmp/packetProcessor{cfg.default_cfg['zmq_port']}")

    def pre_run(self):
        self.init_new_process()
        self.packet_processor.pre_process()

    def post_run(self):
        self._packet_sock.close()
        return None, self.packet_processor.post_process()

    def process(self, data_type=None, data=None):
        # timestamps are not required for online processing
        result = self.packet_processor.process(self._packet_sock.recv(copy=False))
        if result is not None:
            event_data, pixel_data, _timestamps, _ = result

            if pixel_data is not None:
                self.pushOutput(MessageType.PixelData, pixel_data)

            if event_data is not None:
                return MessageType.EventData, event_data
        return None, None

