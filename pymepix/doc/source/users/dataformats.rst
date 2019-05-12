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
::

    data_type,data = timepix.poll()
    if data_type is MessageType.RawData:
        packets,longtime = data

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
::

    data_type,data = timepix.poll()
    if data_type is MessageType.PixelData:
        x,y,toa,tot = data

----------------
Decoded Triggers
----------------

Data Type:
    :class:`MessageType.TriggerData`

Data:
    :array(uint64): trigger number
    :array(float): global trigger time in seconds


Example:
::

    data_type,data = timepix.poll()
    if data_type is MessageType.TriggerData:
        t_num,t_time = data


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
::

    data_type,data = timepix.poll()
    if data_type is MessageType.EventData:
        trigger,x,y,tof,tot = data


-------------
Centroid Data
-------------

Data Type:
    :class:`MessageType.CentroidData`

Data:
    :array(uint64): trigger number
    :array(uint64): center of mass x position
    :array(uint64): center of mass y position
    :array(uint64): total area
    :array(uint64): total time over threshold
    :array(uint64): Ignore (used in future)
    :array(uint64): Ignore (used in future)
    :array(uint64)): time of flight


Example:
::

    data_type,data = timepix.poll()
    if data_type is MessageType.CentroidData:
        trigger,x,y,area,integral,nu,nu,tof = data