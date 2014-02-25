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

class Board(object):
    """Board base class."""

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
        