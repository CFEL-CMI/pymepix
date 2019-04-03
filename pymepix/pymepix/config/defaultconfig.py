from .timepixconfig import TimepixConfig

class DefaultConfig(TimepixConfig):

    def __init__(self):
        pass
    

    def dacCodes(self):
        codes = [(1,       128)     # TPX3_IBIAS_PREAMP_ON  [0-255]
                ,(2,         8)    # TPX3_IBIAS_PREAMP_OFF [0-15]
                ,(3,       128)     # TPX3_VPREAMP_NCAS     [0-255]
                ,(4,         5)     # TPX3_IBIAS_IKRUM      [0-255]
                ,(5,       128)     # TPX3_VFBK             [0-255]
                ,(6,       420)     # TPX3_VTHRESH_FINE     [0-512]
                ,(7,         6)     # TPX3_VTHRESH_COARSE   [0-15]
                ,(8,        84)     # TPX3_IBIAS_DISCS1_ON  [0-255]
                ,(9,         8)     # TPX3_IBIAS_DISCS1_OFF [0- 15]
                ,(10,      128)      # TPX3_IBIAS_DISCS2_ON  [0-255]
                ,(11,        8)      # TPX3_IBIAS_DISCS2_OFF [0-15]
                ,(12,      192)# TPX3_IBIAS_PIXELDAC   [0-255]
                ,(13 ,     128) # TPX3_IBIAS_TPBUFIN    [0-255]
                ,(14  ,    128)  # TPX3_IBIAS_TPBUFOUT   [0-255]
                ,(15   ,   128)   # TPX3_VTP_COARSE       [0-255]
                ,(16    ,  256)    # TPX3_VTP_FINE         [0-512]
                ,(17     , 128)     # TPX3_IBIAS_CP_PLL     [0-255]
                ,(18      ,128)]
        return codes
