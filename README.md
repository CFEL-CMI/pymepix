# libtimepix

This contains two projects. The first is the Pymepix library that is a python module to interface with SPIDR and Timepix.
The second is the PymepixViewer which provides a DAQ GUI software using pymepix and pyqtgraph


## Pympix

Pymepix is a python module that provides high level access to timepix as well as low level access to SPIDR.


### Getting Started


#### Prerequisites

The only real requirement is numpy, for centroiding get the sklearn package:

```
pip install sklearn
```


#### Installing
Clone the directory using:

```
git clone https://<desy-username>@stash.desy.de/scm/cmi/libtimepix.git
```

move into the pymepix project folder

```
cd libtimepix/pymepix
```

Then install

```
python setup.py install
```

Try importing pymepix:
```
import pymepix
```

If there are no errors then it was successful!

## Pymepix Viewer

This is in the process of being ported to the new library and is non functional for now.

