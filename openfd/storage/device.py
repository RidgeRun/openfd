#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013-2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Device related operations.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import math
import openfd.utils as utils
from partition import SDCardPartition
from partition import read_sdcard_partitions
from partition import read_loopdevice_partitions
from partition import USBPartition
from partition import read_usb_partitions

# ==========================================================================
# Public classes
# ==========================================================================

class DeviceException(Exception):
    pass

class SDCardGeometry(object):
    """Geometry for a given device."""
    
    #: Heads in the unit.
    heads = 255.0
    
    #: Sectors in the unit.
    sectors = 63.0
    
    #: Sector byte size.
    sector_byte_size = 512.0
    
    #: Cylinder byte size: 255 * 63 * 512 = 8225280 bytes.
    cyl_byte_size = 8225280.0
    
    #: String used to represent the max available size of a given storage device.
    full_size = "-"
    
    def mb_to_cyl(self, size_mb):
        size_b = int(size_mb) << 20
        size_cyl = size_b / self.cyl_byte_size
        return long(math.floor(size_cyl))

class USBGeometry(object):
    """Geometry for a given device."""
    
    #: Heads in the unit.
    heads = 121.0
    
    #: Sectors in the unit.
    sectors = 62.0
    
    #: Sector byte size.
    sector_byte_size = 512.0
    
    #: Cylinder byte size: 121 * 62 * 512 = 3841024 bytes.
    cyl_byte_size = 3841024.0
    
    #: String used to represent the max available size of a given storage device 
    #: On the command line it means all the cylinders byte available.
    full_size = "-"
    
    #: Max size in Bytes of a given storage device supported
    max_size = 68719476736.0
    
    def mb_to_cyl(self, size_mb):
        size_b = int(size_mb) << 20
        size_cyl = size_b / self.cyl_byte_size
        return long(math.floor(size_cyl))

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

    def sync(self):
        if self._e.check_call('sync') != 0:
            raise DeviceException('Unable to sync')

    @property
    def size_b(self):
        """
        Device size (bytes).
        
        :exception DeviceException: When unable to obtain the size. 
        """
        
        if self._size_b != 0:
            return self._size_b
        cmd = ('sudo fdisk -l %s 2> /dev/null | grep %s | grep Disk | '
               'cut -f 5 -d " "' % (self._device, self._device))
        output = self._e.check_output(cmd)[1]
        if not self._dryrun:
            if not output:
                raise DeviceException('Unable to obtain the size for %s' %
                                      self._device)
            else:
                self._size_b = long(output)
        return self._size_b

    @property
    def size_gb(self):
        """
        Device size (gigabytes).
        
        :exception DeviceException: When unable to obtain the size.
        """
        
        return long(self.size_b >> 30)
    
    @property
    def size_cyl(self):
        """
        Device size (cylinders).
        
        :exception DeviceException: When unable to obtain the size.
        """
        
        size_cyl = self.size_b / self.geometry.cyl_byte_size
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
        
        :exception DeviceException: When unable to sync or unmount.
        """
        
        for part in self.mounted_partitions:
            self.sync()
            if self._e.check_call('sudo umount %s' % part) != 0:
                raise DeviceException('Failed to unmount %s' % part)
    
    def confirm_size_gb(self, size_gb):
        """
        Checks the device's size against `size_gb`, if it's bigger
        it warns the user prompting for confirmation.
        
        Returns true if size is less or equal than size_gb, or if not,
        and the user confirms; false otherwise. 
        """
        
        if self.size_gb > size_gb:
            msg = ('Device %s has %d GB, this is above the 64 GB size limit\n'
                   'The device will be repartitioned, please make sure this '
                   'is the right device' % (self.name, self.size_gb))
            confirmed = self._e.prompt_user(msg, color=self.WARN_COLOR)
            if not confirmed:
                return False
            self._size_b = long(self.geometry.max_size)
        return True

    def confirmed_unmount(self):
        """
        Same as `unmount()`, but prompts the user for confirmation.
        
        :returns: Returns false if the user declined the unmount; true
            otherwise.
        :exception DeviceException: When unable to sync or unmount. 
        """
        
        mounted_partitions = self.mounted_partitions 
        if mounted_partitions:
            msg = ('The following partitions from device %s will be '
                   'unmounted:\n' % self.name)
            for part in mounted_partitions:
                msg += part + '\n'
            confirmed = self._e.prompt_user(msg.rstrip('\n'), self.WARN_COLOR)
            if confirmed:
                self.unmount()
            else:
                return False
        return True

class SDCard(Device):

    def __init__(self, device, dryrun=False):
        """
        :param device: Device associated with this instance, i.e. '/dev/sdb/'.
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        
        Device.__init__(self, device, dryrun)
        self._geometry = SDCardGeometry()
        self._partitions = []
        
    @property
    def partitions(self):
        """
        Returns the list of partitions (:class:`SDCardPartition`) associated
        with this SD card.
        """
        
        return self._partitions
        
    def min_cyl_size(self):
        """
        Sums all the partitions' sizes and returns the total. It is actually
        the minimum size because there could be partitions which size is
        unknown as they can be specified to take as much space as they can.
        The size calculated for such partitions is 1 cylinder - their minimum,
        and hence the total size is also minimum.
        
        Additionally to the partitions' size, the total includes 1 cylinder
        for the Master Boot Record.
        """
        
        # Leave room for the MBR
        min_cyl_size = 1
        for part in self._partitions:
            if part.size == self.geometry.full_size:
                # If size is unspecified, at least estimate 1 cylinder for
                # that partition
                min_cyl_size += 1
            else:
                min_cyl_size += int(part.size)
        return min_cyl_size
        
    def partition_name(self, index):
        if 'mmcblk' in self._device:
            return '%sp%s' % (self.name, index) # i.e. /dev/mmbclk0p1
        else:
            return '%s%s' % (self.name, index)  # i.e. /dev/sdb1
        
    def create_partitions(self):
        """
        Create the partitions in the given device.
        
        :exception DeviceException: When unable to partition.
        """
        
        cmd = ('sudo sfdisk -D' +
              ' -C' + str(int(self.size_cyl)) +
              ' -H' + str(int(self.geometry.heads)) +
              ' -S' + str(int(self.geometry.sectors)) +
              ' '   + self.name + ' << EOF\n')
        for part in self._partitions:
            cmd += str(part.start) + ','
            cmd += str(part.size) + ','
            cmd += str(part.type)
            if part.is_bootable: cmd += ',*'
            cmd += '\n'
        cmd += 'EOF'
        if self._e.check_call(cmd) != 0:
            raise DeviceException('Unable to partition device %s' % self.name)
        
    def format_partitions(self):
        """
        Format the partitions in the given device, assuming these partitions
        were already created (see create_partitions()). To register partitions
        use read_partitions().
        
        :exception DeviceException: When unable to format.
        """

        i = 1
        for part in self._partitions:
            filename = self.partition_name(i)
            if part.filesystem == SDCardPartition.FILESYSTEM_VFAT:
                cmd = 'sudo mkfs.vfat -F 32 %s -n %s' % (filename, part.name)
            elif part.filesystem == SDCardPartition.FILESYSTEM_EXT3:
                cmd = 'sudo mkfs.ext3 %s -L %s'  % (filename, part.name)
            elif (part.filesystem == SDCardPartition.FILESYSTEM_EXT4 or
                  part.filesystem == SDCardPartition.FILESYSTEM_EXT4_WRITEBACK):
                cmd = 'sudo mkfs.ext4 %s -L %s'  % (filename, part.name)
            else:
                raise DeviceException("Can't format partition %s, unknown "
                              "filesystem: %s" % (part.name, part.filesystem))
            if self._e.check_call(cmd) != 0:
                raise DeviceException('Unable to format %s into %s' %
                                (part.name, filename))
            i += 1   
        if self._partitions:
            self.sync()
        
    def mount(self, directory):
        """
        Mounts the partitions in the specified directory.
        
        I.e., if the partitions are called "boot" and "rootfs", and the given
        directory is "/media", this function will mount:
        
           - /media/boot
           - /media/rootfs
        
        :param directory: Directory where to mount the partitions.
        :exception DeviceException: When unable to mount.
        """
        
        i = 1
        for part in self._partitions:
            name = self.partition_name(i)
            mnt_dir = "%s/%s" % (directory.rstrip('/'), part.name)
            if self._e.check_call('mkdir -p %s' % mnt_dir) != 0:
                raise DeviceException('Failed to create directory %s' % mnt_dir)
            # Map the partition's fs to a type that the 'mount' understands
            fs_type = None
            if part.filesystem == SDCardPartition.FILESYSTEM_VFAT:
                fs_type = 'vfat'
            elif part.filesystem == SDCardPartition.FILESYSTEM_EXT3:
                fs_type = 'ext3'
            elif (part.filesystem == SDCardPartition.FILESYSTEM_EXT4 or 
                  part.filesystem == SDCardPartition.FILESYSTEM_EXT4_WRITEBACK):
                fs_type = 'ext4'
            if fs_type:
                cmd = 'sudo mount -t %s %s %s' % (fs_type, name, mnt_dir)
            else:
                cmd = 'sudo mount %s %s' % (name, mnt_dir) # let mount guess
            if self._e.check_call(cmd) != 0:
                raise DeviceException('Failed to mount %s in %s' % 
                                      (name, mnt_dir))
            i += 1

    def optimize_filesystems(self):
        """
        Optimize the filesystems, if applies.
        
        Optimizations supported:
          - FILESYSTEM_EXT4_WRITEBACK: Sets the data mode to "writeback",
              disabling journaling.
            
        Note: The device should be unmounted before running optimizations.
        
        :exception DeviceException: When unable to optimize.
        """
        
        i = 1
        for part in self._partitions:
            filename = self.partition_name(i)
            if part.filesystem == SDCardPartition.FILESYSTEM_EXT4_WRITEBACK:
                cmd = "sudo tune2fs -o journal_data_writeback %s" % filename
                ret = self._e.check_call(cmd)
                if ret != 0:
                    raise DeviceException('Failed optimizing %s' % filename)
                cmd = "sudo tune2fs -O ^has_journal %s" % filename
                ret = self._e.check_call(cmd)
                if ret != 0:
                    raise DeviceException('Failed optimizing %s' % filename)
            i = i + 1

    def check_filesystems(self):
        """
        Checks the integrity of the filesystems in the given device. Upon 
        error, tries to recover using the 'fsck' command.
        
        Note: The device should be unmounted before running this check.
        
        :exception DeviceException: When a filesystem has an error.
        """
        
        # The exit code returned by fsck is the sum of the following conditions
        fsck_outputs = {0    : 'No errors',
                        1    : 'Filesystem errors corrected',
                        2    : 'System should be rebooted',
                        4    : 'Filesystem errors left uncorrected',
                        8    : 'Operational error',
                        16   : 'Usage or syntax error',
                        32   : 'fsck canceled by user request',
                        128  : 'Shared-library error'}
        
        fs_ok = True
        for i in range(1, len(self._partitions) + 1):
            states = []
            filename = self.partition_name(i)
            self.sync()
            ret = self._e.check_call("sudo fsck -y %s" % filename)
            if ret == 0:
                states.append(fsck_outputs[ret])
            else:
                for i in range(len(fsck_outputs)):
                    key = 2 ** i
                    if ret & key:
                        try:
                            states.append(fsck_outputs[key])
                            if key != 1: # keys not counted as fatal errors
                                fs_ok = False
                        except KeyError:
                            pass
            states_str = ''.join("'%s', " % s for s in states).rstrip(', ')
            msg = ("Filesystem check in %s: %s (see 'man fsck', exit code: %s)"
                   % (filename, states_str, ret))
            if fs_ok:
                self._l.debug(msg)
            else:
                raise DeviceException(msg)

    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        """
        
        self._partitions[:] = []
        self._partitions = read_sdcard_partitions(filename)
    
class LoopDevice(Device):
    
    def __init__(self, dryrun=False):
        self._e = utils.executer.get_global_executer()
        self._e.dryrun = dryrun
        Device.__init__(self, self._get_free_device(), dryrun)
        self._geometry = SDCardGeometry()
        self._partitions = []
    
    def _get_free_device(self):
        ret, loop_device = self._e.check_output('sudo losetup -f')
        if ret != 0:
            raise DeviceException('Failed obtaining a free loop device')
        return loop_device.strip()
    
    @property
    def partitions(self):
        """
        Returns the list of partitions (:class:`LoopDevicePartition`) associated
        with this loop device.
        """
        
        return self._partitions
    
    def min_cyl_size(self):
        """
        Sums all the partitions' sizes and returns the total. It is actually
        the minimum size because there could be partitions which size is
        unknown as they can be specified to take as much space as they can.
        The size calculated for such partitions is 1 cylinder - their minimum,
        and hence the total size is also minimum.
        
        Additionally to the partitions' size, the total includes 1 cylinder
        for the Master Boot Record.
        """
        
        # Leave room for the MBR
        min_cyl_size = 1
        for part in self._partitions:
            if part.size == self.geometry.full_size:
                # If size is unspecified, at least estimate 1 cylinder for
                # that partition
                min_cyl_size += 1
            else:
                min_cyl_size += int(part.size)
        return min_cyl_size
    
    def check_img_size(self, img_size_mb):
        img_size_cyl = self.geometry.mb_to_cyl(img_size_mb)
        if img_size_cyl < self.min_cyl_size():
            size_needed_b = (self.min_cyl_size() * self.geometry.cyl_byte_size)
            size_needed_mb = int(size_needed_b) >> 20
            raise DeviceException('Image size of %s MB is too small to hold '
                   'the partitions, the image must be bigger than %s MB to '
                   'hold them.' % (img_size_mb, size_needed_mb))
    
    def attach_device(self, img_name, img_size_mb):
        """
        Creates the image file with a valid format and associates the file
        with the loop device. 
        
        :exception DeviceException: Upon failure on associating the image
            file with the loop device.
        """
        
        cmd = 'dd if=/dev/zero of=%s bs=1M count=%s' % (img_name, img_size_mb)
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise DeviceException('Failed creating file for %s' % img_name)
        
        cmd = 'sudo losetup %s %s' % (self.name, img_name)
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise DeviceException('Failed to associate image file %s to %s'
                                  % (img_name, self.name))
        
        # If we want to reuse the code for creating and formatting partitions
        # the image needs to have a valid format
        cmd = 'sudo mkfs.ext4 %s -L tmp' % self.name
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise DeviceException('Failed to format a temporary filesystem on '
                                  '%s' % img_name)
    
    def attach_partitions(self, img_name, img_size_mb):
        """
        Attaches partitions of the image file to an available loop device.
        
        :exception DeviceException: Upon failure on associating a partition
            with a loop device.
        """
        
        for part in self._partitions:
            device = self._get_free_device()
            if part.size == self.geometry.full_size:
                part_size_cyl = self.geometry.mb_to_cyl(img_size_mb) - \
                    int(part.start)
                size_b = part_size_cyl * int(self.geometry.cyl_byte_size)
            else:
                size_b = int(part.size) * int(self.geometry.cyl_byte_size)
            if int(part.start) == 0:
                # DOS compatibility: We use sfdisk with the -D option, if the
                # partition starts at offset 0, some space have to be wasted.
                # See the corresponding documentation.
                track_offset = int(1 * self.geometry.sectors *
                                        self.geometry.sector_byte_size)
                offset = track_offset
                size_b -= track_offset
            else:
                offset = int(part.start) * int(self.geometry.cyl_byte_size)
            cmd = ('sudo losetup -o %s --sizelimit %s %s %s' %
                                        (offset, size_b, device, img_name))
            ret = self._e.check_call(cmd)
            if ret != 0:
                raise DeviceException('Failed associating image %s to %s' %
                                      (img_name, device))
            part.device = device
    
    def create_partitions(self):
        """
        Create the partitions in the given device.
        
        :exception DeviceException: When unable to partition.
        """
        
        self._l.info("Creating partitions")
        cmd = ('sudo sfdisk -D' +
              ' -C' + str(int(self.size_cyl)) +
              ' -H' + str(int(self.geometry.heads)) +
              ' -S' + str(int(self.geometry.sectors)) +
              ' '   + self.name + ' << EOF\n')
        for part in self._partitions:
            cmd += str(part.start) + ','
            cmd += str(part.size) + ','
            cmd += str(part.type)
            if part.is_bootable: cmd += ',*'
            cmd += '\n'
        cmd += 'EOF'
        if self._e.check_call(cmd) != 0:
            raise DeviceException('Unable to partition device %s' % self.name)
    
    def format_partitions(self):
        """
        Format the partitions in the given device, assuming these partitions
        were already created (see create_partitions()). To register partitions
        use read_partitions().
        
        :exception DeviceException: When unable to format.
        """

        i = 1
        for part in self._partitions:
            if part.filesystem == SDCardPartition.FILESYSTEM_VFAT:
                cmd = 'sudo mkfs.vfat %s -n %s' % (part.device, part.name)
            elif part.filesystem == SDCardPartition.FILESYSTEM_EXT3:
                cmd = 'sudo mkfs.ext3 %s -L %s'  % (part.device, part.name)
            elif (part.filesystem == SDCardPartition.FILESYSTEM_EXT4 or
                  part.filesystem == SDCardPartition.FILESYSTEM_EXT4_WRITEBACK):
                cmd = 'sudo mkfs.ext4 %s -L %s'  % (part.device, part.name)
            else:
                raise DeviceException("Can't format partition %s, unknown "
                              "filesystem: %s" % (part.name, part.filesystem))
            if self._e.check_call(cmd) != 0:
                raise DeviceException('Unable to format %s into %s' %
                                (part.name, part.device))
            i += 1   
        if self._partitions:
            self.sync()
    
    def mount(self, directory):
        """
        Mounts the partitions in the specified directory.
        
        I.e., if the partitions are called "boot" and "rootfs", and the given
        directory is "/media", this function will mount:
        
           - /media/boot
           - /media/rootfs
        
        :param directory: Directory where to mount the partitions.
        :exception DeviceException: When unable to mount.
        """
        
        i = 1
        for part in self._partitions:
            mnt_dir = "%s/%s" % (directory.rstrip('/'), part.name)
            if self._e.check_call('mkdir -p %s' % mnt_dir) != 0:
                raise DeviceException('Failed to create directory %s' % mnt_dir)
            # Map the partition's fs to a type that the 'mount' understands
            fs_type = None
            if part.filesystem == SDCardPartition.FILESYSTEM_VFAT:
                fs_type = 'vfat'
            elif part.filesystem == SDCardPartition.FILESYSTEM_EXT3:
                fs_type = 'ext3'
            elif (part.filesystem == SDCardPartition.FILESYSTEM_EXT4 or
                  part.filesystem == SDCardPartition.FILESYSTEM_EXT4_WRITEBACK):
                fs_type = 'ext4'
            if fs_type:
                cmd = 'sudo mount -t %s %s %s' % (fs_type, part.device, mnt_dir)
            else:
                cmd = 'sudo mount %s %s' % (part.device, mnt_dir) # let mount guess
            if self._e.check_call(cmd) != 0:
                raise DeviceException('Failed to mount %s in %s' % 
                                      (part.device, mnt_dir))
            i += 1
    
    def unmount(self):
        for part in self._partitions:
            if part.device:
                self.sync()
                ret = self._e.check_call('sudo umount %s' % part.device)
                if ret != 0:
                    raise DeviceException('Failed to unmount %s' % part.device)
        Device.unmount(self)
    
    def optimize_filesystems(self):
        """
        Optimize the filesystems, if applies.
        
        Optimizations supported:
          - FILESYSTEM_EXT4_WRITEBACK: Sets the data mode to "writeback",
              disabling journaling.
            
        Note: The device should be unmounted before running optimizations.
        
        :exception DeviceException: When unable to optimize.
        """
        
        for part in self._partitions:
            if part.filesystem == SDCardPartition.FILESYSTEM_EXT4_WRITEBACK:
                cmd = "sudo tune2fs -o journal_data_writeback %s" % part.device
                ret = self._e.check_call(cmd)
                if ret != 0:
                    raise DeviceException('Failed optimizing %s' % self.name)
                cmd = "sudo tune2fs -O ^has_journal %s" % part.device
                ret = self._e.check_call(cmd)
                if ret != 0:
                    raise DeviceException('Failed optimizing %s' % self.name)
    
    def check_filesystems(self):
        """
        Checks the integrity of the filesystems in the given device. Upon 
        error, tries to recover using the 'fsck' command.
        
        Note: The device should be unmounted before running this check.
        
        :exception DeviceException: When a fileystem has an error.
        """
        
        # The exit code returned by fsck is the sum of the following conditions
        fsck_outputs = {0    : 'No errors',
                        1    : 'Filesystem errors corrected',
                        2    : 'System should be rebooted',
                        4    : 'Filesystem errors left uncorrected',
                        8    : 'Operational error',
                        16   : 'Usage or syntax error',
                        32   : 'fsck canceled by user request',
                        128  : 'Shared-library error'}
        
        fs_ok = True
        for part in self._partitions:
            states = []
            self.sync()
            ret = self._e.check_call("sudo fsck -y %s" % part.device)
            if ret == 0:
                states.append(fsck_outputs[ret])
            else:
                for i in range(len(fsck_outputs)):
                    key = 2 ** i
                    if ret & key:
                        try:
                            states.append(fsck_outputs[key])
                            if key != 1: # keys not counted as fatal errors
                                fs_ok = False
                        except KeyError:
                            pass
            states_str = ''.join("'%s', " % s for s in states).rstrip(', ')
            msg = ("Filesystem check in %s: %s (see 'man fsck', exit code: %s)"
                   % (part.device, states_str, ret))
            if fs_ok:
                self._l.debug(msg)
            else:
                raise DeviceException(msg)
    
    def detach_device(self):
        ret = self._e.check_call('sudo losetup -d %s' % self.name)
        if ret != 0:
            raise DeviceException('Failed detaching %s' % self.name)
    
    def detach_partitions(self):
        for part in self._partitions:
            if part.device:
                ret = self._e.check_call('sudo losetup -d %s' % part.device)
                if ret != 0:
                    raise DeviceException('Failed detaching %s' % part.device)
                part.device = None
    
    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        """
        
        self._partitions[:] = []
        self._partitions = read_loopdevice_partitions(filename)

class USB(Device):

    def __init__(self, device, dryrun=False):
        """
        :param device: Device associated with this instance, i.e. '/dev/sdb/'.
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        
        Device.__init__(self, device, dryrun)
        self._geometry = USBGeometry()
        self._partitions = []
        
    @property
    def partitions(self):
        """
        Returns the list of partitions (:class:`USBPartition`) associated
        with this USB drive.
        """
        
        return self._partitions
        
    def min_cyl_size(self):
        """
        Sums all the partitions' sizes and returns the total. It is actually
        the minimum size because there could be partitions which size is
        unknown as they can be specified to take as much space as they can.
        The size calculated for such partitions is 1 cylinder - their minimum,
        and hence the total size is also minimum.
        
        Additionally to the partitions' size, the total includes 1 cylinder
        for the Master Boot Record.
        """
        
        # Leave room for the MBR
        min_cyl_size = 1
        for part in self._partitions:
            if part.size == self.geometry.full_size:
                # If size is unspecified, at least estimate 1 cylinder for
                # that partition
                min_cyl_size += 1
            else:
                min_cyl_size += int(part.size)
        return min_cyl_size
        
    def partition_name(self, index):
        return '%s%s' % (self.name, index)  # i.e. /dev/sdb1
        
    def create_partitions(self):
        """
        Create the partitions in the given device.
        
        :exception DeviceException: When unable to partition.
        """
        
        cmd = ('sudo sfdisk -D' +
              ' -C' + str(int(self.size_cyl)) +
              ' -H' + str(int(self.geometry.heads)) +
              ' -S' + str(int(self.geometry.sectors)) +
              ' '   + self.name + ' << EOF\n')
        for part in self._partitions:
            cmd += str(part.start) + ','
            cmd += str(int(self.size_cyl)) + ','
            cmd += str(part.type)
            if part.is_bootable: cmd += ',*'
            cmd += '\n'
        cmd += 'EOF'
        if self._e.check_call(cmd) != 0:
            raise DeviceException('Unable to partition device %s' % self.name)
        
    def format_partitions(self):
        """
        Format the partitions in the given device, assuming these partitions
        were already created (see create_partitions()). To register partitions
        use read_partitions().
        
        :exception DeviceException: When unable to format.
        """

        i = 1
        for part in self._partitions:
            filename = self.partition_name(i)
            if part.filesystem == USBPartition.FILESYSTEM_VFAT:
                cmd = 'sudo mkfs.vfat -F 32 %s -n %s' % (filename, part.name)
            elif part.filesystem == USBPartition.FILESYSTEM_EXT3:
                cmd = 'sudo mkfs.ext3 %s -L %s'  % (filename, part.name)
            elif (part.filesystem == USBPartition.FILESYSTEM_EXT4 or
                  part.filesystem == USBPartition.FILESYSTEM_EXT4_WRITEBACK):
                cmd = 'sudo mkfs.ext4 %s -L %s'  % (filename, part.name)
            else:
                raise DeviceException("Can't format partition %s, unknown "
                              "filesystem: %s" % (part.name, part.filesystem))
            if self._e.check_call(cmd) != 0:
                raise DeviceException('Unable to format %s into %s' %
                                (part.name, filename))
            i += 1   
        if self._partitions:
            self.sync()
        
    def mount(self, directory):
        """
        Mounts the partitions in the specified directory.
        
        I.e., if the partitions are called "boot" and "rootfs", and the given
        directory is "/media", this function will mount:
        
           - /media/boot
           - /media/rootfs
        
        :param directory: Directory where to mount the partitions.
        :exception DeviceException: When unable to mount.
        """
        
        i = 1
        for part in self._partitions:
            name = self.partition_name(i)
            mnt_dir = "%s/%s" % (directory.rstrip('/'), part.name)
            if self._e.check_call('mkdir -p %s' % mnt_dir) != 0:
                raise DeviceException('Failed to create directory %s' % mnt_dir)
            # Map the partition's fs to a type that the 'mount' understands
            fs_type = None
            if part.filesystem == USBPartition.FILESYSTEM_VFAT:
                fs_type = 'vfat'
            elif part.filesystem == USBPartition.FILESYSTEM_EXT3:
                fs_type = 'ext3'
            elif (part.filesystem == USBPartition.FILESYSTEM_EXT4 or 
                  part.filesystem == USBPartition.FILESYSTEM_EXT4_WRITEBACK):
                fs_type = 'ext4'
            if fs_type:
                cmd = 'sudo mount -t %s %s %s' % (fs_type, name, mnt_dir)
            else:
                cmd = 'sudo mount %s %s' % (name, mnt_dir) # let mount guess
            if self._e.check_call(cmd) != 0:
                raise DeviceException('Failed to mount %s in %s' % 
                                      (name, mnt_dir))
            i += 1

    def optimize_filesystems(self):
        """
        Optimize the filesystems, if applies.
        
        Optimizations supported:
          - FILESYSTEM_EXT4_WRITEBACK: Sets the data mode to "writeback",
              disabling journaling.
            
        Note: The device should be unmounted before running optimizations.
        
        :exception DeviceException: When unable to optimize.
        """
        
        i = 1
        for part in self._partitions:
            filename = self.partition_name(i)
            if part.filesystem == USBPartition.FILESYSTEM_EXT4_WRITEBACK:
                cmd = "sudo tune2fs -o journal_data_writeback %s" % filename
                ret = self._e.check_call(cmd)
                if ret != 0:
                    raise DeviceException('Failed optimizing %s' % filename)
                cmd = "sudo tune2fs -O ^has_journal %s" % filename
                ret = self._e.check_call(cmd)
                if ret != 0:
                    raise DeviceException('Failed optimizing %s' % filename)
            i = i + 1

    def check_filesystems(self):
        """
        Checks the integrity of the filesystems in the given device. Upon 
        error, tries to recover using the 'fsck' command.
        
        Note: The device should be unmounted before running this check.
        
        :exception DeviceException: When a filesystem has an error.
        """
        
        # The exit code returned by fsck is the sum of the following conditions
        fsck_outputs = {0    : 'No errors',
                        1    : 'Filesystem errors corrected',
                        2    : 'System should be rebooted',
                        4    : 'Filesystem errors left uncorrected',
                        8    : 'Operational error',
                        16   : 'Usage or syntax error',
                        32   : 'fsck canceled by user request',
                        128  : 'Shared-library error'}
        
        fs_ok = True
        for i in range(1, len(self._partitions) + 1):
            states = []
            filename = self.partition_name(i)
            self.sync()
            ret = self._e.check_call("sudo fsck -y %s" % filename)
            if ret == 0:
                states.append(fsck_outputs[ret])
            else:
                for i in range(len(fsck_outputs)):
                    key = 2 ** i
                    if ret & key:
                        try:
                            states.append(fsck_outputs[key])
                            if key != 1: # keys not counted as fatal errors
                                fs_ok = False
                        except KeyError:
                            pass
            states_str = ''.join("'%s', " % s for s in states).rstrip(', ')
            msg = ("Filesystem check in %s: %s (see 'man fsck', exit code: %s)"
                   % (filename, states_str, ret))
            if fs_ok:
                self._l.debug(msg)
            else:
                raise DeviceException(msg)

    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        """
        
        self._partitions[:] = []
        self._partitions = read_usb_partitions(filename)
        
