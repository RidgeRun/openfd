#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# Board factory module.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import dm36x_leopard

# ==========================================================================
# Public Classes
# ==========================================================================

class BoardFactoryException(Exception):
    """Board Factory Exception."""

class BoardFactory(object):
    """Factory for `Board` objects."""
    
    def make(self, name):
        """
        Creates a Board instance.
        
        :param name: Board's name.
        :returns: Returns a concrete `Board` instance according to name.
        """
        
        if name == dm36x_leopard.BOARD_NAME:
            return dm36x_leopard.Dm36xLeopard()
        else: raise BoardFactoryException("Don't know which Board instance " 
                                          "to create with name '%s'" % name)
