# Pymepix Viewer

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
