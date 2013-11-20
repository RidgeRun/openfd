.. Installer documentation master file, created by
   sphinx-quickstart on Mon Aug 26 16:21:47 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Installer documentation
=======================

The installer's objective is to aid in the deployment of firmware
to a target board in a variety of ways.

Most of the steps required to prepare a bootable SD card, flash some NAND memory
with U-Boot, and many other scenarios, can be simplified and automated using
this installer.

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

* DM36x - Leopard Board

Examples
--------

The following examples are a very fast overview of how a successful run
of the installer looks like. For more detailed information on how to use
this installer, please refer to the `User Guide`_.

**1. Flashing NAND - Leopard Board DM36x**

This example writes the *kernel* component to NAND. 

Command:
::
    $ python installer.py \
        nand \
        --mmap-file ~/images/nand-mmap.config \
        --serial-port "/dev/ttyUSB0" \
        --serial-baud "115200" \
        --ram-load-addr 0x82000000 \
        --host-ip-addr 10.251.101.24 \
        --tftp-dir "/srv/tftp" \
        --tftp-port 69 \
        --nand-blk-size 131072 \
        --nand-page-size 2048 \
        kernel 

Output:
::
      Uboot <= 'echo sync'
    Configuring uboot network
      Uboot <= 'ping 10.251.101.24'
      Uboot <= 'printenv serverip'
    Installing kernel
      Uboot <= 'printenv kmd5sum'
      Uboot <= 'printenv koffset'
      Uboot <= 'printenv ksize'
      Uboot <= 'printenv kpartitionsize'
      Uboot <= 'setenv autostart no'
      Uboot <= 'tftp 0x82000000 kernel.uImage'
      Uboot <= 'printenv filesize'
      Uboot <= 'setenv autostart yes'
      Uboot <= 'nand erase 0x400000 0x480000'
      Uboot <= 'nand write 0x82000000 0x400000 0x420000'
      Uboot <= 'setenv kmd5sum c0ef71c4d0d84e2f48ddce2bf2b85826'
      Uboot <= 'setenv koffset 0x400000'
      Uboot <= 'setenv ksize 0x420000'
      Uboot <= 'setenv kpartitionsize 0x480000'
      Uboot <= 'saveenv'
    Kernel installation complete
      Uboot <= 'printenv autostart'
      Uboot <= 'echo Installation complete'
    Installation complete

**2. Creating a bootable SD - Leopard Board DM36x**

The following example installs a bootable SD card for the Leopard Board DM36x.

Command:
::
    $ python installer.py \
        sd \ 
        --mmap-file ~/images/sd-mmap.config \
        --device "/dev/sdb" \
        --kernel-file ~/images/kernel.uImage \
        --uflash-bin ~/u-boot-2010.12-rc2-psp03.01.01.39/src/tools/uflash/uflash \
        --ubl-file ~/images/ubl_DM36x_sdmmc.bin \
        --uboot-file ~/images/bootloader \
        --uboot-entry-addr 0x82000000 \
        --uboot-load-addr 0x82000000 \
        --work-dir ~/images \
        --rootfs ~/images/fs/fs \
        --uboot-bootargs "...  mem=83M root=/dev/mmcblk0p2 rootdelay=2 rootfstype=ext3"

Output:
::
    The following partitions from device /dev/sdb will be unmounted:
    /media/rootfs
    /media/boot
    
    Do you want to continue [Y/n]: y
    Creating partitions on /dev/sdb
    You are about to repartition your device /dev/sdb (all your data will be lost)
    Do you want to continue [Y/n]: y
    Formatting partitions on /dev/sdb
    Installing uboot
    Installing uboot environment
    Installing kernel
    Installing rootfs
    Checking filesystems on /dev/sdb
    Installation complete

User Guide
==========

.. toctree::
   attached-board

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

