.. Installer documentation master file, created by
   sphinx-quickstart on Mon Aug 26 16:21:47 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Installer documentation
=======================

The installer's objective is to aid in the deployment of firmware
to a target board in a variety of ways.

Most of the steps required to prepare a bootable SD card, flash some NAND memory
with U-Boot, and many other scenarios in which the engineer has to spend a lot
of time executing manual steps to get the code in the board, can be simplified
and automated using this installer.

Installation modes
------------------

**1. Attached board on communication port**

In this mode, the board is attached to a serial port in your computer, i.e.
`/dev/ttyUSB0`, and the installer interacts with U-Boot through that port. 
 
**2. Deploy all the firmware to an SD card.**

The installer will deploy all the firmware to an SD card that can be used to
boot your board. Optionally, you can also create an image file that you can
use later to write to any SD card.

Features
--------

Main features are:

* Based on the concepts of a Memory Map and a Partition, the installer's main
  input is a file "--mmap-file" which contains a list of partitions that
  specify a memory map for the device to install (SD card, NAND, etc.).
* Dryrun support. The installer is able to run without executing any System
  or U-boot commands, this allows you to see what the installer would do
  before actually running it.
* Runs interactively (and non-interactively). Configurable to prompt the user
  before executing a dangerous operation (like repartitioning your SD card) but
  can also run in non-interactive mode.
* Robust communication with U-Boot (error handling, timeouts, etc.).
* All parameters are received through command line arguments.
* Supports logging.

From a development point of view:

* Written 100% in Python.
* Modular architecture for easier maintenance.
* Test cases use the `pyunit <http://pyunit.sourceforge.net/>`_ framework.
* Well documented with `Sphinx <http://sphinx-doc.org/>`_.
* Makes use of the `rr-python-utils <https://github.com/RidgeRun/rr-python-utils>`_ 
  for general utilities.

Supported platforms
-------------------

The installer supports:

* DM36x - LeopardBoard

Code Documentation
==================

.. toctree::
   :maxdepth: 2

   modules

Code Navigation
===============

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Copyright Notice
================

Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com). All Rights Reserved.

