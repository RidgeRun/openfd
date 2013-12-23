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

from openfd.storage.partition import SDCardPartition
from sdcard import SDCardInstaller
from sdcard import SDCardInstallerError

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
    
    def install_components(self, workdir, imgs):
        i = 1
        for part in self._sd.partitions:
            self._l.info("Partition: %s" % part.name)
            self._l.info("Components: %s" % part.components)
            for comp in part.components:
                if comp == SDCardPartition.COMPONENT_BOOTLOADER:
                    cmd = ('mount | grep %s | cut -f 3 -d " "' %
                           self._sd.partition_name(i))
                    output = self._e.check_output(cmd)[1]
                    mnt_point = output.replace('\n', '')
                    for img in imgs:
                        cmd = "sudo cp %s %s" % (img, mnt_point)
                        ret = self._e.check_call(cmd)
                        if ret != 0:
                            raise SDCardInstallerError('Failed copying %s to %s'
                                                       % (img, mnt_point))
            i += 1
        self._comp_installer.workdir = workdir
        SDCardInstaller.install_components(self)    
    
    def install_imgs(self):
        pass
    