import socket
import socketserver
import numpy as np
from pymepix.config.sophyconfig import SophyConfig

CONFIG_PATH = '/Users/rodenbef/desy/ASI_TPX3CAM_H06/W0028_H06/settings/W0028_H06_50V.spx'
ADDRESS = ("192.168.1.10", 50000)


def test_parameters():
    spx = SophyConfig(CONFIG_PATH)
    conf_params = spx.dacCodes()
    for code, value in conf_params:
        if code in [1, 3, 4, 5, 8, 10, 12, 13, 14, 15, 17]:
            assert 0 <= value <= 255
        elif code in [2, 7, 9, 11]:
            assert 0 <= value <= 15
        elif code in [6, 16]:
            assert 0 <= value <= 511
        elif code == 18:
            pass  # TODO: @firode find out boundaries for PLL_VCNTRL (default is 128)


def test_pixelmask():
    """Check whether the pixelmask is in an appropriate format"""
    # korrekter Wertebereich?
    # ergibt Sinn > mehr unmaskierte als maskierte?
    pass


class TPX3PacketCapture(socketserver.BaseRequestHandler):
    """The part to capture and evaluate the config packets from pymepix"""

    def handle(self):
        while True:
            sock_recv = self.request.recv(1024)
            self.data = np.frombuffer(sock_recv, dtype=np.uint32)

            if len(self.data) > 0:
                cmd = socket.htonl(int(self.data[0]))

                # nocheinmal Sophy Pakete abfangen, als Referenz ansehen!
                # Cmd Code an richtiger Stelle?
                # Conf Wert an richtiger Stelle, sinniger Wertebereich?
                # > hier nicht wieder jeden Wertebereich einzeln checken, bereits im Test zuvor geschehen..


def test_send_config():
    """Pretend to be a TPX3 and capture config packets.
    Check for the right format.
    """
    # socket zum annehmen erstellen

    pass


if __name__ == "__main__":
    test_parameters()
