import socket
import socketserver
import threading
import numpy as np
from pymepix import Pymepix
from pymepix.config.sophyconfig import SophyConfig
from pymepix.util.spidrDummyTCP import TPX3Handler


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
            pass  # TODO: @firode waiting for answer with information about PLL_VCNTRL


def test_pixelmask():
    """Check whether the pixelmask is in an appropriate format"""
    spx = SophyConfig(CONFIG_PATH)
    mask = spx.maskPixels()
    test = spx.testPixels()
    thresh = spx.thresholdPixels()

    # check for correct range of values
    assert mask.min() >= 0 and mask.max() <= 1
    assert test.min() >= 0 and test.max() <= 256
    assert thresh.min() >= 0 and thresh.max() <= 15
    assert np.count_nonzero(mask == 0) > np.count_nonzero(mask == 1)
    print(np.count_nonzero(mask == 1))


class TPX3PacketCapture(TPX3Handler):
    """The part to capture and evaluate the config packets from pymepix"""

    def handle(self):
        self.requestIndex = 0
        # while self.requestIndex<1000:
        while 1:
            self._gather_packet()
            self._process_data()

                # nocheinmal Sophy Pakete abfangen, als Referenz ansehen!
                # Cmd Code an richtiger Stelle?
                # Conf Wert an richtiger Stelle, sinniger Wertebereich?
                # > hier nicht wieder jeden Wertebereich einzeln checken, bereits im Test zuvor geschehen..


def test_send_config():
    """Pretend to be a TPX3 and capture config packets.
    Check for the right format.
    """
    print("Starting server...")  # hier stimmt noch etwas nicht
    server = socketserver.TCPServer(ADDRESS, TPX3PacketCapture)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()

    print("Initializing Pymepix...")
    tpx = Pymepix(ADDRESS)
    tpx[0].loadConfig(CONFIG_PATH)

    print("Starting Pymepix...")
    tpx.start()
    tpx.stop()

    print("Shutting down server")
    server.server_close()


if __name__ == "__main__":
    test_send_config()
