.. OpenFD documentation master file, created by
   sphinx-quickstart on Mon Aug 26 16:21:47 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

OpenFD documentation
====================

OpenFD (Open Firmware Deployer) is an open source tool that helps developers to
deploy their firmware to a target board in a variety of ways. Most of the steps
required to prepare a bootable SD card, flash programming, and other deployment
scenarios, can be simplified and automated using OpenFD.

It is designed for boards that run `U-Boot <http://www.denx.de/wiki/U-Boot>`_ 
as their bootloader, Embedded Linux as their kernel component, and requires a
GNU/Linux host PC.

Supported platforms
-------------------

TI DaVinci™ supported platforms:

* DM36x - Leopard Board

Installation modes
------------------

**1. Attached board on communication port**

In this mode, the board is attached to a serial port in your computer, i.e.
`/dev/ttyUSB0`, and OpenFD interacts with U-Boot through that port. This
mode is useful to transfer images to RAM memory, that can be then flashed to
some NAND or NOR flash memory, or actually booting them immediately from RAM
(useful in a development environment). 
 
**2. Deploy all the firmware to an SD card**

All the firmware to an SD card that can be used to boot your board. Optionally,
you can also create an image file that you can use later to write to any SD card.

For a detailed explanation of each installation mode, please refer to the
`User Guide`_.

Features Overview
-----------------

Main features:

* Based on the concepts of a Memory Map and a Partition, OpenFD's main
  input is a file :option:`--mmap-file` which contains a list of partitions that
  specify a memory map for the device to install (SD card, NAND, etc.).
* All parameters are received through command line arguments.
* Runs interactively (and non-interactively). Configurable to prompt the user
  before executing a dangerous operation (like repartitioning your SD card) but
  can also run in non-interactive mode.
* Dryrun support. OpenFD is able to run without executing any System
  or U-boot commands, this allows you to see what OpenFD would do
  before the actual deployment.
* Robust communication with U-Boot (error handling, timeouts, etc.).
* Logging support.

From a development point of view:

* Written 100% in Python.
* Modular architecture for easier maintenance.
* Test cases use the `pyunit <http://pyunit.sourceforge.net/>`_ framework.
* Well documented with `Sphinx <http://sphinx-doc.org/>`_.
* Makes use of the `rr-python-utils <https://github.com/RidgeRun/rr-python-utils>`_ 
  package for general utilities.

Examples
--------

The following examples are a very fast overview of how a successful OpenFD run
looks like. For detailed information, please refer to the `User Guide`_.

**1. Flashing NAND - Leopard Board DM36x**

This example writes the *kernel* component to NAND. 

Command:
::
    $ openfd \
        nand \
        --mmap-file ~/images/nand-mmap.config \
        --serial-port /dev/ttyUSB0 \
        --ram-load-addr 0x82000000 \
        --host-ip-addr 10.251.101.24 \
        --tftp-dir /srv/tftp \
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

**2. Creating a bootable SD card - Leopard Board DM36x**

The following example installs a bootable SD card for the Leopard Board DM36x.

Command:
::
    $ openfd \
        sd \ 
        --mmap-file ~/images/sd-mmap.config \
        --device /dev/sdb \
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

Installation
============

1. Install Python pip:

    sudo apt-get install python-pip
    
2. Install rr-python-utils:

    sudo pip install git+https://github.com/RidgeRun/rr-python-utils.git#egg=rrutils
    
3. Install OpenFD:

    sudo pip install git+https://github.com/RidgeRun/u-boot-installer.git#egg=openrfd

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

