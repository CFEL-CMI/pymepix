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
module to test packetprocessor functionality
run: pytest test_packetprocessor_pytest.py
'''

import numpy as np
import socket
import time

address = ('127.0.0.1', 50000)

def send_data(packets, chunk_size, start=0, sleep=0.0001):
    ############
    # send data
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_data = np.arange(start, start + packets * chunk_size,
                          dtype=np.uint64)  # chunk size 135 -> max number=1_012_500
    test_data_view = memoryview(test_data)
    time.sleep(1)  # seems to be necessary if this function get called as a Process
    # first packet 0...134, second packet 135...269 and so on
    start = time.time()
    for i in range(0, len(test_data_view), chunk_size):
        sock.sendto(test_data_view[i:i + chunk_size], address)
        time.sleep(sleep)  # if there's no sleep, packets get lost
    stop = time.time()
    dt = stop - start
    print(f'packets sent: {packets}, '
          f'bytes: {len(test_data_view.tobytes())}, '
          f'MBytes: {len(test_data_view.tobytes()) * 1e-6:.1f}, '
          f'{len(test_data_view.tobytes()) * 1e-6 / dt:.2f} MByte/s')
    return test_data

def test_packets_trigger():
    '''
    test functionality of 1st acquisition pipeline step with data been put into Queue for pixelprocesor
    and thread to Raw2Disk
    '''
    from multiprocessing import Queue
    from multiprocessing.sharedctypes import Value
    import queue
    import time
    import threading
    import zmq

    from pymepix.processing.acquisition import AcquisitionPipeline
    from pymepix.processing.udpsampler import UdpSampler
    from pymepix.processing.packetprocessor import PacketProcessor

    # Create the logger
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    end_queue = Queue()  # queue for PacketProcessor

    acqpipline = AcquisitionPipeline('Test', end_queue)

    test_value = Value('I', 0)

    acqpipline.addStage(0, UdpSampler, address, test_value)
    acqpipline.addStage(2, PacketProcessor, num_processes=2)

    ###############
    # take data form Queue where PacketProcessor would be sitting
    ctx = zmq.Context.instance()

    def get_queue_thread(q):
        ctx = zmq.Context.instance()
        sock = ctx.socket(zmq.PAIR)
        sock.connect('inproc://queueThread')
        sock.recv_string()  # receive estabishing message

        received = []
        while True:
            try:
                value = q.get(block=False, timeout=0.5)  # value = (Message.Type, [array, longtime])
                if value is None:
                    break
                messType, data = value
                received.append(data[0])
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
    z_sock.bind('inproc://queueThread')
    t = threading.Thread(target=get_queue_thread, args=(end_queue,))
    t.start()
    # establish connection, seems to be necessary to first send something from binding code....
    z_sock.send_string('hallo')

    end_queue.put(None)
    received = z_sock.recv_pyobj()

    print('waiting for queue thread')
    t.join()
    z_sock.close()

    ############
    # shut everything down
    res = acqpipline._stages[0].udp_sock.send_string("SHUTDOWN")
    acqpipline.stop()

    print('Done and done')