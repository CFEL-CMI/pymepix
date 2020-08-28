import socket
import socketserver
import threading
import numpy as np
import time
from pymepix import Pymepix
from pymepix.config.sophyconfig import SophyConfig
from pymepix.SPIDR.spidrcmds import SpidrCmds
from pymepix.util.spidrDummyTCP import TPX3Handler
from pymepix.timepixdef import DacRegisterCodes


CONFIG_PATH = 'test_assets/test_config_W0028_H06_50V.spx'
ADDRESS = ("192.168.1.10", 50000)


def exact_parameter(code, value):
    """Test for precisely correct interpreted parameters of a known .spx file"""
    if code == DacRegisterCodes.Ibias_Preamp_ON:
        return value == 128
    elif code == DacRegisterCodes.Ibias_Preamp_OFF:
        return value == 8
    elif code == DacRegisterCodes.VPreamp_NCAS:
        return value == 128
    elif code == DacRegisterCodes.Ibias_Ikrum:
        return value == 20
    elif code == DacRegisterCodes.Vfbk:
        return value == 128
    elif code == DacRegisterCodes.Vthreshold_fine:
        return value == 150
    elif code == DacRegisterCodes.Vthreshold_coarse:
        return value == 6
    elif code == DacRegisterCodes.Ibias_DiscS1_ON:
        return value == 128
    elif code == DacRegisterCodes.Ibias_DiscS1_OFF:
        return value == 8
    elif code == DacRegisterCodes.Ibias_DiscS2_ON:
        return value == 128
    elif code == DacRegisterCodes.Ibias_DiscS2_OFF:
        return value == 8
    elif code == DacRegisterCodes.Ibias_PixelDAC:
        return value == 150
    elif code == DacRegisterCodes.Ibias_TPbufferIn:
        return value == 128
    elif code == DacRegisterCodes.Ibias_TPbufferOut:
        return value == 128
    elif code == DacRegisterCodes.VTP_coarse:
        return value == 128
    elif code == DacRegisterCodes.VTP_fine:
        return value == 256
    elif code == DacRegisterCodes.Ibias_CP_PLL:
        return value == 128
    elif code == DacRegisterCodes.PLL_Vcntrl:
        return value == 128


def test_parameters():
    """Test for DAC parameters being in their respective range of values"""
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
            assert True  # TODO: @firode waiting for answer with information about PLL_VCNTRL
        assert exact_parameter(code, value)


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

    # there should be more open pixels than masked ones
    assert np.count_nonzero(mask == 0) > np.count_nonzero(mask == 1)
    print("Successfully done test_pixelmas()")

# socketserver.ThreadingMixIn,
class TPX3PacketCapture(TPX3Handler):
    """The part to capture and evaluate the config packets from pymepix"""

    def handle(self):
        self.shutdown_evt = threading.Event()
        self.requestIndex = 0
        # while self.requestIndex<1000:
        while 1:
            self._gather_packet()

            if self.data == b'shutdown':
                self.shutdown_evt.set()
                break
            if self.shutdown_evt.wait(0.1):
                break

            self._process_data()
            if self.cmd == SpidrCmds.CMD_SET_PIXCONF:
                assert len(self.data) in [53, 149]
                # marks the next row
                assert 0 <= self.data[4] <= 255

            elif self.cmd == SpidrCmds.CMD_SET_DAC:
                assert len(self.data) == 5

                cmd_load = self.data[4]
                dac_cmd = cmd_load >> 16
                value = cmd_load & 0xFFFF
                assert exact_parameter(dac_cmd, value)


def test_send_config():
    """Pretend to be a TPX3 and capture config packets.
    Check for the right format.
    """
    server = socketserver.TCPServer(ADDRESS, TPX3PacketCapture)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()

    tpx = Pymepix(ADDRESS)
    tpx[0].loadConfig(CONFIG_PATH)

    tpx.start()
    tpx.stop()  # TODO: neither socketserver nor pymepix shutdown correctly
    print("Successfully done test_send_config()")
    server.shutdown_event.set()
    print(1.5)
    server.server_close()
    print(2)
    server.shutdown()


    print("server is gone")
    thread.join(1)


if __name__ == "__main__":
    test_parameters()
    test_pixelmask()
    test_send_config()
