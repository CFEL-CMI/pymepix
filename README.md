# libtimepix

This contains two projects. The first is the Pymepix library that is a python module to interface with SPIDR and Timepix.
The second is the PymepixViewer which provides a DAQ GUI software using pymepix and pyqtgraph


## Pymepix

Pymepix is a python module that provides high level access to timepix as well as low level access to SPIDR.


### Getting Started


#### Prerequisites

Pymepix has very few dependencies and mostly uses the batteries included in Python 3.
Installing pymepix should install the prerequisties: numpy and sklearn.


#### Installing
Clone the directory using:

```
https://<desy username>@stash.desy.de/scm/cmipublic/timepix.git
```

move into the pymepix project folder

```
cd timepix/pymepix
```

Then install

```
pip install .
```

To build documentation do

```
python setup.py build_sphinx
```


Try importing pymepix:
```
python -c "import pymepix"
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
https://<desy username>@stash.desy.de/scm/cmipublic/timepix.git
```

move into the pymepixviewer project folder

```
cd timepix/pymepixviewer
```

Then install

```
pip install .
```

#### Running

To run, open terminal or command prompt and do:

```
pymepixviewer
```

If the prerequisites are satisfied and timepix is connected then a window should pop up!