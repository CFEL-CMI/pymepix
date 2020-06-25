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

###################################
# TCP Server
###################################
import struct
import socket
import socketserver
from pymepix.SPIDR.spidrcmds import SpidrCmds
from pymepix.timepixdef import DacRegisterCodes
from pymepix.core.log import Logger
import numpy as np


class TPX3Handler(socketserver.BaseRequestHandler, Logger):
    #def __init__(self):
    #    Logger.__init__(self, "TPX3 TCP Handler")

    def handle(self):
        self.requestIndex = 0
        # while self.requestIndex<1000:
        while 1:
            sock_recv = self.request.recv(1024)  # .strip()
            self.data = np.frombuffer(sock_recv, dtype=np.uint32)
            # print(f'{self.requestIndex} recieved: {self.data}')

            # self.request is the TCP socket connected to the client
            if len(self.data) > 0:
                # self.data = struct.unpack('IIIII', self.data)
                self.cmd = socket.htonl(int(self.data[0]))
                cmdStr = next(name for name, value in vars(SpidrCmds).items() if value == self.cmd)
                print(f'{self.requestIndex} cmd: {cmdStr} {hex(self.cmd)}')
                # print(f"{self.requestIndex} {self.client_address[0]} wrote:", flush=True)
                self.data = [socket.htonl(int(i)) for i in self.data]
                # print(f'{self.requestIndex}\trecieved: {self.data}', flush=True)


                ####################
                # General module
                if self.cmd == SpidrCmds.CMD_GET_SOFTWVERSION:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 111]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_FIRMWVERSION:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 111]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_HEADERFILTER:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_HEADERFILTER:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_RESET_MODULE:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_BUSY:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_CLEAR_BUSY:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_SET_LOGLEVEL:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_DISPLAY_INFO:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_SET_TIMEOFDAY:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_DEVICECOUNT:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 1]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_BOARDID:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_CHIPBOARDID:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 1]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                ####################
                # Configuration: devices
                elif self.cmd == SpidrCmds.CMD_GET_DEVICEID:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_DEVICEIDS:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 1]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_IPADDR_SRC:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, (127 << 24) | (0 << 16) | (0 << 8) | (1 << 0)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_IPADDR_SRC:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_IPADDR_DEST:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    ip = (127 << 24) | (0 << 16) | (0 << 8) | (1 << 0)
                    data = [reply, 0, 0, 0, ip]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_IPADDR_DEST:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_DEVICEPORT:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 8192]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_SERVERPORT:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 50000]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_SERVERPORT:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_DAC:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    dac_code = (self.data[4] << 16)
                    data = [reply, 0, 0, 0, dac_code]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_DAC:
                    cmdLoad = self.data[4]

                    dacCmd = cmdLoad >> 16
                    value = cmdLoad & 0xFFFF  # max DAC cmd is 18
                    dacCmdStr = next(name for name, value in vars(DacRegisterCodes).items() if value == dacCmd)
                    print(f'\t{dacCmdStr}\t{value}')

                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_DACS_DFLT:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_CONFIG_CTPR:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_SET_CTPR:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_CTPR:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 1]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_CTPR_LEON:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_RESET_DEVICE:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_RESET_DEVICES:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_REINIT_DEVICE:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_REINIT_DEVICES:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_EFUSES:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_BURN_EFUSE:
                    print('NEEDS IMPLEMENTATION')

                ####################
                # Configuration: devices
                elif self.cmd == SpidrCmds.CMD_SET_PIXCONF:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_PIXCONF:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 253, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009,
                            16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009,
                            16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009,
                            16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009,
                            16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009,
                            16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009,
                            16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009, 16843009,
                            16843009, 16843009, 16843009]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_RESET_PIXELS:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                ####################
                # Configuration: devices (continued)
                elif self.cmd == SpidrCmds.CMD_GET_TPPERIODPHASE:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 4]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_TPPERIODPHASE:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_SET_TPNUMBER:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_TPNUMBER:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_GENCONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_GENCONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_PLLCONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_PLLCONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_SENSEDAC:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_EXTDAC:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_UPLOAD_PACKET:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_OUTBLOCKCONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_OUTBLOCKCONFIG:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_SLVSCONFIG:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_SET_SLVSCONFIG:
                    print('NEEDS IMPLEMENTATION')

                ####################
                # Trigger
                elif self.cmd == SpidrCmds.CMD_GET_TRIGCONFIG:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_SET_TRIGCONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_AUTOTRIG_START:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_AUTOTRIG_STOP:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                ####################
                # Data-acquisition
                elif self.cmd == SpidrCmds.CMD_SEQ_READOUT:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_DDRIVEN_READOUT:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_PAUSE_READOUT:
                    print('NEEDS IMPLEMENTATION')

                ####################
                # Monitoring
                elif self.cmd == SpidrCmds.CMD_GET_ADC:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_REMOTETEMP:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, np.random.randint(1000, 5000)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_LOCALTEMP:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, np.random.randint(1000, 5000)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_AVDD:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_DVDD:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_AVDD_NOW:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 111]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_SPIDR_ADC:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 111]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_DVDD_NOW:
                    print('NEEDS IMPLEMENTATION')

                ####################
                # Configuration: timer
                elif self.cmd == SpidrCmds.CMD_RESTART_TIMERS:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_RESET_TIMER:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_TIMER:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_TIMER:
                    print('NEEDS IMPLEMENTATION')

                ####################
                # Trigger (continued)
                elif self.cmd == SpidrCmds.CMD_GET_SHUTTERSTART:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_SHUTTEREND:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_EXTSHUTTERCNTR:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_SHUTTERCNTR:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_RESET_COUNTERS:
                    print('NEEDS IMPLEMENTATION')

                ####################
                # Configuration: devices (continued)
                elif self.cmd == SpidrCmds.CMD_GET_PWRPULSECONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_PWRPULSECONFIG:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_PWRPULSE_ENA:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_TPX_POWER_ENA:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_BIAS_SUPPLY_ENA:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 50]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_BIAS_ADJUST:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_DECODERS_ENA:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_OUTPUTMASK:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_READOUTSPEED:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 5]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_READOUTSPEED:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                ####################
                # Configuration: timer (continued)
                elif self.cmd == SpidrCmds.CMD_T0_SYNC:
                    print('NEEDS IMPLEMENTATION')

                ####################
                # Monitoring (continued)
                elif self.cmd == SpidrCmds.CMD_GET_FPGATEMP:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, np.random.randint(1000, 5000)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_FANSPEED:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, np.random.randint(1000, 5000)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_FANSPEED:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_SELECT_CHIPBOARD:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_VDD:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_VDD_NOW:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 111]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_HUMIDITY:
                    print('NEEDS IMPLEMENTATION')

                elif self.cmd == SpidrCmds.CMD_GET_PRESSURE:
                    print('NEEDS IMPLEMENTATION')

                ####################
                # Configuration: non-volatile onboard storage

                ####################
                # Other

                elif self.cmd == SpidrCmds.CMD_GET_SPIDRREG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    count = self.data[4]
                    status = 0xFF0000
                    data = [reply, 0, 0, 0, count, status]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_SPIDRREG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))






                else:
                    print(f"{self.requestIndex}\t {hex(self.cmd)} UNKNOWN", flush=True)
                self.requestIndex += 1


if __name__ == "__main__":
    HOST, PORT = "192.168.1.10", 50000

    with socketserver.TCPServer((HOST, PORT), TPX3Handler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
