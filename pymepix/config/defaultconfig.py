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

from .timepixconfig import TimepixConfig

class DefaultConfig(TimepixConfig):

    def __init__(self):
        pass
    

    def dacCodes(self):
        codes = [(1,       128)     # TPX3_IBIAS_PREAMP_ON  [0-255]
                ,(2,         8)    # TPX3_IBIAS_PREAMP_OFF [0-15]
                ,(3,       128)     # TPX3_VPREAMP_NCAS     [0-255]
                ,(4,         5)     # TPX3_IBIAS_IKRUM      [0-255]
                ,(5,       128)     # TPX3_VFBK             [0-255]
                ,(6,       420)     # TPX3_VTHRESH_FINE     [0-511]
                ,(7,         6)     # TPX3_VTHRESH_COARSE   [0-15]
                ,(8,        84)     # TPX3_IBIAS_DISCS1_ON  [0-255]
                ,(9,         8)     # TPX3_IBIAS_DISCS1_OFF [0- 15]
                ,(10,      128)      # TPX3_IBIAS_DISCS2_ON  [0-255]
                ,(11,        8)      # TPX3_IBIAS_DISCS2_OFF [0-15]
                ,(12,      192)# TPX3_IBIAS_PIXELDAC   [0-255]
                ,(13 ,     128) # TPX3_IBIAS_TPBUFIN    [0-255]
                ,(14  ,    128)  # TPX3_IBIAS_TPBUFOUT   [0-255]
                ,(15   ,   128)   # TPX3_VTP_COARSE       [0-255]
                ,(16    ,  256)    # TPX3_VTP_FINE         [0-511]
                ,(17     , 128)     # TPX3_IBIAS_CP_PLL     [0-255]
                ,(18      ,128)]
        return codes
