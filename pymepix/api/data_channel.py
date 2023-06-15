import threading
import zmq
import queue

from pymepix.api.data_types import ApiDataType
from pymepix.processing.datatypes import MessageType


class Data_Channel(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.q = queue.Queue()
        self.socket = None
        self.address = None
        self.bound = False
        self.lock = threading.Lock()

    def public_address(self):
        return f"tcp://{self.socket.gethostname()}:{self.port}"

    def register(self, api_address):
        with self.lock:
            if self.socket is None:
                self.address = api_address
                host, s_port = api_address.split("//")[-1].split(":")
                self.port = int(s_port)
                context = zmq.Context()
                self.socket = context.socket(zmq.PUB)
                self.socket.bind(f"tcp://{host}:{s_port}")

    def unregister(self):
        with self.lock:
            if self.socket is not None:
                self.socket.unbind(self.address)
                self.address = None
                self.socket = None

    def stop(self):
        self.q.put(None)

    def run(self):
        while True:
            new_data = self.q.get()
            if new_data is None:
                break

            with self.lock:
                if self.socket is not None:
                    self.socket.send_pyobj(new_data)

    def send(self, data_type, data):
        if data_type == ApiDataType.COMMAND:
            self.q.put_nowait({'type': data_type.value, 'data': data.value})
        else:
            self.q.put_nowait({'type': data_type.value, 'data': data})

    def send_data_by_message_type(self, message_type, data):
        if message_type == MessageType.PixelData:
            self.q.put_nowait({'type': ApiDataType.PIXEL.value, 'data': data})
        elif message_type == MessageType.EventData:
            self.q.put_nowait({'type': ApiDataType.TOF.value, 'data': data})
        elif message_type == MessageType.CentroidData:
            self.q.put_nowait({'type': ApiDataType.CENTROID.value, 'data': data})
