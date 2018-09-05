from enum import Enum

class SPIDRReadoutSpeed(Enum):
    HighSpeed = 0x89ABCDEF #High speed magic number
    LowSpeed = 0x12345678 #Low speed magic number
    Default = 0 #Use default readout speed