from enum import Enum

class ChannelDataType(Enum):
    COMMAND = 'comm'
    PIXEL = 'pixel'
    TOF = 'tof'
    CENTROID = 'centroid'


class Commands(Enum):
    START = 'start'
    STOP = 'stop'