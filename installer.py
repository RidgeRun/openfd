# ==========================================================================
#
# Copyright (C) 2012 Ridgerun (http://www.ridgerun.com).
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

Copyright (C) 2012 Ridgerun (http://www.ridgerun.com).
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
    
# ==========================================================================
# Command line arguments
# ==========================================================================

_parser.add_option('', '--devdir', help="DEVDIR path", metavar='<path>', dest='devdir_path')
_parser.add_option('-v', '--verbose', help="Enable debug", dest="verbose", action='store_true')
_parser.add_option('-q', '--quiet', help="Be as quiet as possible", dest="quiet", action='store_true')
    
_options = _parser.get_options()

# Check verbose

if _options.verbose:
    _logger.setLevel(rrutils.logger.DEBUG)

# Check quiet (takes precedence over verbose)

if _options.quiet:
    _logger.setLevel(rrutils.logger.CRITICAL)

# Check devdir path

if not _options.devdir_path:
    try:
        if os.environ['DEVDIR']:
            _options.devdir_path = os.environ['DEVDIR']
        _logger.info('Using DEVDIR ' + _options.devdir_path)
    except KeyError:
        _logger.error('Unable to obtain the $DEVDIR path from the environment.')
        _clean_exit(-1)

# Check bspconfig

bspconfig = _options.devdir_path.rstrip('/') + '/bsp/mach/bspconfig'
if not os.path.isfile(bspconfig):
    _logger.error('Unable to find ' + bspconfig)
    _clean_exit(-1)

# Initialize global config  
_config = rrutils.config.get_global_config(bspconfig)

# the end
_clean_exit(0)
