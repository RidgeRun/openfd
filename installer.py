#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
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

Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
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

# ==========================================================================
# Global variables
# ==========================================================================

_options = []
_parser  = rrutils.Parser()
_logger  = None
_config  = None

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
   
def _validate_mode(mode):    
    """
    Checks for the mode input to be valid.
    """
    
    valid = False
    if mode == 'sd': 
        valid = True
    return valid
    
# ==========================================================================
# Command line arguments
# ==========================================================================

_parser.set_usage('Usage: %prog -m <mode> -f <mmap_config_file> [options]')

_parser.add_option('-m', '--mode', help="Installation mode: sd", metavar='<mode>', dest='installation_mode')
_parser.add_option('-f', '--mmap-config-file', help="Memory map config file", metavar='<mmap>', dest='mmap_file')
_parser.add_option('-v', '--verbose', help="Enable debug", dest="verbose", action='store_true')
_parser.add_option('-q', '--quiet', help="Be as quiet as possible", dest="quiet", action='store_true')
    
_options = _parser.get_options()

# Check verbose

if _options.verbose:
    _logger.setLevel(rrutils.logger.DEBUG)

# Check quiet (takes precedence over verbose)

if _options.quiet:
    _logger.setLevel(rrutils.logger.CRITICAL)

# Check installation mode (required)

if not _options.installation_mode:
    _logger.error('Installation mode required (--mode)')
    _parser.print_help()
    _clean_exit(-1)
elif not _validate_mode(_options.installation_mode):
    print 'Invalid mode.'
    print _parser.get_try_help_message()
    _clean_exit(-1)

# Check mmap file

if not _options.mmap_file:
    _logger.error('Memory map config file required (--mmap-config-file)')
    _parser.print_help()
    _clean_exit(-1)
    
if not os.path.isfile(_options.mmap_file):
    _logger.error('Unable to find ' + _options.mmap_file)
    _clean_exit(-1)

# ==========================================================================
# Main logic
# ==========================================================================

if _options.installation_mode == 'sd':
    
    # @todo
    pass

# the end
_clean_exit(0)
