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
module to test udpsampler functionality
run: pytest test_udpsampler_pytest.py
"""
import os
import pathlib
import socket
import time
from multiprocessing import Queue

import numpy as np

import pymepix.config.load_config as cfg
from pymepix.processing.acquisition import AcquisitionPipeline
from pymepix.processing.udpsampler import UdpSampler

# address at with the UDP sampler listens
address = ("127.0.0.1", 50000)
folder_path = pathlib.Path(__file__).parent / "files"


def send_data(packets, chunk_size, start=0, sleep=0.0001):
    ############
    # send data
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_data = np.arange(
        start, start + packets * chunk_size, dtype=np.uint64
    )  # chunk size 135 -> max number=1_012_500
    test_data_view = memoryview(test_data)
    time.sleep(1)  # seems to be necessary if this function get called as a Process
    # first packet 0...134, second packet 135...269 and so on
    start = time.time()
    for i in range(0, len(test_data_view), chunk_size):
        sock.sendto(test_data_view[i : i + chunk_size], address)
        time.sleep(sleep)  # if there's no sleep, packets get lost
    stop = time.time()
    dt = stop - start
    print(
        f"packets sent: {packets}, "
        f"bytes: {len(test_data_view.tobytes())}, "
        f"MBytes: {len(test_data_view.tobytes()) * 1e-6:.1f}, "
        f"{len(test_data_view.tobytes()) * 1e-6 / dt:.2f} MByte/s"
    )
    return test_data


def send_data_fast(packets, chunk_size):
    ############
    # send data
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_data = np.arange(0, packets * chunk_size, dtype=np.uint64)
    test_data_view = memoryview(test_data)
    time.sleep(1)  # seems to be necessary if this function get called as a Process
    # first packet 0...134, second packet 135...269 and so on
    start = time.time()
    for _ in range(0, len(test_data_view), chunk_size):
        sock.sendto(test_data_view[:chunk_size], address)
    stop = time.time()
    dt = stop - start
    print(
        f"packets sent: {packets}, "
        f"bytes: {len(test_data_view.tobytes())}, "
        f"MBytes: {len(test_data_view.tobytes()) * 1e-6:.1f}, "
        f"{len(test_data_view.tobytes()) * 1e-6 / dt:.2f} MByte/s"
    )


def test_zmq_multifile():
    """
    test functionality of 1st acquisition pipeline step with data been put into Queue for pixelprocesor
    and thread to Raw2Disk
    """

    # Create the logger
    import logging
    import time
    from multiprocessing.sharedctypes import Value

    import zmq

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    end_queue = Queue()

    acqpipline = AcquisitionPipeline("Test", end_queue)

    longtime = Value("L", 0)
    acqpipline.addStage(0, UdpSampler, address, longtime)

    ###############
    # take data form Queue where PacketProcessor would be sitting
    # create connection to packetprocessor
    ctx = zmq.Context.instance()
    packet_sock = ctx.socket(zmq.PULL)
    packet_sock.connect(f"ipc:///tmp/packetProcessor{cfg.default_cfg['zmq_port']}")

    ##############
    # get data from end_queue

    ##########
    # start acquisition pipeline
    acqpipline.start()

    ############
    # start 1st file
    print("######### 1st file ##############")
    # establish connection, seems to be necessary to first send something from binding code....

    fname = folder_path / f'testfile-{time.strftime("%Y%m%d-%H%M%S")}.raw'
    acqpipline._stages[0]._pipeline_objects[0].record = True
    acqpipline._stages[0].udp_sock.send_string(str(fname))
    res = acqpipline._stages[0].udp_sock.recv_string()

    if res == "OPENED":
        rec_fname = acqpipline._stages[0].udp_sock.recv_string()
        print(f"file {rec_fname} opened")
    else:
        print(f"did not open {res}")

    test_data = send_data(packets=10, chunk_size=10, sleep=0.0001)

    ###
    # finish acquisition 1st file
    time.sleep(5)  # permit thread time to empty queue
    print('sent and waited....')
    acqpipline._stages[0]._pipeline_objects[0].record = False
    acqpipline._stages[0]._pipeline_objects[0].close_file = True
    res = acqpipline._stages[0].udp_sock.recv_string()

    if res == "CLOSED":
        print(f"Ok, file {fname} closed")
    else:
        print(f"Problem, file not closed, {res}")
    time.sleep(1)


    # check for data in file
    assert np.fromfile(fname, dtype=np.uint64)[1:].all() == test_data.all()
    assert np.fromfile(fname, dtype=np.uint64)[1:].sum() == test_data.sum()
    assert np.fromfile(fname, dtype=np.uint64)[1:].shape == test_data.shape

    os.remove(fname)

    ############
    # start 2nd file
    ############
    # start thread
    print("\n######### 2nd file ##############")


    fname = folder_path / f'testfile-{time.strftime("%Y%m%d-%H%M%S")}.raw'
    # acqpipline._stages[0]._pipeline_objects[0].outfile_name = fname
    acqpipline._stages[0]._pipeline_objects[0].record = True
    acqpipline._stages[0].udp_sock.send_string(str(fname))
    res = acqpipline._stages[0].udp_sock.recv_string()
    if res == "OPENED":
        rec_fname = acqpipline._stages[0].udp_sock.recv_string()
        print(f"file {rec_fname} opened")
    else:
        print(f"did not open {res}")

    test_data = send_data(packets=100, chunk_size=12, start=233, sleep=0.0001)

    # finish acquisition 2nd file
    time.sleep(5)  # permit thread time to empty queue
    acqpipline._stages[0]._pipeline_objects[0].record = False
    acqpipline._stages[0]._pipeline_objects[0].close_file = True
    res = acqpipline._stages[0].udp_sock.recv_string()

    if res == "CLOSED":
        print(f"file {fname} closed")
    else:
        print(f"problem, {res}")


    # check for data in file
    assert np.fromfile(fname, dtype=np.uint64)[1:].all() == test_data.all()
    assert np.fromfile(fname, dtype=np.uint64)[1:].sum() == test_data.sum()
    assert np.fromfile(fname, dtype=np.uint64)[1:].shape == test_data.shape

    os.remove(fname)

    ############
    # start 3rd file
    ############
    # start thread
    print("\n######### 3rd file ##############")

    fname = folder_path / f'test-{time.strftime("%Y%m%d-%H%M%S")}.raw'
    # acqpipline._stages[0]._pipeline_objects[0].outfile_name = fname
    acqpipline._stages[0]._pipeline_objects[0].record = 1
    acqpipline._stages[0].udp_sock.send_string(str(fname))
    res = acqpipline._stages[0].udp_sock.recv_string()
    if res == "OPENED":
        rec_fname = acqpipline._stages[0].udp_sock.recv_string()
        print(f"file {rec_fname} opened")
    else:
        print(f"did not open {res}")

    test_data = send_data(packets=300, chunk_size=135, start=4003, sleep=0.0001)

    # finish acquisition 3rd file
    time.sleep(5)  # permit thread time to empty queue
    acqpipline._stages[0]._pipeline_objects[0].record = False
    acqpipline._stages[0]._pipeline_objects[0].close_file = True
    res = acqpipline._stages[0].udp_sock.recv_string()
    if res == "CLOSED":
        print(f"file {fname} closed")
    else:
        print(f"problem, {res}")


    # check for data in file
    assert np.fromfile(fname, dtype=np.uint64)[1:].all() == test_data.all()
    assert np.fromfile(fname, dtype=np.uint64)[1:].sum() == test_data.sum()
    assert np.fromfile(fname, dtype=np.uint64)[1:].shape == test_data.shape

    os.remove(fname)

    ############
    # start 4th file
    ############
    # start thread
    print("\n######### 4th file ##############")

    fname = folder_path / f'test-{time.strftime("%Y%m%d-%H%M%S")}.raw'
    # acqpipline._stages[0]._pipeline_objects[0].outfile_name = fname
    acqpipline._stages[0]._pipeline_objects[0].record = True
    acqpipline._stages[0].udp_sock.send_string(str(fname))
    res = acqpipline._stages[0].udp_sock.recv_string()
    if res == "OPENED":
        rec_fname = acqpipline._stages[0].udp_sock.recv_string()
        print(f"file {rec_fname} opened")
    else:
        print(f"did not open {res}")

    #test_data = send_data(packets=100_000, chunk_size=139, start=15000, sleep=1e-6)
    test_data = send_data(packets=1_000, chunk_size=139, start=15000, sleep=1e-6)

    # finish acquisition 4th file
    time.sleep(5)  # permit thread time to empty queue
    acqpipline._stages[0]._pipeline_objects[0].record = False
    acqpipline._stages[0]._pipeline_objects[0].close_file = True
    res = acqpipline._stages[0].udp_sock.recv_string()
    if res == "CLOSED":
        print(f"file {fname} closed")
    else:
        print(f"problem, {res}")


    # check for data in file
    # print('data we got from file:')
    # print(np.fromfile(fname, dtype=np.uint64).shape, test_data.shape,
    #      np.fromfile(fname, dtype=np.uint64).shape[0] / test_data.shape[0])
    assert np.fromfile(fname, dtype=np.uint64)[1:].all() == test_data.all()
    assert np.fromfile(fname, dtype=np.uint64)[1:].sum() == test_data.sum()
    assert np.fromfile(fname, dtype=np.uint64)[1:].shape == test_data.shape

    os.remove(fname)

    ############
    # shut everything down
    res = acqpipline._stages[0].udp_sock.send_string("SHUTDOWN")
    acqpipline.stop()

    print("Done and done")


def test_speed():
    """
    receive data at maximum speed and see how many packets arrived
    """
    # Create the logger
    import logging
    import time
    from multiprocessing import Process
    from multiprocessing.sharedctypes import Value

    import zmq

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    end_queue = Queue()  # queue for PacketProcessor

    acqpipline = AcquisitionPipeline("Test", end_queue)

    test_value = Value("L", 0)

    acqpipline.addStage(0, UdpSampler, address, test_value)
    # acqpipline.addStage(2, PacketProcessor, num_processes=4)

    # create connection to packetprocessor
    ctx = zmq.Context.instance()
    packet_sock = ctx.socket(zmq.PULL)
    packet_sock.connect("ipc:///tmp/packetProcessor32160")

    ##########
    # start acquisition pipeline
    acqpipline.start()

    ############
    # send data as fast as possible
    ############
    # start thread
    print("\n######### speed test ##############")
    fname = folder_path / f'test-{time.strftime("%Y%m%d-%H%M%S")}.raw'
    # acqpipline._stages[0]._pipeline_objects[0].outfile_name = fname
    acqpipline._stages[0]._pipeline_objects[0].record = True
    acqpipline._stages[0].udp_sock.send_string(str(fname))
    res = acqpipline._stages[0].udp_sock.recv_string()
    if res == "OPENED":
        rec_fname = acqpipline._stages[0].udp_sock.recv_string()
        print(f"file {rec_fname} opened")
    else:
        print(f"did not open {res}")

    ############
    # send data
    packets = 50_000
    chunk_size = 139
    test_data = np.arange(0, packets * chunk_size, dtype=np.uint64)
    p = Process(target=send_data_fast, args=(packets, chunk_size))
    p.start()
    p.join()

    # finish acquisition speed test
    acqpipline._stages[0]._pipeline_objects[0].record = False
    acqpipline._stages[0]._pipeline_objects[0].close_file = True
    acqpipline._stages[0]._pipeline_objects[0].enable = False
    res = acqpipline._stages[0].udp_sock.recv_string()
    if res == "CLOSED":
        print(f"file {fname} closed")
    else:
        print(f"problem, {res}")

    # do testing
    # check for data in file
    print("data we got from raw2disk:")
    print(
        f"bytes in file {np.fromfile(fname, dtype=np.uint64).shape}",
        f"bytes sent {test_data.shape}",
        f"ratio {np.fromfile(fname, dtype=np.uint64).shape[0] / test_data.shape[0]}",
    )
    os.remove(fname)

    ############
    # shut everything down
    res = acqpipline._stages[0].udp_sock.send_string("SHUTDOWN")
    acqpipline.stop()

    print("Done and done")



if __name__ == "__main__":
    test_zmq_multifile()
    test_speed()