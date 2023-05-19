import threading
import zmq

import queue


class Client(threading.Thread):

    def __init__(self, channel_address, callback=None, queue_maxsize=4):
        threading.Thread.__init__(self)
        self.daemon = True
        self._socket = None
        self._address = "tcp://{}:{}".format(*channel_address)
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
        return f"tcp://{self.address[0]}:{self.address[0]}"

    def register(self, channel_address):
        self.address = channel_address
        context = zmq.Context()
        self._socket = context.socket(zmq.SUB)

        print('connecting to address: ', "tcp://{}:{}".format(*channel_address))
        # Connects to a bound socket
        self._socket.connect("tcp://{}:{}".format(*channel_address))
        self._socket.subscribe("")

    def run(self):
        print('start receiving data')
        while self.running:
            obj = self._socket.recv_pyobj()
            if not self.q.full():
                self.q.put_nowait(obj)
            if self._callback != None:
                self._callback(obj)
