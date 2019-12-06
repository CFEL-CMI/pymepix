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

import sys
import socket
import selectors
import types
import logging

sel = selectors.DefaultSelector()
#messages = [b"run_0000_20191208-2213.raw"]

def start_connections(host, port, filenames):
    server_addr = (host, port)

    connid = 1
    logging.debug("starting connection", connid, "to", server_addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(server_addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        connid=connid,
        msg_total=sum(len(m) for m in filenames),
        recv_total=0,
        messages=list(filenames),
        outb=b"",
    )
    sel.register(sock, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            logging.debug("received", repr(recv_data), "from connection", data.connid)
            data.recv_total += len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            logging.debug("closing connection", data.connid)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            logging.debug("sending", repr(data.outb), "to connection", data.connid)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]

def main():
    '''
    sys.argv.append('131.169.33.169')
    sys.argv.append(50223)
    sys.argv.append(1)
    if len(sys.argv) != 4:
        print("usage:", sys.argv[0], "<host> <port> <num_connections>")
        sys.exit(1)

    host, port, num_conns = sys.argv[1:4]
    '''
    if len(sys.argv) != 2:
        logging.error("usage:", sys.argv[0], "<filename>")
        sys.exit(1)
    host = '131.169.33.169'
    port = 50223
    filename = [bytes(sys.argv[1].encode('utf-8'))]
    start_connections(host, int(port), filename)

    try:
        while True:
            events = sel.select(timeout=1)
            if events:
                for key, mask in events:
                    service_connection(key, mask)
            # Check for a socket being monitored to continue.
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        logging.debug("caught keyboard interrupt, exiting")
    finally:
        sel.close()

if __name__ == '__main__':
    main()