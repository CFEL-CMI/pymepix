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

'''
module to test udpsampler functionality
run: pytest test_udpsampler_pytest.py
'''
import socket
import ctypes
import time
import numpy as np
from multiprocessing.sharedctypes import Value
from multiprocessing import Queue
from pymepix.processing.udpsampler import UdpSampler
from pymepix.processing.acquisition import AcquisitionPipeline

address = ('127.0.0.1', 50000)


def test_receive():
    '''
    most basic test for receiving functionality done in UdpSampler.process
    '''
    longtime = Value(ctypes.c_int, 1)
    sampler = UdpSampler(address, longtime=longtime)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(8), address)
    # time.sleep(0.1)

    sampler.pre_run()
    time.sleep(0.4)  # sleep for (flush_time > self._flush_timeout) to become true
    data = sampler.process()
    assert sampler._packets_collected == 1
    assert data[0] == 0  # should return <MessageType.RawData: 0>
    assert data[1][1] == 1  # provided longtime gets returned
    assert len(data[1][0]) == 1
    assert data[1][0].sum() == 0

    # send some more data but due to too short time between last check (pre_run), data should not be flushed
    sampler.pre_run()
    sock.sendto(bytes(64), address)
    data = sampler.process()
    assert sampler._packets_collected == 2
    assert data[0] == None
    assert data[1] == None

    # No new packets sent, thus socket should time-out
    sampler.pre_run()
    time.sleep(0.4)
    data = sampler.process()
    assert sampler._packets_collected == 2
    assert data[0] == None
    assert data[1] == None

    # send some more data
    sampler.pre_run()
    time.sleep(0.4)
    sock.sendto(bytes(64), address)
    data = sampler.process()
    assert sampler._packets_collected == 3
    assert data[0] == 0  # should return <MessageType.RawData: 0>
    assert data[1][1] == 1  # provided longtime gets returned
    assert len(data[1][0]) == 16
    assert data[1][0].sum() == 0

    # send 10x 1
    sampler.pre_run()
    time.sleep(0.4)
    sock.sendto(np.array(10 * [1], dtype=np.uint64).tobytes(), address)
    data = sampler.process()
    assert sampler._packets_collected == 4
    assert data[0] == 0  # should return <MessageType.RawData: 0>
    assert data[1][1] == 1  # provided longtime gets returned
    assert len(data[1][0]) == 10
    assert data[1][0].sum() == 10

    # send 1000x 10
    sampler.pre_run()
    time.sleep(0.4)
    sock.sendto(np.array(1000 * [10], dtype=np.uint64).tobytes(), address)
    data = sampler.process()
    assert sampler._packets_collected == 5
    assert data[0] == 0  # should return <MessageType.RawData: 0>
    assert data[1][1] == 1  # provided longtime gets returned
    assert len(data[1][0]) == 1000
    assert data[1][0].sum() == 10000

    # set small chunk size to test receiving data before timer is out
    sampler._chunk_size = 1
    sampler.pre_run()
    sock.sendto(np.array(1000 * [10], dtype=np.uint64).tobytes(), address)
    data = sampler.process()
    assert sampler._packets_collected == 6
    assert data[0] == 0  # should return <MessageType.RawData: 0>
    assert data[1][1] == 1  # provided longtime gets returned
    assert len(data[1][0]) == 1000
    assert data[1][0].sum() == 10000


def test_queue():
    '''
    test functionality of 1st acquisition pipeline step with data been put into queue
    '''
    from pymepix.processing.packetprocessor import PacketProcessor
    from multiprocessing.sharedctypes import Value
    import threading
    # Create the logger
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    end_queue = Queue()

    acqpipline = AcquisitionPipeline('Test', end_queue)

    test_value = Value('I', 0)

    acqpipline.addStage(0, UdpSampler, address, test_value)
    # acqpipline.addStage(2, PacketProcessor, num_processes=4)

    def get_queue_thread(queue, packets, chunk_size):
        recieved = []
        while True:
            value = queue.get()  # value = (Message.Type, [array, longtime])
            # print(value)
            if value is None:
                break
            messType, data = value
            recieved.append(data[0])

        ######
        # do the testing
        if len(recieved) > 1:
            packets_recved = (f'{np.concatenate(recieved).shape} packets received')
        else:
            packets_recved = len(recieved[0])
        assert packets_recved == packets * chunk_size

    chunk_size = 135  # packet size: 135*uint64 = 8640 Byte
    packets = 7500
    t = threading.Thread(target=get_queue_thread, args=(end_queue, packets, chunk_size))
    t.daemon = True
    t.start()

    acqpipline.start()
    # send data
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_data = np.arange(0, packets * chunk_size, dtype=np.uint64)  # chunk size 135 -> max number=1_012_500
    test_data_view = memoryview(test_data)
    for i in range(0, len(test_data_view), chunk_size):
        sock.sendto(test_data_view[i:i + chunk_size], ('127.0.0.1', 50000))
        time.sleep(0.0000001)  # if there's no sleep, packets get lost
    print(f'packets sent: {i + chunk_size}')
    time.sleep(10)  # permit thread time to empty queue
    acqpipline.stop()
    end_queue.put(None)

    t.join()
    print('Done')


if __name__ == "__main__":
    test_queue()
