#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013-2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# SD-card operations related to the installation of a script capable of
# programming flash memory.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
from openfd.storage.partition import SDCardPartition
from openfd.boards.board import BoardError
from sdcard import SDCardInstaller
from sdcard import SDCardInstallerError
from sdcard import LoopDeviceInstaller
from sdcard import LoopDeviceInstallerError

# ==========================================================================
# Public classes
# ==========================================================================

class SDCardExternalInstaller(SDCardInstaller):
    
    def __init__(self, board, device='', dryrun=False,
                 interactive=True, enable_colors=True):
        """
        :param board: :class:`Board` instance.
        :param device: Device name (i.e. '/dev/sdb').
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        :param interactive: Enable interactive mode. The user will
            be prompted before executing dangerous commands.
        :type interactive: boolean
        """
        
        SDCardInstaller.__init__(self, board, device, dryrun,
                                 interactive, enable_colors)
    
    def _install_uboot_env(self, uboot_env_file, uboot_script):
        self._l.info("Installing uboot environment")
        if not self._dryrun:
            with open(uboot_env_file, "w") as uenv:
                env = ("uenvcmd=echo Running Installer... ; "
                       "fatload mmc 0 ${loadaddr} %s ; "
                       "source ${loadaddr}" % os.path.basename(uboot_script))
                self._l.debug("  uEnv.txt <= '%s'" % env)
                uenv.write("%s\n" % env)
    
    def _install_files(self, files):
        i = 1
        self._l.info("Copying files to SD card")
        for part in self._sd.partitions:
            for comp in part.components:
                if comp == SDCardPartition.COMPONENT_BOOTLOADER:
                    cmd = ('mount | grep %s | cut -f 3 -d " "' %
                           self._sd.partition_name(i))
                    output = self._e.check_output(cmd)[1]
                    mnt_point = output.replace('\n', '')
                    for f in files:
                        cmd = "sudo cp %s %s" % (f, mnt_point)
                        ret = self._e.check_call(cmd)
                        if ret != 0:
                            raise SDCardInstallerError('Failed copying %s to %s'
                                                       % (f, mnt_point))
            i += 1
    
    def _generate_script(self, mkimage, script, uboot_script):
        self._l.info("Installing uboot script")
        cmd = ("%s -A %s -T script -n 'Installer Script' -d %s %s" %
                (mkimage, self._board.mkimage_arch, script, uboot_script))
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise SDCardInstallerError("Failed generating uboot image")
    
    def install_components(self, workdir, imgs, mkimage, script):
        try:
            self._board.sd_install_components_external(self._sd)
        except BoardError as e:
            raise SDCardInstallerError(e)
        uboot_script = "%s.scr" % os.path.splitext(script)[0]
        self._generate_script(mkimage, script, uboot_script)
        uboot_env = "%s/uEnv.txt" % workdir
        self._install_uboot_env(uboot_env, uboot_script)
        files = []
        files += imgs
        files += [script, uboot_script, uboot_env]
        self._install_files(files)
    
class LoopDeviceExternalInstaller(LoopDeviceInstaller):
    
    def __init__(self, board, dryrun=False):
        LoopDeviceInstaller.__init__(self, board, dryrun)

    def _install_uboot_env(self, uboot_env_file, uboot_script):
        self._l.info("Installing uboot environment")
        if not self._dryrun:
            with open(uboot_env_file, "w") as uenv:
                env = ("uenvcmd=echo Running Installer... ; "
                       "fatload mmc 0 ${loadaddr} %s ; "
                       "source ${loadaddr}" % os.path.basename(uboot_script))
                self._l.debug("  uEnv.txt <= '%s'" % env)
                uenv.write("%s\n" % env)
    
    def _install_files(self, files):
        self._l.info("Copying files to loop device")
        for part in self._ld.partitions:
            for comp in part.components:
                if comp == SDCardPartition.COMPONENT_BOOTLOADER:
                    cmd = 'mount | grep %s | cut -f 3 -d " "' % part.device
                    output = self._e.check_output(cmd)[1]
                    mnt_point = output.replace('\n', '')
                    for f in files:
                        cmd = "sudo cp %s %s" % (f, mnt_point)
                        ret = self._e.check_call(cmd)
                        if ret != 0:
                            raise LoopDeviceInstallerError('Failed copying %s'
                                                    ' to %s' % (f, mnt_point))
    
    def _generate_script(self, mkimage, script, uboot_script):
        self._l.info("Installing uboot script")
        cmd = ("%s -A %s -T script -n 'Installer Script' -d %s %s" %
                (mkimage, self._board.mkimage_arch, script, uboot_script))
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise LoopDeviceInstallerError("Failed generating uboot image")
    
    def install_components(self, workdir, imgs, mkimage, script):
        try:
            self._board.ld_install_components_external(self._ld)
        except BoardError as e:
            raise LoopDeviceInstallerError(e)
        uboot_script = "%s.scr" % os.path.splitext(script)[0]
        self._generate_script(mkimage, script, uboot_script)
        uboot_env = "%s/uEnv.txt" % workdir
        self._install_uboot_env(uboot_env, uboot_script)
        files = []
        files += imgs
        files += [script, uboot_script, uboot_env]
        self._install_files(files)
    