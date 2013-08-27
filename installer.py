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
                        [--image-size <imagesize>] [--uflash <uflash>]
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
      --image-size <imagesize>
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

# ==========================================================================
# Global variables
# ==========================================================================

_options = []
_parser  = None
_logger  = None

# Constants

MODE_SD = 'sd'
MODE_SERIAL = 'serial'
MODE_LOOPBACK = 'loopback'

# ==========================================================================
# Logging
# ==========================================================================

def _init_logging():

    global _logger

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
        _logger.error('Exiting with code %d' % code) 

    exit(code)

def _abort_install():
    """
    Prints abort message, closes open resources and exits.
    """
    
    _logger.error('Installation aborted')
    _clean_exit(-1)
   
# ==========================================================================
# Command line arguments
# ==========================================================================

def _missing_arg_exit(arg):
    """
    Prints message indicating arg is required, prints help and exit.
    """
    
    _parser.print_help()
    _logger.error('Argument %s is required' % arg)
    _clean_exit(-1)

def _parse_args():
    
    global _parser
    global _options
    
    _parser = rrutils.Parser()
    
    # Required arguments
    
    installation_modes = MODE_SD, MODE_LOOPBACK
    
    _parser.add_option('-m', '--mode',
                       help="Installation mode: % s" % 
                       ''.join('%s' % mode for mode in installation_modes),
                       metavar='<mode>',
                       dest='installation_mode',
                       required=True,
                       choices=installation_modes)
    
    _parser.add_option('-f', '--mmap-config-file',
                       help='Memory map config file',
                       metavar='<mmap>',
                       dest='mmap_file',
                       required=True)
    
    _parser.add_option('--kernel-file',
                       help='Path to the Kernel Image file to be installed.',
                       metavar='<kernel_file>',
                       dest='kernel_file',
                       required=True)
    
    # Optional arguments
    
    _parser.add_option('-y', '--assume-yes',
                       help='Automatic \'yes\' to prompts; '
                       'run non-interactively',
                       dest='interactive',
                       action='store_false',
                       default=True)
    
    _parser.add_option('-v', '--verbose',
                       help='Enable debug',
                       dest='verbose',
                       action='store_true',
                       default=False)
    
    _parser.add_option('-q', '--quiet',
                       help='Be as quiet as possible',
                       dest='quiet',
                       action='store_true',
                       default=False)
    
    _parser.add_option('--dryrun',
                       help='Sets the dryrun mode On (shell commands will be '
                            'logged, but not executed)',
                       dest='dryrun',
                       action='store_true',
                       default=False)
    
    # MODE_SD - Required arguments
    
    _parser.add_option('-d', '--device',
                       help="Device to install",
                       metavar='<device>',
                       dest='device')
    
    # MODE_LOOPBACK - Required arguments
    
    _parser.add_option('--image',
                       help="The filename of the image to create in workdir",
                       metavar='<image>',
                       dest='image')
    
    _parser.add_option('--image-size',
                       help="Size in MB of the image file to create (integer" \
                       " number)",
                       metavar='<imagesize>',
                       dest='imagesize')
    
    # MODE_SD and MODE_LOOPBACK - Required arguments
    
    _parser.add_option('--uflash',
                       help='Path to the uflash tool',
                       metavar='<uflash>',
                       dest='uflash_bin')
    
    _parser.add_option('--ubl-file',
                       help='Path to the UBL file',
                       metavar='<ubl_file>',
                       dest='ubl_file')
    
    _parser.add_option('--uboot-file',
                       help='Path to the U-Boot file',
                       metavar='<uboot_file>',
                       dest='uboot_file')
    
    _parser.add_option('--uboot-entry-addr',
                       help='U-Boot entry address (decimal)',
                       metavar='<uboot_entry_addr>',
                       dest='uboot_entry_addr')
    
    _parser.add_option('--uboot-load-addr',
                       help='U-Boot load address (decimal)',
                       metavar='<uboot_load_addr>',
                       dest='uboot_load_addr')
    
    _parser.add_option('--uboot-bootargs',
                       help='U-Boot bootargs environment variable (passed to the Linux kernel)',
                       metavar='<uboot_bootargs>',
                       dest='uboot_bootargs')
    
    _parser.add_option('--work-dir',
                       help='Directory to perform temporary operations',
                       metavar='<workdir>',
                       dest='workdir')
    
    # MODE_SD and MODE_LOOPBACK - Optional arguments
    
    _parser.add_option('--rootfs',
                       help='Path to the rootfs that will be installed.',
                       metavar='<rootfs>',
                       dest='rootfs',
                       default=None)
    
    # Parse
    
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
        else:
            # Clean the device string    
            _options.device = _options.device.rstrip('/')
    
    # Check LOOPBACK required arguments
    
    if _options.installation_mode == MODE_LOOPBACK:
        
        if not _options.image: _missing_arg_exit('--image')
        
        if not _options.imagesize:
            _missing_arg_exit('--image-size')
        else:
            try:
                int(_options.imagesize)
            except:
                _missing_arg_exit('--image-size, must be an integer')
    
    # Check MODE_SD or MODE_LOOPBACK required arguments
    
    if _options.installation_mode == MODE_SD or _options.installation_mode == MODE_LOOPBACK:
            
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
            _missing_arg_exit('--work-dir')
        else:
            if not os.path.isdir(_options.workdir):
                _logger.error('Unable to find %s' % _options.workdir)
                _clean_exit(-1)
    
        # Check MODE_SD or MODE_LOOPBACK optional arguments
        
        if _options.rootfs:
            if not os.path.isdir(_options.rootfs):
                _logger.error('Unable to find %s' % _options.rootfs)
                _clean_exit(-1)

# ==========================================================================
# Main logic
# ==========================================================================

def main():

    _init_logging()
    _parse_args()

    if _options.installation_mode == MODE_SD or _options.installation_mode == MODE_LOOPBACK:
        
        # Components installer
        
        comp_installer = methods.sdcard.ComponentInstaller()
        comp_installer.uflash_bin = _options.uflash_bin
        comp_installer.ubl_file =_options.ubl_file
        comp_installer.uboot_file = _options.uboot_file
        comp_installer.uboot_entry_addr = _options.uboot_entry_addr
        comp_installer.uboot_load_addr = _options.uboot_load_addr
        comp_installer.bootargs = _options.uboot_bootargs
        comp_installer.kernel_image = _options.kernel_file
        comp_installer.rootfs = _options.rootfs
        comp_installer.workdir = _options.workdir
        
        # SDCard installer
    
        sd_installer = methods.sdcard.SDCardInstaller(comp_installer)
        sd_installer.interactive = _options.interactive
        sd_installer.dryrun = _options.dryrun
        
        # Operations
        
        if _options.installation_mode == MODE_SD:
            sd_installer.set_device(_options.device)
            sd_installer.set_mode(sd_installer.MODE_SD)
            ret = sd_installer.format_sd(_options.mmap_file)
            if ret is False: _abort_install()
        else:
            sd_installer.set_mode(sd_installer.MODE_LOOPBACK)
            ret = sd_installer.format_loopdevice(_options.mmap_file, 
                                                 _options.workdir + 
                                                 _options.image, 
                                                 _options.imagesize)
            if ret is False: _abort_install()
        
        ret = sd_installer.mount_partitions(_options.workdir)
        if ret is False: _abort_install()
        
        ret = sd_installer.install_components()
        if ret is False: _abort_install()
        
        if _options.installation_mode == MODE_SD:
            ret = sd_installer.check_filesystems()
            if ret is False: _abort_install()
        else:
            ret = sd_installer.release_loopdevice()
            if ret is False: _abort_install()
        
    if _options.installation_mode == MODE_SERIAL:
        pass
            
    _logger.info('Installation complete')
    
    _clean_exit(0)
    
if __name__ == '__main__':
    main()
