#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#          Diego Benavides <diego.benavides@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# The installer tool objective is to provide several ways to deploy the
# firmware to the target board. 
#
# ==========================================================================

"""
The installer tool objective is to provide several ways to deploy the
firmware to the target board. Current methods are:

    - Attached board on communication port.
    - Deploy all the firmware to an SD card.
    - Create and SD card installer for flash memory.
    
Command Line Arguments
======================
    
Main help output:
::
    $ ./installer.py -h
    usage: installer.py [-h] [-y] [-v] [-q] [--dryrun] {nand,sd,sd-img} ...
    
    positional arguments:
      {nand,sd,sd-img}  installation mode (--help available)
    
    optional arguments:
      -h, --help        show this help message and exit
      -y, --assume-yes  Automatic 'yes' to prompts; runs non-interactively
      -v, --verbose     Enable debug
      -q, --quiet       Be as quiet as possible
      --dryrun          Sets the dryrun mode On (system and uboot commands will be
                        logged, but not executed)

NAND mode
---------

NAND mode output:
::
    $ ./installer.py nand -h
    usage: installer.py nand [-h] --mmap-file <file> [--nand-blk-size <size>]
                             [--nand-page-size <size>] --serial-port <port>
                             [--serial-baud <baud>] --ram-load-addr <addr>
                             [--uboot-file <file>] [--board-net-mode <mode>]
                             [--board-ip-addr <addr>] --host-ip-addr <addr>
                             --tftp-dir <dir> [--tftp-port <port>]
                             {ipl,bootloader,kernel,fs,cmdline,bootcmd} ...
    
    positional arguments:
      {ipl,bootloader,kernel,fs,cmdline,bootcmd}
                            component (--help available)
        ipl                 Initial Program Loader (UBL)
        bootloader          Bootloader (U-Boot)
        kernel              Kernel
        fs                  Filesystem
        cmdline             Kernel's command line
        bootcmd             U-Boots's bootcmd variable
    
    optional arguments:
      -h, --help            show this help message and exit
      --mmap-file <file>    Memory map config file
      --nand-blk-size <size>
                            NAND block size (bytes)
      --nand-page-size <size>
                            NAND page size (bytes)
      --serial-port <port>  Device name or port number for serial communication
                            with U-Boot (i.e. '/dev/ttyS0')
      --serial-baud <baud>  Baud rate (default: 115200)
      --ram-load-addr <addr>
                            RAM address to load components (decimal or hex)
      --uboot-file <file>   Path to a U-Boot file that can be loaded to RAM and
                            drive the installation
      --board-net-mode <mode>
                            Networking mode: static|dhcp (default: dhcp)
      --board-ip-addr <addr>
                            Board IPv4 address (only required in --board-net-
                            mode=static)
      --host-ip-addr <addr>
                            Host IPv4 address
      --tftp-dir <dir>      TFTP server root directory
      --tftp-port <port>    TFTP server port (default: 69)

NAND mode, IPL component:
::
    $ ./installer.py nand ipl -h
    usage: installer.py nand ipl [-h] [--force]
    
    optional arguments:
      -h, --help  show this help message and exit
      --force     Force component installation

NAND mode, bootloader component:
::
    $ ./installer.py nand bootloader -h
    usage: installer.py nand bootloader [-h]
    
    optional arguments:
      -h, --help  show this help message and exit

NAND mode, kernel component:
::
    $ ./installer.py nand kernel -h
    usage: installer.py nand kernel [-h] [--force]
    
    optional arguments:
      -h, --help  show this help message and exit
      --force     Force component installation

NAND mode, fs component:
::
    $ ./installer.py nand fs -h
    usage: installer.py nand fs [-h] [--force]
    
    optional arguments:
      -h, --help  show this help message and exit
      --force     Force component installation


NAND mode, cmdline component:
::
    $ ./installer.py nand cmdline -h
    usage: installer.py nand cmdline [-h] --cmdline <cmdline> [--gen-mtdparts]
                                     [--mtd-id <id>] [--force]
    
    optional arguments:
      -h, --help           show this help message and exit
      --cmdline <cmdline>  Kernel's command line
      --gen-mtdparts       Generates the mtdparts command line option
      --mtd-id <id>        Unique id used in mapping driver/device (number of
                           flash bank), only necessary when --gen-mtdparts
      --force              Force component installation

NAND mode, bootcmd component:
::
    $ ./installer.py nand bootcmd -h
    usage: installer.py nand bootcmd [-h] --bootcmd <bootcmd> [--force]
    
    optional arguments:
      -h, --help           show this help message and exit
      --bootcmd <bootcmd>  U-Boots's bootcmd variable
      --force              Force component installation

SD mode
-------

SD mode:
::
    $ ./installer.py sd -h
    usage: installer.py sd [-h] --mmap-file <file> --device <dev> --kernel-file
                           <file> --uflash-bin <file> --ubl-file <file>
                           --uboot-file <file> --uboot-entry-addr <addr>
                           --uboot-load-addr <addr> --uboot-bootargs <bootargs>
                           --work-dir <dir> [--rootfs <dir>]
    
    optional arguments:
      -h, --help            show this help message and exit
      --mmap-file <file>    Memory map config file
      --device <dev>        Device to install
      --kernel-file <file>  Path to the Kernel file to be installed.
      --uflash-bin <file>   Path to the uflash tool
      --ubl-file <file>     Path to the UBL file
      --uboot-file <file>   Path to the U-Boot file
      --uboot-entry-addr <addr>
                            U-Boot entry address (decimal or hex)
      --uboot-load-addr <addr>
                            U-Boot load address (decimal or hex)
      --uboot-bootargs <bootargs>
                            U-Boot bootargs environment variable (passed to" " the
                            Linux kernel)
      --work-dir <dir>      Directory to perform temporary operations
      --rootfs <dir>        Path to the rootfs that will be installed.
      
SD mode, create image file:
::
    $ ./installer.py sd-img -h
    usage: installer.py sd-img [-h] --mmap-file <file> --device <dev>
                               --kernel-file <file> --uflash-bin <file> --ubl-file
                               <file> --uboot-file <file> --uboot-entry-addr
                               <addr> --uboot-load-addr <addr> --uboot-bootargs
                               <bootargs> --work-dir <dir> [--rootfs <dir>]
                               [--image <file>] [--image-size-mb <size>]
    
    optional arguments:
      -h, --help            show this help message and exit
      --mmap-file <file>    Memory map config file
      --device <dev>        Device to install
      --kernel-file <file>  Path to the Kernel file to be installed.
      --uflash-bin <file>   Path to the uflash tool
      --ubl-file <file>     Path to the UBL file
      --uboot-file <file>   Path to the U-Boot file
      --uboot-entry-addr <addr>
                            U-Boot entry address (decimal or hex)
      --uboot-load-addr <addr>
                            U-Boot load address (decimal or hex)
      --uboot-bootargs <bootargs>
                            U-Boot bootargs environment variable (passed to" " the
                            Linux kernel)
      --work-dir <dir>      Directory to perform temporary operations
      --rootfs <dir>        Path to the rootfs that will be installed.
      --image <file>        The filename of the image to create in workdir
      --image-size-mb <size>
                            Size in MB of the image file to create
"""

# ==========================================================================
# Imports
# ==========================================================================

import os
import sys
import rrutils
import methods
import argparse
import socket
import serial
import signal
import logging

from rrutils import Uboot
from rrutils import UbootTimeoutException
from methods.board.nand import NandInstaller
from methods.board.ram import TftpRamLoader
from methods.board.ram import RamLoaderException

# ==========================================================================
# Global variables
# ==========================================================================

_args = []
_parser = None
_parser_sd = None
_parser_sd_img = None
_parser_nand = None
_parser_nand_ipl = None
_parser_nand_bootloader = None
_parser_nand_kernel = None
_parser_nand_fs = None
_parser_nand_cmdline = None
_parser_nand_bootcmd = None
_parser_nand_mtdparts = None
_parser_ram = None
_subparsers = None
_subparsers_nand = None
_logger  = None
_executer  = None
_uboot = None

# ==========================================================================
# Constants
# ==========================================================================

# Modes
MODE_SD = 'sd'
MODE_SD_IMG = 'sd-img'
MODE_NAND = 'nand'
MODE_RAM = 'ram'

# Components
COMP_IPL = "ipl"
COMP_BOOTLOADER = "bootloader"
COMP_KERNEL = "kernel"
COMP_FS = "fs"
COMP_CMDLINE = "cmdline"
COMP_BOOTCMD = "bootcmd"
COMP_MTDPARTS = "mtdparts"

# ==========================================================================
# Functions
# ==========================================================================

def _init_logging():
    global _logger
    _program_name = os.path.basename(sys.argv[0])
    _logger = rrutils.logger.get_global_logger(_program_name)
    _logger.setLevel(logging.DEBUG)
    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(logging.Formatter('%(msg)s'))
    if _args.verbose:
        streamhandler.setLevel(logging.DEBUG)
    else:
        streamhandler.setLevel(logging.INFO)
    if _args.quiet:
        streamhandler.setLevel(logging.CRITICAL)
    _logger.addHandler(streamhandler)
    if _args.log_filename:
        filehandler = logging.FileHandler(_args.log_filename, mode='w')
        filehandler.setLevel(logging.DEBUG)
        if _args.verbose:
            filehandler.setFormatter(logging.Formatter('%(levelname)s:'
                                           '%(filename)s:%(lineno)s: %(msg)s'))
        else:
            filehandler.setFormatter(logging.Formatter('%(msg)s'))
        _logger.addHandler(filehandler)

def _init_executer():
    global _executer
    _executer = rrutils.executer.get_global_executer(logger=_logger,
                 dryrun=_args.dryrun, enable_colors=True, verbose=_args.verbose)

def _clean_exit(code=0):
    if _uboot: _uboot.close_comm()
    if code != 0: _logger.debug('Exiting with code %d' % code)
    exit(code)

def _abort_install():
    _logger.error('Installation aborted')
    _clean_exit(-1)

def _sigint_handler(signal, frame):
    _logger.error('\nInstallation interrupted')
    _clean_exit(0)

def _check_is_dir(dirname, arg):
    if not os.path.isdir(dirname):
        _logger.error('Unable to find %s: %s' % (arg, dirname))
        _abort_install()

def _check_is_file(filename, arg):
    if not os.path.isfile(filename):
        _logger.error('Unable to find %s: %s' % (arg, filename))
        _abort_install()

def _check_x_ok(filename, arg):
    if not os.access(filename, os.X_OK):
        _logger.error('No execution permissions on %s: %s' % (arg, filename))
        _abort_install()

def _check_is_int(val, arg):
    try:
        int(val)
    except ValueError:
        _logger.error('%s must be an integer (%s)' % (arg, val))
        _abort_install()

def _check_is_valid_addr(addr, arg):
    if not rrutils.hexutils.is_valid_addr(addr):
        _logger.error('Invalid address on %s: %s' % (arg, addr))
        _abort_install()

def _check_is_valid_ipv4(ip, arg):
    try:
        socket.inet_aton(ip)
    except socket.error:
        _logger.error('Invalid IP address on %s: %s' % (arg, ip))
        _abort_install()

# ==========================================================================
# Command line arguments
# ==========================================================================

def _missing_arg_exit(arg):
    _parser.print_help()
    _logger.error('Argument %s is required' % arg)
    _clean_exit(-1)
    
def _add_args():
    global _args
    global _parser
    global _subparsers
    _parser = argparse.ArgumentParser()
    _subparsers = _parser.add_subparsers(help="installation mode (--help available)",
                                         dest="mode")
    
    _parser.add_argument('-y', '--assume-yes',
                       help='Automatic \'yes\' to prompts; '
                       'runs non-interactively',
                       dest='interactive',
                       action='store_false',
                       default=True)
    
    _parser.add_argument('-v', '--verbose',
                       help='Enable debug',
                       dest='verbose',
                       action='store_true',
                       default=False)
    
    _parser.add_argument('-q', '--quiet',
                       help='Be as quiet as possible',
                       dest='quiet',
                       action='store_true',
                       default=False)
    
    _parser.add_argument('-l', '--log',
                       help="Log to file",
                       metavar='<file>',
                       dest='log_filename')
    
    _parser.add_argument('--dryrun',
                       help='Sets the dryrun mode On (system and uboot '
                            'commands will be logged, but not executed)',
                       dest='dryrun',
                       action='store_true',
                       default=False)

def _add_args_shared(subparser):
    subparser.add_argument('--mmap-file',
                       help='Memory map config file',
                       metavar='<file>',
                       dest='mmap_file',
                       required=True)

def _add_args_sd_shared(subparser):
    _add_args_shared(subparser)

    subparser.add_argument('--kernel-file',
                       help='Path to the Kernel file to be installed.',
                       metavar='<file>',
                       dest='kernel_file',
                       required=True)
    
    subparser.add_argument('--uflash-bin',
                       help='Path to the uflash tool',
                       metavar='<file>',
                       dest='uflash_bin',
                       required=True)
    
    subparser.add_argument('--ubl-file',
                       help='Path to the UBL file',
                       metavar='<file>',
                       dest='ubl_file',
                       required=True)
    
    subparser.add_argument('--uboot-file',
                       help='Path to the U-Boot file',
                       metavar='<file>',
                       dest='uboot_file',
                       required=True)
    
    subparser.add_argument('--uboot-entry-addr',
                       help='U-Boot entry address (decimal or hex)',
                       metavar='<addr>',
                       dest='uboot_entry_addr',
                       required=True)
    
    subparser.add_argument('--uboot-load-addr',
                       help='U-Boot load address (decimal or hex)',
                       metavar='<addr>',
                       dest='uboot_load_addr',
                       required=True)
    
    subparser.add_argument('--uboot-bootargs',
                       help='U-Boot bootargs environment variable (passed to" \
                       " the Linux kernel)',
                       metavar='<bootargs>',
                       dest='uboot_bootargs',
                       required=True)
    
    subparser.add_argument('--work-dir',
                       help='Directory to perform temporary operations',
                       metavar='<dir>',
                       dest='workdir',
                       required=True)
    
    subparser.add_argument('--rootfs',
                       help='Path to the rootfs that will be installed.',
                       metavar='<dir>',
                       dest='rootfs',
                       default=None)
    
def _add_args_sd():
    global _parser_sd
    _parser_sd = _subparsers.add_parser(MODE_SD)
    
    _parser_sd.add_argument('--device',
                   help="Device to install",
                   metavar='<dev>',
                   dest='device',
                   required=True)
    
    _add_args_sd_shared(_parser_sd)

def _add_args_sd_img():
    global _parser_sd
    global _parser_sd_img
    _parser_sd_img = _subparsers.add_parser(MODE_SD_IMG)
    _add_args_sd_shared(_parser_sd_img)
    
    _parser_sd_img.add_argument('--image',
                       help="Filename of the SD card image to create",
                       metavar='<file>',
                       dest='image',
                       required=True)
    
    _parser_sd_img.add_argument('--image-size-mb',
                       help="Size in MB of the SD card image file to create",
                       metavar='<size>',
                       dest='imagesize_mb',
                       required=True)

def _add_args_serial_shared(subparser):
    
    subparser.add_argument('--serial-port',
                       help="Device name or port number for serial communica"
                       "tion with U-Boot (i.e. '/dev/ttyS0')",
                       metavar='<port>',
                       dest='serial_port',
                       required=True)
    
    subparser.add_argument('--serial-baud',
                       help="Baud rate (default: 115200)",
                       metavar='<baud>',
                       dest='serial_baud',
                       default=115200)

def _add_args_tftp_shared(subparser):
      
    net_modes = [TftpRamLoader.MODE_STATIC, TftpRamLoader.MODE_DHCP]
    
    subparser.add_argument('--board-net-mode',
                       help="Networking mode: %s (default: dhcp)" %
                       ''.join('%s|' % mode for mode in net_modes).rstrip('|'),
                       metavar='<mode>',
                       choices=net_modes,
                       dest='board_net_mode',
                       default=TftpRamLoader.MODE_DHCP)

    subparser.add_argument('--board-ip-addr',
                       help="Board IPv4 address (only required in --board-net-"
                       "mode=static)",
                       metavar='<addr>',
                       dest='board_ip_addr')
    
    subparser.add_argument('--host-ip-addr',
                       help="Host IPv4 address",
                       metavar='<addr>',
                       dest='host_ip_addr',
                       required=True)

    subparser.add_argument('--tftp-dir',
                       help="TFTP server root directory",
                       metavar='<dir>',
                       dest='tftp_dir',
                       required=True)

    subparser.add_argument('--tftp-port',
                       help="TFTP server port (default: 69)",
                       metavar='<port>',
                       dest='tftp_port',
                       default=69)

def _add_args_nand():
    global _parser_nand
    global _subparsers_nand
    _parser_nand = _subparsers.add_parser(MODE_NAND)
    
    _subparsers_nand = _parser_nand.add_subparsers(help="component (--help available)",
                                                    dest="component")
    
    _add_args_shared(_parser_nand)
    
    _parser_nand.add_argument('--nand-blk-size',
                       help="NAND block size (bytes)",
                       metavar='<size>',
                       dest='nand_blk_size')
    
    _parser_nand.add_argument('--nand-page-size',
                       help="NAND page size (bytes)",
                       metavar='<size>',
                       dest='nand_page_size')
    
    _add_args_serial_shared(_parser_nand)
    
    _parser_nand.add_argument('--ram-load-addr',
                       help='RAM address to load components (decimal or hex)',
                       metavar='<addr>',
                       dest='ram_load_addr',
                       required=True)
    
    _parser_nand.add_argument('--uboot-file',
                       help='Path to a U-Boot file that can be loaded to RAM '
                       'and drive the installation',
                       metavar='<file>',
                       dest='nand_uboot_file')
  
    _add_args_tftp_shared(_parser_nand)
    _add_args_nand_ipl()
    _add_args_nand_bootloader()
    _add_args_nand_kernel()
    _add_args_nand_fs()
    _add_args_nand_cmdline()
    _add_args_nand_bootcmd()
    _add_args_nand_mtdparts()

def _add_args_nand_ipl():
    global _parser_nand_ipl 
    _parser_nand_ipl = _subparsers_nand.add_parser(COMP_IPL,
                                           help="Initial Program Loader (UBL)")
    
    _parser_nand_ipl.add_argument('--force',
                       help='Force component installation',
                       dest='ipl_force',
                       action='store_true',
                       default=False)

def _add_args_nand_bootloader():
    global _parser_nand_bootloader 
    _parser_nand_bootloader = _subparsers_nand.add_parser(COMP_BOOTLOADER,
                                                  help="Bootloader (U-Boot)")

def _add_args_nand_kernel():
    global _parser_nand_kernel 
    _parser_nand_kernel = _subparsers_nand.add_parser(COMP_KERNEL,
                                                      help="Kernel")
    
    _parser_nand_kernel.add_argument('--force',
                       help='Force component installation',
                       dest='kernel_force',
                       action='store_true',
                       default=False)

def _add_args_nand_fs():
    global _parser_nand_fs 
    _parser_nand_fs = _subparsers_nand.add_parser(COMP_FS,
                                                  help="Filesystem")
    
    _parser_nand_fs.add_argument('--force',
                       help='Force component installation',
                       dest='fs_force',
                       action='store_true',
                       default=False)

def _add_args_nand_cmdline():
    global _parser_nand_cmdline 
    _parser_nand_cmdline = _subparsers_nand.add_parser(COMP_CMDLINE,
                                                  help="Kernel's command line")
    
    _parser_nand_cmdline.add_argument('--cmdline',
                       help="Kernel's command line",
                       metavar='<cmdline>',
                       dest='cmdline',
                       required=True)
    
    _parser_nand_cmdline.add_argument('--force',
                       help='Force component installation',
                       dest='cmdline_force',
                       action='store_true',
                       default=False)

def _add_args_nand_bootcmd():
    global _parser_nand_bootcmd 
    _parser_nand_bootcmd = _subparsers_nand.add_parser(COMP_BOOTCMD,
                                          help="U-Boots's bootcmd variable")
    
    _parser_nand_bootcmd.add_argument('--bootcmd',
                       help="U-Boots's bootcmd variable",
                       metavar='<bootcmd>',
                       dest='bootcmd',
                       required=True)
    
    _parser_nand_bootcmd.add_argument('--force',
                       help='Force component installation',
                       dest='bootcmd_force',
                       action='store_true',
                       default=False)

def _add_args_nand_mtdparts():
    global _parser_nand_mtdparts 
    _parser_nand_mtdparts = _subparsers_nand.add_parser(COMP_MTDPARTS,
                                          help="U-Boots's mtdparts variable")
    
    _parser_nand_mtdparts.add_argument('--mtdparts',
                       help="U-Boots's mtdparts variable",
                       metavar='<mtdparts>',
                       dest='mtdparts',
                       required=True)
    
    _parser_nand_mtdparts.add_argument('--force',
                       help='Force component installation',
                       dest='mtdparts_force',
                       action='store_true',
                       default=False)

def _add_args_ram():
    global _parser_ram
    _parser_ram = _subparsers.add_parser(MODE_RAM)

    _parser_ram.add_argument('--ram-file',
                       help='Path to the file to load in RAM (at --ram-load-addr)',
                       metavar='<file>',
                       dest='ram_file',
                       required=True)

    _parser_ram.add_argument('--ram-load-addr',
                       help='RAM address to load the file (decimal or hex)',
                       metavar='<addr>',
                       dest='ram_load_addr',
                       required=True)
   
    _add_args_serial_shared(_parser_ram)
    _add_args_tftp_shared(_parser_ram)
    
def _check_args():
    if _args.mode == MODE_SD:
        _check_args_sd()
    elif _args.mode == MODE_SD_IMG:
        _check_args_sd_img()
    elif _args.mode == MODE_NAND:
        _check_args_nand()
    elif _args.mode == MODE_RAM:
        _check_args_ram()
    
def _check_args_sd():    
    _check_is_file(_args.mmap_file, '--mmap-file')
    _check_is_file(_args.uflash_bin, '--uflash-bin')
    _check_x_ok(_args.uflash_bin, '--uflash-bin')
    _check_is_file(_args.ubl_file, '--ubl-file')
    _check_is_file(_args.uboot_file, '--uboot-file')
    _check_is_file(_args.kernel_file, '--kernel-file')
    _check_is_valid_addr(_args.uboot_entry_addr, '--uboot-entry-addr')
    _check_is_valid_addr(_args.uboot_load_addr, '--uboot-load-addr')
    _check_is_dir(_args.workdir, '--work-dir')
    if _args.rootfs:
        _check_is_dir(_args.rootfs, '--rootfs')
    _args.workdir = _args.workdir.rstrip('/') 
    if _args.rootfs:
        _check_is_dir(_args.rootfs, '--rootfs')
    
def _check_args_sd_img():
    _check_args_sd()
    _check_is_int(_args.imagesize_mb, '--image-size-mb')
    _args.imagesize_mb = int(_args.imagesize_mb)

def _check_args_serial():
    _check_is_int(_args.serial_baud, '--serial-baud')

def _check_args_tftp():
    _check_is_dir(_args.tftp_dir, '--tftp-dir')
    _check_is_int(_args.tftp_port, '--tftp-port')
    _args.tftp_port = int(_args.tftp_port)
    _check_is_valid_ipv4(_args.host_ip_addr, '--host-ip-addr')
    if _args.board_net_mode == TftpRamLoader.MODE_STATIC:
        _check_is_valid_ipv4(_args.board_ip_addr, '--board-ip-addr')

def _check_args_nand():
    if _args.nand_blk_size:
        _check_is_int(_args.nand_blk_size, '--nand-blk-size')
        _args.nand_blk_size = int(_args.nand_blk_size)
    if _args.nand_page_size:
        _check_is_int(_args.nand_page_size, '--nand-page-size')
        _args.nand_page_size = int(_args.nand_page_size)
    if _args.nand_uboot_file:
        _check_is_file(_args.nand_uboot_file, '--uboot-file')
    _check_is_valid_addr(_args.ram_load_addr, '--ram-load-addr')
    _check_args_serial()
    _check_args_tftp()
    if _args.component == COMP_IPL:
        _check_args_nand_ipl()
    if _args.component == COMP_BOOTLOADER:
        _check_args_nand_bootloader()
    if _args.component == COMP_KERNEL:
        _check_args_nand_kernel()
    if _args.component == COMP_FS:
        _check_args_nand_fs()
    if _args.component == COMP_CMDLINE:
        _check_args_nand_cmdline()
    if _args.component == COMP_BOOTCMD:
        _check_args_nand_bootcmd()
    if _args.component == COMP_MTDPARTS:
        _check_args_nand_mtdparts()

def _check_args_nand_ipl():
    pass
    
def _check_args_nand_bootloader():
    pass
    
def _check_args_nand_kernel():
    pass

def _check_args_nand_fs():
    pass

def _check_args_nand_cmdline():
    pass

def _check_args_nand_bootcmd():
    pass

def _check_args_nand_mtdparts():
    pass

def _check_args_ram():
    _check_is_file(_args.ram_file, '--ram-file')
    _check_is_valid_addr(_args.ram_load_addr, '--ram-load-addr')
    _check_args_serial()
    _check_args_tftp()

def _check_sudo():
    ret = _executer.prompt_sudo()
    if ret != 0:
        _logger.error("Failed obtaining superuser access via sudo")
        _clean_exit(-1)

# ==========================================================================
# Main logic
# ==========================================================================

def main():
    global _uboot
    global _args
    signal.signal(signal.SIGINT, _sigint_handler)
    signal.signal(signal.SIGTERM, _sigint_handler)
    _add_args()
    _add_args_nand()
    _add_args_sd()
    _add_args_sd_img()
    _add_args_ram()
    _args = _parser.parse_args()
    _init_logging()
    _init_executer()
    _check_args()
    
    mode = _args.mode
    
    mode_requires_sudo = [MODE_SD, MODE_SD_IMG]
    if mode in mode_requires_sudo:
        _check_sudo() 
    
    if mode == MODE_SD or mode == MODE_SD_IMG:
        
        # Components installer
        
        comp_installer = methods.sdcard.ComponentInstaller()
        comp_installer.uflash_bin = _args.uflash_bin
        comp_installer.ubl_file =_args.ubl_file
        comp_installer.uboot_file = _args.uboot_file
        comp_installer.uboot_entry_addr = _args.uboot_entry_addr
        comp_installer.uboot_load_addr = _args.uboot_load_addr
        comp_installer.bootargs = _args.uboot_bootargs
        comp_installer.kernel_image = _args.kernel_file
        comp_installer.rootfs = _args.rootfs
        comp_installer.workdir = _args.workdir
        
        # SDCard installer
    
        sd_installer = methods.sdcard.SDCardInstaller(comp_installer)
        sd_installer.interactive = _args.interactive
        sd_installer.dryrun = _args.dryrun
        
        ret = sd_installer.read_partitions(_args.mmap_file)
        if ret is False: _abort_install()
        
        # Operations
        
        if mode == MODE_SD:
            sd_installer.device = _args.device
            sd_installer.mode = sd_installer.MODE_SD
            ret = sd_installer.format_sd()
            if ret is False: _abort_install()
        elif mode == MODE_SD_IMG:
            sd_installer.mode = sd_installer.MODE_LOOPBACK
            ret = sd_installer.format_loopdevice(_args.image, 
                                                 _args.imagesize_mb)
            if ret is False: _abort_install()
        
        ret = sd_installer.mount_partitions(_args.workdir)
        if ret is False: _abort_install()
        
        ret = sd_installer.install_components()
        if ret is False: _abort_install()
        
        ret = sd_installer.release_device()
        if ret is False: _abort_install()
        
    if mode == MODE_NAND or mode == MODE_RAM:
        
        _uboot = Uboot()
        _uboot.serial_logger = _logger
        _uboot.dryrun = _args.dryrun
        
        try:
            ret = _uboot.open_comm(port=_args.serial_port, baud=_args.serial_baud)
            if ret is False: _abort_install()
        except serial.SerialException:
            _abort_install()
        
        try:
            ret = _uboot.sync()
            if ret is False: _abort_install()
            
            tftp_loader = TftpRamLoader(_uboot, _args.board_net_mode)
            tftp_loader.dir = _args.tftp_dir
            tftp_loader.port = _args.tftp_port
            tftp_loader.host_ipaddr = _args.host_ip_addr
            tftp_loader.net_mode = _args.board_net_mode
            if _args.board_net_mode == TftpRamLoader.MODE_STATIC:
                tftp_loader.board_ipaddr = _args.board_ip_addr
            tftp_loader.dryrun = _args.dryrun
            
            if mode == MODE_NAND:
                
                comp_requires_network = [COMP_IPL, COMP_BOOTLOADER, COMP_KERNEL,
                                     COMP_FS]
            
                if _args.component in comp_requires_network:
                    tftp_loader.setup_uboot_network()
            
                nand_installer = NandInstaller(uboot=_uboot, loader=tftp_loader)
                if _args.nand_blk_size:
                    nand_installer.nand_block_size = _args.nand_blk_size
                if _args.nand_page_size:
                    nand_installer.nand_page_size = _args.nand_page_size
                nand_installer.ram_load_addr = _args.ram_load_addr
                nand_installer.dryrun = _args.dryrun
                nand_installer.read_partitions(_args.mmap_file)
                
                if _args.nand_uboot_file:
                    ret = nand_installer.load_uboot_to_ram(_args.nand_uboot_file,
                                                           _args.ram_load_addr)
                    if ret is False: _abort_install()
                
                if _args.component == COMP_IPL:
                    ret = nand_installer.install_ipl(force=_args.ipl_force)
                    if ret is False: _abort_install()
                    
                if _args.component == COMP_BOOTLOADER:
                    ret = nand_installer.install_bootloader()
                    if ret is False: _abort_install()
                    
                if _args.component == COMP_KERNEL:
                    ret = nand_installer.install_kernel(force=_args.kernel_force)
                    if ret is False: _abort_install()
        
                if _args.component == COMP_FS:
                    ret = nand_installer.install_fs(force=_args.fs_force)
                    if ret is False: _abort_install()
        
                if _args.component == COMP_CMDLINE:
                    ret = nand_installer.install_cmdline(_args.cmdline,
                                                         _args.cmdline_force)
                    if ret is False: _abort_install()
               
                if _args.component == COMP_BOOTCMD:
                    ret = nand_installer.install_bootcmd(_args.bootcmd,
                                                         _args.bootcmd_force)
                    if ret is False: _abort_install()
                    
                if _args.component == COMP_MTDPARTS:
                    ret = nand_installer.install_mtdparts(_args.mtdparts,
                                                          _args.mtdparts_force)
                    if ret is False: _abort_install()
            
                _logger.debug("Finishing installation")
                if _args.component in comp_requires_network:
                    if _uboot.get_env('autostart') == 'no':
                        _uboot.set_env('autostart', 'yes')
                        _uboot.save_env()
                        
                _uboot.cmd('echo Installation complete', prompt_timeout=None)
                        
            if mode == MODE_RAM:
                tftp_loader.setup_uboot_network()
                _logger.info("Loading %s to RAM address %s" %
                             (_args.ram_file, _args.ram_load_addr))
                boot_line = "Please press Enter to activate this console"
                tftp_loader.load_file_to_ram_and_boot(_args.ram_file,
                                  _args.ram_load_addr, boot_line, boot_time=60)
            
        except (UbootTimeoutException, RamLoaderException) as e:
            _logger.error(e)
            _abort_install()
            
        _uboot.close_comm()
        
    _logger.info('Installation complete')
    _clean_exit(0)
    
if __name__ == '__main__':
    main()
