import threading
import zmq
import queue

#Use:

#host = "127.0.0.1"
#port = "5556"
#client = Client("tcp://{}:{}".format(host, port))

#data_queue = client.get_queue()
#while True:
#    data = data_queue.get()
#    .....
# one can also suppy the callback function


import threading
import zmq
import numpy as np

import queue

from enum import Enum


# class syntax
class ChannelDataType(Enum):
    COMMAND = 1
    PIXEL = 2
    TOF = 3
    CENTROID = 4


class Client(threading.Thread):

    def __init__(self, channel_address, callback=None, queue_maxsize=32):
        threading.Thread.__init__(self)
        self.daemon = True
        self._socket = None
        self._address = channel_address
        self._callback = callback
        self.q = queue.Queue(queue_maxsize)
        self.register(channel_address)
        self.running = True
        self.start()

    def stop(self):
        self.running = False

    def get_queue(self):
        return self.q

    def public_address(self):
        return f"tcp://{self.socket.gethostname()}:{self.port}"

    def register(self, channel_address):
        self.address = channel_address
        host, s_port = channel_address.split("//")[-1].split(":")
        self.port = int(s_port)
        context = zmq.Context()
        self._socket = context.socket(zmq.SUB)

        print('connecting to address: ', "tcp://{}:{}".format(host, port))
        # Connects to a bound socket
        self._socket.connect("tcp://{}:{}".format(host, port))
        self._socket.subscribe("")

    def run(self):
        print('start receiving data')
        while self.running:
            obj = self._socket.recv_pyobj()
            if not self.q.full():
                self.q.put_nowait(obj)
            if self._callback != None:
                self._callback(obj)