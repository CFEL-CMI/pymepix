##############################################################################
##
# This file is part of Pymepix
#
# https://arxiv.org/abs/1905.07999
#
#
# Pymepix is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pymepix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pymepix.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


class TimepixConfig(object):

    def __init__(self):
        pass

    def biasVoltage(self):
        """Returns bias Voltage"""
        pass

    def dacCodes(self):
        """ Returns an iterator with format daccode,value"""
        pass

    def maskPixels(self):
        """Returns mask pixels"""
        pass

    def testPixels(self):
        """Returns test pixels"""
        pass

    def thresholdPixels(self):
        """Returns threshold pixels"""
        pass
