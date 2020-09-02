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

import numpy as np
import zmq
from multiprocessing.sharedctypes import Value

from .basepipeline import BasePipelineObject
from .datatypes import MessageType


class PixelOrientation(IntEnum):
    """Defines how row and col are intepreted in the output"""
    Up = 0
    """Up is the default, x=column,y=row"""
    Left = 1
    """x=row, y=-column"""
    Down = 2
    """x=-column, y = -row """
    Right = 3
    """x=-row, y=column"""


class PacketProcessor(BasePipelineObject):
    """Processes Pixel packets for ToA, ToT,triggers and events

    This class, creates a UDP socket connection to SPIDR and recivies the UDP packets from Timepix
    It then pre-processes them and sends them off for more processing
    """

    def __init__(self,
                 handle_events=False, event_window=(0.0, 10000.0), position_offset=(0, 0),
                 orientation=PixelOrientation.Up, input_queue=None, create_output=True, num_outputs=1,
                 shared_output=None):
        # set input_queue to None for now, or baseaqusition.build would have to be modified
        # input_queue is replace by zmq
        BasePipelineObject.__init__(self, PacketProcessor.__name__, input_queue=None,
                                    create_output=create_output, num_outputs=num_outputs, shared_output=shared_output)

        self.clearBuffers()
        self._orientation = orientation
        self._x_offset, self._y_offset = position_offset

        self._trigger_counter = 0

        self._handle_events = handle_events
        min_window = event_window[0]
        max_window = event_window[1]
        self._min_event_window = Value('d', min_window)
        self._max_event_window = Value('d', max_window)

    def updateBuffers(self, val_filter):
        self._x = self._x[val_filter]
        self._y = self._y[val_filter]
        self._toa = self._toa[val_filter]
        self._tot = self._tot[val_filter]

    def getBuffers(self, val_filter=None):
        if val_filter is None:
            return np.copy(self._x), np.copy(self._y), np.copy(self._toa), np.copy(self._tot)
        else:
            return np.copy(self._x[val_filter]), np.copy(self._y[val_filter]), np.copy(self._toa[val_filter]), np.copy(
                self._tot[val_filter])

    def clearBuffers(self):
        self._x = None
        self._y = None
        self._tot = None
        self._toa = None
        self._triggers = None

    @property
    def minWindow(self):
        return self._min_event_window.value

    @minWindow.setter
    def minWindow(self, value):
        self._min_event_window.value = value

    @property
    def maxWindow(self):
        return self._max_event_window.value

    @maxWindow.setter
    def maxWindow(self, value):
        self._max_event_window.value = value

    @property
    def _eventWindow(self):
        return self._min_event_window.value, self._max_event_window.value

    def init_new_process(self):
        """create connections and initialize variables in new process"""
        self.debug('create ZMQ socket')
        ctx = zmq.Context.instance()
        self._packet_sock = ctx.socket(zmq.PULL)
        self._packet_sock.connect('ipc:///tmp/packetProcessor')

    def pre_run(self):
        self.info('Running with triggers? {}'.format(self._handle_events))
        self.init_new_process()

    def process(self, data_type=None, data=None):
        packet_view = memoryview(self._packet_sock.recv(copy=False))
        packet = np.frombuffer(packet_view[:-8], dtype=np.uint64)
        # needs to be an integer or "(ltime >> 28) & 0x3" fails
        longtime = int(np.frombuffer(packet_view[-8:], dtype=np.uint64)[0])

        if len(packet) == 0:
            return None, None

        #packets, longtime = data
        #packet = packets

        header = ((packet & 0xF000000000000000) >> 60) & 0xF
        subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

        pixels = packet[np.logical_or(header == 0xA, header == 0xB)]
        triggers = packet[np.logical_and(np.logical_or(header == 0x4, header == 0x6), subheader == 0xF)]

        if pixels.size > 0:
            self.process_pixels(np.int64(pixels), longtime)

        if triggers.size > 0:
            # print('triggers', triggers, longtime)
            self.process_triggers(np.int64(triggers), longtime)

        if self._handle_events:

            events = self.find_events_fast()

            if events is not None:
                return MessageType.EventData, events
            else:
                return None, None
        else:
            return None, None

        return None, None

    def filterBadTriggers(self):
        self._triggers = self._triggers[np.argmin(self._triggers):]

    def find_events_fast(self):
        if self._triggers is None:
            return None
        # self.filterBadTriggers()
        if self._triggers.size < 5:
            return None
        self.filterBadTriggers()
        if self._toa is None:
            return None
        if self._toa.size == 0:
            # Clear out the triggers since they have nothing
            return None

        # Get our start/end triggers to get events
        start = self._triggers[0:-1:]
        if start.size == 0:
            return None

        min_window, max_window = self._eventWindow

        trigger_counter = np.arange(self._trigger_counter, self._trigger_counter + start.size, dtype=np.int)

        self._trigger_counter = trigger_counter[-1] + 1

        # end = self._triggers[1:-1:]
        # Get the first and last triggers in pile
        first_trigger = start[0]
        last_trigger = start[-1]
        # print('First Trigger las trigger',first_trigger,last_trigger)
        # print('TOA before',self._toa)
        # Delete useless pixels behind the first trigger
        self.updateBuffers(self._toa >= first_trigger)
        # grab only pixels we care about
        x, y, toa, tot = self.getBuffers(self._toa < last_trigger)
        # print('triggers',start)
        # print('TOA',toa)
        self.updateBuffers(self._toa >= last_trigger)
        try:
            event_mapping = np.digitize(toa, start) - 1
        except Exception as e:
            self.error('Exception has occured {} due to ', str(e))
            self.error('Writing output TOA {}'.format(toa))
            self.error('Writing triggers {}'.format(start))
            self.error('Flushing triggers!!!')
            self._triggers = self._triggers[-1:]
            return None
        event_triggers = self._triggers[:-1:]
        self._triggers = self._triggers[-1:]

        # print('Trigger delta',triggers,np.ediff1d(triggers))

        tof = toa - event_triggers[event_mapping]
        event_number = trigger_counter[event_mapping]

        exp_filter = (tof >= min_window) & (tof <= max_window)

        result = event_number[exp_filter], x[exp_filter], y[exp_filter], tof[exp_filter], tot[exp_filter]

        if result[0].size > 0:
            return result
        else:
            return None

    def correct_global_time(self, arr, ltime):
        pixelbits = (arr >> 28) & 0x3
        ltimebits = (ltime >> 28) & 0x3
        # diff = (ltimebits - pixelbits).astype(np.int64)
        # neg = (diff == 1) | (diff == -3)
        # pos = (diff == -1) | (diff == 3)
        # zero = (diff == 0) | (diff == 2)

        # res = ( (ltime) & 0xFFFFC0000000) | (arr & 0x3FFFFFFF)
        diff = (ltimebits - pixelbits).astype(np.int64)
        globaltime = (ltime & 0xFFFFC0000000) | (arr & 0x3FFFFFFF)
        neg_diff = (diff == 1) | (diff == -3)
        globaltime[neg_diff] = ((ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg_diff] & 0x3FFFFFFF)
        pos_diff = (diff == -1) | (diff == 3)
        globaltime[pos_diff] = ((ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos_diff] & 0x3FFFFFFF)
        # res[neg] =   ( (ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg] & 0x3FFFFFFF)
        # res[pos] =   ( (ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos] & 0x3FFFFFFF)
        # arr[zero] = ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)
        # arr[zero] =   ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)

        return globaltime

    def process_triggers(self, pixdata, longtime):
        coarsetime = pixdata >> 12 & 0xFFFFFFFF
        coarsetime = self.correct_global_time(coarsetime, longtime)
        tmpfine = (pixdata >> 5) & 0xF
        tmpfine = ((tmpfine - 1) << 9) // 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        time_unit = 25. / 4096
        tdc_time = (coarsetime * 25E-9 + trigtime_fine * time_unit * 1E-9)

        m_trigTime = tdc_time

        # TODO: don't clatter queue with unnecessary stuff for now
        #self.pushOutput(MessageType.TriggerData, m_trigTime)
        # print(m_trigTime)
        if self._handle_events:
            if self._triggers is None:
                self._triggers = m_trigTime
            else:
                self._triggers = np.append(self._triggers, m_trigTime)

    def orientPixels(self, col, row):
        if self._orientation is PixelOrientation.Up:
            return col, row
        elif self._orientation is PixelOrientation.Left:
            return row, 255 - col
        elif self._orientation is PixelOrientation.Down:
            return 255 - col, 255 - row
        elif self._orientation is PixelOrientation.Right:
            return 255 - row, col

    def process_pixels(self, pixdata, longtime):

        dcol = ((pixdata & 0x0FE0000000000000) >> 52)
        spix = ((pixdata & 0x001F800000000000) >> 45)
        pix = ((pixdata & 0x0000700000000000) >> 44)
        col = (dcol + pix // 4)
        row = (spix + (pix & 0x3))

        data = ((pixdata & 0x00000FFFFFFF0000) >> 16)
        spidr_time = (pixdata & 0x000000000000FFFF)
        ToA = ((data & 0x0FFFC000) >> 14)
        FToA = (data & 0xF)
        ToT = ((data & 0x00003FF0) >> 4) * 25
        time_unit = 25. / 4096

        # print('LONGTIME',longtime*25E-9)
        # print('SpidrTime',(spidr_time << 14)*25E-9)
        # print('TOA before global',((spidr_time << 14) |ToA)*25*1E-9)

        ToA_coarse = self.correct_global_time((spidr_time << 14) | ToA, longtime) & 0xFFFFFFFFFFFF
        # print('TOA after global',ToA_coarse*25*1E-9,longtime)
        globalToA = (ToA_coarse << 12) - (FToA << 8)
        # print('TOA after FTOa',globalToA*time_unit*1E-9)
        globalToA += ((col // 2) % 16) << 8
        globalToA[((col // 2) % 16) == 0] += (16 << 8)
        finalToA = globalToA * time_unit * 1E-9

        # print('finalToa',finalToA)
        # Orient the pixels based on Timepix orientation
        x, y = self.orientPixels(col, row)

        # #
        x += self._x_offset
        y += self._y_offset

        # TODO: don't clatter queue with unnecessary stuff for now
        #self.pushOutput(MessageType.PixelData, (x, y, finalToA, ToT))

        # print('PIXEL',finalToA,longtime)
        if self._handle_events:
            if self._x is None:
                self._x = x
                self._y = y
                self._toa = finalToA
                self._tot = ToT
            else:
                self._x = np.append(self._x, x)
                self._y = np.append(self._y, y)
                self._toa = np.append(self._toa, finalToA)
                self._tot = np.append(self._tot, ToT)