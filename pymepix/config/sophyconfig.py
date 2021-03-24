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

import xml.etree.ElementTree as et
import zipfile

import numpy as np

from .timepixconfig import TimepixConfig


class SophyConfig(TimepixConfig):
    """This class provides functionality for interpreting a .spx config file from SoPhy."""

    def __init__(self, filename):
        self._dac_codes = {
            "Ibias_Preamp_ON": 1,
            "Ibias_Preamp_OFF": 2,
            "VPreamp_NCAS": 3,
            "Ibias_Ikrum": 4,
            "Vfbk": 5,
            "Vthreshold_fine": 6,
            "Vthreshold_coarse": 7,
            "Ibias_DiscS1_ON": 8,
            "Ibias_DiscS1_OFF": 9,
            "Ibias_DiscS2_ON": 10,
            "Ibias_DiscS2_OFF": 11,
            "Ibias_PixelDAC": 12,
            "Ibias_TPbufferIn": 13,
            "Ibias_TPbufferOut": 14,
            "VTP_coarse": 15,
            "VTP_fine": 16,
            "Ibias_CP_PLL": 17,
            "PLL_Vcntrl": 18,
        }

        self._dac_values = {
            "Ibias_Preamp_ON": 128,
            "Ibias_Preamp_OFF": 8,
            "VPreamp_NCAS": 128,
            "Ibias_Ikrum": 10,
            "Vfbk": 128,
            "Vthreshold_fine": 150,
            "Vthreshold_coarse": 6,
            "Ibias_DiscS1_ON": 128,
            "Ibias_DiscS1_OFF": 8,
            "Ibias_DiscS2_ON": 128,
            "Ibias_DiscS2_OFF": 8,
            "Ibias_PixelDAC": 150,
            "Ibias_TPbufferIn": 128,
            "Ibias_TPbufferOut": 128,
            "VTP_coarse": 128,
            "VTP_fine": 256,
            "Ibias_CP_PLL": 128,
            "PLL_Vcntrl": 128,
        }
        self.loadFile(filename)

    def loadFile(self, filename):
        spx = zipfile.ZipFile(filename)
        names = spx.namelist()
        xml_string = spx.read(names[0])

        self.parseDAC(xml_string)

        self.parsePixelConfig(spx, names[-3:])

    def parseDAC(self, xmlstring):
        """Reads and formats DAC parameters"""
        root = et.fromstring(xmlstring)
        dac_setting = root.findall(".//entry[@class='sophy.medipix.SPMPXDACCollection']")
        dac_setting = dac_setting[0][0]

        for element in dac_setting.findall(".//element[@class='java.util.Map.Entry']"):
            key = element.find("key")

            entry = element.find("entry")
            data = entry.find("data")
            dac_key = key.items()[-1][-1]
            dac_value = int(data.items()[-1][-1])

            self._dac_values[dac_key] = dac_value
        print(f"DAC Codes: {type(self.dacCodes())} \n{self.dacCodes()}")

    def dacCodes(self):
        """Accessor for the dac parameters

        Returns
        ----------
        :obj:`list` of :obj:`tuples` (<dac code>, <value>)
            The value for every DAC parameter"""
        dac_codes = []
        for key, value in self._dac_values.items():
            code = self._dac_codes[key]
            dac_codes.append((code, value))
        return dac_codes

    def biasVoltage(self):
        pass

    def _reverseBits(self, num):
        bitsize = 4
        binary = bin(num)
        reverse = binary[-1:1:-1]
        reverse = reverse + (bitsize - len(reverse)) * "0"
        return int(reverse, 2)

    def parsePixelConfig(self, zip_file, file_names):
        """Reads and formats the pixel data from config file.

        Notes
        ----------
        The spx config file saves the pixel information row by row while
        the timepix camera expects the information column wise."""
        buffer = zip_file.read(file_names[0])
        self._mask = np.fliplr(
            np.frombuffer(buffer[27:], dtype=np.int16).reshape(256, 256).transpose()
        ).copy()
        buffer = zip_file.read(file_names[1])
        self._test = np.fliplr(
            np.frombuffer(buffer[27:], dtype=np.int16).reshape(256, 256).transpose()
        ).copy()
        buffer = zip_file.read(file_names[2])
        self._thresh = np.frombuffer(buffer[27:], dtype=np.int16).copy() >> 8
        self._thresh = np.fliplr(
            np.array([self._reverseBits(x) for x in self._thresh]).reshape(256, 256).transpose()
        )

    def maskPixels(self):
        """Accessor for the mask pixels [0, 1]

        Returns
        ----------
        :obj:`numpy.ndarray` (256, 256)
            The information which pixels are to be masked"""
        return 1 - (self._mask // 256)

    def testPixels(self):
        """Accessor for the test pixels

        Returns
        ----------
        :obj:`numpy.ndarray` (256, 256)"""
        return self._test

    def thresholdPixels(self):
        """Accessor for the pixel thresholds [0, 15]

        Returns
        ----------
        :obj:`numpy.ndarray` (256, 256)
            The threshold information for each pixel"""
        return self._thresh


def main():
    import matplotlib.pyplot as plt

    spx = SophyConfig("E:/W0028_H06/settings/W0028_H06_50V.spx")
    print(spx.dacCodes())
    # plt.matshow(spx.maskPixels()[::-1,:])
    # plt.show()
    # plt.matshow(spx.thresholdPixels()[::-1,:])
    # plt.show()
    print(spx.maskPixels().max())
    thresh = spx.thresholdPixels()
    print("MAX", np.max(thresh))
    print("MEAN", np.mean(thresh))
    print("STDDEV", np.std(thresh))
    plt.imshow(spx.maskPixels())
    plt.show()

    # plt.hist(thresh.flatten(),bins=16,range=[0,15])
    # plt.show()


if __name__ == "__main__":
    main()
# dac_setting = e.findall(".//entry[@class='sophy.medipix.SPMPXDACCollection']")
# dac_setting = dac_setting[0]
# dac_setting = dac_setting[0]
# In [68]: for element in dac_setting.findall(".//element[@class='java.util.Map.Entry']"):
#     ...:     key=element.find('key')
#     ...:
#     ...:     entry=element.find('entry')
#     ...:     data = entry.find('data')
#     ...:     print(key.items()[-1][-1],data.items()[-1][-1])
