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
from multiprocessing import Value
from ctypes import c_bool

import numpy as np
from pymepix.core.log import Logger

from pymepix.processing.logic.processing_step import ProcessingStep


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


class PacketProcessor(ProcessingStep):
    """ Class responsible to transform the raw data coming from the timepix directly into an easier
    processible data format. Takes into account the pixel- and trigger data to calculate toa and tof
    dimensions.

    Methods
    -------
    process(data):
        Process data and return the result. To use this class only this method should be used! Use the other methods only for testing or 
        if you are sure about what you are doing
    """
    def __init__(self, handle_events=True, event_window=(0.0, 10000.0), position_offset=(0, 0), 
                orientation=PixelOrientation.Up, start_time=0, timewalk_lut=None, *args, **kwargs):
        """
        Constructor for the PacketProcessor.

        Parameters
        ----------
        handle_events : boolean
            Calculate events (tof) only if handle_events is True. Otherwise only pixel-data (toa only) is provided.
        event_window : (float, float)
            The range of tof, used for processing data. Information/ data outside of this range is discarded.
        min_samples : (float, float)
            Offset/ shift of x- and y-position
        orientation : int
        start_time : int
        timewalk_lut
            Data for correction of the time-walk
        parameter_wrapper_classe : ProcessingParameter
            Class used to wrap the processing parameters to make them changable while processing is running (useful for online optimization)
        """
    
        super().__init__("PacketProcessor", *args, **kwargs)
        self._handle_events = self.parameter_wrapper_class(handle_events)
        event_window_min, event_window_max = event_window
        self._event_window_min = self.parameter_wrapper_class(event_window_min)
        self._event_window_max = self.parameter_wrapper_class(event_window_max)
        self._orientation = orientation
        self._x_offset, self._y_offset = position_offset
        self._start_time =  start_time
        self._timewalk_lut = timewalk_lut

        self._trigger_counter = 0

        self.clearBuffers()

    @property
    def event_window(self):
        return (self._event_window_min.value, self._event_window_max.value)

    @event_window.setter
    def event_window(self, event_window):
        event_window_min, event_window_max = event_window
        self._event_window_min.value = event_window_min
        self._event_window_max.value = event_window_max

    @property
    def handle_events(self):
        """:noindex:"""
        return self._handle_events.value

    @handle_events.setter
    def handle_events(self, handle_events):
        self._handle_events.value = handle_events

    def process(self, data):
        packet_view = memoryview(data)
        packet = np.frombuffer(packet_view[:-8], dtype=np.uint64)
        # needs to be an integer or "(ltime >> 28) & 0x3" fails
        longtime = int(np.frombuffer(packet_view[-8:], dtype=np.uint64)[0])

        event_data, pixel_data, timestamps, triggers = None, None, None, None
        if len(packet) > 0:

            trigger1_data = None
            trigger2_data = None

            header = ((packet & 0xF000000000000000) >> 60) & 0xF
            subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

            pixels = packet[np.logical_or(header == 0xA, header == 0xB)]
            triggers1 = packet[
                np.logical_and(
                    np.logical_or(header == 0x4, header == 0x6), subheader == 0xF
                )
            ]
            triggers2 = packet[
                np.logical_and(
                    # sub headers for trigger identification
                    # TDC1     rising edge: 0xF     falling edge: 0xA
                    # TDC2     rising edge: 0xE     falling edge: 0xB
                    header == 0x6, np.logical_or(subheader == 0xE, subheader == 0xB)
                )
            ]

            if triggers1.size > 0:
                trigger1_data = self.process_trigger1(np.int64(triggers1), longtime)

            if triggers2.size > 0:
                trigger2_data = self.process_trigger2(np.int64(triggers2), longtime)

            if pixels.size > 0:
                pixel_data = self.process_pixels(np.int64(pixels), longtime)

                if self.handle_events:
                    result = self.find_events_fast()
                    if result is not None:
                        event_data, timestamps = result
            else:
                self._trigger_counter += triggers1.size

            triggers = [trigger1_data, trigger2_data,]

        return event_data, pixel_data, timestamps, triggers

    def pre_process(self):
        self.info("Running with triggers? {}".format(self.handle_events))

    def post_process(self):
        return self.find_events_fast_post()

    def updateBuffers(self, val_filter):
        self._x = self._x[val_filter]
        self._y = self._y[val_filter]
        self._toa = self._toa[val_filter]
        self._tot = self._tot[val_filter]

    def getBuffers(self, val_filter=None):
        if val_filter is None:
            return (
                np.copy(self._x),
                np.copy(self._y),
                np.copy(self._toa),
                np.copy(self._tot),
            )
        else:
            return (
                np.copy(self._x[val_filter]),
                np.copy(self._y[val_filter]),
                np.copy(self._toa[val_filter]),
                np.copy(self._tot[val_filter]),
            )

    def clearBuffers(self):
        self._x = None
        self._y = None
        self._tot = None
        self._toa = None
        self._triggers = None

    def process_trigger1(self, pixdata, longtime):
        coarsetime = pixdata >> 12 & 0xFFFFFFFF
        coarsetime = self.correct_global_time(coarsetime, longtime)
        tmpfine = (pixdata >> 5) & 0xF
        tmpfine = ((tmpfine - 1) << 9) // 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        time_unit = 25.0 / 4096
        tdc_time = coarsetime * 25e-9 + trigtime_fine * time_unit * 1e-9

        m_trigTime = tdc_time

        if self.handle_events:
            if self._triggers is None:
                self._triggers = m_trigTime
            else:
                self._triggers = np.append(self._triggers, m_trigTime)

        return m_trigTime
    def process_trigger2(self, tidtrigdata, longtime):
        subheader = ((tidtrigdata & 0x0F00000000000000) >> 56) & 0xF
        # TDC2     rising edge: 0xE     falling edge: 0xB
        edge_type = subheader == 0xE

        coarsetime = tidtrigdata >> 12 & 0xFFFFFFFF
        coarsetime = self.correct_global_time(coarsetime, longtime)
        tmpfine = (tidtrigdata >> 5) & 0xF
        tmpfine = ((tmpfine - 1) << 9) // 12
        trigtime_fine = (tidtrigdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        time_unit = 25.0 / 4096
        tdc_time = coarsetime * 25e-9 + trigtime_fine * time_unit * 1e-9

        m_trigTime = tdc_time.astype(float)

        m_trigTime[edge_type == False] *= -1
        # always look at it as abs, sign tells rising or falling edge

        return m_trigTime

    def orientPixels(self, col, row):
        """ Orient the pixels based on Timepix orientation """
        if self._orientation is PixelOrientation.Up:
            return col, row
        elif self._orientation is PixelOrientation.Left:
            return row, 255 - col
        elif self._orientation is PixelOrientation.Down:
            return 255 - col, 255 - row
        elif self._orientation is PixelOrientation.Right:
            return 255 - row, col

    def process_pixels(self, pixdata, longtime):

        dcol = (pixdata & 0x0FE0000000000000) >> 52
        spix = (pixdata & 0x001F800000000000) >> 45
        pix = (pixdata & 0x0000700000000000) >> 44
        col = dcol + pix // 4
        row = spix + (pix & 0x3)

        data = (pixdata & 0x00000FFFFFFF0000) >> 16
        spidr_time = pixdata & 0x000000000000FFFF
        ToA = (data & 0x0FFFC000) >> 14
        FToA = data & 0xF
        ToT = ((data & 0x00003FF0) >> 4) * 25
        time_unit = 25.0 / 4096

        ToA_coarse = (
            self.correct_global_time((spidr_time << 14) | ToA, longtime)
            & 0xFFFFFFFFFFFF
        )
        globalToA = (ToA_coarse << 12) - (FToA << 8)
        globalToA += ((col // 2) % 16) << 8
        globalToA[((col // 2) % 16) == 0] += 16 << 8
        finalToA = globalToA * time_unit * 1e-9

        if self._timewalk_lut is not None:
            finalToA -= self._timewalk_lut[np.int_(ToT // 25) - 1] * 1e3

        x, y = self.orientPixels(col, row)

        x += self._x_offset
        y += self._y_offset

        if self.handle_events:
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

        return x, y, finalToA, ToT

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
        globaltime[neg_diff] = ((ltime - 0x10000000) & 0xFFFFC0000000) | (
            arr[neg_diff] & 0x3FFFFFFF
        )
        pos_diff = (diff == -1) | (diff == 3)
        globaltime[pos_diff] = ((ltime + 0x10000000) & 0xFFFFC0000000) | (
            arr[pos_diff] & 0x3FFFFFFF
        )
        # res[neg] =   ( (ltime - 0x10000000) & 0xFFFFC0000000) | (arr[neg] & 0x3FFFFFFF)
        # res[pos] =   ( (ltime + 0x10000000) & 0xFFFFC0000000) | (arr[pos] & 0x3FFFFFFF)
        # arr[zero] = ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)
        # arr[zero] =   ( (ltime) & 0xFFFFC0000000) | (arr[zero] & 0x3FFFFFFF)

        return globaltime

    def find_events_fast(self):
        if self.__exist_enough_triggers():
            self._triggers = self._triggers[np.argmin(self._triggers) :]

            if self.__toa_is_not_empty():
                # Get our start/end triggers to bin events accordingly
                start = self._triggers
                if start.size > 1:
                    trigger_counter = np.arange(
                        self._trigger_counter, self._trigger_counter + start.size - 1, dtype=int
                    )
                    self._trigger_counter = trigger_counter[-1] + 1

                    # end = self._triggers[1:-1:]
                    # Get the first and last triggers in pile
                    first_trigger = start[0]
                    last_trigger = start[-1]
                    # Delete useless pixels before the first trigger
                    self.updateBuffers(self._toa >= first_trigger)
                    # grab only pixels we care about
                    x, y, toa, tot = self.getBuffers(self._toa < last_trigger)
                    self.updateBuffers(self._toa >= last_trigger)
                    try:
                        event_mapping = np.digitize(toa, start) - 1
                    except Exception as e:
                        self.error("Exception has occured {} due to ", str(e))
                        self.error("Writing output TOA {}".format(toa))
                        self.error("Writing triggers {}".format(start))
                        self.error("Flushing triggers!!!")
                        self._triggers = self._triggers[-1:]
                        return None
                    self._triggers = self._triggers[-1:]

                    tof = toa - start[event_mapping]
                    event_number = trigger_counter[event_mapping]

                    event_window_min, event_window_max = self.event_window
                    exp_filter = (tof >= event_window_min) & (tof <= event_window_max)

                    result = (
                        event_number[exp_filter],
                        x[exp_filter],
                        y[exp_filter],
                        tof[exp_filter],
                        tot[exp_filter],
                    )

                    if result[0].size > 0:
                        timeStamps = np.uint64(
                            start[np.unique(event_mapping)] * 1e9 + self._start_time
                        )  # timestamp in ns for trigger event
                        return result, (np.unique(result[0]), timeStamps)

        return None # Clear out the triggers since they have nothing

    def __exist_enough_triggers(self):
        return self._triggers is not None and self._triggers.size >= 2

    def __toa_is_not_empty(self):
        return self._toa is not None and self._toa.size > 0

    def find_events_fast_post(self):
        """Call this function at the very end of to also have the last two trigger events processed"""
        # add an imaginary last trigger event after last pixel event for np.digitize to work
        if self._toa is not None and self._toa.shape[0] > 0 and self._triggers is not None:
            self._triggers = np.concatenate(
                (self._triggers, np.array([self._toa.max() + 1]))
            )
        else:
            return None, None, None, None

        event_data, timestamps = None, None
        result = self.find_events_fast()
        if result is not None:
            event_data, timestamps = result

        return event_data, None, timestamps, None
