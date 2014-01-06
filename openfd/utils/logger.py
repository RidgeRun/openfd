#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# The Logger module facilitates a uniform creation of a logger instance.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import logging

# ==========================================================================
# Globals
# ==========================================================================

_logger = None

# ==========================================================================
# Functions
# ==========================================================================

def init_global_logger(name):
    """
    Inits the global logger instance.
    
    :param name: Name for the global logger instance.
    :returns: The global logger instance.
    """
    
    global _logger
    if not _logger:
        _logger = logging.getLogger(name)
    return _logger

def get_global_logger():
    """
    Returns a global loggin.getLogger() instance.
    
    :returns: The global logger instance.
    """
    return _logger
