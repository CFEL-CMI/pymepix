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

"""This module contains a list of all (found) commands for the SPIDR board"""
from enum import IntEnum


class SpidrCmds(IntEnum):
    """A class that packages all the commands under a single name"""
    CMD_NOP                =0x000

    #General: module
    CMD_GET_SOFTWVERSION   =0x901
    CMD_GET_FIRMWVERSION   =0x902

    CMD_GET_HEADERFILTER   =0x905
    CMD_SET_HEADERFILTER   =0x906

    CMD_RESET_MODULE       =0x907
    CMD_SET_BUSY           =0x908
    CMD_CLEAR_BUSY         =0x909
    CMD_SET_LOGLEVEL       =0x90A
    CMD_DISPLAY_INFO       =0x90B
    CMD_SET_TIMEOFDAY      =0x90C
    CMD_GET_DEVICECOUNT    =0x90D
    #CMD_GET_PORTCOUNT    =0x90E #### OBSOLETE
    CMD_GET_BOARDID        =0x90E
    CMD_GET_CHIPBOARDID    =0x90F

    #Configuration: devices
    CMD_GET_DEVICEID       =0x110
    CMD_GET_DEVICEIDS      =0x111
    CMD_GET_IPADDR_SRC     =0x112
    CMD_SET_IPADDR_SRC     =0x113
    CMD_GET_IPADDR_DEST    =0x114
    CMD_SET_IPADDR_DEST    =0x115
    #CMD_GET_DEVICEPORTS  =0x115
    #CMD_SET_DEVICEPORT   =0x116
    CMD_GET_DEVICEPORT     =0x116
    CMD_GET_SERVERPORT     =0x117
    #CMD_GET_SERVERPORTS  =0x118
    CMD_SET_SERVERPORT     =0x119
    CMD_GET_DAC            =0x11A
    CMD_SET_DAC            =0x11B

    CMD_SET_DACS_DFLT      =0x11F
    CMD_CONFIG_CTPR        =0x120
    CMD_SET_CTPR           =0x121
    CMD_GET_CTPR           =0x122
    CMD_SET_CTPR_LEON      =0x123

    CMD_RESET_DEVICE       =0x124
    CMD_RESET_DEVICES      =0x125
    CMD_REINIT_DEVICE      =0x126
    CMD_REINIT_DEVICES     =0x127
    CMD_GET_EFUSES         =0x128
    ##ifdef CERN_PROBESTATION
    CMD_BURN_EFUSE         =0x129
    ##endif

    #Configuration: pixels
    CMD_SET_PIXCONF        =0x22A
    CMD_GET_PIXCONF        =0x22D
    CMD_RESET_PIXELS       =0x22E

    #Configuration: devices (continued)
    CMD_GET_TPPERIODPHASE  =0x330
    CMD_SET_TPPERIODPHASE  =0x331
    CMD_SET_TPNUMBER       =0x332
    CMD_GET_TPNUMBER       =0x333
    CMD_GET_GENCONFIG      =0x334
    CMD_SET_GENCONFIG      =0x335
    CMD_GET_PLLCONFIG      =0x336
    CMD_SET_PLLCONFIG      =0x337
    CMD_SET_SENSEDAC       =0x338
    CMD_SET_EXTDAC         =0x33A
    CMD_UPLOAD_PACKET      =0x33B
    CMD_GET_OUTBLOCKCONFIG =0x33C
    CMD_SET_OUTBLOCKCONFIG =0x33D
    CMD_GET_SLVSCONFIG     =0x33E
    CMD_SET_SLVSCONFIG     =0x33F

    #Trigger
    CMD_GET_TRIGCONFIG     =0x440
    CMD_SET_TRIGCONFIG     =0x441
    CMD_AUTOTRIG_START     =0x442
    CMD_AUTOTRIG_STOP      =0x443

    #Data-acquisition
    CMD_SEQ_READOUT        =0x445
    CMD_DDRIVEN_READOUT    =0x446
    CMD_PAUSE_READOUT      =0x447

    #Monitoring
    CMD_GET_ADC            =0x548
    CMD_GET_REMOTETEMP     =0x549
    CMD_GET_LOCALTEMP      =0x54A
    CMD_GET_AVDD           =0x54B
    CMD_GET_DVDD           =0x54C
    CMD_GET_AVDD_NOW       =0x54D
    CMD_GET_SPIDR_ADC      =0x54E
    CMD_GET_DVDD_NOW       =0x54F

    #Configuration: timer
    CMD_RESTART_TIMERS     =0x550
    CMD_RESET_TIMER        =0x551
    CMD_GET_TIMER          =0x552
    CMD_SET_TIMER          =0x553

    #Trigger (continued)
    CMD_GET_SHUTTERSTART   =0x554
    CMD_GET_SHUTTEREND     =0x555
    CMD_GET_EXTSHUTTERCNTR =0x556
    CMD_GET_SHUTTERCNTR    =0x557
    CMD_RESET_COUNTERS     =0x558

    #Configuration: devices (continued)
    CMD_GET_PWRPULSECONFIG =0x55B
    CMD_SET_PWRPULSECONFIG =0x55C
    CMD_PWRPULSE_ENA       =0x55D
    CMD_TPX_POWER_ENA      =0x55E
    CMD_BIAS_SUPPLY_ENA    =0x55F
    CMD_SET_BIAS_ADJUST    =0x560
    CMD_DECODERS_ENA       =0x561
    CMD_SET_OUTPUTMASK     =0x562
    CMD_SET_READOUTSPEED   =0x563
    CMD_GET_READOUTSPEED   =0x564

    #Configuration: timer (continued)
    CMD_T0_SYNC            =0x565

    #Monitoring (continued)
    CMD_GET_FPGATEMP       =0x568
    CMD_GET_FANSPEED       =0x569
    CMD_SET_FANSPEED       =0x56A
    CMD_SELECT_CHIPBOARD   =0x56B
    CMD_GET_VDD            =0x56C
    CMD_GET_VDD_NOW        =0x56D
    CMD_GET_HUMIDITY       =0x56E
    CMD_GET_PRESSURE       =0x56F

    #Configuration: non-volatile onboard storage
    CMD_STORE_ADDRPORTS    =0x670
    CMD_STORE_DACS         =0x671
    CMD_STORE_REGISTERS    =0x672
    CMD_STORE_PIXCONF      =0x673
    CMD_ERASE_ADDRPORTS    =0x674
    CMD_ERASE_DACS         =0x675
    CMD_ERASE_REGISTERS    =0x676
    CMD_ERASE_PIXCONF      =0x677
    CMD_VALID_ADDRPORTS    =0x678
    CMD_VALID_DACS         =0x679
    CMD_VALID_REGISTERS    =0x67A
    CMD_VALID_PIXCONF      =0x67B
    CMD_STORE_STARTOPTS    =0x67C
    CMD_GET_STARTOPTS      =0x67D

    CMD_READ_FLASH         =0x67E
    CMD_WRITE_FLASH        =0x67F

    #Other
    CMD_GET_GPIO           =0x780
    CMD_SET_GPIO           =0x781
    CMD_SET_GPIO_PIN       =0x782
    CMD_GET_SPIDRREG       =0x783
    CMD_SET_SPIDRREG       =0x784
    CMD_SET_CHIPBOARDID    =0x785
    CMD_SET_BOARDID        =0x786

    #Reply bit: set in the reply message in the command identifier
    CMD_REPLY            =0x00010000

    #No-reply bit: set in the command message in the command identifier
    #indicating to the SPIDR server that no reply is expected
    #(to speed up certain operations, such as pixel configuration uploads)
    CMD_NOREPLY          =0x00080000

    CMD_MASK             =0x0000FFFF