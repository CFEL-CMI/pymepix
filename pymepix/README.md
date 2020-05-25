# Pymepix

The `pymepix` Python module provides the control and data-acquisition (DAQ) functionality. It
directly interfaces with the Timepix hardware. Currently, it works with the SPIDR board.

See the accompanying [license](./LICENSE.md) and the [documentation](#documentation) for further
details.


## Getting Started with PymePix
### Prerequisites

Pymepix has very few dependencies and mostly uses the batteries included in Python 3. Installing
pymepix should install the prerequisties `numpy` and `sklearn` if not already present.


### Installing

Run the installation script through
```
pip install .
```
or to directly use the setup.py run
```
python setup.py install
```
Standard `setuptools` options such as `develop` or `--user` are available; see the
[documentation](#documentation) for details.

Try importing pymepix outside the actual source code:
```
python -c "import pymepix"
```
If there are no errors then the installation was, fundamentally, successful.


## Documentation

To build the included documentation run

```
python setup.py build_sphinx
```
Up-to date documentation will also be available on readthedocs.



<!-- Put Emacs local variables into HTML comment
Local Variables:
coding: utf-8
fill-column: 100
End:
-->
