# Pymepix Viewer

Pymepix-viewer is a graphical user interface for data acquisition using the pymepix library. It is still in development so expect some instability and bugs

## Getting Started


### Prerequisites

PyQt5 is a requirement. This can be installed (painfully) manually here:

https://www.metachris.com/2016/03/how-to-install-qt56-pyqt5-virtualenv-python3/

or easily using Anaconda3:

```
conda install pyqt=5
```



### Installing
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

### Running

To run, open terminal or command prompt and do:

```
pymepixviewer
```

If the prerequisites are satisfied and timepix is connected then a window should pop up!