#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# SD-card operations related to the installation of a script capable of
# programming flash memory.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

from sdcard import SDCardInstaller

# ==========================================================================
# Public classes
# ==========================================================================

class SDCardExternalInstaller(SDCardInstaller):
    
    def __init__(self, comp_installer, device='', dryrun=False,
                 interactive=True, enable_colors=True):
        """
        :param comp_installer: :class:`ComponentInstaller` instance.
        :param device: Device name (i.e. '/dev/sdb').
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        :param interactive: Enable interactive mode. The user will
            be prompted before executing dangerous commands.
        :type interactive: boolean
        """
        
        SDCardInstaller.__init__(self, comp_installer, device, dryrun,
                                 interactive, enable_colors)
    
    def install_components(self):
        SDCardInstaller.install_components(self)
    