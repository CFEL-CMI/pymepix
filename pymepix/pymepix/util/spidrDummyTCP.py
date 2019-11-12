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
import numpy as np


class MyTCPHandler(socketserver.BaseRequestHandler):

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

                if self.cmd == SpidrCmds.CMD_GET_DEVICECOUNT:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 1]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_DEVICEID:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_SPIDRREG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    count = self.data[4]
                    status = 0xFF0000
                    data = [reply, 0, 0, 0, count, status]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_IPADDR_DEST:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    ip = (127 << 24) | (0 << 16) | (0 << 8) | (1 << 0)
                    data = [reply, 0, 0, 0, ip]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_SERVERPORT:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 50000]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_RESET_DEVICE:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_REINIT_DEVICE:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_DAC:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_RESET_PIXELS:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

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

                elif self.cmd == SpidrCmds.CMD_GET_HEADERFILTER:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_HEADERFILTER:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_TIMER:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_DAC:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    dac_code = (self.data[4] << 16)
                    data = [reply, 0, 0, 0, dac_code]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_SPIDRREG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_DECODERS_ENA:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_DDRIVEN_READOUT:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_RESET_TIMER:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_RESTART_TIMERS:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

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

                elif self.cmd == SpidrCmds.CMD_BIAS_SUPPLY_ENA:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 50]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_SET_BIAS_ADJUST:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_PLLCONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_REMOTETEMP:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, np.random.randint(1000, 5000)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_LOCALTEMP:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, np.random.randint(1000, 5000)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_FPGATEMP:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, np.random.randint(1000, 5000)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_FANSPEED:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, np.random.randint(1000, 5000)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_TPPERIODPHASE:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 4]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_CTPR:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 1]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_DEVICEPORT:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 8192]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_IPADDR_SRC:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, (127 << 24) | (0 << 16) | (0 << 8) | (1 << 0)]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_OUTBLOCKCONFIG:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))

                elif self.cmd == SpidrCmds.CMD_GET_AVDD:
                    reply = self.cmd | SpidrCmds.CMD_REPLY
                    data = [reply, 0, 0, 0, 0]
                    self.request.sendall(struct.pack('%sI' % len(data), *[socket.htonl(i) for i in data]))


                else:
                    print(f"{self.requestIndex}\t {hex(self.cmd)} UNKNOWN", flush=True)
            self.requestIndex += 1


if __name__ == "__main__":
    HOST, PORT = "127.0.0.10", 50015

    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
