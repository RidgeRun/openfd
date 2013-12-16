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
# The Executer module is in charge of executing commands in the shell.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import math
import openfd.utils as utils

# ==========================================================================
# Public classes
# ==========================================================================

class DeviceGeometry(object):
    """Geometry for a given device."""
    
    #: Heads in the unit.
    heads = 255.0
    
    #: Sectors in the unit.
    sectors = 63.0
    
    #: Sector byte size.
    sector_byte_size = 512.0
    
    #: Cylinder byte size: 255 * 63 * 512 = 8225280 bytes.
    cylinder_byte_size = 8225280.0
    
    #: String used to represent the max available size of a given storage device.
    full_size = "-"

class Device(object):
    """Representation of a device, like /dev/sda or /dev/sdb or so. """

    #: Color for dangerous warning messages.
    WARN_COLOR = 'yellow'
    
    def __init__(self, device, dryrun=False):
        """
        :param device: Device associated with this instance, i.e. '/dev/sdb/'.
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        self._device = device
        self._geometry = DeviceGeometry()
        self._size_b = 0
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._e.dryrun = dryrun
        self._dryrun = dryrun
    
    @property
    def device(self):
        """
        Device associated with this instance, i.e. '/dev/sdb/'.
        """
        
        return self._device
    
    name = device
    
    def __set_dryrun(self, dryrun):
        self._e.dryrun = dryrun
        self._dryrun = dryrun
        
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                      doc="""Enable dryrun mode. System commands will be
                     logged, but not executed.""")

    def __set_geometry(self, geometry):
        self._geometry = geometry
        
    def __get_geometry(self):
        return self._geometry
    
    geometry = property(__get_geometry, __set_geometry,
                      doc=""":class:`DeviceGeometry` instance.""")

    @property
    def size_b(self):
        """
        Device size (bytes).
        """
        
        if self._size_b != 0:
            return self._size_b
        cmd = ('sudo fdisk -l %s | grep %s | grep Disk | cut -f 5 -d " "' %
            (self._device, self._device))
        output = self._e.check_output(cmd)[1]
        if not self._dryrun:
            if not output:
                self._l.error('Unable to obtain the size for %s' % self._device)
            else:
                self._size_b = long(output)
        return self._size_b

    @property
    def size_gb(self):
        """
        Device size (gigabytes).
        """
        
        return long(self.size_b >> 30)
    
    @property
    def size_cyl(self):
        """
        Device size (cylinders).
        """
        
        size_cyl = self.size_b / self.geometry.cylinder_byte_size
        return long(math.floor(size_cyl))
    
    @property
    def is_mounted(self):
        """
        True if the device is mounted or if it's part of a RAID array,
        false otherwise.
        """
        
        is_mounted = False
        cmd1 = 'grep --quiet %s /proc/mounts' % self._device
        cmd2 = 'grep --quiet %s /proc/mdstat' % self._device
        if self._e.check_call(cmd1) == 0: is_mounted = True
        if self._e.check_call(cmd2) == 0: is_mounted = True
        return is_mounted

    @property
    def mounted_partitions(self):
        """
        Returns a list with the device's mounted partitions.
        """

        partitions = []
        cmd = 'mount | grep %s | cut -f 3 -d " "' % self._device
        output = self._e.check_output(cmd)[1]
        if output:
            partitions = output.strip().split('\n')
        return partitions

    @property
    def exists(self):
        """
        True if the device exists, false otherwise.
        """
        
        cmd = 'sudo fdisk -l %s' % self._device
        output = self._e.check_output(cmd)[1]
        return True if output else False

    def unmount(self):
        """
        Unmounts any mounted partitions.
        
        Returns true on success; false otherwise.
        """
        
        for part in self.mounted_partitions:
            cmd = 'sync'
            if self._e.check_call(cmd) != 0:
                self._l.error('Unable  to sync')
                return False
            cmd = 'sudo umount %s' % part
            if self._e.check_call(cmd) != 0:
                self._l.error('Failed to unmount %s' % part)
                return False
        return True
    
    def confirm_size_gb(self, size_gb):
        """
        Checks the device's size against `size_gb`, if it's bigger
        it warns the user prompting for confirmation.
        
        Returns true if size is less or equal than size_gb, or if not,
        and the user confirms; false otherwise. 
        """
        
        if self.size_gb > size_gb:
            msg = ('Device %s has %d gigabytes, are you sure this is the right '
                   'device' % (self.name, self.size_gb))
            confirmed = self._e.prompt_user(msg, color=self.WARN_COLOR)
            if not confirmed:
                return False
        return True

    def confirmed_unmount(self):
        """
        Same as `unmount()`, but prompts the user for confirmation.
        
        Returns true on success; false otherwise. 
        """
        
        mounted_partitions = self.mounted_partitions 
        if mounted_partitions:
            msg = ('The following partitions from device %s will be '
                   'unmounted:\n' % self.name)
            for part in mounted_partitions:
                msg += part + '\n'
            confirmed = self._e.prompt_user(msg, self.WARN_COLOR)
            if confirmed:
                return self.unmount()
        return True

    def partition_suffix(self, partition_index):
        """
        This function returns a string with the standard partition numeric
        suffix, depending on the type of device.
        
        For example, the first partition (index = 1) in device
        /dev/sdb is going to have the suffix "1", so that one can compose
        the complete partition's filename: /dev/sdb1. While a device like
        /dev/mmcblk0 will provoke a partition suffix "p1", so that the complete
        filename for the first partition is "/dev/mmcblk0p1".  
        """
        
        if 'mmcblk' in self._device or 'loop' in self._device:
            return 'p%s' % partition_index
        else:
            return '%s' % partition_index
