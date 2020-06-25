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

from enum import IntEnum, Enum


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
    Disable = 0
    Enable = 0x40
    Mask = 0x40


class TimerOverflow(IntEnum):
    CycleOverflow = 0
    StopOverflow = 0x80
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


class DacRegisterCodes(IntEnum):
    Ibias_Preamp_ON = 1
    Ibias_Preamp_OFF = 2
    VPreamp_NCAS = 3
    Ibias_Ikrum = 4
    Vfbk = 5
    Vthreshold_fine = 6
    Vthreshold_coarse = 7
    Ibias_DiscS1_ON = 8
    Ibias_DiscS1_OFF = 9
    Ibias_DiscS2_ON = 10
    Ibias_DiscS2_OFF = 11
    Ibias_PixelDAC = 12
    Ibias_TPbufferIn = 13
    Ibias_TPbufferOut = 14
    VTP_coarse = 15
    VTP_fine = 16
    Ibias_CP_PLL = 17
    PLL_Vcntrl = 18
