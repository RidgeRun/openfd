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
# USB operations related to the installation of a script capable of
# programming flash memory.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import openfd.utils as utils
from openfd.storage.device import USB
from openfd.storage.partition import USBPartition
from openfd.boards.board import BoardError

# ==========================================================================
# Definitions
# ==========================================================================

#: Warn the user when manipulating a device above this size.
WARN_DEVICE_SIZE_GB = 64

#: Color for dangerous warning messages.
WARN_COLOR = 'yellow'

# ==========================================================================
# Public classes
# ==========================================================================

class USBInstallerError(Exception):
    """Exceptions for USBInstaller"""

class USBInstaller(object):
    
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

        """
        USBInstaller.__init__(self, board, device, dryrun,
                                 interactive, enable_colors)
        """
        
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._e.enable_colors = enable_colors
        self._board = board
        self._usb = USB(device)
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        self._usb.dryrun = dryrun
        self._board.dryrun = dryrun
        self._interactive = interactive
        self._partitions = []    

    def __set_device(self, device):
        self._usb = USB(device)
        self._usb.dryrun = self._dryrun
    
    def __get_device(self):
        return self._usb.name
    
    device = property(__get_device, __set_device,
                      doc="""Device name (i.e. '/dev/sdb').""")
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._board.dryrun = dryrun
        self._e.dryrun = dryrun
        self._usb.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. Systems commands will be
                     logged, but not executed.""")
    
    def __set_interactive(self, interactive):
        self._interactive = interactive
    
    def __get_interactive(self):
        return self._interactive
    
    interactive = property(__get_interactive, __set_interactive,
                           doc="""Enable interactive mode. The user will
                           be prompted before executing dangerous commands.""")
    
    def __set_enable_colors(self, enable):
        self._e.enable_colors = enable
    
    def __get_enable_colors(self):
        return self._e.enable_colors
    
    enable_colors = property(__get_enable_colors, __set_enable_colors,
                           doc="""Enable colored messages.""")

    def _install_uboot_env(self, uboot_env_file, uboot_script):
        self._l.info("Installing uboot environment")
        if not self._dryrun:
            with open(uboot_env_file, "w") as uenv:
                env = ("uenvcmd=echo Running Installer... ; "
                       "fatload usb 0 ${loadaddr} %s ; "
                       "source ${loadaddr}" % os.path.basename(uboot_script))
                self._l.debug("  uEnv.txt <= '%s'" % env)
                uenv.write("%s\n" % env)
    
    def _install_files(self, files):
        i = 1
        self._l.info("Copying files to USB drive")
        for part in self._usb.partitions:
            for comp in part.components:
                if comp == USBPartition.COMPONENT_BOOTLOADER:
                    cmd = ('mount | grep %s | cut -f 3 -d " "' %
                           self._usb.partition_name(i))
                    output = self._e.check_output(cmd)[1]
                    mnt_point = output.replace('\n', '')
                    for f in files:
                        cmd = "sudo cp %s %s" % (f, mnt_point)
                        ret = self._e.check_call(cmd)
                        if ret != 0:
                            raise USBInstallerError('Failed copying %s to %s'
                                                       % (f, mnt_point))
            i += 1
    
    def _generate_script(self, mkimage, script, uboot_script):
        self._l.info("Installing uboot script")
        cmd = ("%s -A %s -T script -n 'Installer Script' -d %s %s" %
                (mkimage, self._board.mkimage_arch, script, uboot_script))
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise USBInstallerError("Failed generating uboot image")


    def mount_partitions(self, directory):
        """
        Mounts the partitions in the specified directory.
        
        :exception DeviceException: When unable to mount.
        """
        
        self._usb.mount(directory)

    def _format_checks(self):
        if self._usb.exists is False:
            raise USBInstallerError('No disk on %s' % self._usb.name)
        if self._usb.is_mounted:
            if self._interactive:
                ret = self._usb.confirmed_unmount()
                if ret is False:
                    raise USBInstallerError('User canceled')
            else:
                self._usb.unmount()
        if  self._usb.size_cyl == 0:
            raise USBInstallerError('%s size is 0' % self._usb.name)
        if self._usb.size_cyl < self._usb.min_cyl_size():
            raise USBInstallerError('Size of partitions is too large to '
                                       'fit in %s' % self._usb.name)
        
    def _format_confirms(self):
        if self._usb.confirm_size_gb(WARN_DEVICE_SIZE_GB) is False:
            raise USBInstallerError('User canceled')
        msg = ('You are about to format %s (all your data will be lost)' 
               % self._usb.name)
        confirmed = self._e.prompt_user(msg, WARN_COLOR)
        if not confirmed:
            raise USBInstallerError('User canceled')
        
    def format(self):
        """
        Creates and formats the partitions in the SD card.
        
        :returns: Returns true on success; false otherwise.
        :exception DeviceException: On failure formatting the device.
        :exception USBInstallerError: On failure executing this action. 
        """
        
        if not self.dryrun:
            self._format_checks()
        if self._interactive:
            self._format_confirms()
        self._l.info('Formatting %s (this may take a while)' % self._usb.name)
        self._usb.create_partitions()
        self._usb.format_partitions()

    def release(self):
        """
        Unmounts all partitions and release the given device.
        
        :exception DeviceException: On failure releasing the device.
        """
        
        self._usb.unmount()
        self._usb.optimize_filesystems()
        self._usb.check_filesystems()
    
    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        :returns: Returns true on success; false otherwise.
        """
        
        self._usb.read_partitions(filename)
    
    def install_components(self, workdir, imgs, mkimage, script):
        uboot_script = "%s.scr" % os.path.splitext(script)[0]
        self._generate_script(mkimage, script, uboot_script)
        uboot_env = "%s/uEnv.txt" % workdir
        self._install_uboot_env(uboot_env, uboot_script)
        files = []
        files += imgs
        files += [script, uboot_script, uboot_env]
        self._install_files(files)
