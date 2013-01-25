#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
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

# Optional arguments

_parser.add_option('-d', '--device',
                   help="Device to install",
                   metavar='<device>',
                   dest='device')

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

_options = _parser.get_options()

# Check verbose

if _options.verbose:
    _logger.setLevel(rrutils.logger.DEBUG)

# Check quiet (takes precedence over verbose)

if _options.quiet:
    _logger.setLevel(rrutils.logger.CRITICAL)


# Check mmap file

if not os.path.isfile(_options.mmap_file):
    _logger.error('Unable to find ' + _options.mmap_file)
    _clean_exit(-1)

# Check device

if _options.installation_mode == MODE_SD:
    if not _options.device:
        _logger.error('No device supplied (--device)')
        _parser.print_help()
        _clean_exit(-1)
        
# Clean the device string

_options.device = _options.device.rstrip('/')

# ==========================================================================
# Main logic
# ==========================================================================

if _options.installation_mode == MODE_SD:

    sd_installer = methods.sdcard.SDCardInstaller()
    
    sd_installer.set_interactive(_options.interactive)
    sd_installer.set_dryrun(_options.dryrun)
    
    ret = sd_installer.format_sd(_options.mmap_file, _options.device)
    
    if ret is False:
        _logger.error('Installation aborted')
        _clean_exit(-1)
        
    _logger.info('Installation complete')

# the end
_clean_exit(0)
