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
# Board factory module.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import importlib
import dm36x_leopard
import dm816x_z3
import dummy_evm
import openfd.boards

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
        if name == dm816x_z3.BOARD_NAME:
            return dm816x_z3.Dm816xZ3()
        elif name == dummy_evm.BOARD_NAME:
            return dummy_evm.DummyEvm()
        else:
            raise BoardFactoryException("Don't know which Board instance " 
                                          "to create with name '%s'" % name)

    def supported_boards(self):
        boards = []
        boards_dir = os.path.dirname(openfd.boards.__file__)
        for board_file in os.listdir(boards_dir):
            base = os.path.splitext(board_file)[0]
            if base == '__init__' or base.startswith('.'):
                continue
            mod = importlib.import_module('openfd.boards.%s' % base)
            try:
                if mod.BOARD_NAME not in boards:
                    boards.append(mod.BOARD_NAME)
            except AttributeError:
                pass
        return sorted(boards)
