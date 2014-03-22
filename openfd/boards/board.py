#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013-2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Board module.
#
# ==========================================================================

# ==========================================================================
# Public Classes
# ==========================================================================

class BoardError(Exception):
    """Exceptions for Board"""

class Board(object):
    """Board base class."""
    
    # Command-line arguments
    
    def add_args(self, parser):
        raise NotImplementedError
    
    def check_args(self, args):
        raise NotImplementedError

    # Flash-related interfaces
    
    def comp_name(self, comp):
        raise NotImplementedError
    
    def erase_cmd(self):
        raise NotImplementedError
    
    def pre_write_cmd(self, comp):
        raise NotImplementedError
    
    def write_cmd(self, comp):
        raise NotImplementedError
    
    def post_write_cmd(self, comp):
        raise NotImplementedError
    
    # Method sdcard - Component installation
    
    def sd_init_comp_installer(self, args):
        raise NotImplementedError
    
    def sd_install_components(self):
        raise NotImplementedError
    
    def ld_install_components(self):
        raise NotImplementedError
    
    def sd_install_components_external(self, sd):
        raise NotImplementedError
    
    def ld_install_components_external(self, ld):
        raise NotImplementedError
    