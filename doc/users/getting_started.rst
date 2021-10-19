
.. _getting_started:

===============
Getting started
===============

.. _installing:

Installing
----------

Installing from PyPI (platform-independent)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Execute :code:`pip install pymepix`. This should install pymepix including all dependencies.


Installing from git source directly (platform-independent)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can clone pymepix from our main git repository::

    git clone https://github.com/CFEL-CMI/pymepix.git

Navigate into the pymepix library (:code:`cd pymepix`) and run :code:`pip install .`

Build Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To build the documentation for pymepix locally perform the following commands. 
The first line is only required if there are changes in the package structure or new 
classes or packages have been added. To only build the existing documentation only the 
second line must be executed.

.. code:: shell
    :number-lines: 1

    sphinx-apidoc -o ./doc/api ./pymepix
    python setup.py build_sphinx



Adapt :code:`pymepix/config/default.yaml` according to your setup.

Dependencies
------------

The majority of pymepix only depends on numpy. To use centroiding, the scikit-learn package is required

- *numpy*
- *scikit-learn*: Centroiding and data reduction (Using DBSCAN algorithm for clustering)
- *scipy*: Calculation of the centroids properties from the identified clusters
- *pyzmq*: Inter process communication in the processing pipeline
- *h5py*: Saving processed data as hdf5 files
- *tqdm*: Display a progessbar for post processing
- *pyyaml*: Konfiguration of camera (ip, port, ...)
- *pyserial* (optional): Only used for inclusion of USBTrainID at FLASH and XFEL
