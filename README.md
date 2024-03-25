Thia repository is deprectaed, please see the public project at https://gitlab.desy.de/CMI/CMI-public/pymepix instead.


branch for implementing zmq for packetprocessor

# Pymepix

The `pymepix` Python module provides the control and data-acquisition (DAQ) functionality. It
directly interfaces with the Timepix hardware. Currently, it works with the SPIDR board.

See the accompanying [license](./LICENSE.md) and the [documentation](#documentation) for further
details.


## Getting Started with PymePix
### Prerequisites

Obviously, you need a Timpix3cam with SPIDR board, we are using versions of
[TPX3CAM](https://www.amscins.com/tpx3cam/) from [ASI](https://www.amscins.com).

Pymepix has very few dependencies and mostly uses the batteries included in Python 3. Installing
pymepix should install the prerequisties `numpy` and `sklearn` if not already present.


### Installing

Run the installation script through
```bash
python3 -m pip install .
```
if you try to install in a Conda or virtual environment, you need to do
```bash
python3 -m pip install --user .
```

Standard `setuptools` options such as `-e` for development are available; see, e.g., the
[PymePix documentation](https://pymepix.readthedocs.io) for some details.

Try importing pymepix outside the actual source code:
```
python -c "import pymepix"
```
If there are no errors then the installation was, fundamentally, successful.


## Documentation

Documentation is available at [readthedocs](https://pymepix.readthedocs.io); you can locally build
the included documentation by running

```
python setup.py build_sphinx
```



<!-- Put Emacs local variables into HTML comment
Local Variables:
coding: utf-8
fill-column: 100
End:
-->
