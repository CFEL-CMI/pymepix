Here are two scripts which simulate a very rudimentary TimePix camera.
A scenario may look like the following:

local-loopback with 127.0.0.1

local-loopback with 127.0.0.10

wherever you create the timepix object put the corresponding addresses like:

`self._timepix = pymepix.Pymepix(('127.0.0.10', 50015), src_ip_port=('127.0.0.1', 0))`

The port is set in the following script and needs to match.

`spidrDummTCP.py`: is the actual camera and recieves commands and send the requested information. 
At this stage this is mostly random but should enable you to develop and test code without the necessary need of a pysical device.
The list of commands implemented isn't complete at this point. Unfortunately this script needs to be restart with every restart of you software. I haven't had the time to lookup the right socket parameters, yet.

`spidrDummUDP.py`: this simple script sends raw (previously recorded with pymepix) data from your virtual camera.