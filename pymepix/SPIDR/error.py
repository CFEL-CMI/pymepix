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

class SPIDRErrorDefs:
    ERR_NONE            = 0x00000000
    ERR_UNKNOWN_CMD     = 0x00000001
    ERR_MSG_LENGTH      = 0x00000002
    ERR_SEQUENCE        = 0x00000003
    ERR_ILLEGAL_PAR     = 0x00000004
    ERR_NOT_IMPLEMENTED = 0x00000005
    ERR_TPX3_HARDW      = 0x00000006
    ERR_ADC_HARDW       = 0x00000007
    ERR_DAC_HARDW       = 0x00000008
    ERR_MON_HARDW       = 0x00000009
    ERR_FLASH_STORAGE   = 0x0000000A
    ERR_MONITOR         = 0x0000000B






class PymePixException(Exception):
    
    ERR_STR=   [
            "no error",
            "ERR_UNKNOWN_CMD",
            "ERR_MSG_LENGTH",
            "ERR_SEQUENCE",
            "ERR_ILLEGAL_PAR",
            "ERR_NOT_IMPLEMENTED",
            "ERR_TPX3_HARDW",
            "ERR_ADC_HARDW",
            "ERR_DAC_HARDW",
            "ERR_MON_HARDW",
            "ERR_FLASH_STORAGE"
        ]


    TPX3_ERR_STR =[
            "no error",
            "TPX3_ERR_SC_ILLEGAL",
            "TPX3_ERR_SC_STATE",
            "TPX3_ERR_SC_ERRSTATE",
            "TPX3_ERR_SC_WORDS",
            "TPX3_ERR_TX_TIMEOUT",
            "TPX3_ERR_EMPTY",
            "TPX3_ERR_NOTEMPTY",
            "TPX3_ERR_FULL",
            "TPX3_ERR_UNEXP_REPLY",
            "TPX3_ERR_UNEXP_HEADER",
            "TPX3_ERR_LINKS_UNLOCKED"
        ]

    SPIDR_ERR_STR=[
        "SPIDR_ERR_I2C_INIT",
        "SPIDR_ERR_LINK_INIT",
        "SPIDR_ERR_MPL_INIT",
        "SPIDR_ERR_MPU_INIT",
        "SPIDR_ERR_MAX6642_INIT",
        "SPIDR_ERR_INA219_0_INIT",
        "SPIDR_ERR_INA219_1_INIT",
        "SPIDR_ERR_I2C"
    ]

    STORE_ERR_STR = [
        "no error",
        "STORE_ERR_TPX",
        "STORE_ERR_WRITE",
        "STORE_ERR_WRITE_CHECK",
        "STORE_ERR_READ",
        "STORE_ERR_UNMATCHED_ID",
        "STORE_ERR_NOFLASH"
    ]

    MONITOR_ERR_STR = [
        "MON_ERR_TEMP_DAQ",
        "MON_ERR_POWER_DAQ",
    ]

    def __init__(self, error_code):

        self.message = self.errorMessage(error_code)

        Exception.__init__(self, self.message)

    def errorMessage(self, code):

        err_id = code & 0xFF

        message = ""

        if err_id >= len(self.ERR_STR) or err_id < 0:
            return 'Unknown error code {}'.format(err_id)
        else:
            message += "Recieved error code {}: {}".format(err_id, self.ERR_STR[err_id])

        if err_id == 6:
            err = (code & 0xFF00) >> 8
            message += ', '
            if err > len(self.TPX3_ERR_STR):
                message += '<unknown>'
            else:
                message += self.TPX3_ERR_STR[err]

        return message
