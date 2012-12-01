#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
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

Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
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
import partition
import geometry
import ConfigParser
import rrutils

# ==========================================================================
# Public Classes
# ==========================================================================

class SDCardInstaller:
    """
    Class to handle SD-card operations.
    """

    # Used to warn the user when partitioning a device above this size
    WARN_DEVICE_SIZE_GB = 128
    
    # Used for dangerous warning messages
    WARN_COLOR = 'yellow'

    def __init__(self):
        """
        Constructor.
        """
        
        self._config      = rrutils.config.get_global_config()
        self._logger      = rrutils.logger.get_global_logger()
        self._executer    = rrutils.executer.Executer()
        self._dryrun      = False
        self._interactive = True
        self._partitions  = []
        self._executer.set_logger(self._logger)
    
    def _confirm_device_size(self, device):
        """
        Checks the device's size against WARN_DEVICE_SIZE_GB, if it's bigger
        it warns the user that the device does not look like an SD card.
        
        Returns false if the user confirms the device is not an SD card; true
        otherwise. 
        """
        
        size_is_good = True
        size_gb = self.get_device_size_gb(device) 
        
        if size_gb > SDCardInstaller.WARN_DEVICE_SIZE_GB:
            
            msg  = 'Device ' + device + ' has ' + str(size_gb) + ' gigabytes, '
            msg += 'it does not look like an SD card'
            
            msg_color = SDCardInstaller.WARN_COLOR 
            
            confirmed = self._executer.prompt_user(msg, msg_color)
                 
            if not confirmed:
                size_is_good = False
            
        return size_is_good
            
    def set_dryrun(self, dryrun):
        """
        Sets on/off the dryrun mode. In dryrun mode any commands will
        not be executed (just logged).
        """
        
        self._dryrun = dryrun
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
        
    def device_exists(self, device):
        """
        Returns true if the device exists, false otherwise.
        """
        
        ret     = 0
        output  = ''
        exists  = True
        
        cmd = 'sudo fdisk -l ' + device + ' 2>/dev/null'
        
        ret, output = self._executer.check_output(cmd)
        
        if output == "":
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
        ret    = 0
        output = ""
        
        cmd = 'sudo fdisk -l ' + device + ' | grep ' + device + \
                  ' | grep Disk | cut -f 5 -d " "'
        
        ret, output = self._executer.check_output(cmd)

        if not self._dryrun:
            if output == "":
                self._logger.error("Unable to obtain the size for " + device)
            else:
                size = long(output)
        
        return size
    
    def get_device_size_cyl(self, device):
        """
        Returns the given device size, in cylinders.
        """
        
        size_b   = self.get_device_size_b(device)
        size_cyl = size_b / geometry.CYLINDER_BYTE_SIZE 
        
        return int(math.floor(size_cyl))
    
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
            self._logger.error('Unable to partition device ' + device +
                               ' (size is 0).')
            return False
        
        # Check we have enough size to fit all the partitions.
        # Starting the count at cylinder 1 leaving space for
        # the Master Boot Record.
        min_cyl_size = 1
        for part in self._partitions:
            if part.get_size() == geometry.FULL_SIZE:
                # If size is unspecified, at least estimate 1 cylinder for
                # that partition
                min_cyl_size += 1
            else:
                min_cyl_size += int(part.get_size())
        
        if cylinders < min_cyl_size and not self._dryrun:
            self._logger.error('Size of partitions is too large to fit in ' +
                               device + '.')
            return False

        # Just before creating the partitions, prompt the user
        if self._interactive:
            
            msg  = 'You are about to repartition your device ' + device
            msg += ' (all your data will be lost)'
            
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
            cmd += str(part.get_start()) + ','
            cmd += str(part.get_size()) + ','
            cmd += str(part.get_type())
            if part.is_bootable():
                cmd += ',*'
            cmd += '\n'
        
        cmd += 'EOF'
        
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Unable to partition device ' + device)
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
            
            # Compose the device + partition suffix to reference the new
            # partition. For example, first partition in device /dev/sdb
            # is going to be /dev/sdb1, while a device like /dev/mmcblk0
            # will have the first partition named /dev/mmcblk0p1
            device_part = device + str(partition_index)
            if device.find('mmcblk') != -1:
                device_part = device + 'p' + str(partition_index)
            
            # Format
            cmd = ''
            if part.get_filesystem() == partition.Partition.FILESYSTEM_VFAT:
                cmd  = 'sudo mkfs.vfat -F 32 '
                cmd += device_part + ' -n ' + part.get_name()
            elif part.get_filesystem() == partition.Partition.FILESYSTEM_EXT3:
                cmd  = 'sudo mkfs.ext3 ' + device_part
                cmd += ' -L ' + part.get_name()
            else:
                self._logger.warning("Can't format partition " +
                                     part.get_name() + ", unknown filesystem: " +
                                     part.get_filesystem())
            
            if cmd:
                if self._executer.check_call(cmd) == 0:
                    self._logger.info('Formatted ' + part.get_name() +
                                      ' (' + part.get_filesystem() + ')' +
                                      ' into ' + device_part)
                    partition_index += 1
                else:
                    self._logger.error('Unable to format ' +
                                       part.get_name() + ' into ' +
                                       device_part)
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
            self._logger.info('Try inserting the SD card again and ' +
                               'unmounting the partitions.')
            self._logger.error('No valid disk is available on ' + device + '.')
            return False
        
        # Check device is not mounted
        if self.device_is_mounted(device) and not self._dryrun:
            self._logger.info('Your device ' + device + ' seems to be ' +
                               'either mounted, or belongs to a RAID array ' +
                               'in your system.')
            self._logger.error('Device ' + device + ' is mounted, refusing ' +
                               'to install.')
            return False
        
        # Read the partitions
        self._logger.info('Reading ' + filename + ' ...')
        if not self.read_partitions(filename):    
            return False
        
        # Create partitions
        self._logger.info('Creating partitions on ' + device + ' ...')
        if not self.create_partitions(device):
            return False
        
        # Format partitions
        self._logger.info('Formatting partitions on ' + device + ' ...')
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
            self._logger.error("File " + filename + " does not exist.")
            return False
        
        config = ConfigParser.RawConfigParser()
        config.readfp(open(filename))
        
        for section in config.sections():
            
            part = None
            
            if config.has_option(section, 'name'):
                part = partition.Partition(config.get(section, 'name'))
            
            if part:
                if config.has_option(section, 'start'):
                    part.set_start(config.get(section, 'start'))
                    
                if config.has_option(section, 'size'):
                    part.set_size(config.get(section, 'size'))
                    
                if config.has_option(section, 'bootable'):
                    part.set_bootable(config.getboolean(section, 'bootable'))
                
                if config.has_option(section, 'type'):
                    part.set_type(config.get(section, 'type'))
                    
                if config.has_option(section, 'filesystem'):
                    part.set_filesystem(config.get(section, 'filesystem'))
                
                self._partitions.append(part)
                
        return True
                
    def __str__(self):
        """
        To string.
        """
        
        _str  = ''
        _str += 'Dryrun mode: ' + ('On' if self._dryrun else "Off") + '\n'
        _str += 'Partitions: ' + '\n'
        for part in self._partitions:
            _str +=  part.__str__()
        return _str

# ==========================================================================
# Test cases
# ==========================================================================

if __name__ == '__main__':

    # Initialize the logger
    rrutils.logger.basic_config(verbose=True)
    logger = rrutils.logger.get_global_logger('sdcard-test')
    
    sd_installer = SDCardInstaller()
    
    # Check device existence (positive test case)
    
    device = "/dev/sdb1"    
    if sd_installer.device_exists(device):
        print "Device " + device + " exists."
    else:
        print "Device " + device + " doesn't exist."
    
    # Check device existence (negative test case)
        
    device = "/dev/sdbX"    
    if sd_installer.device_exists(device):
        print "Device " + device + " exists."
    else:
        print "Device " + device + " doesn't exist."

    # Check if the device is mounted (positive test case)
    
    device = "/dev/sdb1"
    if sd_installer.device_is_mounted(device):
        print "Device " + device + " is mounted."
    else:
        print "Device " + device + " isn't mounted."
        
    # Check if the device is mounted (negative test case)
    
    device = "/dev/sdbX"
    if sd_installer.device_is_mounted(device):
        print "Device " + device + " is mounted."
    else:
        print "Device " + device + " isn't mounted."
    
    # Test read_partitions
    sdcard_mmap_filename = '../../../../../images/sd-mmap.config'
    
    sd_installer.read_partitions(sdcard_mmap_filename)

    # Test get_device_size_b
    
    device = "/dev/sdb"
    size = sd_installer.get_device_size_b(device)
    print "Device " + device + " has " + str(size) + " bytes"

    # Test get_device_size_gb
    
    device = "/dev/sdb"
    size = sd_installer.get_device_size_gb(device)
    print "Device " + device + " has " + str(size) + " gigabytes"

    # Test get_device_size_cyl
    
    device = "/dev/sdb"
    size = sd_installer.get_device_size_cyl(device)
    print "Device " + device + " has " + str(size) + " cylinders"

    # Test create partitions
    
    device = "/dev/sdb"
    sd_installer.set_dryrun(True)
    sd_installer.create_partitions(device)
    sd_installer.set_dryrun(False)
    
    # Test format partitions
    
    device = "/dev/sdb"
    sd_installer.set_dryrun(True)
    sd_installer.format_partitions(device)
    device = "/dev/mmcblk0"
    sd_installer.format_partitions(device)
    sd_installer.set_dryrun(False)

    # Test format sd

    device = "/dev/sdb"    
    sd_installer.set_dryrun(True)
    sd_installer.format_sd(sdcard_mmap_filename, device)
    sd_installer.set_dryrun(False)
    
    # Test _confirm_device_size 
    device = "/dev/sdb"
    if sd_installer._confirm_device_size(device) is False:
        print "User declined device as SD card"
    
    # Test to string
    
    print sd_installer.__str__()
