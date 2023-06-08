from enum import Enum


class ApiDataType(Enum):
    COMMAND = 'comm'
    PIXEL = 'pixel'
    TOF = 'tof'
    CENTROID = 'centroid'


class Commands(Enum):
    START_RECORD = 'start_record'
    STOP_RECORD = 'stop_record'
