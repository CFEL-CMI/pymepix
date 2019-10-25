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


"""SPIDR related classes"""

import socket
import numpy as np
from .error import PymePixException
from .spidrcmds import SpidrCmds
from .spidrdevice import SpidrDevice
from .spidrdefs import SpidrRegs,SpidrShutterMode,SpidrReadoutSpeed
from pymepix.core.log import Logger
import threading
class SPIDRController(Logger):
    """Object that interfaces over ethernet with the SPIDR board

    This object interfaces with the spidr board through TCP and is used to send commands and receive data.
    It can be treated as a list of :class:`SpidrDevice` objects to talk to a specific device

    Parameters
    ----------
    dst_ip_port : :obj:`tuple` of :obj:`str` and :obj:`int`
        socket style tuple of SPIDR ip address and port
    src_ip_port : :obj:`tuple` of :obj:`str` and :obj:`int`, optional
        socket style tuple of the IP address and port of the interface that is connecting to SPIDR

    Examples
    --------

    The class can be used to talk to SPIDR

    >>> spidr = SPIDRController(('192.168.1.10',50000))
    >>> spidr.fpgaTemperature
    39.5

    Or access a specific :class:`SpidrDevice` (e.g. Timepix/Medipix)

    >>> spidr[0].deviceId
    7272
    >>> spidr[1].deviceId
    2147483648



    .. Warning::
        This object assumes SPIDR is working as intended however since this is still in development there are a few functions
        that do not behave as they should, this will be documented in their relevant areas.



    """
    def __init__(self,dst_ip_port,src_ip_port=('192.168.1.1',0)):
        Logger.__init__(self,SPIDRController.__name__)

        self.info('Connecting to {}:{}'.format(*dst_ip_port))

        self._sock = socket.create_connection(dst_ip_port,source_address=src_ip_port)
        self._request_lock = threading.Lock()
        self._req_buffer = np.ndarray(shape=(512,),dtype=np.uint32)
        self._reply_buffer = bytearray(4096)
        self._reply_view = memoryview(self._reply_buffer)

        self._vec_htonl = np.vectorize(self.convertHtonl)
        self._vec_ntohl = np.vectorize(self.convertNtohl)

        self._pixel_config = np.ndarray(shape=(256,256),dtype=np.uint8)
        #self.resetModule(SpidrReadoutSpeed.Default)
        self._devices = []
        self._initDevices()



    def __getitem__(self, key):
        return self._devices[key]

    def __len__(self):
        return len(self._devices)

    def _initDevices(self):

        count = self.deviceCount

        for x in range(count):
            self._devices.append(SpidrDevice(self,x))

    def resetModule(self,readout_speed):
        """Resets the SPIDR board and sets a new readout speed

        Parameters
        ----------
        readout_speed : :class:`SpidrReadoutSpeed`
            Read-out speed the device will operate at

        Notes
        ----------
        Its not clear if this does anything as its not usually used

        """
        self.requestGetInt(SpidrCmds.CMD_RESET_MODULE,0,readout_speed.value)

    #-----------------Registers-----------------------
    @property
    def CpuToTpx(self):
        """Cpu2Tpx register access

        Parameters
        ----------
        value : int
            Value to write to the register

        Returns
        ----------
        int
            Current value of the register

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        Notes
        ----------
        Register controls clock setup

        """
        return self.getSpidrReg(SpidrRegs.SPIDR_CPU2TPX_WR_I)

    @CpuToTpx.setter
    def CpuToTpx(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_CPU2TPX_WR_I,value)

        #---------Shutter registers---------
    @property
    def ShutterTriggerCtrl(self):
        """Shutter Trigger Control register access

        Parameters
        ----------
        value : int
            Value to write to the register

        Returns
        ----------
        int
            Current value of the register

        Raises
        ----------
        :class:`PymePixException`
            Communication error


        """

        return self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_CTRL_I)

    @ShutterTriggerCtrl.setter
    def ShutterTriggerCtrl(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_CTRL_I,value)

    @property
    def ShutterTriggerMode(self):
        """Controls how the shutter is triggered

        Parameters
        ----------
        value : :class:`SpidrShutterMode`
            Shutter trigger mode to set

        Returns
        ----------
        :class:`SpidrShutterMode`
            Current shutter operation mode read from SPIDR

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        Notes
        ----------
        AutoTrigger is the only functioning trigger mode that SPIDR can operate in


        """
        return SpidrShutterMode(self.ShutterTriggerCtrl &0x7)

    @ShutterTriggerMode.setter
    def ShutterTriggerMode(self,mode):
        reg = self.ShutterTriggerCtrl
        reg &= ~0x7
        reg |= mode.value
        self.ShutterTriggerCtrl = reg



    @property
    def ShutterTriggerCount(self):
        """Number of times the shutter is triggered in auto trigger mode

        Parameters
        ----------
        value : int
            Trigger count to set for auto trigger mode ( Set to 0 for infinite triggers)

        Returns
        ----------
        int:
            Current value of the trigger count read from SPIDR

        Raises
        ----------
        :class:`PymePixException`
            Communication error


        """
        return self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_CNT_I)

    @ShutterTriggerCount.setter
    def ShutterTriggerCount(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_CNT_I,value)

    @property
    def ShutterTriggerFreq(self):
        """Triggering frequency for the auto trigger

        Parameters
        ----------
        value : float
            Frequency in mHz

        Returns
        ----------
        float:
            Frequency value in mHz read from SPIDR

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        freq = self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_FREQ_I)

        mhz = 40000000000.0/freq

        return int(mhz)

    @ShutterTriggerFreq.setter
    def ShutterTriggerFreq(self,mhz):


        freq = 40000000000.0/mhz
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_FREQ_I,freq)

    @property
    def ShutterTriggerLength(self):
        """Length of time shutter remains open at each trigger

        Parameters
        ----------
        value : int
            Length in ns

        Returns
        ----------
        value: int
            Current length in ns read from SPIDR

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        return self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_LENGTH_I)*25

    @ShutterTriggerLength.setter
    def ShutterTriggerLength(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_LENGTH_I,(value+24)//25)

    @property
    def ShutterTriggerDelay(self):
        """Delay time before shutter can be triggered again in auto trigger mode

        Parameters
        ----------
        value : int
            Time in ns

        Returns
        ----------
        value: int
            Current time in ns read from SPIDR

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        return self.getSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_DELAY_I)*25

    @ShutterTriggerDelay.setter
    def ShutterTriggerDelay(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_SHUTTERTRIG_DELAY_I,value//25)

    @property
    def DeviceAndPorts(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_DEVICES_AND_PORTS_I)

    @property
    def TdcTriggerCounter(self):
        """Trigger packets sent by SPIDR since last counter reset"""
        return self.getSpidrReg(SpidrRegs.SPIDR_TDC_TRIGGERCOUNTER_I)

    @property
    def UdpPacketCounter(self):
        """UDP packets sent by SPIDR since last counter reset"""
        return self.getSpidrReg(SpidrRegs.SPIDR_UDP_PKTCOUNTER_I)

    @property
    def UdpMonPacketCounter(self):
        return self.getSpidrReg(SpidrRegs.SPIDR_UDPMON_PKTCOUNTER_I)

    @property
    def UdpPausePacketCounter(self):
        """UDP packets collected during readout pause since last counter reset"""
        return self.getSpidrReg(SpidrRegs.SPIDR_UDPPAUSE_PKTCOUNTER_I)

    @UdpPacketCounter.setter
    def UdpPacketCounter(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_UDP_PKTCOUNTER_I,0)

    @UdpMonPacketCounter.setter
    def UdpMonPacketCounter(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_UDPMON_PKTCOUNTER_I,0)

    @UdpPausePacketCounter.setter
    def UdpPausePacketCounter(self,value):
        return self.setSpidrReg(SpidrRegs.SPIDR_UDPPAUSE_PKTCOUNTER_I,0)

    #---------------------------------------------------

    @property
    def softwareVersion(self):
        """Software version

        Returns
        --------
        int:
            Version number of software in the SPIDR board


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """

        return self.requestGetInt(SpidrCmds.CMD_GET_SOFTWVERSION,0)

    @property
    def firmwareVersion(self):
        """Firmware version

        Returns
        --------
        int:
            Version number of firmware within the FPGA


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """


        return self.requestGetInt(SpidrCmds.CMD_GET_FIRMWVERSION,0)

    @property
    def localTemperature(self):
        """Local ????!?!? Temperature read from sensor

        Returns
        --------
        float:
            Temperature in Celsius


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        return self.requestGetInt(SpidrCmds.CMD_GET_LOCALTEMP,0)/1000

    @property
    def remoteTemperature(self):
        """Remote ????!?!? Temperature read from sensor

        Returns
        --------
        float:
            Temperature in Celsius


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        return self.requestGetInt(SpidrCmds.CMD_GET_REMOTETEMP,0)/1000

    @property
    def fpgaTemperature(self):
        """Temperature of FPGA board read from sensor

        Returns
        --------
        float:
            Temperature in Celsius


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        return self.requestGetInt(SpidrCmds.CMD_GET_FPGATEMP,0)/1000


    @property
    def humidity(self):
        """Humidity read from sensor

        Returns
        --------
        int:
            Humidity as percentage


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        return self.requestGetInt(SpidrCmds.CMD_GET_HUMIDITY,0)

    @property
    def pressure(self):
        """Pressure read from sensor

        Returns
        --------
        int:
            Pressure in bar


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        return self.requestGetInt(SpidrCmds.CMD_GET_PRESSURE,0)

    @property
    def chipboardFanSpeed(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_FANSPEED,0,0)

    @property
    def spidrFanSpeed(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_FANSPEED,0,1)


    @property
    def avdd(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_AVDD,0,3)/1000)

    @property
    def vdd(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_VDD,0,3)/1000)

    @property
    def dvdd(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_DVDD,0,3)/1000)


    @property
    def avddNow(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_AVDD_NOW,0,3)/1000)

    @property
    def vddNow(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_VDD_NOW,0,3)/1000)

    @property
    def dvddNow(self):
        return tuple(self.requestGetInts(SpidrCmds.CMD_GET_DVDD_NOW,0,3)/1000)

    @property
    def deviceCount(self):
        """ Count of devices connected to SPIDR

        Returns
        ---------
        int:
            Number of devices connected to SPIDR

        Raises
        ----------
        :class:`PymePixException`
            Communication error



        .. Warning::
            SPIDR always returns 4 since it currently can't determine if the devices
            are actually valid or not

        """
        return self.requestGetInt(SpidrCmds.CMD_GET_DEVICECOUNT,0)

    @property
    def deviceIds(self):
        """ The ids of all devices connected to the SPIDR board

        Returns
        ---------
        :obj:`list` of :obj:`int`:
            A list all connected device ids


        Raises
        ----------
        :class:`PymePixException`
            Communication error


        Notes
        --------
        Index of devices are the same as the those in the SPIDRController list


        >>> spidr[1].deviceId == spidr.deviceIds[1]
        True

        """
        device_count = self.deviceCount
        return self.requestGetInts(SpidrCmds.CMD_GET_DEVICEIDS,0,device_count)


    @property
    def linkCounts(self):
        links = self.DeviceAndPorts

        return ((links &0xF00) >> 8) + 1






    @property
    def chipboardId(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_CHIPBOARDID,0)

    def setBusy(self):
        return self.requestSetInt(SpidrCmds.CMD_SET_BUSY,0,0)

    def clearBusy(self):
        return self.requestSetInt(SpidrCmds.CMD_CLEAR_BUSY,0,0)

    def resetDevices(self):
        """ Resets all devices"""
        self.requestSetInt(SpidrCmds.CMD_RESET_DEVICES,0,0)

    def reinitDevices(self):
        """ Resets and initializes all devices

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        self.requestSetInt(SpidrCmds.CMD_REINIT_DEVICES,0,0)


    def setPowerPulseEnable(self,enable):
        self.requestSetInt(SpidrCmds.CMD_PWRPULSE_ENA,0,int(enable))

    def setTpxPowerPulseEnable(self,enable):
        self.requestSetInt(SpidrCmds.CMD_TPX_POWER_ENA,0,int(enable))

    def setBiasSupplyEnable(self,enable):
        """ Enables/Disables bias supply voltage

        Parameters
        -----------
        enable : bool
            True - enables bias supply voltage
            False - disables bias supply voltage

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        self.requestSetInt(SpidrCmds.CMD_BIAS_SUPPLY_ENA,0,int(enable))



    @property
    def biasVoltage(self):
        """ Bias voltage

        Parameters
        -----------
        volts : int
            Bias voltage to supply in volts
            Minimum is 12V and Maximum is 104V

        Returns
        -----------
        int:
            Current bias supply in volts

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """

        adc_data = self.requestGetInt(SpidrCmds.CMD_GET_SPIDR_ADC,0,1)
        return (((adc_data & 0xFFF)*1500 + 4095) / 4096) / 10
    @biasVoltage.setter
    def biasVoltage(self,volts):
        if volts < 12: volts = 12
        if volts > 104: volts = 104

        dac_value = int(((volts-12)*4095)/(104-12))
        self.info('Setting bias Voltage to {} V (Dac value {})'.format(volts,dac_value))
        self.requestSetInt(SpidrCmds.CMD_SET_BIAS_ADJUST,0,dac_value)


    def enableDecoders(self,enable):
        """Determines whether the internal FPGA decodes ToA values

        Time of Arrival from UDP packets are gray encoded
        if this is enabled then SPIDR will decode them for you, otherwise
        you have to do this yourself after extracting them

        Parameters
        -----------
        enable: bool
            True - enable FPGA decoding
            False - disable FPGA decoding

        Raises
        ----------
        :class:`PymePixException`
            Communication error


        .. Tip::
            Enable this


        """
        self.requestSetInt(SpidrCmds.CMD_DECODERS_ENA,0,int(enable))

    def enablePeriphClk80Mhz(self):
        self.CpuToTpx |= ( 1<<24)

    def disablePeriphClk80Mhz(self):
        self.CpuToTpx &= ~(1<<24)

    def enableExternalRefClock(self):
        """SPIDR recieves its reference clock externally

        This is often used when combining multiple Timepixs together so they can synchronize their clocks.
        The SPIDR board essentially acts as a slave to other SPIDRs

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """

        self.CpuToTpx |= ( 1<<25)

    def disableExternalRefClock(self):
        """SPIDR recieves its reference clock internally

        This should be set in single SPIDR mode. When combining other SPIDR board, the master will set this
        to disabled

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        self.CpuToTpx &= ~(1<<25)


    def sequentialReadout(self,tokens,now ):

        if( now ): tokens |= 0x80000000
        self.requestSetInt( SpidrCmds.CMD_SEQ_READOUT, 0, tokens )




    def datadrivenReadout(self):
        """Set SPIDR into data driven readout mode

        Data driven mode refers to the pixels packets sent as they are hit rather
        than camera style frames

        Raises
        ----------
        :class:`PymePixException`
            Communication error


        .. Warning::
            This is the only tested mode for pymepix. It is recommended that this is enabled

        """
        self.requestSetInt( SpidrCmds.CMD_DDRIVEN_READOUT, 0, 0 )




    def pauseReadout(self):

        self.requestSetInt( SpidrCmds.CMD_PAUSE_READOUT, 0, 0 )



    def setShutterTriggerConfig(self,mode,length_us,freq_hz,count,delay_ns=0):
        """Set the shutter configuration in one go


        Parameters
        ----------
        mode: int
            Shutter trigger mode

        length_us: int
            Shutter open time in microseconds

        freq_hz: int
            Auto trigger frequency in Hertz

        count: int
            Number of triggers

        delay_ns: int, optional
            Delay between each trigger (Default: 0)

        Raises
        ----------
        :class:`PymePixException`
            Communication error


        """


        data =  [mode,length_us,freq_hz,count,delay_ns]

        if delay_ns == 0:
            data.pop()

        self.requestSetInts(SpidrCmds.CMD_SET_TRIGCONFIG,0,data)

    @property
    def shutterTriggerConfig(self):
        config = self.requestGetInts(SpidrCmds.CMD_GET_TRIGCONFIG,0,5)

        return tuple(config)

    def startAutoTrigger(self):
        """Starts the auto trigger

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        self.requestSetInt(SpidrCmds.CMD_AUTOTRIG_START,0,0)

    def stopAutoTrigger(self):
        """Stops the auto trigger

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """

        self.requestSetInt(SpidrCmds.CMD_AUTOTRIG_STOP,0,0)


    def openShutter(self):
        """Immediately opens the shutter indefinetly

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        Notes
        ---------
        This overwrites shutter configurations with one that forces
        an open shutter

        """
        self.setShutterTriggerConfig( SpidrShutterMode.Auto.value, 0, 10, 1,0)
        self.startAutoTrigger()

    def closeShutter(self):
        """Immediately closes the shutter

        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        self.stopAutoTrigger()

    @property
    def externalShutterCounter(self):
        return self.requestGetInt(SpidrCmds.CMD_GET_EXTSHUTTERCNTR,0)

    @property
    def shutterCounter(self):

        return self.requestGetInt(SpidrCmds.CMD_GET_SHUTTERCNTR,0)

    def restartTimers(self):
        """Restarts SPIDR and Device timers

        Synchronizes both the SPIDR clock and Timepix/Medipix clocks so both trigger
        and ToA timestamps match

        .. Important::
            This must be done if event selection is required (e.g. time of flight) otherwise
            the timestamps will be offset




        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        return self.requestSetInt( SpidrCmds.CMD_RESTART_TIMERS, 0, 0 )

    def resetCounters(self):
        self.requestSetInt(SpidrCmds.CMD_RESET_COUNTERS,0,0)

    def resetTimers(self):
        """Resets all timers to zero

        Sets the internal 48-bit timers for all Timepix/Medipix devices to zero


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        self.requestSetInt(SpidrCmds.CMD_RESET_TIMER,0,0)

    def getAdc(self,channel,nr_of_samples):
        args = (channel & 0xFFFF) | ((nr_of_samples & 0xFFFF) << 16)
        self.requestGetInt(SpidrCmds.CMD_GET_SPIDR_ADC,0,args)





    def resetPacketCounters(self):
        self.UdpPacketCounter = 0
        self.UdpMonPacketCounter = 0
        self.UdpPausePackerCounter = 0
        for idx,dev in enumerate(self):
            self.setSpidrReg(SpidrRegs.SPIDR_PIXEL_PKTCOUNTER_I,idx)



    def getSpidrReg(self,addr):

        res = self.requestGetInts(SpidrCmds.CMD_GET_SPIDRREG,0,2,addr)
        if res[0] != addr:
            raise Exception('Incorrect register address returned {} expected {}'.format(res[0],addr))

        return res[1]


    def setSpidrReg(self,addr,value):
        self.requestSetInts(SpidrCmds.CMD_SET_SPIDRREG,0,[addr,value])


    def request(self,cmd,dev_nr,message_length,expected_bytes=0):
        """Sends a command and (may) receive a reply

        Parameters
        -----------
        cmd: :class:`SpidrCmds`
            Command to send
        dev_nr: int
            Device to send the request to. 0 is SPIDR and device number n is n+1
        message_length: int
            Length of the message in bytes
        expected_bytes: int
            Length of expected reply from request (if any) (Default: 0)


        Returns
        -----------
        :obj:`numpy.array` of :obj:`int` or :obj:`None`:
            Returns a numpy array of ints if reply expected, otherwise None


        Raises
        ----------
        :class:`PymePixException`
            Communication error

        """
        with self._request_lock:
            self.debug('Command: {}, Device Id: {} Message Length: {} Expected Reply: {}'.format(SpidrCmds(cmd).name,dev_nr,message_length,expected_bytes))
            self._req_buffer[0] = socket.htonl(cmd)
            self._req_buffer[1] = socket.htonl(message_length)
            self._req_buffer[2] = 0
            self._req_buffer[3] = socket.htonl(dev_nr)
            self.debug('Request Buffer: {}'.format(self._req_buffer[0:message_length]))
            self._sock.send(self._req_buffer.tobytes()[0:message_length])

            if cmd & SpidrCmds.CMD_NOREPLY: return

            bytes_returned = self._sock.recv_into(self._reply_view,4096)

            if bytes_returned < 0:
                raise Exception('Failed to get reply')

            if bytes_returned < expected_bytes:
                raise Exception("Unexpected reply length, got {} expected at least {}".format(bytes_returned,expected_bytes))


            _replyMsg = np.frombuffer(self._reply_buffer,dtype=np.uint32)
            self.debug('reply message: {}'.format(_replyMsg))
            error = socket.ntohl(int(_replyMsg[2]))
            if error != 0:
                try:
                    raise PymePixException(error)
                except PymePixException as e:
                    if 'ERR_EMPTY' in e.message:
                        pass
                    else:
                        raise


            reply = socket.ntohl(int(_replyMsg[0]))

            if reply != cmd | SpidrCmds.CMD_REPLY:
                raise Exception('Unexpected Reply {}'.format(reply))

            if socket.ntohl(int(_replyMsg[3])) != dev_nr:
                raise Exception('Unexpected device {}'.format(dev_nr))

            return _replyMsg


    # def customRequest(self,request,total_bytes):
    #     self._sock.send(self._req_buffer.tobytes()[0:total_bytes])
    #     sock_recv= self._sock.recv(4096)
    #     missing_bytes = ((len(sock_recv)//32) + 1)*32
    #     buffer = sock_recv + b" "*missing_bytes

    #     arr = np.frombuffer(buffer,dtype=np.uint32)
    #     print(self._vec_ntohl(arr))
    def convertNtohl(self,x):
        return socket.ntohl(int(x))

    def convertHtonl(self,x):
        return socket.htonl(int(x))

    def requestGetInt(self,cmd,dev_nr,arg=0):
        msg_length = 20
        self._req_buffer[4] = socket.htonl(arg)

        reply = self.request(cmd,dev_nr,msg_length,msg_length)

        return socket.ntohl(int(reply[4]))

    def requestGetInts(self,cmd,dev_nr,num_ints,args=0):
        msg_length = 20
        self._req_buffer[4] = socket.htonl(args)
        expected_len = (4 + num_ints)*4

        reply = self.request(cmd,dev_nr,msg_length,expected_len)

        return self._vec_ntohl(reply[4:4+num_ints])

    def requestGetBytes(self,cmd,dev_nr,expected_bytes,args=0):
        msg_length = (4+1)*4
        self._req_buffer[4]=0
        expected_len = 16 + expected_bytes
        #Cast reply as an uint8
        reply = self.request(cmd,dev_nr,msg_length,expected_len)
        return np.copy(reply[4:].view(dtype=np.uint8)[:expected_bytes])

    def requestGetIntBytes(self,cmd,dev_nr,expected_bytes,args=0):
        msg_length = (4+1)*4
        self._req_buffer[4]=socket.htonl(args)
        expected_len = 20 + expected_bytes
        #Cast reply as an uint8
        int_total = expected_bytes + ((expected_bytes) & 5)
        reply = self.request(cmd,dev_nr,msg_length,expected_len)
        int_val = socket.ntohl(int(reply[4]))

        byte_val = np.copy(reply[5:].view(dtype=np.uint8)[:expected_bytes])

        return int_val,byte_val

    def requestSetInt(self,cmd,dev_nr,value):
        msg_length = (4+1)*4
        self._req_buffer[4] = socket.htonl(value)

        self.request(cmd,dev_nr,msg_length,20)


    def requestSetInts(self,cmd,dev_nr,value):
        num_ints = len(value)
        msg_length = (4+num_ints)*4

        self._req_buffer[4:4+num_ints] = self._vec_htonl(value)[:]

        self.request(cmd,dev_nr,msg_length,20)

    def requestSetIntBytes(self,cmd,dev_nr,value_int,value_bytes):
        num_bytes = len(value_bytes)
        msg_length = (4+1)*4 + num_bytes
        self._req_buffer[4] = socket.htonl(value_int)

        self._req_buffer[5:].view(dtype=np.uint8)[:num_bytes] = value_bytes[:]

        self.request(cmd,dev_nr,msg_length,20)




def main():
    import logging
    logging.basicConfig(level=logging.INFO)

    spidr = SPIDRController(('192.168.1.10',50000))
    print('Local temp: {} C'.format(spidr.localTemperature))

    print ('FW: {:8X}'.format(spidr.firmwareVersion))
    print ('SW: {:8X}'.format(spidr.softwareVersion))
    print ('Device Ids {}'.format(spidr.deviceIds))
    for idx,dev in enumerate(spidr):
        print ("Device {}: {}".format(idx,dev.deviceId))

    print ('CHIP Fanspeed: ',spidr.chipboardFanSpeed)
    print ('SPIDR Fanspeed: ',spidr.spidrFanSpeed)
    print ('Pressure: ',spidr.pressure, 'mbar')
    print ('Humidity: ',spidr.humidity,'%')
    print ('Temperature: ',spidr.localTemperature,' C')
    spidr.resetDevices()
    spidr.reinitDevices()
    print (spidr[0].ipAddrSrc)
    print (spidr[0].ipAddrDest)
    print (spidr[0].devicePort)
    print(spidr[0].serverPort)
    print (spidr[0].headerFilter)
    print(spidr[0].TpPeriodPhase)
    print(spidr.ShutterTriggerFreq)


if __name__=="__main__":
    main()
