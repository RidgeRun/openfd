====================================
Attached board on communication port
====================================

Overview
========

This mode assumes that you have a board attached to your host PC through a
communication port.

DM36x Leopard Board
-------------------

Setup
^^^^^

1. Plug your DM36x Leopard Board to a serial port, in this example we will
assume that the serial port is `/dev/ttyUSB0`.

2. Turn On your board and stop it at the U-Boot prompt. In this example *termnet*
is used to communicate with the board, and the autoboot was stopped to get to the
Uboot's prompt.
::
    $ termnet 127.0.0.1 3001
    Baudrate set to: 115200
    Port Settings are: 8NC0S0
    Port Device set to: /dev/ttyUSB0
    Baudrate set to: 115200
    Port Settings are: 8NC0S0
    ...
    U-Boot 2010.12-rc2 (Nov 19 2013 - 09:25:06)
    
    Cores: ARM 432 MHz
    DDR:   340 MHz
    I2C:   ready
    DRAM:  128 MiB
    NAND:  256 MiB
    MMC:   davinci: 0, davinci: 1
    Net:   Ethernet PHY: GENERIC @ 0x00
    DaVinci-EMAC
    Hit any key to stop autoboot:  0 
    DM368 LEOPARD #
    
3. Close your terminal session (in this case *termnet*), so that the installer
can communicate with U-Boot through the available serial port.
::
    DM368 LEOPARD # 
    termnet>>quit

At this point you are ready to execute the installer.

Installing to NAND
^^^^^^^^^^^^^^^^^^

The installation to NAND supports installing these components:

* IPL: The *Initial Program Loader*, or UBL in the case of the DM36x
* Bootloader: U-Boot
* Kernel
* Filesystem

Before anything, we have to setup the NAND memory map.

Creating the NAND Memory Map
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Take into account the following parameters for NAND memory in the DM36x Leopard
Board. You can obtain this information by issuing the `nand info` command
in U-Boot.

* NAND block size: 128Kb (131072 bytes, or 0x20000 in hex)

This is important as you will setup your memory map specifying how much NAND
blocks you want for each partition.

For each NAND partition you should specify (at least):

* `name`: a friendly name, like 'uboot'
* `start_blk`: the starting NAND block of the partition
* `size_blks`: the size in NAND blocks of the partition
* `image`: filename of the image to install

For example, take that you want to reproduce this memory map:
::
    +--------+-----------+-------------+
    | Name   | Start blk | Size (blks) |
    +--------+-----------+-------------+
    | ubl    |     1     |      1      |
    | uboot  |     25    |      3      |
    | kernel |     32    |      36     |
    | rootfs |     68    |     1600    |
    +--------+-----------+----------+---

A memory map file that implements the layout above, using the 
`ConfigParser <http://docs.python.org/2/library/configparser.html>`_ syntax:
::
    [ipl]
    name = ubl
    start_blk = 1
    size_blks = 1
    image = ~/images/nandbin
    
    [bootloader]
    name = uboot
    start_blk = 25
    size_blks = 3
    image = ~/images/bootloader.nandbin
    
    [kernel]
    name = kernel
    start_blk = 32
    size_blks = 36
    image = ~/images/kernel.uImage
    
    [fs]
    name = rootfs
    start_blk = 68
    size_blks = 1600
    image = ~/images/fsimage.uImage

Note that there is an intentional correspondence between the section names:
[ipl], [bootloader], [kernel], [fs] and the actual component that you want to
install. **These section names can't be changed**, but still you can name a
partition by it's friendly name (i.e. 'uboot').

In the case of the [ipl] section, for a DM368x we will install UBL ("User Boot
Loader"), in the [bootloader] section we will install U-Boot, and typically
you would install Linux in [kernel] and some filesystem in [fs] (like a `ubifs`
or `jffs2` filesystem).

Save your memory map to a file "nand-mmap.config", and we will supply the 
filename to the installer as a CLI argument.

.. hint:: There is a NAND partition for the "U-Boot environment". In the DM36x
  it typically starts at block 30 (see U-Boot's config variable
  `CONFIG_ENV_OFFSET`) and has a size of 2 blocks. Don't write on top of it.

.. note:: This documentation does not refer to the process of generating images
          for any component.

Calling the installer
~~~~~~~~~~~~~~~~~~~~~

At any time, you can query the supported/required arguments for the installer
using `-h` or :option:`--help`. The installer has positional arguments, so you
can use the help at different levels.
::
    installer.py -h
    installer.py nand -h
    installer.py nand ipl -h
    installer.py nand bootloader -h
    installer.py nand kernel -h
    installer.py nand fs -h
    installer.py nand cmdline -h
    installer.py nand bootcmd -h

General arguments
.................

The installer's general arguments are as follows:
::
    installer.py --help

* :option:`-y, --assume-yes`: Automatic 'yes' to prompts; runs non-interactively.
* :option:`-v, --verbose`: Verbose output (useful for debugging).
* :option:`-q, --quiet`: Quiet output (takes precedence over :option:`--verbose`:)
* :option:`--dryrun`: Sets the dryrun mode On (system and uboot commands will be
  logged, but not executed) 

NAND arguments
..............

For NAND installation, several general arguments are required.
::
    installer.py nand --help
    
* :option:`--mmap-file`: Path to the memory map file that we created in the
  `Creating the NAND Memory Map`_ section.
* :option:`--nand-blk-size`: The NAND block size (131072 for the DM36x).
* :option:`--nand-page-size`: The NAND page size (2048 for the DM36x).
* :option:`--ram-load-addr`: RAM address to load components (hex or decimal).
  Before writing an image to NAND, the installer will first transfer your image
  via TFTP to RAM. This address indicates where in RAM the images will be
  transferred to.
* :option:`--uboot-file`: (Optional) Path to a U-Boot file that can be loaded to
  RAM and drive the installation. Use this in case that you want the installer
  to communicate with a known U-Boot, which is different than the U-Boot
  currently installed in the board. If specified, the installer will first
  load this U-Boot to RAM, execute it, and then install any specified component.
  Note that this U-Boot image won't be written to NAND.

Serial port settings:

* :option:`--serial-port`: Device name or port number for serial communication
  (i.e. `/dev/ttyUSB0`)
* :option:`--serial-baud`: Baud rate for the serial port (default 115200).

Network settings:

* :option:`--host-ip-addr`: IP address of the host PC (usually `eth0` in your machine).
* :option:`--ttfp-dir`: TFTP server root directory in your host PC (default
  `/srv/tftp`).
* :option:`--tftp-port`: TFTP server port (default 69).

If your network does not support DHCP, you also have to manually specify your
board's IP:

* :option:`--board-net-mode`: Set to "`static`".
* :option:`--board-ip-addr`: The static IP address for your board. 

Example of the general arguments for NAND installation:
::
    $ python installer.py \
        nand \
        --mmap-file ~/images/nand-mmap.config \
        --serial-port /dev/ttyUSB0
        --ram-load-addr 0x82000000 \
        --host-ip-addr 10.251.101.24 \
        --tftp-dir /srv/tftp \
        --nand-blk-size 131072 \
        --nand-page-size 2048

.. warning:: This installer uses TFTP to transfer the images to the board. It has
  been experienced that such transfer is very slow when your host PC is
  connected to the network via WiFi, we recommend that you plug both your host
  PC and your board to the network via ethernet.

Per component arguments
.......................

Most of the components does not required any additional arguments, all the 
required information regarding components is provided by the
:option:`--mmap-file` (see `Creating the NAND Memory Map`_).

All components, except the bootloader, implement the :option:`--force` switch
that can be used to force the component installation. This is because after
installing the image to NAND the installer will save in uboot's environment
some variables that record the partition's `offset`, `size`, and `md5sum` to
avoid re-installing the component's image if it's not necessary.

This command installs the kernel partition to NAND:
::
    $ python installer.py \
        --verbose \
        nand \
        --mmap-file ~/images/nand-mmap.config \
        --serial-port /dev/ttyUSB0
        --ram-load-addr 0x82000000 \
        --host-ip-addr 10.251.101.24 \
        --tftp-dir /srv/tftp \
        --nand-blk-size 131072 \
        --nand-page-size 2048 \
        kernel \
        --force
