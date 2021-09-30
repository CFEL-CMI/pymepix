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
from multiprocessing import Value

from pymepix.processing.logic.processing_parameter import ProcessingParameter

class UnknownParameterTypeException(Exception):
    pass

class SharedProcessingParameter(ProcessingParameter):

    def __init__(self, value) :
        if isinstance(value, int):
            super().__init__(Value('i', value, lock=False))
        elif isinstance(value, float):
            super().__init__(Value('d', value, lock=False))
        else:
            raise UnknownParameterTypeException()

    @property
    def value(self):
        return self._value.value

    @value.setter
    def value(self, value):
        self._value.value = value
