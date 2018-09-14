from enum import IntEnum,Enum


class PacketType(Enum):
    Trigger = 0
    Pixel = 1


class Polarity(IntEnum):
    Positive = 0x0
    Negative = 0x1

class OperationMode(IntEnum):
    ToAandToT = 0x0
    ToA = 0x2
    EventiTot = 0x4
    Mask = 0x6

class GrayCounter(IntEnum):
    Disable = 0x0
    Enable = 0x8
    Mask = 0x8

class TestPulse(IntEnum):
    Disable = 0x0
    Enable = 0x20
    Mask = 0x20

class SuperPixel(IntEnum):
    Disable= 0
    Enable = 0x40
    Mask = 0x40


class TimerOverflow(IntEnum):
    CycleOverflow=0
    StopOverflow=0x80
    Mask = 0x80

class TestPulseDigAnalog(IntEnum):
    FrontEndAnalog = 0x000
    DiscriminatorDigital = 0x200
    Mask = 0x200

class TestPulseGenerator(IntEnum):
    Internal = 0
    External = 0x400
    Mask = 0x400
class TimeofArrivalClock(IntEnum):
    PhaseShiftedGray = 0x0
    SystemClock = 0x800
    Mask = 0x800



