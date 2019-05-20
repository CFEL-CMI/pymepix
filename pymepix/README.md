# Pymepix

Pymepix is a python module that provides high level access to timepix as well as low level access to SPIDR.


## Getting Started


### Prerequisites

Pymepix has very few dependencies and mostly uses the batteries included in Python 3.
Installing pymepix should install the prerequisties: numpy and sklearn.


### Installing from PyPi

To install simply do:

```
pip install pymepix
```

Try importing pymepix:

```
python -c "import pymepix"
```

If there are no errors then it was successful!


### Installing from source

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