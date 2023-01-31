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


class Client(threading.Thread):

    def __init__(self, channel_address):
        threading.Thread.__init__(self)
        self.daemon = True
        self.socket = None
        self.address = None
        self.q = queue.Queue(maxsize=16)
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
        self.socket = context.socket(zmq.SUB)

        # Connects to a bound socket
        self.socket.connect("tcp://{}:{}".format(host, port))
        self.socket.subscribe("")

    def run(self):
        while self.running:
            obj = self.socket.recv_pyobj()
            if not self.q.full():
                self.q.put_nowait(obj)