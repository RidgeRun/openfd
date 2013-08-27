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

"""
SD-card operations to support the installer.
"""

# ==========================================================================
# Imports
# ==========================================================================

import os
import math
from partition import Partition
import component
import geometry
import ConfigParser
import rrutils

# ==========================================================================
# Public Classes
# ==========================================================================

class SDCardInstaller(object):
    """
    Class to handle SD-card operations.
    """

    # Used to warn the user when partitioning a device above this size
    WARN_DEVICE_SIZE_GB = 128
    
    # Used for dangerous warning messages
    WARN_COLOR = 'yellow'
    
    # Used to indicate the installation mode
    MODE_SD = 'sd'
    MODE_LOOPBACK = 'loopback'
    
    def __init__(self, comp_installer):
        """
        Constructor.
        """
        
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._dryrun = False
        self._interactive = True
        self._partitions = []
        self._executer.logger = self._logger
        self._comp_installer = comp_installer
        self._loopdevice_partitions = {}
        self._device = None
        self._mode = None
    
    def set_mode(self, mode):
        """
        Sets the mode.
        """
        self._mode = mode
    
    def get_mode(self):
        """
        Gets the mode.
        """
        return self._mode
    
    def set_device(self, device):
        """
        Sets the device.
        """
        self._device = device
    
    def get_device(self):
        """
        Gets the device.
        """
        return self._device
    
    def _confirm_device_size(self):
        """
        Checks the device's size against WARN_DEVICE_SIZE_GB, if it's bigger
        it warns the user that the device does not look like an SD card.
        
        Returns true if the user confirms the device is an SD card; false
        otherwise. 
        """
        
        device = self._device
        
        size_is_good = True
        size_gb = self.get_device_size_gb() 
        
        if size_gb > SDCardInstaller.WARN_DEVICE_SIZE_GB:
            
            msg = ('Device %s has %d gigabytes, it does not look like an '
                   'SD card' % (device, size_gb))
            
            msg_color = SDCardInstaller.WARN_COLOR 
            
            confirmed = self._executer.prompt_user(msg, msg_color)
                 
            if not confirmed:
                size_is_good = False
            
        return size_is_good
    
    def _confirm_device_auto_unmount(self):
        """
        Checks for mounted partitions on the device, if there are it warns
        the user that the partitions will be auto-unmounted.
        
        Returns true if the user confirms the auto-unmount operations; false
        otherwise. 
        """
        
        device = self._device
        
        auto_unmount = True
        
        partitions = self.get_device_mounted_partitions()
        
        if partitions:
        
            msg = ('The following partitions from device %s will be '
                   'unmounted:\n' % device)
            
            for part in partitions:
                msg += part + '\n'
        
            msg_color = SDCardInstaller.WARN_COLOR
            confirmed = self._executer.prompt_user(msg, msg_color)
        
            if not confirmed:
                auto_unmount = False
        
        return auto_unmount
    
    def _min_total_cyl_size(self):
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
            if part.size == geometry.FULL_SIZE:
                # If size is unspecified, at least estimate 1 cylinder for
                # that partition
                min_cyl_size += 1
            else:
                min_cyl_size += int(part.size)
        
        return min_cyl_size
            
    def __set_dryrun(self, dryrun):
        """
        Sets on/off the dryrun mode. In dryrun mode any commands will
        not be executed (just logged).
        """
        
        self._dryrun = dryrun
        self._comp_installer.dryrun = dryrun
        self._executer.dryrun = dryrun
    
    def __get_dryrun(self):
        """
        Returns true if the dryrun mode is on; false otherwise.
        """
        
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Gets or sets the dryrun mode.""")
    
    def __set_interactive(self, interactive):
        """
        Sets on/off the interactive mode. In interactive mode the user
        will be prompted before some actions, such as partitioning a device.
        When the interactive mode is off, it will run non-interactively.
        """
        
        self._interactive = interactive
    
    def __get_interactive(self):
        """
        Returns true if the interactive mode is on; false otherwise.
        """
        
        return self._interactive
    
    interactive = property(__get_interactive, __set_interactive,
                           doc="""Gets or sets the interactive mode.""")

    def get_device_size_gb(self):
        """
        Returns the given device size, in gigabytes.
        """
        
        size_b = self.get_device_size_b()
        return long(size_b >> 30)

    def get_device_size_b(self):
        """
        Returns the given device size, in bytes.
        """
        
        device = self._device
        
        size   = 0
        
        cmd = 'sudo fdisk -l ' + device + ' | grep ' + device + \
                  ' | grep Disk | cut -f 5 -d " "'
        
        output = self._executer.check_output(cmd)[1]

        if not self._dryrun:
            if not output:
                self._logger.error('Unable to obtain the size for %s' % device)
            else:
                size = long(output)
        
        return size
    
    def get_device_size_cyl(self):
        """
        Returns the given device size, in cylinders.
        """
        
        size_b = self.get_device_size_b()
        size_cyl = size_b / geometry.CYLINDER_BYTE_SIZE 
        
        return int(math.floor(size_cyl))
    
    def get_partition_suffix(self, partition_index):
        """
        This function returns a string with the standard partition numeric
        suffix, depending on the type of device.
        
        For example, the first partition (index = 1) in device
        /dev/sdb is going to have the suffix "1", so that one can compose
        the complete partition's filename: /dev/sdb1. While a device like
        /dev/mmcblk0 will provoke a partition suffix "p1", so that the complete
        filename for the first partition is "/dev/mmcblk0p1".  
        """
        
        device = self._device
        
        suffix = ''
        
        if device.find('mmcblk') != -1 or device.find('/dev/loop') != -1:
            suffix = 'p' + str(partition_index)
        else:
            suffix = str(partition_index)
        
        return suffix
    
    def get_partition_filename(self, partition_index):
        # Get the complete filename for the partition (i.e. /dev/sdb1)
        device_part = self._device + \
                        self.get_partition_suffix(partition_index)
            
        if self._mode == self.MODE_LOOPBACK:
                device_part = self._loopdevice_partitions[device_part]
        return device_part
    
    def get_device_mounted_partitions(self):
        """
        Returns a list with the mounted partitions from the given device.
        """
        
        device = self._device
        
        partitions = []
        
        cmd = 'mount | grep ' + device + '  | cut -f 3 -d " "'
        output = self._executer.check_output(cmd)[1]
        
        if output:
            partitions = output.strip().split('\n')
        
        return partitions
    
    def device_exists(self):
        """
        Returns true if the device exists, false otherwise.
        """
        
        device = self._device

        exists  = True
        
        cmd = 'sudo fdisk -l ' + device + ' 2>/dev/null'
        
        output = self._executer.check_output(cmd)[1]
        
        if not output:
            exists = False
            
        return exists
    
    def device_is_mounted(self):
        """
        Returns true if the device is mounted or if it's part of a RAID array,
        false otherwise.
        """
        
        device = self._device
        
        is_mounted = False
        
        cmd1 = 'grep --quiet ' + device + ' /proc/mounts'
        cmd2 = 'grep --quiet ' + device + ' /proc/mdstat'
        
        if self._executer.check_call(cmd1) == 0: is_mounted = True
        if self._executer.check_call(cmd2) == 0: is_mounted = True
        
        return is_mounted
    
    def mount_partitions(self, directory):
        """
        Mounts the partitions of the given device in the specified directory.
        To register partitions use read_partitions().
        
        I.e., if the partitions are called "boot" and "rootfs", and the given
        dir is "/media", this function will mount:
        
           /media/boot
           /media/rootfs
        
        Returns true on success; false otherwise.
        """
        
        device = self._device
        
        directory = directory.rstrip('/')
        if not os.path.isdir(directory):
            self._logger.error('Directory %s does not exist' % directory)
            return False
        
        partition_index = 1
        for part in self._partitions:
        
            # Get the complete filename for the partition (i.e. /dev/sdb1)
            device_part = self.get_partition_filename(partition_index)
                            
            mount_point = directory + '/' + part.name
        
            # Create the directory where to mount
            
            cmd = 'mkdir -p ' + mount_point
            if self._executer.check_call(cmd) != 0:
                self._logger.error('Failed to create directory %s' %
                                   mount_point)
                return False
            
            # Map the partition's filesystem to a type that the 'mount'
            # command understands
            
            part_type = None
            
            if part.filesystem == Partition.FILESYSTEM_VFAT:
                part_type = 'vfat'
            elif part.filesystem == Partition.FILESYSTEM_EXT3:
                part_type = 'ext3'
            
            # Now mount
            
            if part_type:
                cmd = 'sudo mount -t ' + part_type + ' ' + device_part + ' ' + \
                      mount_point
            else:
                # Let mount try to guess the partition type
                cmd = 'sudo mount ' + device_part + ' ' + mount_point
            
            if self._executer.check_call(cmd) != 0:
                self._logger.error('Failed to mount %s in %s' % (device_part,
                                                                 mount_point))        
                return False
            
            partition_index += 1
            
        return True
    
    def auto_unmount_partitions(self):
        """
        Auto-unmounts the partitions of the given device.
        
        Returns true on success; false otherwise.
        """
        
        partitions = self.get_device_mounted_partitions()
        
        for part in partitions:
        
            cmd = 'sudo umount ' + part
            
            if self._executer.check_call(cmd) != 0:
                self._logger.error('Failed to unmount %s' % part)
                return False
        
        return True
    
    def create_partitions(self):
        """
        Create the partitions in the given device. To register
        partitions use read_partitions().
        
        Returns true on success; false otherwise
        """
        
        device = self._device
        
        cylinders = self.get_device_size_cyl()
        heads     = int(geometry.HEADS)
        sectors   = int(geometry.SECTORS)
        
        # Check we were able to get correctly the device size
        if cylinders == 0 and not self._dryrun:
            self._logger.error('Unable to partition device %s (size is 0)' %
                               device)
            return False
        
        # Check we have enough size to fit all the partitions and the MBR.
        if cylinders < self._min_total_cyl_size() and not self._dryrun:
            self._logger.error('Size of partitions is too large to fit in %s' %
                               device)
            return False

        # Just before creating the partitions, prompt the user
        if self._interactive and self._mode != self.MODE_LOOPBACK:
            
            msg = ('You are about to repartition your device %s '
                   '(all your data will be lost)' % device)
            
            msg_color = SDCardInstaller.WARN_COLOR
            
            confirmed = self._executer.prompt_user(msg, msg_color)
                
            if not confirmed:
                return False
            
        # Create the partitions        
        cmd = 'sudo sfdisk -D' + \
              ' -C' + str(cylinders) + \
              ' -H' + str(heads) + \
              ' -S' + str(sectors) + \
              ' '   + device + ' << EOF\n'
  
        for part in self._partitions:
            cmd += str(part.start) + ','
            cmd += str(part.size) + ','
            cmd += str(part.type)
            if part.is_bootable():
                cmd += ',*'
            cmd += '\n'
        
        cmd += 'EOF'
        
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Unable to partition device %s' % device)
            return False
        
        return True

    def format_partitions(self):
        """
        Format the partitions in the given device, assuming these partitions
        were already created (see create_partitions()). To register partitions
        use read_partitions().
        
        Returns true on success; false otherwise.
        """
        
        partition_index = 1
        
        for part in self._partitions:
            
            # Get the complete filename for the partition (i.e. /dev/sdb1)
            device_part = self.get_partition_filename(partition_index)
            
            # Format
            cmd = ''
            if part.filesystem == Partition.FILESYSTEM_VFAT:
                cmd  = 'sudo mkfs.vfat -F 32 '
                cmd += device_part + ' -n ' + part.name
            elif part.filesystem == Partition.FILESYSTEM_EXT3:
                cmd  = 'sudo mkfs.ext3 ' + device_part
                cmd += ' -L ' + part.name
            else:
                msg = ("Can't format partition %s, unknown filesystem: %s" %
                       (part.name, part.filesystem))
                self._logger.error(msg)
                return False
            
            if cmd:
                if self._executer.check_call(cmd) == 0:
                    msg = ('Formatted %s (%s) into %s' % (part.name,
                                                          part.filesystem,
                                                          device_part))
                    partition_index += 1
                else:
                    self._logger.error('Unable to format %s into %s' %
                                       (part.name, device_part))
                    return False
        
        return True

    def format_sd(self, filename):
        """
        This function will create and format the partitions as specified
        by 'mmap-config-file' to the sd-card referenced by 'device'.
        
        Returns true on success; false otherwise. 
        """
        
        device = self._device
        
        # Dummy check to try to verify with the user if the device is
        # actually an SD card
        if self._interactive:
            if self._confirm_device_size() is False:
                return False
        
        # Check device existence
        if not self.device_exists() and not self._dryrun:
            self._logger.info('Try inserting the SD card again and '
                               'unmounting the partitions')
            self._logger.error('No valid disk is available on %s' % device)
            return False
        
        # Check device is not mounted
        if self.device_is_mounted() and not self._dryrun:
            
            if self._interactive:
                if self._confirm_device_auto_unmount() is False:
                    return False
                
            # Auto-unmount
            if not self.auto_unmount_partitions():
                self._logger.error('Failed auto-unmounting %s, refusing to '
                                   'install' % device)
                return False
        
        # Read the partitions
        self._logger.info('Reading %s ...' % filename)
        if not self.read_partitions(filename):    
            return False
        
        # Create partitions
        self._logger.info('Creating partitions on %s ...' % device)
        if not self.create_partitions():
            return False
        
        # Format partitions
        self._logger.info('Formatting partitions on %s ...' % device)
        if not self.format_partitions():
            return False
        
        return True
    
    def _test_image_size(self, image_size):
        """
        Test that the image will be big enough to hold the partitions.
        
        Returns true on success; false otherwise.
        """
        
        image_size_bytes = int(image_size) << 20
        image_size_cyl = image_size_bytes / geometry.CYLINDER_BYTE_SIZE
        
        if image_size_cyl < self._min_total_cyl_size():
            image_min_size_needed = (self._min_total_cyl_size() * 
                                    geometry.CYLINDER_BYTE_SIZE)
            image_min_size_needed = int(image_min_size_needed) >> 20
            self._logger.error('Image size of %s MB is too small to hold the '
                                'partitions, the image must be bigger than %s MB '
                                'to hold them.' %(image_size, 
                                                  image_min_size_needed))
            return False
        return True
    
    def _create_image_file(self, image_name, image_size):
        """
        Creates the image file with a valid format.
        It associates the file with a loopdevice. 
        
        Returns true on success; false otherwise.
        """
        
        cmd =  'dd if=/dev/zero of=%s bs=1M count=%s' % (image_name,
                                                         image_size)
        ret = self._executer.check_call(cmd)
        if ret != 0:
            self._logger.error('Failed to create file for the image %s'
                               % image_name)
            return False
                
        cmd = 'sudo losetup -f'
        ret, loopdevice = self._executer.check_output(cmd)
        if ret == 0:
            loopdevice = loopdevice.rstrip('\n')
            self.set_device(loopdevice)
            cmd = 'sudo losetup %s %s' % (self._device,  image_name)
            ret = self._executer.check_call(cmd)
            
            if ret != 0:
                self._logger.error('Failed to associate image file %s to %s'
                                   % (image_name, self._device))
                return False
        else:
            self._logger.error('Failed when searching free loop devices')
            return False
        
        # If we want to reuse the code for creating and formatting partitions
        # the image needs to have a valid format
        cmd = 'sudo mkfs.vfat -F 32 %s -n tmp' % self._device
        ret = self._executer.check_call(cmd)
        if ret != 0:
            self._logger.error('Failed to format a temporal filesystem on %s'
                               % image_name)
            return False
        
        return True
    
    def _associate_loopdevice_partitions(self, image_name):
        """
        Associates parts of the image file to an available /dev/loop*,
        so that it works as a device partition.
        
        Returns true on success; false otherwise.
        """
        
        partition_index = 1
        for part in self._partitions:
            device_part = self._device + \
                            self.get_partition_suffix(partition_index)
            
            cmd = 'sudo losetup -f'
            ret, free_device = self._executer.check_output(cmd)
            
            if ret != 0:
                self._detach_loopdevice()
                self._logger.error('Can not find a free loopdevice')
                return False
            
            free_device = free_device.rstrip('\n')
            self._loopdevice_partitions[device_part] = free_device
            offset = int(part.start)*int(geometry.CYLINDER_BYTE_SIZE)
            if part.size == '-':
                cmd = 'sudo losetup -o %s %s %s' % (offset, free_device,
                                                        image_name)
            else:
                part_size = int(int(part.size)*geometry.CYLINDER_BYTE_SIZE)
                cmd = ('sudo losetup -o %s --sizelimit %s %s %s' 
                           % (offset, part_size, free_device, image_name))
                
            ret = self._executer.check_call(cmd)
            
            partition_index += 1
        return True
    
    def format_loopdevice(self, filename, image_name, image_size):
        """
        This method will create an image file, this file contains
        the formatted the partitions as specified by 'mmap-config-file'.
        This image can later be set on an sdcard.
        
        This method recieves:
        filename -> the mmap-config-file
        image_name -> the name(with path) of the image file to be created
        image_size -> the size in MB for the image file
        
        Returns true on success; false otherwise. 
        """
        
        # Read the partitions
        self._logger.info('Reading %s ...' % filename)
        if not self.read_partitions(filename): return False
        
        # test image file size
        self._logger.info('Testing size of image file %s...' % image_name)
        if not self._test_image_size(image_size): return False
        
        # Create image file
        self._logger.info('Creating image file %s' % image_name)
        if not self._create_image_file(image_name, image_size): return False
        
        # Create partitions
        self._logger.info('Creating partitions on %s ...' % self._device)
        if not self.create_partitions():
            return False
        
        # Create partitions
        self._logger.info('Associating partitions for loopdevice...')
        if not self._associate_loopdevice_partitions(image_name): return False
        
        # Format partitions
        self._logger.info('Formatting partitions on %s ...'
                          % self._device)
        if not self.format_partitions(): return False
        
        return True
    
    def _detach_loopdevice(self):
        """
        Detach all loopdevices associated with a partition, also it detaches
        the image.
        
        Returns true on success; false otherwise.
        """
        
        for dev in self._loopdevice_partitions.itervalues():
            cmd = 'sudo losetup -d %s' % dev
            ret = self._executer.check_call(cmd)
            if ret != 0:
                self._logger.error('Failed releasing loopdevice %s' %dev)
                return False
        
        cmd = 'sudo losetup -d %s' % self._device
        ret = self._executer.check_call(cmd)
        if ret != 0:
            self._logger.error('Failed releasing loopdevice %s'
                               % self._device)
            return False
        self._loopdevice_partitions.clear()
        
        return True
    
    def release_loopdevice(self):
        """
        Releases all loopdevices used when creating an image file.
        Should be run after finishing the process.
        
        Returns true on success; false otherwise.
        """
        
        # Unmount partitions
        for dev in self._loopdevice_partitions.itervalues():
            cmd = 'sync'
            ret = self._executer.check_call(cmd)
            if ret != 0:
                self._logger.error('unable  to sync loopdevice %s' %dev)
                return False
            cmd = 'sudo umount %s' % dev
            ret = self._executer.check_call(cmd)
            if ret != 0:
                self._logger.error('Failed unmounting loopdevice %s' %dev)
                return False
        
        # do a filesystem check
        ret = self.check_filesystems()
        if not ret:
            self._logger.error('Failed image filesystem check')
            return False
        
        # detach loopdevice
        if not self._detach_loopdevice(): return False
        
        return True
    
    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        Returns true on success; false otherwise.  
        """
        
        # Reset the partitions list
        
        self._partitions[:] = []
        
        if not os.path.exists(filename):
            self._logger.error('File %s does not exist' % filename)
            return False
        
        config = ConfigParser.RawConfigParser()
        config.readfp(open(filename))
        
        for section in config.sections():
            
            part = None
            
            if config.has_option(section, 'name'):
                part = Partition(config.get(section, 'name'))
            
            if part:
                if config.has_option(section, 'start'):
                    part.start = config.get(section, 'start')
                    
                if config.has_option(section, 'size'):
                    part.size = config.get(section, 'size')
                    
                if config.has_option(section, 'bootable'):
                    part.bootable = config.getboolean(section, 'bootable')
                
                if config.has_option(section, 'type'):
                    part.type = config.get(section, 'type')
                    
                if config.has_option(section, 'filesystem'):
                    part.filesystem = config.get(section, 'filesystem')
                
                if config.has_option(section, 'components'):
                    components = config.get(section, 'components')
                    components = components.strip(', ')
                    part.components = components.replace(' ','').split(',')
                
                self._partitions.append(part)
        return True
    
    def check_filesystems(self):
        """
        Checks the integrity of the filesystems in the given device. Upon 
        error, tries to recover using the 'fsck' command.
        
        Returns true on success; false otherwise.
        """
        
        device = self._device
        
        if not self.device_exists() and not self._dryrun:
            self._logger.error("Device %s doesn't exist" % device)
            return False
        
        if self.device_is_mounted():
            if not self.auto_unmount_partitions():
                self._logger.error("Can't unmount partitions from %s" % device)
                return False
        
        # According to 'man fsck' the exit code returned by fsck is the sum
        # of the following conditions
        fsck_outputs = {0    : 'no errors',
                        1    : 'filesystem errors corrected',
                        2    : 'system should be rebooted',
                        4    : 'filesystem errors left uncorrected',
                        8    : 'operational error',
                        16   : 'usage or syntax error',
                        32   : 'fsck canceled by user request',
                        128  : 'shared-library error'}
        
        fs_ok = True
        
        for partition_index in range(1,len(self._partitions)+1):
            fs_state = ''
            device_part = self.get_partition_filename(partition_index)
            cmd = "sudo fsck -y " + device_part
            ret = self._executer.check_call(cmd)
            if ret == 0 or ret == 1:
                fs_state += fsck_outputs[ret]
            else:
                for i in range(len(fsck_outputs)):
                    key = 2 ** i
                    if ret & key:
                        fs_state += fsck_outputs[key]
                        fs_ok = False
            self._logger.info('%s filesystem condition: %s' % (device_part,
                                                               fs_state))
            
            if not fs_ok: break
            
        return fs_ok
    
    def install_components(self):
        """
        Installs the specified components for each partition.
        
        Returns true on success, false otherwise.
        """
        
        device = self._device
        
        partition_index = 1
        
        for part in self._partitions:
            
            device_part = self.get_partition_filename(partition_index)
            
            cmd = 'mount | grep ' + device_part + '  | cut -f 3 -d " "'
            ret, output = self._executer.check_output(cmd)
            mount_point = output.replace('\n', '')
            
            for component in part.components:
                
                if component == Partition.COMPONENT_BOOTLOADER:
                    ret = self._comp_installer.install_uboot(device)
                    if ret is False: return False
                    
                    ret =  self._comp_installer.install_uboot_env(mount_point)
                    if ret is False: return False
                    
                elif component == Partition.COMPONENT_KERNEL:
                    ret = self._comp_installer.install_kernel(mount_point)
                    if ret is False: return False
                    
                elif component == Partition.COMPONENT_ROOTFS:
                    if self._comp_installer.rootfs is None:
                        # This is valid because rootfs argument is optional
                        msg = ('No directory specified for "%s" '
                                   ' omitting...' %
                                   (Partition.COMPONENT_ROOTFS))
                        self._logger.info(msg)
                    else:
                        ret = self._comp_installer.install_rootfs(mount_point)
                        if ret is False: return False
                
                elif component == Partition.COMPONENT_BLANK:
                    pass
                
                else:
                    self._logger.error('Component %s is not valid' % component)
                    return False
                
            partition_index += 1
        
        return True
                
    def __str__(self):
        """
        To string.
        """
        
        _str  = ''
        _str += 'Interactive: ' + ('On' if self._interactive else "Off") + '\n'
        _str += 'Dryrun mode: ' + ('On' if self._dryrun else "Off") + '\n'
        _str += 'Partitions: ' + '\n'
        for part in self._partitions:
            _str +=  part.__str__()
        return _str

# ==========================================================================
# Test cases
# ==========================================================================

if __name__ == '__main__':

# ==========================================================================
# Test cases  - Support functions
# ==========================================================================

    import time

    def tc_start(tc_id, sleep_time=1):
        """
        Sleeps for 'sleep_time' and then prints the given test case header.
        """
        
        tc_header  = '=' * 20
        tc_header += 'TEST CASE ' + str(tc_id)
        tc_header += '=' * 20
        
        time.sleep(sleep_time)
        print tc_header

# ==========================================================================
# Test cases  - Initialization
# ==========================================================================

    # Devdir info
    devdir = ''
    
    try:
        if os.environ['DEVDIR']:
            devdir = os.environ['DEVDIR'] 
    except KeyError:
        print 'Unable to obtain $DEVDIR from the environment.'
        exit(-1)

    # Initialize the logger
    rrutils.logger.basic_config(verbose=True)
    logger = rrutils.logger.get_global_logger('sdcard-test')
    
    # Component installer
    
    uflash_bin = devdir + \
       '/bootloader/u-boot-2010.12-rc2-psp03.01.01.39/src/tools/uflash/uflash'
    ubl_file = devdir + '/images/ubl_DM36x_sdmmc.bin'
    uboot_file = devdir + '/images/bootloader'
    uboot_entry_addr = '0x82000000' # 2181038080
    uboot_load_addr = '2181038080' # 0x82000000
    kernel_image = devdir + '/images/kernel.uImage'
    rootfs = devdir + '/fs/fs'
    workdir = devdir + "/images"

    comp_installer = component.ComponentInstaller()
    
    comp_installer.uflash_bin = uflash_bin
    comp_installer.ubl_file = ubl_file
    comp_installer.uboot_file = uboot_file
    comp_installer.uboot_entry_addr = uboot_entry_addr
    comp_installer.uboot_load_addr = uboot_load_addr
    comp_installer.kernel_image = kernel_image
    comp_installer.rootfs = rootfs
    comp_installer.workdir = workdir
    
    # SD card installer 
    
    sd_installer = SDCardInstaller(comp_installer)
    
    # The following test cases will be run over the following device,
    # in the given dryrun mode, unless otherwise specified in the test case.
    
    # WARNING: Dryrun mode is set by default, but be careful
    # you don't repartition a device you don't want to.
    
    device = "/dev/sdb"
    sd_installer.dryrun = True
    sd_installer.interactive = True
    
# ==========================================================================
# Test cases - Unit tests
# ==========================================================================
    
    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0) 
    
    # Check device existence (positive test case)
    
    sd_installer.set_mode(sd_installer.MODE_SD)
    
    sd_installer.set_device(device)
    
    if sd_installer.device_exists():
        print "Device " + sd_installer.get_device() + " exists."
    else:
        print "Device " + sd_installer.get_device() + " doesn't exist."
    
    # --------------- TC 2 ---------------
    
    tc_start(2)
    
    # Check device existence (negative test case)
    
    temp_device = "/dev/sdbX"
    
    sd_installer.set_device(temp_device)
    
    if sd_installer.device_exists():
        print "Device " + sd_installer.get_device() + " exists."
    else:
        print "Device " + sd_installer.get_device() + " doesn't exist."

    # --------------- TC 3 ---------------
    
    tc_start(3)

    # Check if the device is mounted (positive test case)
    
    sd_installer.set_device(device)
    
    if sd_installer.device_is_mounted():
        print "Device " + sd_installer.get_device() + " is mounted."
    else:
        print "Device " + sd_installer.get_device() + " isn't mounted."
    
    # --------------- TC 4 ---------------
    
    tc_start(4)
        
    # Check if the device is mounted (negative test case)
    
    temp_device = "/dev/sdbX"
    
    sd_installer.set_device(temp_device)
    
    if sd_installer.device_is_mounted():
        print "Device " + sd_installer.get_device() + " is mounted."
    else:
        print "Device " + sd_installer.get_device() + " isn't mounted."
    
    # --------------- TC 5 ---------------
    
    tc_start(5)
    
    # Test read_partitions
    sdcard_mmap_filename = '../../../../../images/sd-mmap.config'
    
    if not os.path.isfile(sdcard_mmap_filename):
        print 'Unable to find ' + sdcard_mmap_filename
        exit(-1)
    
    sd_installer.read_partitions(sdcard_mmap_filename)
    
    print "Partitions at " + sdcard_mmap_filename + " read succesfully." 

    # --------------- TC 6 ---------------
    
    tc_start(6)

    # Test get_device_size_b
    
    sd_installer.set_device(device)
    
    size = sd_installer.get_device_size_b()
    print ("Device " + sd_installer.get_device() + " has " + str(size) + 
           " bytes")

    # --------------- TC 7 ---------------
    
    tc_start(7)

    # Test get_device_size_gb
    
    size = sd_installer.get_device_size_gb()
    print ("Device " + sd_installer.get_device() + " has " + str(size) + 
           " gigabytes")

    # --------------- TC 8 ---------------
    
    tc_start(8)

    # Test get_device_size_cyl
    
    size = sd_installer.get_device_size_cyl()
    print ("Device " + sd_installer.get_device() + " has " + str(size) + 
           " cylinders")

    # --------------- TC 9 ---------------
    
    tc_start(9)

    # Test get_device_mounted_partitions
    
    print "Device " + device + " mounted partitions:"
    print sd_installer.get_device_mounted_partitions()
    
    # --------------- TC 10 ---------------
    
    tc_start(10)
    
    # Test auto_unmount_partitions
    if sd_installer.device_is_mounted():
        print ('Partitions on %s mounted, now will try to auto-unmount' 
               %sd_installer.get_device())
        # Auto-unmount
        if sd_installer.auto_unmount_partitions():
            print 'Partitions on %s unmounted' %sd_installer.get_device()
        else:
            print 'Can not unmount partitions on %s' %sd_installer.get_device()
    else:
        print ('Partitions on %s not mounted, nothing to be done here' 
               %sd_installer.get_device())
    
    # --------------- TC 11 ---------------
    
    tc_start(11)

    # Test create partitions
    
    if not sd_installer.create_partitions():
        print 'failed to create partitions on %s' %sd_installer.get_device()

    # --------------- TC 12 ---------------
    
    tc_start(12)

    # Test get_partition_suffix
    
    devices_list = ['/dev/sdb','/dev/mmcblk0','/dev/loop0']
    
    for i in devices_list:
        sd_installer.set_device(i)
        print 'Partition suffix for %s:' %sd_installer.get_device() 
        print sd_installer.get_partition_suffix('1')
    
    # --------------- TC 13 ---------------
    
    tc_start(13)

    # Test format_partitions
    
    sd_installer.set_device(device)
    
    if sd_installer.format_partitions():
        print 'Partitions on %s formatted' %sd_installer.get_device()
    else:
        print 'Can not format partitions on %s' %sd_installer.get_device()
    
    
    # --------------- TC 14 ---------------
    
    tc_start(14)
    
    # Test _confirm_device_size 
    
    if sd_installer._confirm_device_size() is False:
        print "User declined device as SD card"
    else:
        print "Device " + sd_installer.get_device() + " confirmed as SD card"
 
    # --------------- TC 15 ---------------
    
    tc_start(15)
    
    # Test _confirm_device_auto_unmount

    if sd_installer._confirm_device_auto_unmount() is False:
        print "User declined to auto-unmount"

    # --------------- TC 16 ---------------
    
    tc_start(16)
    
    # Test device_auto_unmount
 
    if sd_installer.auto_unmount_partitions():
        print "Device " + sd_installer.get_device() + " is unmounted"
    else:
        print "Failed auto-unmounting " + sd_installer.get_device()

    
    # --------------- TC 17 ---------------
    
    tc_start(17)

    # Test format sd
    
    sd_installer.set_device(device)
    
    if sd_installer.format_sd(sdcard_mmap_filename):
        print ('Partitions on %s formatted using format_sd method' 
               %sd_installer.get_device())
    else:
        print ('Can not format partitions on %s using format_sd method' 
               %sd_installer.get_device())

    # --------------- TC 18 ---------------
    
    tc_start(18)
    
    # Test to string
    
    print sd_installer.__str__()

    # --------------- TC 16 ---------------
    
    tc_start(16)
    
    # Test mount_partitions
    
    if sd_installer.mount_partitions(devdir + '/images'):
        print "Partitions from " + device + " successfully mounted"
    else:
        print "Failed mounting partitions from " + device
    
    # --------------- TC 17 ---------------
    
    tc_start(17)
    
    # Test install_components
    
    if sd_installer.install_components():
        print "Components successfully installed on " + device
    else:
        print "Failed installing components on " + device
    
    # --------------- TC 18 ---------------
    
    tc_start(18)
    
    sd_installer.set_mode(sd_installer.MODE_LOOPBACK)
    
    # Test format_loopdevice
    # This must fail because of the image size
    sdcard_mmap_filename = '../../../../../images/sd-mmap.config'
    image_name = devdir + '/images/test_image.img'
    image_size = '1'
    
    if sd_installer.format_loopdevice(sdcard_mmap_filename, image_name,
                                      image_size):
        print "Succesfully format the loopdevice for the image " + image_name
    else:
        print "Failed to format the loopdevice for the image " + image_name

    # --------------- TC 19 ---------------
    
    tc_start(19)
    
    # Test format_loopdevice
    image_size = '256'
    
    if sd_installer.format_loopdevice(sdcard_mmap_filename, image_name,
                                      image_size):
        print "Succesfully format the loopdevice for the image " + image_name
    else:
        print "Failed to format the loopdevice for the image " + image_name
    
    # --------------- TC 20 ---------------
    
    tc_start(20)
    
    # Test release_loopdevice
    
    if sd_installer.mount_partitions(devdir + '/images'):
        print "Partitions from " + device + " successfully mounted"
    else:
        print "Failed mounting partitions from " + device    
    
    
    if sd_installer.release_loopdevice():
        print "Succesfully release all loopdevices for the image " + image_name
    else:
        print "Failed to release all loopdevices for the image " + image_name
    
    print "Test cases finished"
