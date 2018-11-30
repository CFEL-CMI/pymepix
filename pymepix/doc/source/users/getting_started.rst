
.. _getting_started:

===============
Getting started
===============

.. _installing:

Installing
----------

Installing from git source directly (platform-independent)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can clone pymepix from our main git repository::

    git clone https://<desy-username>@stash.desy.de/scm/cmi/libtimepix.git

Move into the pymepix library::

    cd libtimepix/pymepix

Then, just do::

    python setup.py install

To build documentation do::
    
    python setup.py build_sphinx

Dependencies
------------

The majority of pymepix only depends on numpy. To use centroiding, the sklearn package is required

