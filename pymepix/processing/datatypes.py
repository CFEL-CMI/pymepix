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

"""Defines data that is passed between processing objects"""
from enum import IntEnum


class MessageType(IntEnum):
    """Defines the type of message that is being passed into a multiprocessing queue"""
    RawData = 0
    """Raw UDP packets"""
    PixelData = 1
    """Decoded Pixel/Trigger Data"""
    TriggerData = 8
    """Decoded Triggers"""
    EventData = 2
    """Event Data"""
    CentroidData = 3
    """Centroided Data"""
    OpenFileCommand = 4
    """Open File message"""
    CloseFileCommand = 5
    """Close File Message"""
