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

Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
All Rights Reserved.

The contents of this software are proprietary and confidential to RidgeRun,
LLC.  No part of this program may be photocopied, reproduced or translated
into another programming language without prior written consent of 
RidgeRun, LLC.
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

    def __init__(self, comp_installer):
        """
        Constructor.
        """
        
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._dryrun = False
        self._interactive = True
        self._partitions = []
        self._executer.set_logger(self._logger)
        self._comp_installer = comp_installer
        self._workdir = None
    
    def _confirm_device_size(self, device):
        """
        Checks the device's size against WARN_DEVICE_SIZE_GB, if it's bigger
        it warns the user that the device does not look like an SD card.
        
        Returns true if the user confirms the device is an SD card; false
        otherwise. 
        """
        
        size_is_good = True
        size_gb = self.get_device_size_gb(device) 
        
        if size_gb > SDCardInstaller.WARN_DEVICE_SIZE_GB:
            
            msg = ('Device %s has %d gigabytes, it does not look like an '
                   'SD card' % (device, size_gb))
            
            msg_color = SDCardInstaller.WARN_COLOR 
            
            confirmed = self._executer.prompt_user(msg, msg_color)
                 
            if not confirmed:
                size_is_good = False
            
        return size_is_good
    
    def _confirm_device_auto_unmount(self, device):
        """
        Checks for mounted partitions on the device, if there are it warns
        the user that the partitions will be auto-unmounted.
        
        Returns true if the user confirms the auto-unmount operations; false
        otherwise. 
        """
        
        auto_unmount = True
        
        partitions = self.get_device_mounted_partitions(device)
        
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
            
    def set_dryrun(self, dryrun):
        """
        Sets on/off the dryrun mode. In dryrun mode any commands will
        not be executed (just logged).
        """
        
        self._dryrun = dryrun
        self._comp_installer.dryrun = dryrun
        self._executer.set_dryrun(dryrun)
    
    def get_dryrun(self):
        """
        Returns true if the dryrun mode is on; false otherwise.
        """
        
        return self._dryrun
    
    def set_interactive(self, interactive):
        """
        Sets on/off the interactive mode. In interactive mode the user
        will be prompted before some actions, such as partitioning a device.
        When the interactive mode is off, it will run non-interactively.
        """
        
        self._interactive = interactive
    
    def get_interactive(self):
        """
        Returns true if the interactive mode is on; false otherwise.
        """
        
        return self._interactive

    def set_workdir(self, workdir):
        """
        Sets the path to the directory where to create temporary files
        and also mount devices.
        """
        
        self._comp_installer.workdir = workdir
        self._workdir = workdir
    
    def get_workdir(self):
        """
        Gets the working directory.
        """
        
        return self._workdir

    def get_device_size_gb(self, device):
        """
        Returns the given device size, in gigabytes.
        """
        
        size_b = self.get_device_size_b(device)
        return long(size_b >> 30)

    def get_device_size_b(self, device):
        """
        Returns the given device size, in bytes.
        """
        
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
    
    def get_device_size_cyl(self, device):
        """
        Returns the given device size, in cylinders.
        """
        
        size_b = self.get_device_size_b(device)
        size_cyl = size_b / geometry.CYLINDER_BYTE_SIZE 
        
        return int(math.floor(size_cyl))
    
    def get_partition_suffix(self, device, partition_index):
        """
        This function returns a string with the standard partition numeric
        suffix, depending on the type of device.
        
        For example, the first partition (index = 1) in device
        /dev/sdb is going to have the suffix "1", so that one can compose
        the complete partition's filename: /dev/sdb1. While a device like
        /dev/mmcblk0 will provoke a partition suffix "p1", so that the complete
        filename for the first partition is "/dev/mmcblk0p1".  
        """
        
        suffix = ''
        
        if device.find('mmcblk') != -1:
            suffix = 'p' + str(partition_index)
        else:
            suffix = str(partition_index)
        
        return suffix
    
    def get_device_mounted_partitions(self, device):
        """
        Returns a list with the mounted partitions from the given device.
        """
        
        partitions = []
        
        cmd = 'mount | grep ' + device + '  | cut -f 3 -d " "'
        output = self._executer.check_output(cmd)[1]
        
        if output:
            partitions = output.strip().split('\n')
        
        return partitions
    
    def device_exists(self, device):
        """
        Returns true if the device exists, false otherwise.
        """

        exists  = True
        
        cmd = 'sudo fdisk -l ' + device + ' 2>/dev/null'
        
        output = self._executer.check_output(cmd)[1]
        
        if not output:
            exists = False
            
        return exists
    
    def device_is_mounted(self, device):
        """
        Returns true if the device is mounted or if it's part of a RAID array,
        false otherwise.
        """
        
        is_mounted = False
        
        cmd1 = 'grep --quiet ' + device + ' /proc/mounts'
        cmd2 = 'grep --quiet ' + device + ' /proc/mdstat'
        
        if self._executer.check_call(cmd1) == 0: is_mounted = True
        if self._executer.check_call(cmd2) == 0: is_mounted = True
        
        return is_mounted
    
    def mount_partitions(self, device, directory):
        """
        Mounts the partitions of the given device in the specified directory.
        To register partitions use read_partitions().
        
        I.e., if the partitions are called "boot" and "rootfs", and the given
        dir is "/media", this function will mount:
        
           /media/boot
           /media/rootfs
        
        Returns true on success; false otherwise.
        """
        
        directory = directory.rstrip('/')
        if not os.path.isdir(directory):
            self._logger.error('Directory %s does not exist' % directory)
            return False
        
        partition_index = 1
        for part in self._partitions:
        
            # Get the complete filename for the partition (i.e. /dev/sdb1)
            device_part = device + \
                            self.get_partition_suffix(device, partition_index)
                            
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
    
    def auto_unmount_partitions(self, device):
        """
        Auto-unmounts the partitions of the given device.
        
        Returns true on success; false otherwise.
        """
        
        partitions = self.get_device_mounted_partitions(device)
        
        for part in partitions:
        
            cmd = 'sudo umount ' + part
            
            if self._executer.check_call(cmd) != 0:
                self._logger.error('Failed to unmount %s' % part)
                return False
        
        return True
    
    def create_partitions(self, device):
        """
        Create the partitions in the given device. To register
        partitions use read_partitions().
        
        Returns true on success; false otherwise
        """
        
        cylinders = self.get_device_size_cyl(device)
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
        if self._interactive:
            
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
            if part.is_bootable:
                cmd += ',*'
            cmd += '\n'
        
        cmd += 'EOF'
        
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Unable to partition device %s' % device)
            return False
        
        return True

    def format_partitions(self, device):
        """
        Format the partitions in the given device, assuming these partitions
        were already created (see create_partitions()). To register partitions
        use read_partitions().
        
        Returns true on success; false otherwise.
        """
        
        partition_index = 1
        
        for part in self._partitions:
            
            # Get the complete filename for the partition (i.e. /dev/sdb1)
            device_part = device + \
                            self.get_partition_suffix(device, partition_index)
            
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

    def format_sd(self, filename, device):
        """
        This function will create and format the partitions as specified
        by 'mmap-config-file' to the sd-card referenced by 'device'.
        
        Returns true on success; false otherwise. 
        """
        
        # Dummy check to try to verify with the user if the device is
        # actually an SD card
        if self._interactive:
            if self._confirm_device_size(device) is False:
                return False
        
        # Check device existence
        if not self.device_exists(device) and not self._dryrun:
            self._logger.info('Try inserting the SD card again and '
                               'unmounting the partitions')
            self._logger.error('No valid disk is available on %s' % device)
            return False
        
        # Check device is not mounted
        if self.device_is_mounted(device) and not self._dryrun:
            
            if self._interactive:
                if self._confirm_device_auto_unmount(device) is False:
                    return False
                
            # Auto-unmount
            if not self.auto_unmount_partitions(device):
                self._logger.error('Failed auto-unmounting %s, refusing to '
                                   'install' % device)
                return False
        
        # Read the partitions
        self._logger.info('Reading %s ...' % filename)
        if not self.read_partitions(filename):    
            return False
        
        # Create partitions
        self._logger.info('Creating partitions on %s ...' % device)
        if not self.create_partitions(device):
            return False
        
        # Format partitions
        self._logger.info('Formatting partitions on %s ...' % device)
        if not self.format_partitions(device):
            return False
        
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
                    part.components = components.replace(' ','').split(',')
                
                self._partitions.append(part)
                
        return True
    
    def check_filesystems(self, device):
        """
        Checks the integrity of the filesystems in the given device. Upon 
        error, tries to recover using the 'fsck' command.
        
        Returns true on success; false otherwise.
        """
        
        if not self.device_exists(device) and not self._dryrun:
            self._logger.error("Device %s doesn't exist" % device)
            return False
        
        if self.device_is_mounted(device):
            if not self.auto_unmount_partitions(device):
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
        
        partition_index = 1
        
        for part in self._partitions:
            fs_state = ''
            device_part = device + \
                            self.get_partition_suffix(device, partition_index)
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
            
            partition_index += 1
            
        return fs_ok
    
    def install_components(self, device):
        """
        Installs the specified components for each partition.
        
        Returns true on success, false otherwise.
        """
        
        partition_index = 1
        
        for part in self._partitions:
            
            device_part = device + \
                            self.get_partition_suffix(device, partition_index)
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
                        err_msg = ('No directory for component %s in "%s" '
                                   'partition' %
                                   (Partition.COMPONENT_ROOTFS, part.name))
                        self._logger.error(err_msg)
                        return False
                    ret = self._comp_installer.install_rootfs(mount_point)
                    if ret is False: return False
                    
                else:
                    self._logger.error('Component %s is not valid', component)
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
    sd_installer.set_dryrun(True)
    sd_installer.set_interactive(True)
    
# ==========================================================================
# Test cases - Unit tests
# ==========================================================================
    
    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0) 
    
    # Check device existence (positive test case)
    
    if sd_installer.device_exists(device + "1"):
        print "Device " + device + " exists."
    else:
        print "Device " + device + " doesn't exist."
    
    # --------------- TC 2 ---------------
    
    tc_start(2)
    
    # Check device existence (negative test case)
    
    temp_device = "/dev/sdbX"    
    if sd_installer.device_exists(temp_device):
        print "Device " + temp_device + " exists."
    else:
        print "Device " + temp_device + " doesn't exist."

    # --------------- TC 3 ---------------
    
    tc_start(3)

    # Check if the device is mounted (positive test case)
    
    if sd_installer.device_is_mounted(device):
        print "Device " + device + " is mounted."
    else:
        print "Device " + device + " isn't mounted."
    
    # --------------- TC 4 ---------------
    
    tc_start(4)
        
    # Check if the device is mounted (negative test case)
    
    temp_device = "/dev/sdbX"
    if sd_installer.device_is_mounted(temp_device):
        print "Device " + temp_device + " is mounted."
    else:
        print "Device " + temp_device + " isn't mounted."
    
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
    
    size = sd_installer.get_device_size_b(device)
    print "Device " + device + " has " + str(size) + " bytes"

    # --------------- TC 7 ---------------
    
    tc_start(7)

    # Test get_device_size_gb
    
    size = sd_installer.get_device_size_gb(device)
    print "Device " + device + " has " + str(size) + " gigabytes"

    # --------------- TC 8 ---------------
    
    tc_start(8)

    # Test get_device_size_cyl
    
    size = sd_installer.get_device_size_cyl(device)
    print "Device " + device + " has " + str(size) + " cylinders"

    # --------------- TC 9 ---------------
    
    tc_start(9)

    # Test get_device_mounted_partitions
    
    print "Device " + device + " mounted partitions:"
    print sd_installer.get_device_mounted_partitions(device)
    
    # --------------- TC 10 ---------------
    
    tc_start(10)

    # Test create partitions
    
    sd_installer.create_partitions(device)

    # --------------- TC 11 ---------------
    
    tc_start(11)

    # Test format sd

    sd_installer.format_sd(sdcard_mmap_filename, device)
    
    # --------------- TC 12 ---------------
    
    tc_start(12)
    
    # Test _confirm_device_size 
    
    if sd_installer._confirm_device_size(device) is False:
        print "User declined device as SD card"
    else:
        print "Device " + device + " confirmed as SD card"

    # --------------- TC 13 ---------------
    
    tc_start(13)
    
    # Test _confirm_device_auto_unmount

    if sd_installer._confirm_device_auto_unmount(device) is False:
        print "User declined to auto-unmount"

    # --------------- TC 14 ---------------
    
    tc_start(14)
    
    # Test device_auto_unmount
 
    if sd_installer.auto_unmount_partitions(device):
        print "Device " + device + " is unmounted"
    else:
        print "Failed auto-unmounting " + device

    # --------------- TC 15 ---------------
    
    tc_start(15)
    
    # Test to string
    
    print sd_installer.__str__()

    # --------------- TC 16 ---------------
    
    tc_start(16)
    
    # Test mount_partitions
    
    if sd_installer.mount_partitions(device, devdir + '/images'):
        print "Partitions from " + device + " successfully mounted"
    else:
        print "Failed mounting partitions from " + device
    
    # --------------- TC 17 ---------------
    
    tc_start(17)
    
    # Test install_components
    
    if sd_installer.install_components(device):
        print "Components successfully installed on " + device
    else:
        print "Failed installing components on " + device
    
    print "Test cases finished"
