trainidUSB
==========

Function that decodes the timing information in the 115KBaud protocol received via USB.

Information has the following format: <STX><Data payload><8bit CRC><ETX>

:Author: Bruno Fernandes	 
:Email: bruno.fernandes@xfel.eu

##############

trainidUSB.py
=============

Syntax
------
trainidUSB [-rtcBbh] [device]

Keys
----
-r  show information as received by the interface (no STX and ETX)
-t  display time at which information was received
-c  calculate CRC data payload and check if matches
-B  interpret beam mode data
-b  interpret beam mode data (short form)
-h  display this menu

Arguments
---------
**device** if not provided, default is /dev/ttyUSB0

Usage
-----

To use the function, simple call it in your shell,  like so::

	$ ./trainidUSB.py
	


trainidUSB.sh
=============

Syntax
------
trainidUSB [-rtocbTh] [-s stx] [-e etx] [device]

Keys
----
-r  show information as received by the interface (no STX and ETX)
-t  display time at which information was received
-o  overwrite output every time new information is received
-c  calculate CRC data payload and check if matches
-b  interpret beam mode data
-T  test mode. Device is a file in the system, each line has data payload and crc data as if received from timing system
-s stx    update value used for STX. Variable stx is ASCII decimal value
-e etx    update value used for ETX. Variable etx is ASCII decimal value
-h   display this menu

Arguments
---------
**device** if not provided, default is /dev/ttyUSB0

Usage
-----

To use the function, first source it in your bash shell and then call it. Like so::

	$ source trainidUSB.sh
	$ trainidUSB

To use it test mode with the provided ``testinput.txt`` file::

	$ source trainidUSB.sh	
	$ trainidUSB -T testinput.txt

	
