.. _overview:

===============================
General overview
===============================
The main Pymepix library is built up in several different submodules
which each tackle a different task in working with the Timepix camera.
As seen in the API index those are
* `config`
* `core`
* `processing`
* `SPIDR`
* `util`

The top layer Pymepix consists of `pymepix`, `timepixdef` and `timepixdevice`.

pymepix
----------

`pymepix` provides the highest level of interaction with the library.
A single `Pymepix` object will hold all connected Timepix devices and manage the users' interaction with those.


timepixdevice and timepixdef
----------------------------

| A `timepixdevice` object holds all the communication with a single camera.
  It basically configures, starts and stops.
| The `timepixdef` has multiple enums to encode all kinds of parameters for Timepix.


config module
-------------

| The `config` module gets the information for config parameters.
| `timepixconf` is the base class for the possible configurations.
| `defaultconfig` holds hardcoded config parameters for the camera to initialize.
| `sophyconfig` imports information from SoPhy (.spx) config files.
  It reads and transforms that information to be used by Pymepix.


core module
-----------

The `core` module consists of only the log class.
It defines functionality for Pymepix' needs and uses the basic python logging module.


processing module
-----------------

The `processing` module provides the data pipeline to process the incoming camera data.
Pymepix can use different acquisition pipelines to process the data.
Those are defined in `acquisition` with the base functionality provided by `baseacquisition`.
An acquisition pipeline determines which steps work in what order on the incoming data and connects those.

Each pipeline consists of acquisition stages (`baseacquisition`),
where one stage holds the information about one logical step in the pipeline.
Those tasks are currently `udpsampler` (capturing the packets), `rawtodisk` (saving the raw data),
`pipline_packet_processor` (interpreting the raw packets) and `pipeline_centroid_calculator` (compress data by finding blob centers).
Each of these specific pipeline steps overwrites the `BasePipelineObject`,
which is in fact a python `multiprocessing.Process`.

The majority of the logic for the pipeline_packet_processor and the pipeline_centroid_calculator is separated in the classes `centroid_calculator`
and `packet_processor`. The `pipeline_` classes only add functionality for the integration of those classes into the multiprocessing pipeline.

Each stage knows the task it has to fulfill and then creates one or multiple processes
to work on that task in parallel.

`datatypes` provides an enum to classify the data that is passed through the pipeline at each step.


SPIDR module
------------

This module communicates with the SPIDR chip of the Timepix.
One `spidrcontroller` knows about one or more `spidrdevices`.
`spidrcmds` lists the known commands to pass information and instructions to a chip.
`spidrdefs` extends those commands by constants that can be passed.
error contains information on possible errors from SPIDR.


util module
-----------

| `storage` provides some functionality to save data.
| `spidrDummyTCP` and -`UDP` can be used to simulate a timepix camera.
  Both are still rudimentary but helpful for debugging.
| `spidrDummyTCP` accepts packets in so the configuration of timepix can be tested.
| `spidrDummyUDP` samples and sends packets from a given file into the void.
  This can be used to test the pipeline functionality by capturing those packets with Pymepix.

Class overview
--------------

.. raw:: html

    <object data="users/assets/pymepix_class_diagram.svg" type="image/svg+xml"></object>
