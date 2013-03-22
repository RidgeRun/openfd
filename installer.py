#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
# Author: Diego Benavides <diego.benavides@ridgerun.com>
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

Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
All Rights Reserved.

The contents of this software are proprietary and confidential to RidgeRun,
LLC.  No part of this program may be photocopied, reproduced or translated
into another programming language without prior written consent of 
RidgeRun, LLC.
"""

# ==========================================================================
# Imports
# ==========================================================================

import os
import sys
import rrutils
import methods

# ==========================================================================
# Global variables
# ==========================================================================

_options = []
_parser  = rrutils.Parser()
_logger  = None

# Constants

MODE_SD = 'sd'

# ==========================================================================
# Logging
# ==========================================================================

_program_name = os.path.basename(sys.argv[0])

rrutils.logger.basic_config(verbose=True)
_logger = rrutils.logger.get_global_logger(_program_name,
                                           level=rrutils.logger.INFO)

# ==========================================================================
# Functions
# ==========================================================================

def _clean_exit(code=0):
    """
    Closes open resources and exits.
    """
    
    if code == 0:
        pass
    else:
        _logger.error('Exiting with code ' + str(code)) 

    exit(code)

def _missing_arg_exit(arg):
    """
    Prints message indicating arg is required, prints help and exit.
    """
    
    _parser.print_help()
    _logger.error('argument ' + arg + ' is required')
    _clean_exit(-1)

def _abort_install():
    """
    Prints abort message, closes open resources and exits.
    """
    
    _logger.error('Installation aborted')
    _clean_exit(-1)
   
# ==========================================================================
# Command line arguments
# ==========================================================================

# Required arguments

installation_modes = MODE_SD

_parser.add_option('-m', '--mode',
                   help="Installation mode: %s" % installation_modes,
                   metavar='<mode>',
                   dest='installation_mode',
                   required=True,
                   choices=[MODE_SD])

_parser.add_option('-f', '--mmap-config-file',
                   help="Memory map config file",
                   metavar='<mmap>',
                   dest='mmap_file',
                   required=True)

_parser.add_option('--kernel-file',
                   help="Path to the Kernel Image file to be installed.",
                   metavar='<kernel_file>',
                   dest='kernel_file',
                   required=True)

# Optional arguments

_parser.add_option('-y', '--assume-yes',
                   help="Automatic 'yes' to prompts; run non-interactively",
                   dest='interactive',
                   action='store_false',
                   default=True)

_parser.add_option('-v', '--verbose',
                   help="Enable debug",
                   dest="verbose",
                   action='store_true',
                   default=False)

_parser.add_option('-q', '--quiet',
                   help="Be as quiet as possible",
                   dest="quiet",
                   action='store_true',
                   default=False)

_parser.add_option('--dryrun',
                   help="Sets the dryrun mode On (shell commands will be " \
                        "logged, but not executed)",
                   dest='dryrun',
                   action='store_true',
                   default=False)

# MODE_SD - Required arguments

_parser.add_option('-d', '--device',
                   help="Device to install",
                   metavar='<device>',
                   dest='device')

_parser.add_option('--uflash',
                   help="Path to the uflash tool",
                   metavar='<uflash>',
                   dest='uflash_bin')

_parser.add_option('--ubl-file',
                   help="Path to the UBL file",
                   metavar='<ubl_file>',
                   dest='ubl_file')

_parser.add_option('--uboot-file',
                   help="Path to the U-Boot file",
                   metavar='<uboot_file>',
                   dest='uboot_file')

_parser.add_option('--uboot-entry-addr',
                   help="U-Boot entry address (decimal)",
                   metavar='<uboot_entry_addr>',
                   dest='uboot_entry_addr')

_parser.add_option('--uboot-load-addr',
                   help="U-Boot load address (decimal)",
                   metavar='<uboot_load_addr>',
                   dest='uboot_load_addr')

_parser.add_option('--uboot-bootargs',
                   help="U-Boot bootargs environment variable (passed to the Linux kernel)",
                   metavar='<uboot_bootargs>',
                   dest='uboot_bootargs')

_parser.add_option('--workdir',
                   help="On " + MODE_SD + " mode, sets the work directory",
                   metavar='<workdir>',
                   dest='workdir')

# MODE_SD - Optional arguments

_parser.add_option('--rootfs',
                   help="Path to the rootfs that will be installed.",
                   metavar='<rootfs>',
                   dest='rootfs',
                   default=None)

_options = _parser.get_options()

# Check verbose

if _options.verbose:
    _logger.setLevel(rrutils.logger.DEBUG)

# Check quiet (takes precedence over verbose)

if _options.quiet:
    _logger.setLevel(rrutils.logger.CRITICAL)

# Check mmap file

if not os.path.isfile(_options.mmap_file):
    _logger.error('Unable to find %s.' % _options.mmap_file)
    _clean_exit(-1)

# Check MODE_SD required arguments

if _options.installation_mode == MODE_SD:
    
    if not _options.device:
        _missing_arg_exit('-d/--device')
        
    if not _options.uflash_bin:
        _missing_arg_exit('--uflash')
    else:
        if not os.path.isfile(_options.uflash_bin):
            _logger.error('Unable to find %s' % _options.uflash_bin)
            _clean_exit(-1)
        elif not os.access(_options.uflash_bin, os.X_OK):
            _logger.error('No execute permissions on %s' % _options.uflash_bin)
            _clean_exit(-1)
        
    if not _options.ubl_file:
        _missing_arg_exit('--ubl-file')
    else:
        if not os.path.isfile(_options.ubl_file):
            _logger.error('Unable to find %s' % _options.ubl_file)
            _clean_exit(-1)
        
    if not _options.uboot_file:
        _missing_arg_exit('--uboot-file')
    else:
        if not os.path.isfile(_options.uboot_file):
            _logger.error('Unable to find %s' % _options.uboot_file)
            _clean_exit(-1)
        
    if not _options.uboot_entry_addr:
        _missing_arg_exit('--uboot-entry-addr')
    
    if not _options.uboot_load_addr:
        _missing_arg_exit('--uboot-load-addr')
        
    if not _options.uboot_bootargs:
        _missing_arg_exit('--uboot-bootargs')
    
    if not _options.workdir:
        _missing_arg_exit('--workdir')
    else:
        if not os.path.isdir(_options.workdir):
            _logger.error('Unable to find %s' % _options.workdir)
            _clean_exit(-1)

# Check MODE_SD optional arguments

    if _options.rootfs:
        if not os.path.isdir(_options.rootfs):
            _logger.error('Unable to find %s' % _options.rootfs)
            _clean_exit(-1)
        
# Clean the device string

_options.device = _options.device.rstrip('/')

# ==========================================================================
# Main logic
# ==========================================================================

if _options.installation_mode == MODE_SD:
    
    # Bootloader installer
    
    bl_installer = methods.sdcard.BootloaderInstaller()
    bl_installer.set_dryrun(_options.dryrun)
    bl_installer.set_uflash_bin(_options.uflash_bin)
    bl_installer.set_ubl_file(_options.ubl_file)
    bl_installer.set_uboot_file(_options.uboot_file)
    bl_installer.set_uboot_entry_addr(_options.uboot_entry_addr)
    bl_installer.set_uboot_load_addr(_options.uboot_load_addr)
    bl_installer.set_bootargs(_options.uboot_bootargs)
    bl_installer.set_kernel_image(_options.kernel_file)
    bl_installer.set_workdir(_options.workdir)
    
    # Filesystem installer
    
    fs_installer = methods.sdcard.FilesystemInstaller()
    fs_installer.set_dryrun(_options.dryrun)
    fs_installer.set_rootfs(_options.rootfs)
    fs_installer.set_workdir(_options.workdir)

    # SDCard installer

    sd_installer = methods.sdcard.SDCardInstaller(bl_installer, fs_installer)
    sd_installer.set_interactive(_options.interactive)
    sd_installer.set_dryrun(_options.dryrun)
    sd_installer.set_workdir(_options.workdir)
    
    # Operations
    
    ret = sd_installer.format_sd(_options.mmap_file, _options.device)
    if ret is False: _abort_install()
    
    ret = sd_installer.mount_partitions(_options.device,_options.workdir)
    if ret is False: _abort_install()
    
    ret = sd_installer.install_components(_options.dryrun, _options.device)
    if ret is False: _abort_install()
    
    ret = sd_installer.check_fs(_options.device)
    if ret is False: _abort_install()
        
_logger.info('Installation complete')

_clean_exit(0)
