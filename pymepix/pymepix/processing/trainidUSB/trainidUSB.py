#!/usr/bin/env python
from __future__ import print_function

import serial
from datetime import datetime
# Checking if device is there
import stat, os
# Arguments
import sys, getopt
# Signal to stop script
import signal


def trainidUSB(DEVICE='/dev/ttyUSB0', r='', t='', c='', B='', b='', T=''):
    """ Function that decodes the timing information in the 115Kbaud protocol received via USB 
    Arguments should just be pass a string (like "yes" "ok") to enable

    Keyword arguments :
    [r] raw            : raw mode. Show information as received by the interface (no STX and ETX)
    [t] time           : display time at which information was received
    [c] crc            : calculate CRC data payload and check if matches
    [B] checkBeam      : interpret beam mode data (not compatible with raw)
    [b] checkBeamShort : interpret beam mode data and display in short form  (not compatible with raw)
    [T] test           : test mode. Device is a file in the system, each line has data payload and crc data as if received from timing system  
    """

    # Information fields read from the USB interface
    timingInfoNames = ['Train ID', 'Beam Mode', 'CRC']
    # Number of bytes in each information field 
    timingInfoLength = [16, 8, 2]

    # Beam Locations	
    beamLocations = ['Injector 1', 'Injector 2', 'Acc_L1-L3', 'TLD', 'SASE1/3', 'SASE2']
    # Beam Modes	
    beamModeInfo = ['[1] Single Bunch Operation', '[S]hort mode (<= 30 Bunches)', '[M]edium Mode (<= 300/500 Bunches)',
                    '[F]ull Mode (No restrictions)']

    # If raw mode, beam mode is not available
    if r:
        B = ''
        b = ''

    # Configure serial interface
    ser = serial.Serial(DEVICE, 115200)

    def stopScript(sig, frame):
        print('Stopping script, see you later!')
        ser.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, stopScript)

    while True:
        # Align with beginning of word (STX = ASCII 02)
        while chr(2) != ser.read(1):
            pass

        # Add time info if requested
        outputString = '' if not t else str(datetime.now().strftime("%H:%M:%S.%f")) + ': '

        # Get information
        if r:
            for info in range(sum(timingInfoLength)):
                outputString += ser.read(1)

        else:
            # Reset information on each run
            timingInfo = {k: '' for k in timingInfoNames}
            # Get info according to Information fields and bytes fields
            # Information fields are in order, so do not use standard Python dictionary
            for info in range(len(timingInfoNames)):
                for sizeInfo in range(timingInfoLength[info]):
                    timingInfo[timingInfoNames[info]] += ser.read(1)
            # Check if last byte is a ETX 
            if chr(3) != ser.read(1):
                print("Not properly align, skipping this run.")
                continue

            crc = ''
            # Calculate crc
            if c:
                crcVal = 0
                # data payload
                timingPayload = timingInfo['Train ID'] + timingInfo['Beam Mode']
                for i in range(0, len(timingPayload), 2):
                    crcVal ^= int(timingPayload[i:i + 2], 16)
                if crcVal != int(timingInfo['CRC'], 16):
                    crc = ' !!!Problem!!! Calculated CRC: ' + str(hex(crcVal)[2:]).upper()

                    # Train ID in decimal
            timingInfo['Train ID'] = int(timingInfo['Train ID'], 16)

            # Add values plus crc
            for info in timingInfoNames:
                outputString += info + ' : ' + str(timingInfo[info]) + ' '
            outputString += crc

        # Print output
        print(outputString)

        # Check Beam Modes
        if B or b:
            beamMode = ''
            for location in range(len(beamLocations)):
                localIndex = format(int(timingInfo['Beam Mode'][location:location + 1], 16), '04b').find('1')
                locationMode = '[0] No Bunches allowed' if localIndex < 0 else beamModeInfo[localIndex]
                beamMode += '  {message: <{width}}'.format(message=beamLocations[location] + ' : ',
                                                           width=15 if B else 10)
                beamMode += locationMode + '\n' if B else locationMode[0:3]
            print(beamMode)


def main(argv):
    timingArguments = ['r', 't', 'c', 'B', 'b']
    timingArgumentsHelp = {
        'r': 'raw mode. Show information as received by the interface (no further processing).',
        't': 'display time at which information was received',
        'c': 'calculate CRC data payload and check if matches',
        'B': 'interpret beam mode data',
        'b': '[short] interpret beam mode data',
        'h': 'print this menu'
    }
    timingArgumentsDict = {k: '' for k in timingArguments}

    # Check Arguments
    try:
        opts, args = getopt.getopt(argv, 'h' + ''.join(timingArguments))
    except getopt.GetoptError:
        print('trainidUSB.py -' + 'h' + ''.join(timingArguments))
        sys.exit(2)
    for opt, val in opts:
        if '-h' == opt:
            print('-' * 30)
            print('trainidUSB')
            print('-' * 30)
            print('Syntax: ./trainidUSB.py -' + 'h' + ''.join(timingArguments) + ' [device]')
            print('Function that decodes the timing information in the 115Kbaud protocol received via USB')
            print('Key:')
            for argument in timingArguments:
                print(' -' + argument + ' : ' + timingArgumentsHelp[argument])
            print(' -h : ' + timingArgumentsHelp['h'])
            print(' device : if not provided, default is /dev/ttyUSB0')

            sys.exit(0)
        else:
            timingArgumentsDict[opt[1:]] = 'on'

    device = args[0] if args else '/dev/ttyUSB0'

    def checkUSB(usb):
        try:
            stat.S_ISBLK(os.stat(device).st_mode)
        except:
            return False
        return True

    if not checkUSB(device):
        print('Device ' + device + ' is not available in the system. Exiting...')
        sys.exit(1)

    trainidUSB(device, **timingArgumentsDict)


if __name__ == "__main__":
    main(sys.argv[1:])
