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

"""Module that contains constants that can be passed into spidr"""
from enum import Enum,IntEnum

class SpidrReadoutSpeed(Enum):
    HighSpeed = 0x89ABCDEF #High speed magic number
    LowSpeed = 0x12345678 #Low speed magic number
    Default = 0 #Use default readout speed


class SpidrRegs(IntEnum):
    SPIDR_CPU2TPX_WR_I           =0x01C8
    SPIDR_SHUTTERTRIG_CTRL_I     =0x0290
    SPIDR_SHUTTERTRIG_CNT_I      =0x0294
    SPIDR_SHUTTERTRIG_FREQ_I     =0x0298
    SPIDR_SHUTTERTRIG_LENGTH_I   =0x029C
    SPIDR_SHUTTERTRIG_DELAY_I    =0x02AC
    SPIDR_DEVICES_AND_PORTS_I    =0x02C0
    SPIDR_TDC_TRIGGERCOUNTER_I   =0x02F8
    SPIDR_FE_GTX_CTRL_STAT_I     =0x0300
    SPIDR_PIXEL_PKTCOUNTER_I     =0x0340
    SPIDR_IPMUX_CONFIG_I         =0x0380
    SPIDR_UDP_PKTCOUNTER_I       =0x0384
    SPIDR_UDPMON_PKTCOUNTER_I    =0x0388
    SPIDR_UDPPAUSE_PKTCOUNTER_I  =0x038C
    SPIDR_PIXEL_PKTCOUNTER_OLD_I =0x0390
    SPIDR_PIXEL_FILTER_I         =0x0394


ALL_PIXELS = 256

class SpidrShutterMode(Enum):
    ExternalRisingFalling   =0
    ExternalFallingRising   =1
    ExternalRisingTimer     =2
    ExternalFallingTimer    =3
    Auto                    =4
    PulseCounter            =5
    Open = 6
