.. _dataformats:

============
Data Formats
============

Contains a list of possible data formats output during acquisition. Each entry of the data section represents another element in the tuple.
Example shows how to read the data through polling


-----------
UDP Packets
-----------

Data Type:
    :class:`MessageType.RawData`

Data:
    :array(uint64): list of UDP packets
    :uint64: global timer from Timepix at time packets were recieved

Example:

.. code:: python
    :number-lines: 1

    data_type, data = timepix.poll()
    if data_type is MessageType.RawData:
        packets, longtime = data

--------------
Decoded Pixels
--------------

Data Type:
    :class:`MessageType.PixelData`

Data:
    :array(uint64): pixel x position
    :array(uint64): pixel y position
    :array(float): global time of arrival in seconds
    :array(uint64)): time over threshold in nanoseconds

Example:

.. code:: python
    :number-lines: 1

    data_type, data = timepix.poll()
    if data_type is MessageType.PixelData:
        x, y, toa, tot = data

----------------
Decoded Triggers
----------------

Data Type:
    :class:`MessageType.TriggerData`

Data:
    :array(uint64): trigger number
    :array(float): global trigger time in seconds


Example:

.. code:: python
    :number-lines: 1

    data_type, data = timepix.poll()
    if data_type is MessageType.TriggerData:
        t_num, t_time = data


--------------------
Time of Flight/Event
--------------------

Data Type:
    :class:`MessageType.EventData`

Data:
    :array(uint64): trigger number
    :array(uint64): pixel x position
    :array(uint64): pixel y position
    :array(float): time of flight relative to its trigger in seconds
    :array(uint64)): time over threshold in nanoseconds


Example:

.. code:: python
    :number-lines: 1

    data_type, data = timepix.poll()
    if data_type is MessageType.EventData:
        trigger, x, y, tof, tot = data


-------------
Centroid Data
-------------

Data Type:
    :class:`MessageType.CentroidData`

Data:
    :array(uint64): trigger number
    :array(float): center of mass x position
    :array(float): center of mass y position
    :array(float): minimum cluster time of flight
    :array(float): average cluster time over threshold
    :array(uint64): maximum cluster time over threshold
    :array(uint64): cluster size


Example:

.. code:: python
    :number-lines: 1

    data_type, data = timepix.poll()
    if data_type is MessageType.CentroidData:
        trigger, x, y, tof, avg_tot, max_tot, size = data
