"""Defines different packet types in Timepix4"""
from enum import IntEnum


class PacketType(IntEnum):
    """Defines different types of Timepix4 packet"""
    """Corresponds to EoC header, if a unique one exists (not the case for pixel data) """
    RawData = 0
    """Raw 8-byte word"""
    PixelData = 1
    """Decoded Pixel Data"""
    TriggerData = 2
    """Decoded Trigger Data (NB - only distinguishable from pixeldata after processing) """
    PC24bitData = 3
    """Data from photon counting 24 bit mode"""
    NoData = 4
    """Slow control link packets of FFFFFFFF00000000 indicate no data - this is a special case"""
    Heartbeat = 0xE0
    """Heartbeat timestamp"""
    ShutterRise = 0xE1
    """Shutter rise timestamp"""
    ShutterFall = 0xE2
    """Shutter fall timestamp"""
    T0Sync = 0xE3
    """Synchronisation timestamp"""
    SignalRise = 0xE4
    """Configurable input signal timestamp"""
    SignalFall = 0xE5
    """Configurable input signal fall timestamp"""
    CtrlDataTest = 0xEA
    """Continuous flow of test packets"""
    FrameStart = 0xF0
    """Indicates start of frame in frame mode"""
    FrameEnd = 0xF1
    """Indicates end of frame in frame mode"""
    SequenceStart = 0xF2
    """Indicates start of sequence in frame mode"""
    SequenceEnd = 0xF3
    """Indicates end of sequence in frame mode"""
    DESYHeader = 0xF8
    """Indicates DESY-specific header added to data stream"""
    Unknown = -1
    """Can be used to deal with other cases"""


class ReadoutMode(IntEnum):
    # Not found in manual yet - just assuming
    Frame8bit = 0
    Frame16bit = 1
    Event = 2
    PC24bit = 3
