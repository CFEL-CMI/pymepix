==========================
Connecting and Configuring
==========================

-----------
Connecting
-----------

Connecting to SPIDR can be done with:

>>> timepix = Pymepix(('192.168.1.10',50000))

Where the IP address is the one seen on the OLED screen on timepix. The number of devices can be found using:

>>> len(timepix)
1

Meaning we have one device. To access this device directly, use::

    tpx0 = timepix[0]

And to check the device name:

    >>> tpx0.deviceName
    W0026_K08


-----------
Configuring
-----------

To set the biasVoltage to 50 Volts in spidr you can do::

    >>> timepix.biasVoltage = 50

Setting the  we can manage its settings directly. To easily setup the device we can use a SoPhy config file (.spx)::

    tpx0.loadConfig('myFile.spx')

This sets up all the DAC setting and pixel configurations.
Individual parameters can also be set for example. To set the fine threshold to 100 mV do:

>>> tpx0.Vthreshold_fine = 100

pixel threshold configurations can be set by passing a 256x256 numpy array::

    import numpy as np
    tpx0.pixelThreshold[...] = 0

The same for pixel masks, to set a checkboard mask do::

    tpx0.pixelMask[::2] = 1

These need to be uploaded to timepix before they take effect:

    >>> tpx0.uploadPixels()

The full list of parameters that can be set can be found in :ref:`timepixdevice`.