#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#          Diego Benavides <diego.benavides@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# SD-card operations to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

from openfd.storage.partition import SDCardPartition
from openfd.storage.device import DeviceException
from openfd.storage.device import SDCard
import component
import openfd.utils

# ==========================================================================
# Public Classes
# ==========================================================================

class SDCardInstaller(object):
    """
    Class to handle SD-card operations to support the installer.
    
    Typical flow:
    ::
        1. read_partitions()
        2. format_sd() / format_loopdevice()
        3. mount_partitions()
        4. install_components()
        5. release_device()
    """

    #: Warn the user when partitioning a device above this size.
    WARN_DEVICE_SIZE_GB = 128
    
    #: Color for dangerous warning messages.
    WARN_COLOR = 'yellow'
    
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
        
        self._l = openfd.utils.logger.get_global_logger()
        self._e = openfd.utils.executer.get_global_executer()
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
        
        Returns true on success; false otherwise.
        """
        
        try:
            self._sd.mount(directory)
        except DeviceException as e:
            self._l.error(e)
            return False
        return True
    
    def _create_partitions(self):
        """
        Create the partitions in the given device.
        
        Returns true on success; false otherwise
        """
        
        # Check we were able to get correctly the device size
        if  self._sd.size_cyl == 0 and not self._dryrun:
            self._l.error('Unable to partition device %s (size is 0)' %
                               self._sd.name)
            return False
        
        # Check we have enough size to fit all the partitions and the MBR.
        if self._sd.size_cyl < self._sd.min_cyl_size() and not self._dryrun:
            self._l.error('Size of partitions is too large to fit in %s' %
                               self._sd.name)
            return False
        # Just before creating the partitions, prompt the user
        if self._interactive:
            msg = ('You are about to repartition your device %s '
                   '(all your data will be lost)' % self._sd.name)
            msg_color = SDCardInstaller.WARN_COLOR
            confirmed = self._e.prompt_user(msg, msg_color)
            if not confirmed:
                return False
            
        try:
            self._sd.create_partitions()
        except DeviceException as e:
            self._l.error(e)
            return False
        
        return True

    def _format_partitions(self):
        """
        Format the partitions in the given device, assuming these partitions
        were already created (see create_partitions()). To register partitions
        use read_partitions().
        
        Returns true on success; false otherwise.
        """
        
        try:
            self._sd.format_partitions()
        except DeviceException as e:
            self._l.error(e)
            return False
        return True

    def format(self):
        """
        Creates and formats the partitions in the SD card.
        
        :returns: Returns true on success; false otherwise. 
        """
        
        if not self._sd.exists and not self._dryrun:
            self._l.error('No valid disk available on %s' % self._sd.name)
            return False
        
        if self._interactive:
            if self._sd.confirm_size_gb(self.WARN_DEVICE_SIZE_GB) is False:
                return False
        
        if self._sd.is_mounted and not self._dryrun:
            try:
                if self._interactive:
                    ret = self._sd.confirmed_unmount()
                    if ret is False:
                        return False
                else:
                    ret = self._sd.unmount()
            except DeviceException as e:
                self._l.error(e)
                return False
        
        self._l.info('Formatting %s (this may take a while)' % self._sd.name)
        try:
            ret = self._create_partitions()
            if ret is False:
                return False
            ret = self._format_partitions()
            if ret is False:
                return False
        except DeviceException as e:
            self._l.error(e)
            return False
        
        return True

    def release(self):
        """
        Unmounts all partitions and release the given device.
        
        :returns: Returns true on success; false otherwise.
        """
        
        try:
            self._sd.check_filesystems()
        except DeviceException as e:
            self._l.error(e)
            return False
        return True
    
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
        
        :returns: Returns true on success, false otherwise.
        """
        
        i = 1
        for part in self._sd.partitions:
            device_part = self._sd.partition_name(i)
            cmd = 'mount | grep %s  | cut -f 3 -d " "' % device_part
            ret, output = self._e.check_output(cmd)
            mount_point = output.replace('\n', '')
            for component in part.components:
                if component == SDCardPartition.COMPONENT_BOOTLOADER:
                    ret = self._comp_installer.install_uboot(self._sd.name)
                    if ret is False: return False
                    ret =  self._comp_installer.install_uboot_env(mount_point)
                    if ret is False: return False
                elif component == SDCardPartition.COMPONENT_KERNEL:
                    ret = self._comp_installer.install_kernel(mount_point)
                    if ret is False: return False
                elif component == SDCardPartition.COMPONENT_ROOTFS:
                    if self._comp_installer.rootfs is None:
                        msg = ('No directory specified for "%s", omitting...' %
                                   (SDCardPartition.COMPONENT_ROOTFS))
                        self._l.warning(msg)
                    else:
                        ret = self._comp_installer.install_rootfs(mount_point)
                        if ret is False: return False
                elif component == SDCardPartition.COMPONENT_BLANK:
                    pass
                else:
                    self._l.error('Component %s is not valid' % component)
                    return False
            i += 1
        return True
