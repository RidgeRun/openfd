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
    
Help output:
::
    usage: installer.py [-h] -m <mode> -f <mmap> --kernel-file <kernel_file> [-y]
                        [-v] [-q] [--dryrun] [-d <device>] [--image <image>]
                        [--image-size <imagesize_mb>] [--uflash <uflash>]
                        [--ubl-file <ubl_file>] [--uboot-file <uboot_file>]
                        [--uboot-entry-addr <uboot_entry_addr>]
                        [--uboot-load-addr <uboot_load_addr>]
                        [--uboot-bootargs <uboot_bootargs>] [--work-dir <workdir>]
                        [--rootfs <rootfs>]
    
    optional arguments:
      -h, --help            show this help message and exit
      -m <mode>, --mode <mode>
                            Installation mode: sdloopback
      -f <mmap>, --mmap-config-file <mmap>
                            Memory map config file
      --kernel-file <kernel_file>
                            Path to the Kernel Image file to be installed.
      -y, --assume-yes      Automatic 'yes' to prompts; run non-interactively
      -v, --verbose         Enable debug
      -q, --quiet           Be as quiet as possible
      --dryrun              Sets the dryrun mode On (shell commands will be
                            logged, but not executed)
      -d <device>, --device <device>
                            Device to install
      --image <image>       The filename of the image to create in workdir
      --image-size <imagesize_mb>
                            Size in MB of the image file to create (integer
                            number)
      --uflash <uflash>     Path to the uflash tool
      --ubl-file <ubl_file>
                            Path to the UBL file
      --uboot-file <uboot_file>
                            Path to the U-Boot file
      --uboot-entry-addr <uboot_entry_addr>
                            U-Boot entry address (decimal)
      --uboot-load-addr <uboot_load_addr>
                            U-Boot load address (decimal)
      --uboot-bootargs <uboot_bootargs>
                            U-Boot bootargs environment variable (passed to the
                            Linux kernel)
      --work-dir <workdir>  Directory to perform temporary operations
      --rootfs <rootfs>     Path to the rootfs that will be installed.
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

from methods.board.nand import NandInstallerTFTP
from methods.board.image_gen import NandImageGenerator

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
_subparsers = None
_subparsers_nand = None
_logger  = None
_uboot = None

# ==========================================================================
# Constants
# ==========================================================================

# Modes
MODE_SD = 'sd'
MODE_SD_IMG = 'sd-img'
MODE_NAND = 'nand'
MODE_LOOPBACK = 'loopback'

# Components
COMP_IPL = "ipl"
COMP_BOOTLOADER = "bootloader"
COMP_KERNEL = "kernel"
COMP_FS = "fs"
COMP_CMDLINE = "cmdline"
COMP_BOOTCMD = "bootcmd"

# ==========================================================================
# Logging
# ==========================================================================

def _init_logging():

    global _logger

    _program_name = os.path.basename(sys.argv[0])
    
    rrutils.logger.basic_config(verbose=False)
    _logger = rrutils.logger.get_global_logger(_program_name,
                                               level=rrutils.logger.INFO)

# ==========================================================================
# Functions
# ==========================================================================

def _clean_exit(code=0):
    if uboot: uboot.close_comm()
    if code != 0: _logger.debug('Exiting with code %d' % code)
    exit(code)

def _abort_install():
    _logger.error('Installation aborted')
    _clean_exit(-1)

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
    
    _parser.add_argument('--dryrun',
                       help='Sets the dryrun mode On (shell commands will be '
                            'logged, but not executed)',
                       dest='dryrun',
                       action='store_true',
                       default=False)

def _add_args_shared(subparser):
    subparser.add_argument('--mmap-file',
                       help='Memory map config file',
                       metavar='<file>',
                       dest='mmap_file')

def _add_args_sd_shared(subparser):
    _add_args_shared(subparser)
    
    subparser.add_argument('--device',
                       help="Device to install",
                       metavar='<dev>',
                       dest='device',
                       required=True)
    
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
    _add_args_sd_shared(_parser_sd)

def _add_args_sd_img():
    global _parser_sd
    global _parser_sd_img
    _parser_sd_img = _subparsers.add_parser(MODE_SD_IMG)
    _add_args_sd_shared(_parser_sd_img)
    
    _parser_sd_img.add_argument('--image',
                       help="The filename of the image to create in workdir",
                       metavar='<file>',
                       dest='image')
    
    _parser_sd_img.add_argument('--image-size-mb',
                       help="Size in MB of the image file to create",
                       metavar='<size>',
                       dest='imagesize_mb')

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
    
    _parser_nand.add_argument('--serial-port',
                       help="Device name or port number for serial communica"
                       "tion with U-Boot (i.e. '/dev/ttyS0')",
                       metavar='<port>',
                       dest='serial_port',
                       required=True)
    
    _parser_nand.add_argument('--serial-baud',
                       help="Baud rate (default: 115200)",
                       metavar='<baud>',
                       dest='serial_baud',
                       default=115200)
    
    _parser_nand.add_argument('--ram-load-addr',
                       help='RAM address to load components (decimal or hex)',
                       metavar='<addr>',
                       dest='ram_load_addr',
                       required=True)
    
    net_modes = [NandInstallerTFTP.MODE_STATIC, NandInstallerTFTP.MODE_DHCP]
    
    _parser_nand.add_argument('--board-net-mode',
                       help="Networking mode: %s (default: dhcp)" %
                       ''.join('%s|' % mode for mode in net_modes).rstrip('|'),
                       metavar='<mode>',
                       choices=net_modes,
                       dest='board_net_mode',
                       default=NandInstallerTFTP.MODE_DHCP)

    _parser_nand.add_argument('--board-ip-addr',
                       help="Board IPv4 address (only required in --board-net-"
                       "mode=static)",
                       metavar='<addr>',
                       dest='board_ip_addr')
    
    _parser_nand.add_argument('--host-ip-addr',
                       help="Host IPv4 address",
                       metavar='<addr>',
                       dest='host_ip_addr',
                       required=True)

    _parser_nand.add_argument('--tftp-dir',
                       help="TFTP server root directory",
                       metavar='<dir>',
                       dest='tftp_dir',
                       required=True)

    _parser_nand.add_argument('--tftp-port',
                       help="TFTP server port (default: 69)",
                       metavar='<port>',
                       dest='tftp_port',
                       default=69)
    
    _add_args_nand_ipl()
    _add_args_nand_bootloader()
    _add_args_nand_kernel()
    _add_args_nand_fs()
    _add_args_nand_cmdline()
    _add_args_nand_bootcmd()

def _add_args_nand_ipl():
    global _parser_nand_ipl 
    _parser_nand_ipl = _subparsers_nand.add_parser(COMP_IPL,
                                           help="Initial Program Loader (UBL)")

def _add_args_nand_bootloader():
    global _parser_nand_bootloader 
    _parser_nand_bootloader = _subparsers_nand.add_parser(COMP_BOOTLOADER,
                                                  help="Bootloader (U-Boot)")

def _add_args_nand_kernel():
    global _parser_nand_kernel 
    _parser_nand_kernel = _subparsers_nand.add_parser(COMP_KERNEL,
                                                      help="Kernel")
     
    _parser_nand_kernel.add_argument('--kernel-file',
                       help='Path to the Kernel file to be installed',
                       metavar='<file>',
                       dest='kernel_file',
                       required=True)
    
    _parser_nand_kernel.add_argument('--kernel-start-blk',
                       help="Start block in NAND for the kernel image",
                       metavar='<blk>',
                       required=True,
                       dest='kernel_start_blk')
    
    _parser_nand_kernel.add_argument('--kernel-size-blks',
                       help=("Size in NAND blocks for the kernel partition, if "
                            "omitted the size will be calculated using the "
                            "size of the image and the extra blocks"),
                       metavar='<blks>',
                       dest='kernel_size_blks')
    
    _parser_nand_kernel.add_argument('--kernel-extra-blks',
                       help=("Extra NAND blocks to reserve for the kernel "
                             "partition (only makes sense when --kernel-"
                             "size-blks has not been specified) (default: 3)"),
                       metavar='<blks>',
                       dest='kernel_extra_blks',
                       default=3)
    
    _parser_nand_kernel.add_argument('--force',
                       help='Force component installation',
                       dest='kernel_force',
                       action='store_true',
                       default=False)

def _add_args_nand_fs():
    global _parser_nand_fs 
    _parser_nand_fs = _subparsers_nand.add_parser(COMP_FS,
                                                  help="Filesystem")
    
    _parser_nand_fs.add_argument('--fs-file',
                       help='Path to the Filesystem file to be installed',
                       metavar='<file>',
                       dest='fs_file',
                       required=True)
    
    _parser_nand_fs.add_argument('--fs-start-blk',
                       help="Start block in NAND for the filesystem image",
                       metavar='<blk>',
                       required=True,
                       dest='fs_start_blk')
    
    _parser_nand_fs.add_argument('--fs-size-blks',
                       help=("Size in NAND blocks for the filesystem "
                            "partition, if omitted the size will be calculated "
                            "using the size of the image and the extra blocks"),
                       metavar='<blks>',
                       dest='fs_size_blks')
    
    _parser_nand_fs.add_argument('--fs-extra-blks',
                       help=("Extra NAND blocks to reserve for the filesystem "
                             "partition (only makes sense when --fs-size-blks "
                             "has not been specified) (default: 19)"),
                       metavar='<blks>',
                       dest='fs_extra_blks',
                       default=19)
    
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

def _check_args():
    global _args
    _args = _parser.parse_args()
    if _args.verbose:
        _logger.setLevel(rrutils.logger.DEBUG)
    if _args.quiet: # quiet has precedence over verbose
        _logger.setLevel(rrutils.logger.CRITICAL)
    if _args.mode == MODE_SD:
        _check_args_sd()
    elif _args.mode == MODE_SD_IMG:
        _check_args_sd_img()
    elif _args.mode == MODE_NAND:
        _check_args_nand()
    
def _check_args_sd():    
    _check_is_file(_args.mmap_file, '--mmap-file')
    _check_is_file(_args.uflash_bin, '--uflash-bin')
    _check_x_ok(_args.uflash_bin, '--uflash-bin')
    _check_is_file(_args.ubl_file, '--ubl-file')
    _check_is_file(_args.uboot_file, '--uboot-file')
    _check_is_valid_addr(_args.uboot_entry_addr, '--uboot-entry-addr')
    _check_is_valid_addr(_args.uboot_load_addr, '--uboot-load-addr')
    _check_is_dir(_args.workdir, '--work-dir')
    _args.workdir = _args.workdir.rstrip('/') 
    if _args.rootfs:
        _check_is_dir(_args.rootfs, '--rootfs')
    
def _check_args_sd_img():
    _check_args_sd()
    _check_is_int(_args.imagesize_mb, '--image-size')
    _args.imagesize_mb = int(_args.imagesize_mb)

def _check_args_nand():
    if _args.nand_blk_size:
        _check_is_int(_args.nand_blk_size, '--nand-blk-size')
        _args.nand_blk_size = int(_args.nand_blk_size)
    if _args.nand_page_size:
        _check_is_int(_args.nand_page_size, '--nand-page-size')
        _args.nand_page_size = int(_args.nand_page_size)
    _check_is_valid_addr(_args.ram_load_addr, '--ram-load-addr')
    _check_is_dir(_args.tftp_dir, '--tftp-dir')
    _check_is_int(_args.tftp_port, '--tftp-port')
    _args.tftp_port = int(_args.tftp_port)
    _check_is_int(_args.serial_baud, '--serial-baud')
    _check_is_valid_ipv4(_args.host_ip_addr, '--host-ip-addr')
    if _args.board_net_mode == NandInstallerTFTP.MODE_STATIC:
        _check_is_valid_ipv4(_args.board_ip_addr, '--board-ip-addr')
    if _args.component == COMP_KERNEL:
        _check_args_nand_kernel()
    if _args.component == COMP_FS:
        _check_args_nand_fs()
    if _args.component == COMP_CMDLINE:
        _check_args_nand_cmdline()
    if _args.component == COMP_BOOTCMD:
        _check_args_nand_bootcmd()

def _check_args_nand_bootloader():
    _check_is_file(_args.bc_bin, '--bc-bin')
    _check_x_ok(_args.bc_bin, '--bc-bin')
    _check_is_file(_args.uboot_file, '--uboot-file')
    _check_is_int(_args.uboot_start_blk, '--uboot-start-blk')
    _check_is_valid_addr(_args.uboot_entry_addr, '--uboot-entry-addr')
    _check_is_valid_addr(_args.uboot_load_addr, '--uboot-load-addr')
    _args.uboot_start_blk = int(_args.uboot_start_blk)
    
def _check_args_nand_kernel():
    _check_is_file(_args.kernel_file, '--kernel-file')
    _check_is_int(_args.kernel_start_blk, '--kernel-start-blk')
    _args.kernel_start_blk = int(_args.kernel_start_blk)
    if _args.kernel_size_blks:
        _check_is_int(_args.kernel_size_blks, '--kernel-size-blks')
        _args.kernel_size_blks = int(_args.kernel_size_blks)
    if _args.kernel_extra_blks:
        _check_is_int(_args.kernel_extra_blks, '--kernel-extra-blks')
        _args.kernel_extra_blks = int(_args.kernel_extra_blks)

def _check_args_nand_fs():
    _check_is_file(_args.fs_file, '--fs-file')
    _check_is_int(_args.fs_start_blk, '--fs-start-blk')
    _args.fs_start_blk = int(_args.fs_start_blk)
    if _args.fs_size_blks:
        _check_is_int(_args.fs_size_blks, '--fs-size-blks')
        _args.fs_size_blks = int(_args.fs_size_blks)
    if _args.fs_extra_blks:
        _check_is_int(_args.fs_extra_blks, '--fs-extra-blks')
        _args.fs_extra_blks = int(_args.fs_extra_blks)

def _check_args_nand_cmdline():
    pass # nothing to check

def _check_args_nand_bootcmd():
    pass # nothing to check

# ==========================================================================
# Main logic
# ==========================================================================

def main():
    global uboot

    _init_logging()
    _add_args()
    _add_args_nand()
    _add_args_sd()
    _add_args_sd_img()
    _check_args()
    
    mode = _args.mode
    
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
            ret = sd_installer.format_loopdevice(_args.workdir +
                                                 _args.image, 
                                                 _args.imagesize_mb)
            if ret is False: _abort_install()
        
        ret = sd_installer.mount_partitions(_args.workdir)
        if ret is False: _abort_install()
        
        ret = sd_installer.install_components()
        if ret is False: _abort_install()
        
        ret = sd_installer.release_device()
        if ret is False: _abort_install()
        
    if mode == MODE_NAND:
        
        uboot = rrutils.uboot.Uboot()
        uboot.dryrun = _args.dryrun
        
        try:
            ret = uboot.open_comm(port=_args.serial_port, baud=_args.serial_baud)
            if ret is False: _abort_install()
        except serial.SerialException:
            _abort_install()
        
        ret = uboot.sync()
        if ret is False: _abort_install()
        
        nand_installer = NandInstallerTFTP(uboot=uboot)
        if _args.nand_blk_size:
            nand_installer.nand_block_size = _args.nand_blk_size
        if _args.nand_page_size:
            nand_installer.nand_page_size = _args.nand_page_size
        nand_installer.net_mode = _args.board_net_mode
        if _args.board_net_mode == NandInstallerTFTP.MODE_STATIC:
            nand_installer.target_ipaddr = _args.board_ip_addr
        nand_installer.host_ipaddr = _args.host_ip_addr
        nand_installer.tftp_dir = _args.tftp_dir
        nand_installer.tftp_port = _args.tftp_port
        nand_installer.ram_load_addr = _args.ram_load_addr
        nand_installer.dryrun = _args.dryrun
        nand_installer.read_partitions(_args.mmap_file)
        
        comp_requires_network = [COMP_IPL, COMP_BOOTLOADER, COMP_KERNEL, COMP_FS]
        if _args.component in comp_requires_network:
            ret = nand_installer.setup_uboot_network()
            if ret is False: _abort_install()
        
        if _args.component == COMP_IPL:
            ret = nand_installer.install_ubl()
            if ret is False: _abort_install()
        if _args.component == COMP_BOOTLOADER:
            ret = nand_installer.install_uboot()
            if ret is False: _abort_install()
            
        if _args.component == COMP_KERNEL:
            ret = nand_installer.install_kernel(_args.kernel_file,
                                      _args.kernel_start_blk, 
                                      _args.kernel_size_blks,
                                      _args.kernel_extra_blks,
                                      _args.kernel_force)
            if ret is False: _abort_install()

        if _args.component == COMP_FS:
            ret = nand_installer.install_fs(_args.fs_file,
                                      _args.fs_start_blk,
                                      _args.fs_size_blks,
                                      _args.fs_extra_blks,                                      
                                      _args.fs_force)
            if ret is False: _abort_install()

        if _args.component == COMP_CMDLINE:
            ret = nand_installer.install_cmdline(_args.cmdline,
                                                 _args.cmdline_force)
            if ret is False: _abort_install()
       
        if _args.component == COMP_BOOTCMD:
            ret = nand_installer.install_bootcmd(_args.bootcmd,
                                                 _args.bootcmd_force)
            if ret is False: _abort_install()
       
        try:
            _logger.info("Finishing installation")
            if _args.component in comp_requires_network:
                if uboot.get_env('autostart') == 'no':
                    uboot.set_env('autostart', 'yes')
                    uboot.save_env()
            uboot.cmd('echo Installation complete')
        except rrutils.uboot.UbootTimeoutException as e:
            _logger.error(e)
            _abort_install()
            
        uboot.close_comm()
        
    _logger.info('Installation complete')
    _clean_exit(0)
    
if __name__ == '__main__':
    main()
