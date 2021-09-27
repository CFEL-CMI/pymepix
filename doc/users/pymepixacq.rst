.. _pymepixacq:

===========================
PymepixAcq - Command line
===========================


Included with pymepix is a command line code using the pymepix library to acquire from timepix. The command line interface includes two different commands:
 - "connect": to connect to a running timepix camera and record data
 - "post-process": to post-process recorded raw data files into easier usable hdf5 files containing raw and centroided data

Doing::

    pymepix-acq --help

Outputs the help::

    usage: pymepix-acq [-h] {connect,post-process} ...

    Timepix acquisition script

    positional arguments:
        {connect,post-process}
         connect             Connect to TimePix camera and acquire data.
         post-process        Perform post-processing with a acquired raw data file.

    optional arguments:
        -h, --help            show this help message and exit


You can access the documentation for both commands by executing "pymepix-acq connect -h" or "pymepix-acq post-process -h" respectively.