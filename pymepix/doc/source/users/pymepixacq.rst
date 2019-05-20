.. _pymepixacq:

===========================
PymepixAcq - Command line
===========================


Included with pymepix is a command line code using the pymepix library to acquire from timepix. It is run using::

    pymepix-acq --time 10 --output my_file

Doing::

    pymepix-acq --help


Outputs the help::

    usage: pymepix-acq [-h] [-i IP] [-p PORT] [-s SPX] [-v BIAS] -t TIME -o OUTPUT
                    [-d DECODE] [-T TOF]

    Timepix acquisition script

    optional arguments:
    -h, --help                 show this help message and exit
    -i IP, --ip IP             IP address of Timepix
    -p PORT, --port PORT       TCP port to use for the connection
    -s SPX, --spx SPX          Sophy config file to load
    -v BIAS, --bias BIAS       Bias voltage in Volts
    -t TIME, --time TIME       Acquisition time in seconds
    -o OUTPUT, --output OUTPUT output filename prefix
    -d DECODE, --decode DECODE Store decoded values instead
    -T TOF, --tof TOF          Compute TOF if decode is enabled


TODO: MORE DOCS