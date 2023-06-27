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

import numpy as np
import math
from enum import IntEnum
from pymepix.processing.logic.processing_step import ProcessingStep

from pymepix.processing.logic.datatypes_tpx4 import PacketType, ReadoutMode


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


class PacketProcessor_tpx4(ProcessingStep):
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
                 orientation=PixelOrientation.Up, start_time=0, timewalk_lut=None,
                 trigger_pixels_indxs=[0,1,2,3], *args, **kwargs):
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
        self._PC24bit = self.parameter_wrapper_class(False)
        self._orientation = orientation
        self._x_offset, self._y_offset = position_offset
        self._start_time = start_time
        self._timewalk_lut = timewalk_lut

        self._trigger_counter = 0

        self.clearBuffers()

        self.decode_gray = self.makeinversegraycode()

        # Dictionary for decoding ultrafast ToA
        self.decode_ufT = {0x0F: 0, 0x0E: 0.1953125, 0x0C: 0.390625, 0x08: 0.5859375, 0x00: 0.78125, 0x01: 0.9765625, 0x03: 1.171875, 0x07: 1.3671875}
        self.npa_decode_ufT = np.zeros((0x10,), dtype=float)
        for key, val in self.decode_ufT.items():
            self.npa_decode_ufT[key] = val

        self.int64be = np.dtype(np.int64)
        self.int64be = self.int64be.newbyteorder('>')

        self.trigger_pixels_indxs = trigger_pixels_indxs

        #trigger is used for calculation of ToF, by default first one from



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

    @property
    def PC24bit(self):
        return self._PC24bit

    @PC24bit.setter
    def PC24bit(self, PC24bit):
        self._PC24bit = PC24bit

    def makeinversegraycode(self):
        arraylength = 2 ** 16
        lut = np.zeros(arraylength, dtype=np.uint16)
        for inval in range(arraylength):
            n = inval
            inv = 0
            while (n):
                inv = inv ^ n
                n = n >> 1
            lut[inval] = inv
        return lut

    def process(self, data):

        event_data, pixel_data, timestamps, triggers = None, None, None, None

        packet_view = memoryview(data)
        rawpacketarray = np.frombuffer(packet_view[:-8], self.int64be)

        longtime = int(np.frombuffer(packet_view[-8:], dtype=np.uint64)[0])

        if len(rawpacketarray) > 0:  # longtime data sent from spidr TCP server, probably will be not needed

            arange_index = np.arange(len(rawpacketarray))

            endofcol = ((rawpacketarray & 0x7F80000000000000) >> 55)

            pixel_entries = endofcol <= 0xDF

            timing_entries = np.logical_and(PacketType.Heartbeat.value <= endofcol,
                                            endofcol <= PacketType.CtrlDataTest.value)

            pixel_packets = rawpacketarray[pixel_entries]
            if len(pixel_packets) == 0:
                return None

            if self.PC24bit==False:
                #x, y, ToA, ToT = self.dataPC24bitdecode(rawpacketarray[pixel_entries])
                raise NotImplementedError("Not implemented PC24bitdecode!")
            else:
                x, y, ToA, ToT = self.process_pixels(pixel_packets)

            decodedtimestamps = self.timestampeventdecode(rawpacketarray[timing_entries])

            ToA = self.correct_coarsetime(ToA, arange_index[pixel_entries], decodedtimestamps, arange_index[timing_entries])

            triggers = self.find_triggers(x, y, ToA)

            pixel_data = (x,y,ToA,ToT)

            if self.handle_events:
                result = self.find_events_fast()
                if result is not None:
                    event_data, timestamps = result

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

    def process_pixels(self, rawpackets, gray=False):
        """Decodes pixel hit data.

        Parameters
        ----------
        rawpacket : 8-byte integer value (big endian format, I believe)

        Returns
        -------
        tuple
            The decoded packet, with the following elements:
            - PacketType.PixelData
            - Pixel x co-ordinate
            - Pixel y co-ordinate
            - Time of arrival (ns). This incorporates all three pixel internal timers, but not additional global information (e.g from heartbeat signal) and so rolls over every 1.5ms. Additionally, does not (yet) implement timewalk correction
            - Time over threshold (ns)
            - Pileup - indicates pileup occurred (1) or not (0)
        """

        top = ((rawpackets >> 63) & 0x1)  # 1 bit, 63
        endofcol = ((rawpackets >> 55) & 0xff)  # 8 bits, 62:55
        # 6 bit superpixel value starts with a 4-bit superpixel group
        # 6-bit value is needed for finding x,y position, and 4-bit spg for correcting ToA
        spgroup = ((rawpackets >> 51) & 0x0f)  # 4 bits, 54:51
        superpixel = ((rawpackets >> 49) & 0x3f)  # 6 bits, 54:49.
        pixel = ((rawpackets >> 46) & 0x07)  # 3 bits, 48:46
        ToA_raw = ((rawpackets >> 30) & 0xffff)  # 16 bits, 45:30
        if gray:
            ToA_raw = self.decode_gray[ToA_raw]

        ufToA_start_raw = ((rawpackets >> 26) & 0x0f)  # 4 bits, 29:26
        ufToA_stop_raw = ((rawpackets >> 22) & 0x0f)  # 4 bits, 25:22
        fToA_rise_raw = ((rawpackets >> 17) & 0x1f)  # 5 bits, 21:17
        fToA_fall_raw = ((rawpackets >> 12) & 0x1f)  # 5 bits, 16:12
        ToT_raw = ((rawpackets >> 1) & 0x7ff)  # 11 bits, 11:1
        #pileup = (rawpackets & 0x01)  # 1 bit, 0

        step_To = 25.
        step_fTo = 1.5625
        step_DLL = 0.78125

        # Ultrafast ToA rise/fall values:
        # These measure time delays between signal and 640 MHz clock
        ToA = ToA_raw * step_To - fToA_rise_raw * step_fTo + self.npa_decode_ufT[ufToA_start_raw] - self.npa_decode_ufT[
            ufToA_stop_raw]
        # Additionally, there is a correction related to clock distribution down the columns
        ToA = ToA + (spgroup - 15) * step_DLL

        # fToA rise and fall provide more accurate ToT -
        ToT = ToT_raw * step_To + fToA_rise_raw * step_fTo - fToA_fall_raw * step_fTo

        # Will define top left as x=0, y=0, as with Lambda
        x = 2 * endofcol + (pixel > 3)
        y = superpixel * 4 + pixel % 4
        x = np.abs(447 * top - x)
        y = np.abs(511 * (1 - top) - y)

        # Need to check if this is a special external timestamp pixel, and return appropriate type
        # How external timestamps are fed in is configurable; minimum granularity is superpixel
        # Need to find more details of this - is the whole superpixel overridden?

        if self.handle_events:
            if self._x is None:
                self._x = x
                self._y = y
                self._toa = ToA
                self._tot = ToT
            else:
                self._x = np.append(self._x, x)
                self._y = np.append(self._y, y)
                self._toa = np.append(self._toa, ToA)
                self._tot = np.append(self._tot, ToT)

        return x, y, ToA, ToT # , pileup

    def dataPC24bitdecode(self, rawpackets):
        """Decodes 24 bit photon counting mode data.

        Parameters
        ----------
        rawpacket : 8-byte integer value (big endian format, I believe)

        Returns
        -------
        tuple
            The decoded packet, with the following elements:
            - PacketType.PC24bitData
            - Pixel x co-ordinate
            - Pixel y co-ordinate
            - 24-bit count value
        """

        top = ((rawpackets >> 63) & 0x1)  # 1 bit, 63
        endofcol = ((rawpackets >> 55) & 0xff)  # 8 bits, 62:55
        # 6 bit superpixel value starts with a 4-bit superpixel group
        # 6-bit value is needed for finding x,y position, and 4-bit spg for correcting ToA
        # spgroup = ((rawpackets >> 51) & 0x0f) # 4 bits, 54:51  # not used?
        superpixel = ((rawpackets >> 49) & 0x3f)  # 6 bits, 54:49.
        pixel = ((rawpackets >> 46) & 0x07)  # 3 bits, 48:46
        counts = rawpackets & 0xffffff  # 24 bits, 23:0

        # Will define top left as x=0, y=0, as with Lambda
        x = 2 * endofcol + (pixel > 3)
        y = superpixel * 4 + pixel % 4
        x = np.abs(447 * top - x)
        y = np.abs(511 * (1 - top) - y)

        data_type = np.empty((len(rawpackets),), dtype=PacketType)
        data_type.fill(PacketType.PC24bitData)

        return data_type, x, y, counts

    def timestampeventdecode(self, rawpackets):
        """Various Timepix4 special events which include timestamp data.
        These are Heartbeat, ShutterRise/Fall, T0Sync, SignalRise/Fall and CtrlDataTest

        Parameters
        ----------
        rawpacket : 8-byte integer value (big endian format)

        Returns
        -------
        tuple
            The decoded packet, with the following elements:
            - PacketType
            - Timestamp (ns). This is 48 bits long with a 40 MHz clock - so it has 25ns resolution and a range of up to 7 million s (7e15 ns)
        """

        endofcol = ((rawpackets & 0x7F80000000000000) >> 55)  # 8 bits, 62:55

        currentpackettype = np.array(list(map(PacketType, endofcol)), dtype=PacketType)

        timestamp_raw = (rawpackets & 0x0000FFFFFFFFFFFF)  # 48 bits, 47:00
        step_To = 25.
        timestamp = timestamp_raw * step_To  # Range up to 7 million seconds

        return currentpackettype, timestamp

    def controleventdecode(self, rawpackets):
        """Decodes special packets in Frame mode aimed at helping image decoding.
        The image is split up into "sequences", each of which corresponds to a different region of the chip,
        and each frame and sequence has a header and trailer (FrameStart, FrameEnd, SequenceStart, SequenceEnd)

        Parameters
        ----------
        rawpacket : 8-byte integer value (big endian format)

        Returns
        -------
        tuple
            The decoded packet, with the following elements:
            - PacketType
            - Top - indicates if the data came from the top half (1) or bottom half (0) of the chip
            - Segment - each segment consists of 1/8 of the columns from one half of the chip - see manual
            - Readout mode - int Enum defined in datatypes.py, indicating 8 bit or 16 bit.
        """

        def packettype_mapper(packet):
            try:
                t = PacketType(packet)
                return t
            except ValueError:
                return PacketType.Unknown

        endofcol = ((rawpackets & 0x7F80000000000000) >> 55)  # 8 bits, 62:55
        currentpackettype = np.array(list(map(packettype_mapper, endofcol)), dtype=PacketType)
        top = ((rawpackets >> 63) & 0x1)  # 1 bit, 63
        segment = ((rawpackets & 0x0070000000000000) >> 52)  # 3 bit, 54:52
        readoutmode = np.array(list(map(ReadoutMode, ((rawpackets & 0x000C000000000000) >> 50))),
                               dtype=ReadoutMode)  # 2 bit, 51:50. Use enum.
        return currentpackettype, top, segment, readoutmode

    def DESYheaderdecode(self, rawpackets, array=False):
        """Placeholder function for dealing with packet headers added by our firmware.
        I suggest an 8-byte header as discussed below.
        First byte would be 7C, and corresponding "end of column" code F8 (since this code is bits 55:62)

        Parameters
        ----------
        rawpacket : 8-byte integer value (big endian format)
        array : Boolean, default false. If true, input consists of an array that must be converted to 64 bit int.

        Returns
        -------
        tuple
            The decoded packet, with the following elements (proposed):
            - PacketType.DESYHeader
            - Chip number (0-127)
            - Image number (32 bit - up to 4e9)
            - Packet number (16 bit - up to 65000)

        """

        currentpackettype = np.empty((len(rawpackets),), dtype=PacketType)
        currentpackettype.fill(PacketType.DESYHeader)
        chip = ((rawpackets & 0x007F000000000000) >> 56)  # 8 bit, 63:56
        imageno = ((rawpackets & 0x0000FFFFFFFF0000) >> 16)  # 32 bit, 53:52
        packetno = (rawpackets & 0x000000000000FFFF)  # 16 bit, 15:0
        return currentpackettype, chip, imageno, packetno

    def correct_coarsetime(self, ToA, pixel_indxs, Time_events, time_indxs):
        rollovertime = 25. * 2 ** 16
        heartbeats_entries = Time_events[0] == PacketType.Heartbeat
        coarsetime = np.floor(Time_events[1][heartbeats_entries] / rollovertime)*rollovertime

        return ToA + coarsetime[np.digitize(pixel_indxs, time_indxs[heartbeats_entries])-1]

    # ToF, triggers = find_trigger_events(decodedpackets[1], decodedpackets[2], decodedpackets[3])

    def find_triggers(self, x, y, ToA):
        "the first index in trig_indxs will be used for calculation of ToF"
        trigger_entries = [trig_i == x + 450 * y for trig_i in self.trigger_pixels_indxs]

        #ToF = None
        #if sum(trigger_entries[0]) > 0:
        #    ToF = ToA - ToA[np.digitize(ToA, ToA[trigger_entries[0]])]

        triggers = [ToA[trig] for trig in trigger_entries]

        if self.handle_events:
            if self._triggers is None:
                self._triggers =  np.copy(triggers[0])
            else:
                self._triggers = np.append(self._triggers, triggers[0])

    def find_events_fast(self):
        if self.__exist_enough_triggers():
            self._triggers = self._triggers[np.argmin(self._triggers) :]
            if self.__toa_is_not_empty():
                start = self._triggers

            if start.size > 1:
                trigger_counter = np.arange(
                    self._trigger_counter, self._trigger_counter + start.size - 1, dtype=int
                )
                self._trigger_counter = trigger_counter[-1] + 1

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
                    start[np.unique(event_mapping)]
                )  # times for trigger event

            return result, (np.unique(result[0]), timeStamps)

        return None  # Clear out the triggers since they have nothing

    def __exist_enough_triggers(self):
        return self._triggers is not None and self._triggers.size >= 2

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



def main():
    filename = '/home/samartse/TPX4/2023-03-15_30MHz_events_1min_4700_EQ_cosmics_bias_100V_08.raw'
    filename = '/home/samartse/TPX4/2023-05-30_events_HV100_cosmic_30s_bytes.bin'
    # file = open(filename,"rb")
    # bin_data = file.read()
    with open(filename, 'rb') as data_file:
        #bin_data = np.load(data_file)
        bin_data = data_file.read()

    packetprocessor = PacketProcessor_tpx4()
    event_data, pixel_data, timestamps, triggers = packetprocessor.process(bin_data)
    print('event_data: ', event_data)
    print('pixel_data: ', pixel_data)
    print('timestamps: ', timestamps)
    print('triggers: ', triggers)




if __name__ == "__main__":
    main()