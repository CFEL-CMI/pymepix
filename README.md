# libtimepix

This contains two projects. The first is the Pymepix library that is a python module to interface with SPIDR and Timepix.
The second is the PymepixViewer which provides a DAQ GUI software using pymepix and pyqtgraph


## Pymepix

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

To build documentation do

```
python setup.py build_sphinx
```


Try importing pymepix:
```
import pymepix
```

If there are no errors then it was successful!

## Pymepix Viewer

Pymepix-viewer is a graphical user interface for data acquisition using the pymepix library. It is still in development so expect some instability and bugs

### Getting Started


#### Prerequisites

Pyqtgraph is required (and by extension PyQt), install using:

```
pip install pyqtgraph
```


#### Installing
Clone the directory using:

```
git clone https://<desy-username>@stash.desy.de/scm/cmi/libtimepix.git
```

move into the pymepixviewer project folder

```
cd libtimepix/pymepixviewer
```

Then install

```
python setup.py install
```

#### Running

To run, open terminal or command prompt and do:

```
pymepixviewer
```

If the prerequisites are satisfied and timepix is connected then a window should pop up!