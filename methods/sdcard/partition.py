#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
# Author: Diego Benavides <diego.benavides@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# Representation of a memory partition.
#
# ==========================================================================

"""
Representation of a memory partition.

Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
All Rights Reserved.

The contents of this software are proprietary and confidential to RidgeRun,
LLC.  No part of this program may be photocopied, reproduced or translated
into another programming language without prior written consent of 
RidgeRun, LLC.
"""

# ==========================================================================
# Classes
# ==========================================================================

class Partition:
    """ Class that represents a file system partition. """
    
    # Common partition types definitions that can be used in combination
    # with the 'sfdisk' command.
    
    TYPE_UNKNOWN = 'unknown'
    TYPE_LINUX_NATIVE = 'L'
    TYPE_FAT32 = '0xc'
    
    # Common partition filesystems
    
    FILESYSTEM_UNKNOWN = 'unknown'
    FILESYSTEM_VFAT = 'vfat'
    FILESYSTEM_EXT3 = 'ext3'
    
    # Common partition components
    COMPONENT_BOOTLOADER = 'bootloader'
    COMPONENT_KERNEL = 'kernel'
    COMPONENT_ROOTFS = 'rootfs'
    
    def __init__(self, name):
        """
        Constructor.
        """
        
        self._name       = name
        self._start      = 0
        self._size       = 0
        self._bootable   = False
        self._type       = ''
        self._filesystem = ''
        self._mount_point = None
        self._components = None
        
    @classmethod
    def hex_format(self, decimal_value, width=8, upper=True):
        """
        Returns the given decimal value as hex of given width (left zeros
        will be appended). After meeting the width requirement, the
        prefix '0x' will be added.
        
        Use the upper switch to have the hexadecimal value all in upper case.
        
        Example:
        
          Suppose the decimal value 3:
          
            width = 1 -> returns 0x3
            width = 2 -> returns 0x03
            ...
            width = 8 -> returns 0x00000003 
        """
        
        # Get the hex value and remove the '0x' prefix
        hex_value = hex(int(decimal_value))[2:]
        
        # Left fill with zeros 
        hex_value = hex_value.zfill(width)
        
        # Uppercase
        if upper:
            hex_value = hex_value.upper()
       
        return '0x' + hex_value
    
    @classmethod
    def decode_partition_type(self, partition_type):
        """
        Given a string indicating the type of a partition, such as 'L' for
        Linux Native or '0xc' for FAT32, returns a friendly name, such as 
        'Linux Native' or 'FAT32'.
        """
        
        friendly_type = Partition.TYPE_UNKNOWN
        
        if partition_type == Partition.TYPE_FAT32:
            friendly_type = 'W95 FAT32 (LBA)'
        elif partition_type == Partition.TYPE_LINUX_NATIVE:
            friendly_type = 'Linux Native'
        
        return friendly_type
                    
    def set_start(self, start):
        """
        Sets the partition start address (decimal).
        """
        
        self._start = start
        
    def get_start(self, hex_format=False):
        """
        Gets the partition start address (decimal).
        """
        
        if hex_format:
            return Partition.hex_format(self._start)
        else:
            return self._start
        
    def set_size(self, size):
        """
        Sets the partition size (decimal). Size can be '-' to indicate
        the max size available (where not specified).
        """
        
        self._size = size
        
    def get_size(self, hex_format=False):
        """
        Gets the partition size (decimal).
        
        If hex_format is True, the size will be returned as a hex value,
        padded to 8 digits and with the '0x' prefix.     
        """
    
        if self._size == '-':
            return '-'
        
        if hex_format:
            return Partition.hex_format(self._size)
        else:
            return self._size
    
    def get_name(self):
        """
        Gets the partition name.
        """
        
        return self._name
        
    def set_bootable(self, bootable):
        """
        Sets the bootable property (true/false) for this partition. 
        """
        
        self._bootable = bootable
        
    def set_type(self, type):
        """
        Sets the partition type, according to the specification given
        in the 'sfdisk' command. Last retrieved:
        
          Id is given in hex, without the 0x prefix, or is [E|S|L|X],
          where L (LINUX_NATIVE (83)) is the default, S is LINUX_SWAP (82),
          E is EXTENDED_PARTITION  (5), and X is LINUX_EXTENDED (85).
          
        Most common types:
            - Partition.TYPE_FAT32: '0xc'
            - Partition.TYPE_LINUX_NATIVE: 'L'
        """
        
        self._type = type
        
    def get_type(self):
        """
        Gets the partition type. See set_type() documentation for more info
        on common partition types.
        """
        
        return self._type
    
    def set_filesystem(self, filesystem):
        """
        Sets the filesystem.
        
        Most common filesystems:
            - Partition.FILESYSTEM_VFAT
            - Partition.FILESYSTEM_EXT3
        """
        
        self._filesystem = filesystem
        
    def get_filesystem(self):
        """
        Gets the filesystem. See set_filesystem() documentation for more info
        on common filesystems.
        """
        
        return self._filesystem
    
    def set_components(self,components):
        """
        Sets the components that will be installed on this partition.
        """
        self._components = components
    
    def get_components(self):
        """
        Gets the components that will be installed on this partition.
        """
        return self._components
    
    def set_mount_point(self, mount_point):
        """
        Sets the partition mount point.
        """
        self._mount_point = mount_point
    
    def get_mount_point(self):
        """
        Gets the partition mount point.
        """
        return self._mount_point
    
    def set_device(self, device):
        """
        Sets the device where the partition is placed.
        Example:
        /dev/sdb
        """
        self._device = device
    
    def get_device(self):
        """
        Gets the device where the partition is placed.
        """
        return self._device
    
    def set_device_partition(self, device_partition):
        """
        Sets the device partition.
        Example:
        /dev/sdb1
        """
        self._device_partition = device_partition
    
    def get_device_partition(self):
        """
        Gets the device partition.
        """
        return self._device_partition
    
    def is_bootable(self):
        """
        Returns true if the partition is bootable, false otherwise.
        """
        
        return self._bootable
    
    def __str__(self):
        """
        To string.
        """
        
        _str  = ''
        _str += 'Device:     ' + str(self._device) + '\n'
        _str += 'Partition:  ' + str(self._device_partition) + '\n'
        _str += 'Name:       ' + self._name + '\n'
        _str += 'Start:      ' + str(self._start) + '\n'
        _str += 'Size:       ' + str(self._size) + '\n'
        _str += 'Bootable:   ' + ('Yes' if self._bootable else 'No') + '\n'
        _str += 'Type:       ' + self._type + '\n'
        _str += 'Filesystem: ' + self._filesystem + '\n'
        _str += 'Mount point:' + str(self._mount_point) + '\n'
        return _str

# ==========================================================================
# Test cases
# ==========================================================================        

if __name__ == '__main__':
    
    p = Partition('test-partition')
    
    print p.get_name()
    
    p.set_size(100)
    
    print p.get_size()
    print p.get_size(hex_format=True)
    
    p.set_size('-')
    
    print p.get_size()
    print p.get_size(hex_format=True)
    
    p.set_size(100)
    print p.get_size(hex_format=True)
    
    p.set_start(100)
    print p.get_start()
    print p.get_start(hex_format=True)
    
    p.set_bootable(True)
    if p.is_bootable():
        print "Partition " + p.get_name() + " is bootable"
    else:
        print "Partition " + p.get_name() + " is not bootable"
        
    p.set_type(Partition.TYPE_FAT32)
    p.set_filesystem(Partition.FILESYSTEM_VFAT)
    
    print p.__str__()
