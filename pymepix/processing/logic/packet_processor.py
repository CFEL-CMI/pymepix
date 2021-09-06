from enum import IntEnum

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
    def __init__(self, handle_events=True, event_window=(0.0, 10000.0), position_offset=(0, 0), 
                orientation=PixelOrientation.Up, start_time=0, timewalk_lut=None):
    
        super().__init__("PacketProcessor")
        self._handle_events = handle_events
        self._min_window, self._max_window = event_window
        self._orientation = orientation
        self._x_offset, self._y_offset = position_offset
        self._start_time =  start_time
        self._timewalk_lut = timewalk_lut

        self._trigger_counter = 0

        self.clearBuffers()

    def process(self, data):
        packet_view = memoryview(data)
        packet = np.frombuffer(packet_view[:-8], dtype=np.uint64)
        # needs to be an integer or "(ltime >> 28) & 0x3" fails
        longtime = int(np.frombuffer(packet_view[-8:], dtype=np.uint64)[0])

        if len(packet) > 0:

            header = ((packet & 0xF000000000000000) >> 60) & 0xF
            subheader = ((packet & 0x0F00000000000000) >> 56) & 0xF

            pixels = packet[np.logical_or(header == 0xA, header == 0xB)]
            triggers = packet[
                np.logical_and(
                    np.logical_or(header == 0x4, header == 0x6), subheader == 0xF
                )
            ]

            if pixels.size > 0:
                self.process_pixels(np.int64(pixels), longtime)

                if triggers.size > 0:
                    self.process_triggers(np.int64(triggers), longtime)

                if self._handle_events:
                    return self.find_events_fast()

        return None

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

    def process_triggers(self, pixdata, longtime):
        coarsetime = pixdata >> 12 & 0xFFFFFFFF
        coarsetime = self.correct_global_time(coarsetime, longtime)
        tmpfine = (pixdata >> 5) & 0xF
        tmpfine = ((tmpfine - 1) << 9) // 12
        trigtime_fine = (pixdata & 0x0000000000000E00) | (tmpfine & 0x00000000000001FF)
        time_unit = 25.0 / 4096
        tdc_time = coarsetime * 25e-9 + trigtime_fine * time_unit * 1e-9

        m_trigTime = tdc_time

        if self._handle_events:
            if self._triggers is None:
                self._triggers = m_trigTime
            else:
                self._triggers = np.append(self._triggers, m_trigTime)

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

        # TODO: don't clatter queue with unnecessary stuff for now
        # self.pushOutput(MessageType.PixelData, (x, y, finalToA, ToT))

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
                start = self._triggers[0:-1:]
                if start.size > 0:
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
                        self._triggers = self._triggers[-2:]
                        return None
                    self._triggers = self._triggers[-2:]

                    tof = toa - start[event_mapping]
                    event_number = trigger_counter[event_mapping]

                    exp_filter = (tof >= self._min_window) & (tof <= self._max_window)

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
        return self._triggers is not None and self._triggers.size >= 4

    def __toa_is_not_empty(self):
        return self._toa is not None and self._toa.size > 0

    def find_events_fast_post(self):
        """Call this function at the very end of to also have the last two trigger events processed"""
        # add an imaginary last trigger event after last pixel event for np.digitize to work
        if self._toa is not None:
            self._triggers = np.concatenate(
                (self._triggers, np.array([self._toa.max() + 1, self._toa.max() + 2]))
            )
        return self.find_events_fast()