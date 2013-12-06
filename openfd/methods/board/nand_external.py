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
# Support to generate an external installer for SD.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
from string import Template  

# ==========================================================================
# Public Classes
# ==========================================================================

class ExternalInstaller(object):
    """
    Install components to NAND memory.
    """

    def __init__(self, board):
        self._substitions = {}
        self._board = board
    
    def _general_substitions(self):
        self._substitions['mach_desc'] = self._board.mach_description
    
    def write(self, in_file, out_file):
        with open(in_file, 'r') as in_f:
            t = Template(in_f.read())
            with open(out_file, 'w') as out_f: 
                out_f.write(t.safe_substitute(self._substitions))
                
    def install_ipl(self):
        pass
