.. currentmodule:: pymepix


===============================
Pymepix Developer documentation
===============================


This developer documentation contains the API reference for `pymepix`.


API reference
-------------

.. toctree::
   :maxdepth: 2

   api/modules


Known issues and planned improvements
-------------------------------------

.. todo:: Synchronize the different (near)"stale" feature branches into develop and get into an
          actual (agile) git-flow development mode with progress being accumulated on `develop/`

.. todo:: TimePix doesn't get configured correctly and such SoPhy is still required for this, but
          compare branch XFELNov2019 for current progress.

.. todo:: Centroiding is in many cases too slow for long data acquisition and not all data received
          gets saved to disk. Implement facilities to ensure data is saved to disk at highest
          priority and 'real-time' analysis, e.g., centroiding, is performed on as much data as
          possible -- but nor more.

.. todo:: Following the previous ToDo: improve performance of centroiding.

.. todo:: Implement the FLASH/EuXFEL specific trainID reader on develop using programmable logic to
          turn it on (only) when available and wanted.



.. comment
   Local Variables:
   coding: utf-8
   mode: fly-spell
   fill-column: 100
   truncate-lines: t
   End:
