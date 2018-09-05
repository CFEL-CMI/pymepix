
class SPIDRErrorDefs:
    ERR_NONE            = 0x00000000
    ERR_UNKNOWN_CMD     = 0x00000001
    ERR_MSG_LENGTH      = 0x00000002
    ERR_SEQUENCE        = 0x00000003
    ERR_ILLEGAL_PAR     = 0x00000004
    ERR_NOT_IMPLEMENTED = 0x00000005
    ERR_TPX3_HARDW      = 0x00000006
    ERR_ADC_HARDW       = 0x00000007
    ERR_DAC_HARDW       = 0x00000008
    ERR_MON_HARDW       = 0x00000009
    ERR_FLASH_STORAGE   = 0x0000000A
    ERR_MONITOR         = 0x0000000B






class PymePixException(Exception):
    
    ERR_STR=   [
            "no error",
            "ERR_UNKNOWN_CMD",
            "ERR_MSG_LENGTH",
            "ERR_SEQUENCE",
            "ERR_ILLEGAL_PAR",
            "ERR_NOT_IMPLEMENTED",
            "ERR_TPX3_HARDW",
            "ERR_ADC_HARDW",
            "ERR_DAC_HARDW",
            "ERR_MON_HARDW",
            "ERR_FLASH_STORAGE"
        ]
    def __init__(self,error_code): 

        self.message = self.errorMessage(error_code)

        Exception.__init__(self,self.message)

    def errorMessage(self,code):
        
        err_id = code &0xFF

        if err_id >= len(self.ERR_STR) or err_id < 0:
            return 'Unknown error code {}'.format(err_id)

        return "Recieved error code {}: {}".format(err_id,self.ERR_STR[err_id])
        