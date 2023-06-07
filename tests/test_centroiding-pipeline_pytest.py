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

"""
module to test packetprocessor functionality
run: pytest test_packetprocessor_pytest.py
to be able to use this test comment 'elif self._buffer_list_idx == 4:' in udpsampler to send all data
"""

import pathlib
import socket

import numpy as np

address = ("127.0.0.1", 50000)

folder_path = pathlib.Path(__file__).parent / "files"
def send_data(packets=1_000, chunk_size=139, start=0, sleep=0.0001):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with open(folder_path / 'centroid_pipeline_test.raw', 'rb+') as data_file:
        raw_data = np.fromfile(data_file)
    sock.sendto(raw_data, address)


def test_packets_trigger():
    """
    test functionality of 1st acquisition pipeline step with data been put into Queue for pixelprocesor
    and thread to Raw2Disk
    """
    # Create the logger
    import logging
    import pickle
    import queue
    import threading
    import time
    from multiprocessing import Queue
    from multiprocessing.sharedctypes import Value

    import zmq

    from pymepix.processing.acquisition import CentroidPipeline
    from pymepix.processing.datatypes import MessageType

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    end_queue = Queue()  # queue for PacketProcessor
    longtime = Value("L", 2233861246990)  # longtime

    acqpipline = CentroidPipeline(end_queue, address, longtime)

    ###############
    # take data form Queue where PacketProcessor would be sitting
    ctx = zmq.Context.instance()

    def get_queue_thread(q):
        ctx = zmq.Context.instance()
        sock = ctx.socket(zmq.PAIR)
        sock.connect("inproc://queueThread")
        sock.recv_string()  # receive estabishing message

        received = []
        while True:
            try:
                value = q.get(block=False, timeout=0.5)
                if value is None:
                    break
                messType, data = value
                received.append(value)
            except queue.Empty:
                pass
            # print(value)
        sock.send_pyobj(received)
        time.sleep(5)  # give zmq thread time to send data

    ##########
    # start acquisition pipeline
    acqpipline.start()

    ############
    # start
    z_sock = ctx.socket(zmq.PAIR)
    z_sock.bind("inproc://queueThread")
    t = threading.Thread(target=get_queue_thread, args=(end_queue,))
    t.start()
    # establish connection, seems to be necessary to first send something from binding code....
    z_sock.send_string("hallo")

    # wait before sending data
    time.sleep(2)
    send_data()
    time.sleep(1)

    # stop things and test results
    end_queue.put(None)
    received = z_sock.recv_pyobj()
    for i in received:

        if i[0] == MessageType.PixelData:
            pixels = i[1]
        elif i[0] == MessageType.CentroidData:
            centroids = i[1]
        elif i[0] == MessageType.EventData:
            events = i[1]

    with open(folder_path / "raw_test_data_events.bin", "rb") as f:
        events_orig = pickle.load(f)
    assert events[0].all() == events_orig[0].all()  # event_nr
    assert events[1].all() == events_orig[1].all()  # x
    assert events[2].all() == events_orig[2].all()  # y
    assert events[3].all() == events_orig[3].all()  # tof
    assert events[4].all() == events_orig[4].all()  # tot

    with open(folder_path / "raw_test_data_pixels.bin", "rb") as f:
        pixels_orig = pickle.load(f)
    assert pixels[0].all() == pixels_orig[0].all()  # x
    assert pixels[1].all() == pixels_orig[1].all()  # y
    assert pixels[2].all() == pixels_orig[1].all()  # tof
    assert pixels[3].all() == pixels_orig[3].all()  # tot

    #with open("files/raw_test_data_centroids.bin", "rb") as f:
    #    centroids_orig = pickle.load(f)
    #assert centroids[0].all() == centroids_orig[0].all()
    #assert centroids[1].all() == centroids_orig[1].all()
    #assert centroids[2].all() == centroids_orig[2].all()
    #assert centroids[3].all() == centroids_orig[3].all()
    #assert centroids[4].all() == centroids_orig[4].all()
    print('centroids: ', centroids)


    print("waiting for queue thread")
    t.join()
    z_sock.close()

    ############
    # shut everything down
    _ = acqpipline._stages[0].udp_sock.send_string("SHUTDOWN")
    acqpipline.stop()

    print("Done and done")


if __name__ == "__main__":
    test_packets_trigger()
