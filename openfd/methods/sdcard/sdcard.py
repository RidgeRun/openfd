#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012-2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#          Diego Benavides <diego.benavides@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# SD-card operations to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import openfd.utils as utils
from openfd.storage.partition import SDCardPartition
from openfd.storage.partition import LoopDevicePartition
from openfd.storage.device import SDCard
from openfd.storage.device import LoopDevice
from component import ComponentInstallerError

# ==========================================================================
# Public Classes
# ==========================================================================

#: Warn the user when manipulating a device above this size.
WARN_DEVICE_SIZE_GB = 128

#: Color for dangerous warning messages.
WARN_COLOR = 'yellow'

# ==========================================================================
# Public Classes
# ==========================================================================

class SDCardInstallerError(Exception):
    """Exceptions for SDCardInstaller"""

class LoopDeviceInstallerError(Exception):
    """Exceptions for LoopDeviceInstaller"""

class SDCardInstaller(object):
    """
    Class to handle SD-card operations to support the installer.
    
    Typical flow:
    ::
        1. read_partitions()
        2. format()
        3. mount_partitions()
        4. install_components()
        5. release()
    """
    
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
        
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._e.enable_colors = enable_colors
        self._comp_installer = comp_installer
        self._sd = SDCard(device)
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        self._sd.dryrun = dryrun
        self._comp_installer.dryrun = dryrun
        self._interactive = interactive
        self._partitions = []
        self._loopdevice_partitions = {}
    
    def __set_device(self, device):
        self._sd = SDCard(device)
        self._sd.dryrun = self._dryrun
    
    def __get_device(self):
        return self._sd.name
    
    device = property(__get_device, __set_device,
                      doc="""Device name (i.e. '/dev/sdb').""")
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._comp_installer.dryrun = dryrun
        self._e.dryrun = dryrun
        self._sd.dryrun = dryrun
    
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

    def mount_partitions(self, directory):
        """
        Mounts the partitions in the specified directory.
        
        :exception DeviceException: When unable to mount.
        """
        
        self._sd.mount(directory)

    def _format_checks(self):
        if self._sd.exists is False:
            raise SDCardInstallerError('No disk on %s' % self._sd.name)
        if self._sd.is_mounted:
            if self._interactive:
                ret = self._sd.confirmed_unmount()
                if ret is False:
                    raise SDCardInstallerError('User canceled')
            else:
                self._sd.unmount()
        if  self._sd.size_cyl == 0:
            raise SDCardInstallerError('%s size is 0' % self._sd.name)
        if self._sd.size_cyl < self._sd.min_cyl_size():
            raise SDCardInstallerError('Size of partitions is too large to '
                                       'fit in %s' % self._sd.name)
        
    def _format_confirms(self):
        if self._sd.confirm_size_gb(WARN_DEVICE_SIZE_GB) is False:
            raise SDCardInstallerError('User canceled')
        msg = ('You are about to repartition %s (all your data will be lost)' 
               % self._sd.name)
        confirmed = self._e.prompt_user(msg, WARN_COLOR)
        if not confirmed:
            raise SDCardInstallerError('User canceled')
        
    def format(self):
        """
        Creates and formats the partitions in the SD card.
        
        :returns: Returns true on success; false otherwise.
        :exception DeviceException: On failure formatting the device.
        :exception SDCardInstallerError: On failure executing this action. 
        """
        
        if not self.dryrun:
            self._format_checks()
        if self._interactive:
            self._format_confirms()
        self._l.info('Formatting %s (this may take a while)' % self._sd.name)
        self._sd.create_partitions()
        self._sd.format_partitions()

    def release(self):
        """
        Unmounts all partitions and release the given device.
        
        :exception DeviceException: On failure releasing the device.
        """
        
        self._sd.unmount()
        self._sd.check_filesystems()
    
    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        :returns: Returns true on success; false otherwise.
        """
        
        self._sd.read_partitions(filename)
    
    def install_components(self):
        """
        Installs the specified components for each partition.
        
        :exception SDCardInstallerError: On failure installing the components.
        """
        
        i = 1
        for part in self._sd.partitions:
            device_part = self._sd.partition_name(i)
            cmd = 'mount | grep %s  | cut -f 3 -d " "' % device_part
            output = self._e.check_output(cmd)[1]
            mount_point = output.replace('\n', '')
            for comp in part.components:
                try:
                    if comp == SDCardPartition.COMPONENT_BOOTLOADER:
                        self._comp_installer.install_uboot(self._sd.name)
                        self._comp_installer.install_uboot_env(mount_point)
                    elif comp == SDCardPartition.COMPONENT_KERNEL:
                        self._comp_installer.install_kernel(mount_point)
                    elif comp == SDCardPartition.COMPONENT_ROOTFS:
                        if self._comp_installer.rootfs is None:
                            self._l.warning('No directory for "%s", omitting...'
                                        % (SDCardPartition.COMPONENT_ROOTFS))
                        else:
                            self._comp_installer.install_rootfs(mount_point)
                    else:
                        raise SDCardInstallerError('Component %s is not valid'
                                                   % comp)
                except ComponentInstallerError as e:
                    raise SDCardInstallerError(e)
            i += 1

class LoopDeviceInstaller(object):
    """
    Class to handle SD-card operations in a loopback file to support the
    installer.
    
    Typical flow:
    ::
        1. read_partitions()
        2. format()
        3. mount_partitions()
        4. install_components()
        5. release()
    """
    
    def __init__(self, comp_installer, dryrun=False):
        """
        :param comp_installer: :class:`ComponentInstaller` instance.
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._comp_installer = comp_installer
        self._ld = LoopDevice()
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        self._ld.dryrun = dryrun
        self._comp_installer.dryrun = dryrun
        self._partitions = []
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._comp_installer.dryrun = dryrun
        self._e.dryrun = dryrun
        self._ld.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. Systems commands will be
                     logged, but not executed.""")
    
    def format(self, img_name, img_size_mb):
        """
        Creates and formats the partitions in the SD card.
        
        :returns: Returns true on success; false otherwise.
        :exception DeviceException: On failure formatting the device. 
        """
        
        if not self.dryrun:
            self._ld.check_img_size(img_size_mb)
        self._l.info('Formatting %s (this may take a while)' % self._ld.name)
        self._ld.attach_device(img_name, img_size_mb)
        self._ld.create_partitions()
        self._ld.attach_partitions(img_name, img_size_mb)
        self._ld.format_partitions()
    
    def mount_partitions(self, directory):
        """
        Mounts the partitions in the specified directory.
        
        :exception DeviceException: When unable to mount.
        """
        
        self._ld.mount(directory)

    def install_components(self):
        """
        Installs the specified components for each partition.
        
        :exception LoopDeviceInstallerError: On failure installing the components.
        """
        
        i = 1
        for part in self._ld.partitions:
            cmd = 'mount | grep %s  | cut -f 3 -d " "' % part.device
            output = self._e.check_output(cmd)[1]
            mount_point = output.replace('\n', '')
            for comp in part.components:
                try:
                    if comp == LoopDevicePartition.COMPONENT_BOOTLOADER:
                        self._comp_installer.install_uboot(self._ld.name)
                        self._comp_installer.install_uboot_env(mount_point)
                    elif comp == LoopDevicePartition.COMPONENT_KERNEL:
                        self._comp_installer.install_kernel(mount_point)
                    elif comp == LoopDevicePartition.COMPONENT_ROOTFS:
                        if self._comp_installer.rootfs is None:
                            self._l.warning('No directory for "%s", omitting...'
                                    % (LoopDevicePartition.COMPONENT_ROOTFS))
                        else:
                            self._comp_installer.install_rootfs(mount_point)
                    else:
                        raise LoopDeviceInstallerError('Component %s is not '
                                                       'valid' % comp)
                except ComponentInstallerError as e:
                    raise LoopDeviceInstallerError(e)
            i += 1
    
    def release(self):
        """
        Unmounts all partitions and release the given device.
        
        :exception DeviceException: On failure releasing the device.
        """
        
        self._ld.unmount()
        self._ld.check_filesystems()
        self._ld.detach_partitions()
        self._ld.detach_device()
    
    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        :returns: Returns true on success; false otherwise.
        """
        
        self._ld.read_partitions(filename)
