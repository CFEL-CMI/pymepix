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

import argparse
import socket
import struct
import time

import numpy as np


def main():

    parser = argparse.ArgumentParser(description="Dummy UDP sender")

    parser.add_argument(
        "--ip",
        dest="ip",
        type=str,
        default='127.0.0.1',
        help="IP address of Timepix",
    )
    
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=50000,
        help="Port address of Timepix",
    )
    
    parser.add_argument(
        "--filename",
        dest="filename",
        type=str,
        default='',
        help="filename of source data",
    )

    parser.add_argument(
        "--repeats",
        dest="repeats",
        type=int,
        default=1,
        help="number of cycles to send the data",
    )

    parser.add_argument(
        "--chunk_size",
        dest="chunk_size",
        type=int,
        default=1,
        help="size of chunk to be sent at once",
    )

    parser.add_argument(
        "--wait_time",
        dest="wait_time",
        type=float,
        default=0.0,
        help="wait_time between the packet sending",
    )

    args = parser.parse_args()


    HOST, PORT = args.ip, args.port
    # data = " ".join(sys.argv[1:])

    # SOCK_DGRAM is the socket type to use for UDP sockets
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    fName = args.filename

    repeats = args.repeats

    chunk_size = args.chunk_size

    wait_time = args.wait_time

    data = np.fromfile(fName, dtype=np.uint64)

    total = len(data)*repeats
    last_progress = 0
    startTime = time.time()
    for rep in range(repeats):
        for i, packet in enumerate(data.reshape((len(data)//chunk_size,chunk_size))[:]):
            #sock.sendto(struct.pack("Q", packet), (HOST, PORT))
            sock.sendto(packet.tobytes(), (HOST, PORT))
            time.sleep(wait_time)
            progress = int((i*chunk_size+rep*len(data)) / total * 100)
            if progress != 0 and progress % 5 == 0 and progress != last_progress:
                print(f"Progress {progress :.1f}%")
                last_progress = progress
            # received = str(sock.recv(1024), "utf-8")
    stopTime = time.time()
    timeDiff = stopTime - startTime
    num_packets = rep * len(data)
    print(
        f"sent {num_packets} packets; {64*i*1e-6:.2f}MBits {(64*num_packets*1e-6)/timeDiff:.2f}MBits/sec; {(64*num_packets*1e-6/8)/timeDiff:.2f}MByte/sec"
    )

if __name__ == "__main__":
    main()
