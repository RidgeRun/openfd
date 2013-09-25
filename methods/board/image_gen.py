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
# NAND images generator to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import rrutils

# ==========================================================================
# Public Classes
# ==========================================================================

class NandImageGenerator(object):
    """
    NAND images generator.
    """
    
    def __init__(self, bc_bin=None, image_dir=None, dryrun=False):
        """
        :param bc_bin: Path to the TI DM36x Binary Creator tool.
        :param image_dir: Path to the directory where to place the generated
            images.
        """
        self._bc_bin = bc_bin
        self._image_dir = image_dir
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._executer.logger = self._logger
        self._dryrun = dryrun

    def __set_bc_bin(self, bc_bin):
        if os.path.isfile(bc_bin) and os.access(bc_bin, os.W_OK):
            self._bc_bin = bc_bin
        
    def __get_bc_bin(self):
        return self._bc_bin
    
    bc_bin = property(__get_bc_bin, __set_bc_bin,
                      doc="""Path to the TI DM36x Binary Creator tool.""")
    
    def __set_image_dir(self, image_dir):
        if os.path.isdir(image_dir) and os.access(image_dir, os.W_OK):
            self._image_dir = image_dir
    
    def __get_image_dir(self):
        return self._image_dir
    
    image_dir = property(__get_image_dir, __set_image_dir,
                         doc="""Path to the directory where to place the
                         generated images.""")

    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._executer.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                      doc="""Enable dryrun mode. Systems commands will be
                     logged, but not executed.""")
