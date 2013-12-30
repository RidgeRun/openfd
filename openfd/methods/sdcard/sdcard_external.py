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

import os
from openfd.storage.partition import SDCardPartition
from sdcard import SDCardInstaller
from sdcard import SDCardInstallerError
from sdcard import LoopDeviceInstaller
from sdcard import LoopDeviceInstallerError

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
        cmd = ("%s -A arm -T script -n 'Installer Script' -d %s %s" %
                (mkimage, script, uboot_script))
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise SDCardInstallerError("Failed generating uboot image")
    
    def install_components(self, workdir, imgs, mkimage, script):
        self._comp_installer.install_uboot(self._sd.name)
        uboot_script = "%s.scr" % os.path.splitext(script)[0]
        self._generate_script(mkimage, script, uboot_script)
        uboot_env = "%s/uEnv.txt" % workdir
        self._install_uboot_env(uboot_env, uboot_script)
        files = []
        files += imgs
        files += [script, uboot_script, uboot_env]
        self._install_files(files)
    
class LoopDeviceExternalInstaller(LoopDeviceInstaller):
    
    def __init__(self, comp_installer, dryrun=False):
        LoopDeviceInstaller.__init__(self, comp_installer, dryrun)

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
                            raise SDCardInstallerError('Failed copying %s to %s'
                                                       % (f, mnt_point))
    
    def _generate_script(self, mkimage, script, uboot_script):
        self._l.info("Installing uboot script")
        cmd = ("%s -A arm -T script -n 'Installer Script' -d %s %s" %
                (mkimage, script, uboot_script))
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise LoopDeviceInstallerError("Failed generating uboot image")
    
    def install_components(self, workdir, imgs, mkimage, script):
        self._comp_installer.install_uboot(self._ld.name)
        uboot_script = "%s.scr" % os.path.splitext(script)[0]
        self._generate_script(mkimage, script, uboot_script)
        uboot_env = "%s/uEnv.txt" % workdir
        self._install_uboot_env(uboot_env, uboot_script)
        files = []
        files += imgs
        files += [script, uboot_script, uboot_env]
        self._install_files(files)
    
