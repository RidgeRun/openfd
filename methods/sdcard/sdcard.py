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
    
    #: Installs on the SD-card
    MODE_SD = 'sd'
    
    #: Installs on a loopback file instead of a real SD-card.
    MODE_LOOPBACK = 'loopback'
    
    def __init__(self, comp_installer, device='', mode=None, dryrun=False,
                 interactive=True, enable_colors=True):
        """
        :param comp_installer: :class:`ComponentInstaller` instance.
        :param device: Device name (i.e. '/dev/sdb').
        :param mode: Installation mode. Possible values: :const:`MODE_SD`,
            :const:`MODE_LOOPBACK`.
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        :param interactive: Enable interactive mode. The user will
            be prompted before executing dangerous commands.
        :type interactive: boolean
        """
        
        self._l = rrutils.logger.get_global_logger()
        self._e = rrutils.executer.get_global_executer()
        self._e.enable_colors = enable_colors
        self._comp_installer = comp_installer
        self._d = rrutils.device.Device(device)
        self._mode = mode
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        self._d.dryrun = dryrun
        self._comp_installer.dryrun = dryrun
        self._interactive = interactive
        self._partitions = []
        self._loopdevice_partitions = {}
    
    def __set_mode(self, mode):
        self._mode = mode
    
    def __get_mode(self):
        return self._mode
    
    mode = property(__get_mode, __set_mode, doc="""Installation mode. Possible
            values: :const:`MODE_SD`, :const:`MODE_LOOPBACK`.""")
    
    def __set_device(self, device):
        self._d.name = device
    
    def __get_device(self):
        return self._d.name
    
    device = property(__get_device, __set_device,
                      doc="""Device name (i.e. '/dev/sdb').""")
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._comp_installer.dryrun = dryrun
        self._e.dryrun = dryrun
    
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
    
    def _confirm_device_size(self):
        """
        Checks the device's size against WARN_DEVICE_SIZE_GB, if it's bigger
        it warns the user that the device does not look like an SD card.
        
        Returns true if the user confirms the device is an SD card; false
        otherwise. 
        """
        
        size_is_good = True
        if self._d.size_gb > SDCardInstaller.WARN_DEVICE_SIZE_GB:
            msg = ('Device %s has %d gigabytes, it does not look like an '
                   'SD card' % (self._d.name, self._d.size_gb))
            msg_color = SDCardInstaller.WARN_COLOR 
            confirmed = self._e.prompt_user(msg, msg_color)
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
        
        auto_unmount = True
        if self._d.mounted_partitions:
            msg = ('The following partitions from device %s will be '
                   'unmounted:\n' % self._d.name)
            for part in self._d.mounted_partitions:
                msg += part + '\n'
            msg_color = SDCardInstaller.WARN_COLOR
            confirmed = self._e.prompt_user(msg, msg_color)
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

    def _get_device_size_cyl(self):
        """
        Returns the given device size, in cylinders.
        """
        
        size_cyl = self._d.size_b / geometry.CYLINDER_BYTE_SIZE
        return int(math.floor(size_cyl))
    
    def _get_partition_filename(self, partition_index):
        """
        Gets the complete filename for the partition (i.e. /dev/sdb1)
        """
        
        p = self._d.name + self._d.partition_suffix(partition_index)    
        if self._mode == self.MODE_LOOPBACK:
            p = self._loopdevice_partitions[p]
        return p
    
    def mount_partitions(self, directory):
        """
        Mounts the partitions in the specified directory.
        
        I.e., if the partitions are called "boot" and "rootfs", and the given
        directory is "/media", this function will mount:
        
           - /media/boot
           - /media/rootfs
        
        :param directory: Directory where to mount the partitions.
        :returns: Returns true on success; false otherwise.
        """
        
        if not self._partitions: return True
        
        directory = directory.rstrip('/')
        if not os.path.isdir(directory):
            self._l.error('Directory %s does not exist' % directory)
            return False
        
        partition_index = 1
        for part in self._partitions:
        
            part_name = self._get_partition_filename(partition_index)
            mount_point = directory + '/' + part.name
        
            # Create the directory where to mount
            cmd = 'mkdir -p %s' % mount_point
            if self._e.check_call(cmd) != 0:
                self._l.error('Failed to create directory %s' % mount_point)
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
                cmd = 'sudo mount -t %s %s %s' % (part_type, part_name,
                                                  mount_point)
            else:
                # Let mount try to guess the partition type
                cmd = 'sudo mount %s %s' % (part_name, mount_point)            
            if self._e.check_call(cmd) != 0:
                self._l.error('Failed to mount %s in %s' % (part_name,
                                                            mount_point))        
                return False
            
            partition_index += 1
            
        return True
    
    def _create_partitions(self):
        """
        Create the partitions in the given device.
        
        Returns true on success; false otherwise
        """
        
        cylinders = self._get_device_size_cyl()
        
        # Check we were able to get correctly the device size
        if cylinders == 0 and not self._dryrun:
            self._l.error('Unable to partition device %s (size is 0)' %
                               self._d.name)
            return False
        
        # Check we have enough size to fit all the partitions and the MBR.
        if cylinders < self._min_total_cyl_size() and not self._dryrun:
            self._l.error('Size of partitions is too large to fit in %s' %
                               self._d.name)
            return False

        # Just before creating the partitions, prompt the user
        if self._interactive and self._mode != self.MODE_LOOPBACK:
            msg = ('You are about to repartition your device %s '
                   '(all your data will be lost)' % self._d.name)
            msg_color = SDCardInstaller.WARN_COLOR
            confirmed = self._e.prompt_user(msg, msg_color)
            if not confirmed:
                return False
            
        # Create the partitions        
        cmd = ('sudo sfdisk -D' +
              ' -C' + str(cylinders) +
              ' -H' + str(int(geometry.HEADS)) +
              ' -S' + str(int(geometry.SECTORS)) +
              ' '   + self._d.name + ' << EOF\n')
        for part in self._partitions:
            cmd += str(part.start) + ','
            cmd += str(part.size) + ','
            cmd += str(part.type)
            if part.is_bootable: cmd += ',*'
            cmd += '\n'
        cmd += 'EOF'
        
        if self._e.check_call(cmd) != 0:
            self._l.error('Unable to partition device %s' % self._d.name)
            return False
        
        return True

    def _format_partitions(self):
        """
        Format the partitions in the given device, assuming these partitions
        were already created (see create_partitions()). To register partitions
        use read_partitions().
        
        Returns true on success; false otherwise.
        """
        
        partition_index = 1
        
        for part in self._partitions:
            
            # Get the complete filename for the partition (i.e. /dev/sdb1)
            device_part = self._get_partition_filename(partition_index)
            
            # Format
            cmd = ''
            if part.filesystem == Partition.FILESYSTEM_VFAT:
                cmd = 'sudo mkfs.vfat -F 32 %s -n %s' % (device_part, part.name)
            elif part.filesystem == Partition.FILESYSTEM_EXT3:
                cmd = 'sudo mkfs.ext3 %s -L %s'  % (device_part, part.name)
            else:
                msg = ("Can't format partition %s, unknown filesystem: %s" %
                       (part.name, part.filesystem))
                self._l.error(msg)
                return False
            
            if self._e.check_call(cmd) == 0:
                msg = ('Formatted %s (%s) into %s' % (part.name,
                                              part.filesystem, device_part))
            else:
                self._l.error('Unable to format %s into %s' %
                                (part.name, device_part))
                return False
        
            partition_index += 1
            
        if self._partitions:
            ret = self._e.check_call('sync')
            if ret != 0:
                self._l.error('Unable  to sync')
                return False
        
        return True

    def format_sd(self):
        """
        Creates and formats the partitions in the SD card.
        
        :returns: Returns true on success; false otherwise. 
        """
        
        if not self._partitions: return True
        if self._mode != SDCardInstaller.MODE_SD:
            self._l.error('Not in MODE_SD.')
            return False
        
        # Check that the device is actually an SD card
        if self._interactive:
            if self._confirm_device_size() is False:
                return False
        
        if not self._d.exists and not self._dryrun:
            self._l.error('No valid disk available on %s' % self._d.name)
            return False
        
        if self._d.is_mounted and not self._dryrun:    
            if self._interactive:
                if self._confirm_device_auto_unmount() is False:
                    return False
            if not self._d.unmount():
                self._l.error('Failed auto-unmounting %s, refusing to install'
                                % self._d.name)
                return False
        
        self._l.info('Creating partitions on %s' % self._d.name)
        if not self._create_partitions():
            return False
        
        self._l.info('Formatting partitions on %s' % self._d.name)
        if not self._format_partitions():
            return False
        
        return True
    
    def _test_image_size(self, image_size_mb):
        """
        Test that the image will be big enough to hold the partitions.
        
        Returns true on success; false otherwise.
        """
        
        size_b = int(image_size_mb) << 20
        size_cyl = size_b / geometry.CYLINDER_BYTE_SIZE
        
        if size_cyl < self._min_total_cyl_size():
            size_needed_b = (self._min_total_cyl_size() *
                                geometry.CYLINDER_BYTE_SIZE)
            size_needed_mb = int(size_needed_b) >> 20
            self._l.error('Image size of %s MB is too small to hold the '
                   'partitions, the image must be bigger than %s MB to '
                   'hold them.' % (image_size_mb, size_needed_mb))
            return False
        
        return True
    
    def _create_image_file(self, image_name, image_size):
        """
        Creates the image file with a valid format and associates the file
        with a loopdevice. 
        
        Returns true on success; false otherwise.
        """
        
        cmd = 'dd if=/dev/zero of=%s bs=1M count=%s' % (image_name, image_size)
        ret = self._e.check_call(cmd)
        if ret != 0:
            self._l.error('Failed to create file for the image %s' % image_name)
            return False
                
        cmd = 'sudo losetup -f'
        ret, loopdevice = self._e.check_output(cmd)
        if ret == 0:
            loopdevice = loopdevice.rstrip('\n')
            self.device = loopdevice
            cmd = 'sudo losetup %s %s' % (self._d.name,  image_name)
            ret = self._e.check_call(cmd)
            if ret != 0:
                self._l.error('Failed to associate image file %s to %s'
                                   % (image_name, self._d.name))
                return False
        else:
            self._l.error('Failed when searching for free loop devices')
            return False
        
        # If we want to reuse the code for creating and formatting partitions
        # the image needs to have a valid format
        cmd = 'sudo mkfs.vfat -F 32 %s -n tmp' % self._d.name
        ret = self._e.check_call(cmd)
        if ret != 0:
            self._l.error('Failed to format a temporal filesystem on %s'
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
            device_part = (self._d.name +
                            self._d.partition_suffix(partition_index))
            
            cmd = 'sudo losetup -f'
            ret, free_device = self._e.check_output(cmd)
            
            if ret != 0:
                self._detach_loopdevice()
                self._l.error("Can't find a free loopdevice")
                return False
            
            free_device = free_device.rstrip('\n')
            self._loopdevice_partitions[device_part] = free_device
            offset = int(part.start) * int(geometry.CYLINDER_BYTE_SIZE)
            if part.size == geometry.FULL_SIZE:
                cmd = 'sudo losetup -o %s %s %s' % (offset, free_device,
                                                        image_name)
            else:
                part_size = int(int(part.size)*geometry.CYLINDER_BYTE_SIZE)
                cmd = ('sudo losetup -o %s --sizelimit %s %s %s'
                           % (offset, part_size, free_device, image_name))
                
            ret = self._e.check_call(cmd)
            if ret != 0:
                self._l.error('Failed associating image %s to %s' %
                              (image_name, free_device))
                return False
            
            partition_index += 1
            
        return True
    
    def format_loopdevice(self, image_filename, image_size_mb):
        """
        Creates and formats the partitions in the loopdevice.
        
        :param image_filename: Filename of the loopback image to create.
        :param image_size_mb: Loopback image size, in megabytes.
        :returns: Returns true on success; false otherwise. 
        """
        
        if not self._partitions: return True
        
        if self._mode != SDCardInstaller.MODE_LOOPBACK:
            self._l.error('Not in MODE_LOOPBACK.')
            return False
        
        if not self._test_image_size(image_size_mb):
            return False
        
        self._l.info('Creating image file %s' % image_filename)
        if not self._create_image_file(image_filename, image_size_mb):
            return False
        
        self._l.info('Creating partitions on %s' % self._d.name)
        if not self._create_partitions(): return False
        
        self._l.info('Associating partitions for loopdevice')
        if not self._associate_loopdevice_partitions(image_filename):
            return False
        
        self._l.info('Formatting partitions on %s' % self._d.name)
        if not self._format_partitions(): return False
        
        return True
    
    def _detach_loopdevice(self):
        """
        Detach all loopdevices associated with a partition and then detaches
        the device itself.
        
        Returns true on success; false otherwise.
        """
        
        for dev in self._loopdevice_partitions.itervalues():
            cmd = 'sudo losetup -d %s' % dev
            ret = self._e.check_call(cmd)
            if ret != 0:
                self._l.error('Failed releasing loopdevice %s' %dev)
                return False
        cmd = 'sudo losetup -d %s' % self._d.name
        ret = self._e.check_call(cmd)
        if ret != 0:
            self._l.error('Failed releasing loopdevice %s' % self._d.name)
            return False
        self._loopdevice_partitions.clear()
        return True
    
    def _release_sd(self):
        """
        Unmounts all the partitions in the SD card.
        
        Returns true on success; false otherwise. 
        """
            
        self._l.info('Checking filesystems on %s' % self._d.name)
        return self._check_filesystems()
    
    def _release_loopdevice(self):
        """
        Releases all loopdevices used when creating an image file. Should be
        run after finishing the process.
        
        Returns true on success; false otherwise.
        """
        
        # Unmount partitions
        for dev in self._loopdevice_partitions.itervalues():
            cmd = 'sync'
            ret = self._e.check_call(cmd)
            if ret != 0:
                self._l.error('unable  to sync loopdevice %s' %dev)
                return False
            cmd = 'sudo umount %s' % dev
            ret = self._e.check_call(cmd)
            if ret != 0:
                self._l.error('Failed unmounting loopdevice %s' %dev)
                return False
            
        ret = self._check_filesystems()
        if not ret:
            self._l.error('Failed image filesystem check')
            return False
        
        ret = self._detach_loopdevice()
        if not ret: return False
        
        return True

    def release_device(self):
        """
        Unmounts all partitions and release the given device.
        
        :returns: Returns true on success; false otherwise.
        """
        
        if self._partitions:
            if self._mode == SDCardInstaller.MODE_SD:
                return self._release_sd()
            elif self.mode == SDCardInstaller.MODE_LOOPBACK:
                return self._release_loopdevice()
        return True

    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        :returns: Returns true on success; false otherwise.  
        """
        
        # Reset the partitions list
        
        self._partitions[:] = []
        
        if not os.path.exists(filename):
            self._l.error('File %s does not exist' % filename)
            return False
        
        self._l.debug('Reading file %s' % filename)
        
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
    
    def _check_filesystems(self):
        """
        Checks the integrity of the filesystems in the given device. Upon 
        error, tries to recover using the 'fsck' command.
        
        Returns true on success; false otherwise.
        """
        
        if not self._d.exists and not self._dryrun:
            self._l.error("Device %s doesn't exist" % self._d.name)
            return False
        
        if self._d.is_mounted:
            if not self._d.unmount():
                self._l.error("Can't unmount partitions from %s" % self._d.name)
                return False
        
        # According to 'man fsck' the exit code returned by fsck is the sum
        # of the following conditions
        fsck_outputs = {0    : 'No errors',
                        1    : 'Filesystem errors corrected',
                        2    : 'System should be rebooted',
                        4    : 'Filesystem errors left uncorrected',
                        8    : 'Operational error',
                        16   : 'Usage or syntax error',
                        32   : 'fsck canceled by user request',
                        128  : 'Shared-library error'}
        
        fs_ok = True
        
        for partition_index in range(1,len(self._partitions)+1):
            fs_state = []
            device_part = self._get_partition_filename(partition_index)
            cmd = 'sync'
            if self._e.check_call(cmd) != 0:
                self._l.error('Unable  to sync')
                return False
            cmd = "sudo fsck -y %s" % device_part
            ret = self._e.check_call(cmd)
            if ret == 0:
                fs_state.append(fsck_outputs[ret])
            else:
                for i in range(len(fsck_outputs)):
                    key = 2 ** i
                    if ret & key:
                        try:
                            fs_state.append(fsck_outputs[key])
                            if key != 1: # keys not counted as fatal errors
                                fs_ok = False
                        except KeyError:
                            pass
                fs_states = ''.join("'%s', " % st for st in fs_state)
                fs_states = fs_states.rstrip(', ')
                self._l.debug("Filesystem check in %s: %s (see 'man fsck', exit "
                              "code: %s)" % (device_part, fs_states, ret))
            if not fs_ok: break
        return fs_ok
    
    def install_components(self):
        """
        Installs the specified components for each partition.
        
        :returns: Returns true on success, false otherwise.
        """
        
        partition_index = 1
        
        for part in self._partitions:
            
            device_part = self._get_partition_filename(partition_index)
            
            cmd = 'mount | grep %s  | cut -f 3 -d " "' % device_part
            ret, output = self._e.check_output(cmd)
            mount_point = output.replace('\n', '')
            
            for component in part.components:
                
                if component == Partition.COMPONENT_BOOTLOADER:
                    ret = self._comp_installer.install_uboot(self._d.name)
                    if ret is False: return False
                    
                    ret =  self._comp_installer.install_uboot_env(mount_point)
                    if ret is False: return False
                    
                elif component == Partition.COMPONENT_KERNEL:
                    ret = self._comp_installer.install_kernel(mount_point)
                    if ret is False: return False
                    
                elif component == Partition.COMPONENT_ROOTFS:
                    if self._comp_installer.rootfs is None:
                        # This is valid because rootfs argument is optional
                        msg = ('No directory specified for "%s", omitting...' %
                                   (Partition.COMPONENT_ROOTFS))
                        self._l.info(msg)
                    else:
                        ret = self._comp_installer.install_rootfs(mount_point)
                        if ret is False: return False
                
                elif component == Partition.COMPONENT_BLANK:
                    pass
                
                else:
                    self._l.error('Component %s is not valid' % component)
                    return False
                
            partition_index += 1
        
        return True
