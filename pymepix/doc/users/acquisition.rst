.. highlight:: python
   :linenothreshold: 6


===========
Acquisition
===========

Acquisition can be started and stopped by::

    import time
    from pymepix import Pymepix

    #Connect
    timepix = Pymepix(('192.168.1.10',50000))

    #Start acquisition
    timepix.start()

    #Wait
    time.sleep(1.0)

    #Stop acquisition
    timepix.stop()


Pymepix provides data as a tuple given by (:class:`MessageType`,data). These are explained in :ref:`dataformats`.
Retrieving the data can be done in to ways: Polling or Callback

-------
Polling
-------

Polling is where pymepix will place anything retrieved from Timepix into a ring polling buffer. This
is the default mode but to reenable it you can use::

>>> timepix.enablePolling(maxlen=1000)

where *maxlen* describes the maximum number of elements in the buffer before older values are
overwritten.

The user can retrieve this data by using:

>>> timepix.poll()
(MessageType.RawData,(array[98732405897234589802345,dtype=uint8],12348798))

If there is nothing in the polling buffer then a :class:`PollBufferEmpty` exception is raised
The poll buffer is limited in size but can be extended by doing:

>>> timepix.pollBufferLength = 5000

This will clear all objects using the polling buffer.

--------
Callback
--------

The callback method allows the user to deal with the data immediately when it is recieved. Setting
this will clear the polling buffer of any contents.

To set a callback, first you need a function, for example::

    def my_callback(data_type,data):
        print('My callback is running!!!!')


The format of the function must accept two parameters, :class:`MessageType` and
an extra data parameter. These are explained in :ref:`dataformats`. Now to make
pymepix use it simply do:

>>> timepix.dataCallback = my_callback

Now when acquisition is started:

>>> timepix.start()

The output seen is::

.. code-block:: sh

    My callback is running!!!!
    My callback is running!!!!
    My callback is running!!!!
    My callback is running!!!!
    My callback is running!!!!


-------------
Pipelines
-------------

Pymepix uses pipelines objects in order to process data. Each pipeline is set for each timepix
device so each timepix can have a different data pipeline. You can configure them to postprocess or
output data in certain ways. For example the :class:`PixelPipeline` object will read from a UDP
packet stream and decode the stream into *pixel x*, *pixel y*, *time of arrival* and *time over
threshold* arrays. All data is progated forward through the pipeline so both UDP packets and decoded
pixels are output.

To use the (default) :class:`PixelPipeline` pipeline on the first connected timepix device you can
do::

    from pymepix.processing import PixelPipeline,CentroidPipeline

    timepix[0].setupAcquisition(PixelPipeline)

If you need centroid you instead can do:

>>> timepix[0].setupAcquisition(CentroidPipeline)

Configuring the pipelines can be done using the acquisition property for the timepix device, for
example to enable TOFs you can do:

>>> timepix[0].acquisition.enableEvents = True

A list of pipelines and setting can be found in :ref:`acquisition`




.. Local Variables:
.. fill-column: 100
.. coding: utf-8
.. End:
