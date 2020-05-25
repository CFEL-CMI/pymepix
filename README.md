# PymePix project

Python framework for Timepix (version 3 and later) controls and data acquisition.


## Current status

See the list of ToDos in the [documentation](#documentation) for known issues and planned
improvements.


## PymePix Python module

This repository contains the actual `pymepix` framework with the control and data-acquisition (DAQ)
functionality, which directly interfaces with the Timepix hardware. Currently, it works with the
SPIDR board.

`pymepix` provides high level access to Timepix settings and data as well as low level access to
SPIDR.


## PymepixViewer entrance-level GUI

Furthermore, there is the PymepixViewer which provides a simple graphical-user interface (GUI) using
pymepix and pyqtgraph. The latter is not meant to replace a full DAQ GUI, but to provide easy
entrance to using Timepix3 with pymepix.



# Getting Started with PymePix

## Prerequisites

Pymepix has very few dependencies and mostly uses the batteries included in Python 3. Installing
pymepix should install the prerequisties `numpy` and `sklearn` if not already present.


## Installing

In the pymepix project folder `./pymepix` run the installation script through
```
pip install .
```
or
```
python setup.py install
```
Standard `setuptools` options such as `develop` or `--user` are available; see the
[documentation](#documentation) for details.

Try importing pymepix:
```
python -c "import pymepix"
```
If there are no errors then the installation was, fundamentally, successful.


## Documentation

To build the included documentation run

```
python setup.py build_sphinx
```


# The Pymepix viewer

Pymepix-viewer is a basic graphical user interface for data acquisition using the pymepix library.
It is not meant as a full-fledged and stable DAQ-GUI, but to demonstrate the capabilities of
`pymepix`, to provide an initial operational system for easy entrance to Timepix operation, and as a
reference implementation for `pymepix` use.

## Prerequisites

For the PymePix viewer PyQt5 is a requirement. This can be installed [(painfully)
manually](https://www.metachris.com/2016/03/how-to-install-qt56-pyqt5-virtualenv-python3) or using
package managers such as [Anaconda](https://www.anaconda.com) (`conda install pyqt=5`), MacPorts
(`sudo port install py38-pyqt5`), or similar.


## Installing

In the pymepixviewer project folder `./pymepixviewer` run the installation script through
```
pip install .
```
or
```
python setup.py install
```
Standard `setuptools` options such as `develop` or `--user` are available; see the
[documentation](#documentation) for details.


## Running

To run the gui start it from a terminal as
```
pymepixviewer
```

If the prerequisites are satisfied and timepix is connected then a window should open. See the
documentation for further details.



<!-- Put Emacs local variables into HTML comment
Local Variables:
coding: utf-8
fill-column: 100
End:
-->
