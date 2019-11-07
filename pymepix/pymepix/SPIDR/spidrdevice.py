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

import weakref
from .spidrcmds import SpidrCmds
import numpy as np
from .spidrdefs import SpidrRegs
from pymepix.core.log import Logger


class SpidrDevice(Logger):
    """Object that interfaces with a specific device (Timepix/Medipix) connect to SPIDR

    This object handles communication and management of a specific device. There is no need
    to create this object directly as :class:`SpidrController` automatically creates it for you
    and is accessed by its [] getter methods

    Parameters
    ----------
    spidr_ctrl: :class:`SpidrController`
        SPIDR controller object the device belongs to
    device_num:
        Device index from SPIDR (Starts from 1)


    """

    def __init__(self, spidr_ctrl, device_num):
        Logger.__init__(self, SpidrDevice.__name__)
        self._ctrl = weakref.proxy(spidr_ctrl)
        self._dev_num = device_num

        self.info('Device {} with id {} created'.format(self._dev_num, self.deviceId))

        self.clearPixelConfig()

    def clearPixelConfig(self):
        self._pixel_mask = np.ones(shape=(256, 256), dtype=np.uint8)
        self._pixel_threshold = np.zeros(shape=(256, 256), dtype=np.uint8)
        self._pixel_test = np.zeros(shape=(256, 256), dtype=np.uint8)

    @property
    def deviceId(self):
        """Returns unique device Id

        Parameters
        ----------
        spidr_ctrl: :class:`SpidrController`
            SPIDR controller object the device belongs to
        device_num:
            Device index from SPIDR (Starts from 1)


        """
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_DEVICEID, self._dev_num)

    @property
    def headerFilter(self):
        mask = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_HEADERFILTER, self._dev_num)

        eth_mask = mask & 0xFFFF
        cpu_mask = (mask >> 16) & 0xFFFF

        return eth_mask, cpu_mask

    def setHeaderFilter(self, eth_mask, cpu_mask):
        to_write = (eth_mask & 0xFFFF) | ((cpu_mask & 0xFFFF) << 16)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_HEADERFILTER, self._dev_num, to_write)

    def reset(self):
        self._ctrl.requestSetInt(SpidrCmds.CMD_RESET_DEVICE, self._dev_num, 0)

    def reinitDevice(self):
        self._ctrl.requestSetInt(SpidrCmds.CMD_REINIT_DEVICE, self._dev_num, 0)

    def setSenseDac(self, dac_code):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_SENSEDAC, self._dev_num, dac_code)

    def setExternalDac(self, dac_code, dac_val):
        dac_data = ((dac_code & 0xFFFF) << 16) | (dac_val & 0xFFFF)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_EXTDAC, self._dev_num, dac_data)

    def getDac(self, dac_code):

        dac_data = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_DAC, self._dev_num, dac_code)

        if (dac_data >> 16) & 0xFFFF != dac_code:
            raise Exception('DAC code mismatch')

        return dac_data & 0xFFFF

    def setDac(self, dac_code, dac_val):
        dac_data = ((dac_code & 0xFFFF) << 16) | (dac_val & 0xFFFF)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_DAC, self._dev_num, dac_data)

    def setDacDefault(self):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_DACS_DFLT, self._dev_num)

    @property
    def genConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_GENCONFIG, self._dev_num)

    @genConfig.setter
    def genConfig(self, value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_GENCONFIG, self._dev_num, value)

    @property
    def pllConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_PLLCONFIG, self._dev_num)

    @pllConfig.setter
    def pllConfig(self, value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_PLLCONFIG, self._dev_num, value)

    @property
    def outBlockConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_OUTBLOCKCONFIG, self._dev_num)

    @outBlockConfig.setter
    def outBlockConfig(self, value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_OUTBLOCKCONFIG, self._dev_num, value)

    def setOutputMask(self, value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_OUTPUTMASK, self._dev_num, value)

    @property
    def readoutSpeed(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_READOUTSPEED, self._dev_num)

    @readoutSpeed.setter
    def readoutSpeed(self, mbits):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_READOUTSPEED, self._dev_num, mbits)

    @property
    def linkStatus(self):
        reg_addr = SpidrRegs.SPIDR_FE_GTX_CTRL_STAT_I + (self._dev_num << 2)
        status = self._ctrl.getSpidrReg(reg_addr)

        enabled = (~status) & 0xFF
        locked = (status & 0xFF0000) >> 16

        return status, enabled, locked

    @property
    def slaveConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_SLVSCONFIG, self._dev_num)

    @slaveConfig.setter
    def slaveConfig(self, value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_GET_SLVSCONFIG, self._dev_num, value)

    @property
    def powerPulseConfig(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_PWRPULSECONFIG, self._dev_num)

    @powerPulseConfig.setter
    def powerPulseConfig(self, value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_GET_PWRPULSECONFIG, self._dev_num, value)

    def uploadPacket(self, packet):
        self._ctrl.requestSetIntBytes(SpidrCmds.CMD_UPLOAD_PACKET, self._dev_num, len(packet), packet)

    @property
    def TpPeriodPhase(self):
        tp_data = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_TPPERIODPHASE, self._dev_num)

        return tp_data & 0xFFFF, (tp_data >> 16) & 0xFFFF

    def setTpPeriodPhase(self, period, phase):
        tp_data = ((phase & 0xFFFF) << 16) | (period & 0xFFFF)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_TPPERIODPHASE, self._dev_num, tp_data)

    @property
    def tpNumber(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_TPNUMBER, self._dev_num)

    @tpNumber.setter
    def tpNumber(self, value):
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_TPNUMBER, self._dev_num, value)

    @property
    def columnTestPulseRegister(self):
        _cptr = self._ctrl.requestGetBytes(SpidrCmds.CMD_GET_CTPR, self._dev_num, 256 // 8)
        # Store it locally for use
        self._cptr = _cptr
        return _cptr

    @columnTestPulseRegister.setter
    def columnTestPulseRegister(self, _cptr):
        self._ctrl.requestSetIntBytes(SpidrCmds.CMD_SET_CTPR, self._dev_num, 0, _cptr)
        self._cptr = self.columnTestPulseRegister

    def getPixelConfig(self):

        for y in range(256):
            # print('Requested row {}'.format(y))
            column, pixelrow = self._ctrl.requestGetIntBytes(SpidrCmds.CMD_GET_PIXCONF, self._dev_num, 256, y)

            # print ('Column : {} Pixels: {}'.format(row,pixelcolumn))
            self._pixel_mask[column, :] = pixelrow[:] & 0x1
            self._pixel_threshold[column, :] = (pixelrow[:] >> 1) & 0xf
            self._pixel_test[column, :] = (pixelrow[:] >> 5) & 0x1
            # self._pixel_config[self._pixel_idx][column,:] = pixelrow[:]

    def resetPixels(self):
        self._ctrl.requestSetInt(SpidrCmds.CMD_RESET_PIXELS, self._dev_num, 0)

    def resetPixelConfig(self, index=-1, all_pixels=False):

        self.clearPixelConfig()

    def setSinglePixelThreshold(self, x, y, threshold):

        threshold &= 0xF
        self._pixel_threshold[x, y] = threshold
        # self._pixel_config[self._pixel_idx][x,y] =~0x01E
        # self._pixel_config[self._pixel_idx][x,y] |= threshold<<1

    def setPixelThreshold(self, threshold):

        threshold &= 0xF
        self._pixel_threshold[...] = threshold[...]

    def setSinglePixelMask(self, x, y, mask):

        self._pixel_mask[x, y] = mask

    def setPixelMask(self, mask):
        self._pixel_mask[...] = mask[...] & 0x1

    def setSinglePixelTestBit(self, x, y, val):
        self._pixel_test[x, y] = val

    def setPixelTestBit(self, test):
        self._pixel_test[...] = test[...] & 0x1

    def uploadPixelConfig(self, formatted=True, columns_per_packet=1):

        columns_per_packet = max(1, columns_per_packet)
        columns_per_packet = min(4, columns_per_packet)

        if formatted:
            self._uploadFormatted(columns_per_packet)
            return

        raise NotImplementedError

    def _uploadFormatted(self, columns_per_packet):
        # TIMEPIX_BITS=6
        # nbytes = columns_per_packet*(256*TIMEPIX_BITS)//8

        # for x in range(0,256,columns_per_packet):
        #     for col in range(0,columns_per_packet):
        #         to_write = self._pixel_config[self._pixel_idx][x+col,:]
        #         offset = 0
        #         packet = np.packbits(np.unpackbits(to_write).reshape(-1,8)[:,2:8].reshape(-1))

        #     self._ctrl.req
        self.resetPixels()
        final_pixels = (self._pixel_mask & 0x1) | (self._pixel_threshold & 0xf) << 1 | (self._pixel_test & 1) << 5
        self.debug('FINAL_PIXELS {}'.format(final_pixels))
        # Flatten and unpack the bits of the matrix selecting only the necessary bits
        for x in range(0, 256):
            start_col = x
            end_col = x + 1
            matrix_packet = final_pixels[:, start_col:end_col].reshape(256)
            # @print (matrix_packet.shape,matrix_packet.dtype)
            # print ('Sending packet with columns {}-{}'.format(start_col,end_col))
            self._ctrl.requestSetIntBytes(SpidrCmds.CMD_SET_PIXCONF, self._dev_num, x, matrix_packet)

            # request_packet = np.ndarray(shape=(512,),dtype=np.int32)

            # request_packet[0] = socket.htonl(SpidrCmds.CMD_SET_PIXCONF)
            # message_length = (4+1+matrix_packet_int.shape[0])*4
            # request_packet[1] = socket.htonl(message_length)
            # request_packet[2]=0
            # request_packet[3] = socket.htonl(self._dev_num)
            # request_packet[4] = 0
            # #request_packet[4:4+column_mask.shape[0]] = column_mask[:]
            # start= 5
            # end = start + matrix_packet_int.shape[0]
            # request_packet[start:end] = matrix_packet_int[:]

            # self._ctrl.customRequest(request_packet,message_length)

        # Should be length 393216

    @property
    def timer(self):
        return tuple(self._ctrl.requestGetInts(SpidrCmds.CMD_GET_TIMER, self._dev_num, 2))

    @timer.setter
    def timer(self, time):
        if len(time) != 2:
            raise ValueError(tuple)
        self._ctrl.requestSetInts(SpidrCmds.CMD_SET_TIMER, self._dev_num, list(time))

    @property
    def shutterStart(self):
        return tuple(self._ctrl.requestGetInts(SpidrCmds.CMD_GET_SHUTTERSTART, self._dev_num, 2))

    @property
    def shutterEnd(self):
        return tuple(self._ctrl.requestGetInts(SpidrCmds.CMD_GET_SHUTTEREND, self._dev_num, 2))

    def t0Sync(self):
        self._ctrl.requestSetInt(SpidrCmds.CMD_T0_SYNC, self._dev_num, 0)

    @property
    def pixelPacketCounter(self):
        return self._ctrl.getSpidrReg(SpidrRegs.SPIDR_PIXEL_PKTCOUNTER_I + self._dev_num)

    def getDacOut(self, nr_samples):
        return self._ctrl.getAdc(self._dev_num, nr_samples)

    @property
    def ipAddrSrc(self):

        val = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_IPADDR_SRC, self._dev_num)

        return "{}.{}.{}.{}".format((val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, (val >> 0) & 0xFF)

    @ipAddrSrc.setter
    def ipAddrSrc(self, ipaddr):

        split = ipaddr.split['.']

        first = int(split[0]) & 0xFF
        second = int(split[1]) & 0xFF
        third = int(split[2]) & 0xFF
        forth = int(split[3]) & 0xFF

        comb = (first << 24) | (second << 16) | (third << 8) | (forth << 0)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_IPADDR_SRC, self._dev_num, comb)

    @property
    def ipAddrDest(self):
        val = self._ctrl.requestGetInt(SpidrCmds.CMD_GET_IPADDR_DEST, self._dev_num)

        return "{}.{}.{}.{}".format((val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, (val >> 0) & 0xFF)

    @ipAddrDest.setter
    def ipAddrDest(self, ipaddr):
        split = ipaddr.split['.']

        first = int(split[0]) & 0xFF
        second = int(split[1]) & 0xFF
        third = int(split[2]) & 0xFF
        forth = int(split[3]) & 0xFF

        comb = (first << 24) | (second << 16) | (third << 8) | (forth << 0)
        self._ctrl.requestSetInt(SpidrCmds.CMD_SET_IPADDR_DEST, self._dev_num, comb)

    @property
    def devicePort(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_DEVICEPORT, self._dev_num)

    @property
    def serverPort(self):
        return self._ctrl.requestGetInt(SpidrCmds.CMD_GET_SERVERPORT, self._dev_num)

    @serverPort.setter
    def serverPort(self, value):
        return self._ctrl.requestSetInt(SpidrCmds.CMD_SET_SERVERPORT, self._dev_num, value)
