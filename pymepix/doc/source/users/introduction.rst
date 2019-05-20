.. _introduction:

============
Introduction
============

Pymepix is intended to bridge the gap between Timepix3 and Python. The goal of the library is to
allow a user without deep technical knowledge of Timepix3 to establish a connection, start
acquisition, and retrieve and plot pixel and timing information in as few lines of code as possible;
at the same time it provides all details to unleash the full power of Timepix3-SPIDR hardware. This
is achieved by classes that act as a black-box, handling all of the low level TCP communication and
decoding of the UDP data-stream, presenting them in a pythonic fashion. More advanced and
lower-level control of SPIDR and Timepix3 is still available from these black-box classes or can be
established directly by the user. For easy installation, it only depends on the standard python
library, numpy and scikit-learn.
