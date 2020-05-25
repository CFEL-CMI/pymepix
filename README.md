# PymePix project

Python framework for Timepix (version 3 and later) controls and data acquisition.


## Current status

See the list of ToDos in the [documentation](#documentation) for known issues and planned
improvements.


## PymePix Python module

The `pymepix/` directory contains the actual `pymepix` framework with the control and
data-acquisition (DAQ) functionality. `pymepix` directly interfaces with the Timepix hardware.
Currently, it works with the [SPIDR](https://wiki.nikhef.nl/detector/Main/SpiDr) board.

`pymepix` provides high level access to Timepix settings and data as well as low level access to
[SPIDR](https://wiki.nikhef.nl/detector/Main/SpiDr).


## PymepixViewer entrance-level GUI

Furthermore, there is the PymepixViewer in `pymepixviewer/`, which provides a simple graphical-user
interface (GUI) using pymepix and pyqtgraph. The latter is not meant to replace a full DAQ GUI, but
to provide easy entrance to using Timepix3 with pymepix.



<!-- Put Emacs local variables into HTML comment
Local Variables:
coding: utf-8
fill-column: 100
End:
-->
