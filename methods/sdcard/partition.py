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
# Representation of a memory partition.
#
# ==========================================================================

"""
Representation of a memory partition.

Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
All Rights Reserved.

The contents of this software are proprietary and confidential to RidgeRun,
LLC.  No part of this program may be photocopied, reproduced or translated
into another programming language without prior written consent of 
RidgeRun, LLC.
"""

# ==========================================================================
# Classes
# ==========================================================================

class Partition(object):
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
        
        self._name = name
        self._start = 0
        self._size = 0
        self._bootable = False
        self._type = ''
        self._filesystem = ''
        self._components = []
    
    @property
    def name(self):
        """
        Gets the partition name.
        """
        
        return self._name
       
    def __set_start(self, start):
        """
        Sets the partition start address (decimal).
        """
        
        self._start = start
        
    def __get_start(self):
        """
        Gets the partition start address (decimal).
        """
        
        return self._start
        
    start = property(__get_start, __set_start,
                     doc="""Gets or sets the partition start address
                     (decimal).""")
        
    def __set_size(self, size):
        """
        Sets the partition size (decimal). Size can be '-' to indicate
        the max size available (where not specified).
        """
        
        self._size = size
        
    def __get_size(self):
        """
        Gets the partition size (decimal). Size can be '-' to indicate
        the max size available (where not specified).
        """
        
        return self._size
    
    size = property(__get_size, __set_size,
                    doc="""Gets or sets the partition size (decimal). Size can
                    be '-' to indicate the max size available (where not
                    specified).""")
    
    def __set_type(self, partition_type):
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
        
        self._type = partition_type
        
    def __get_type(self):
        """
        Gets the partition type. See __set_type() documentation for more info
        on common partition types.
        """
        
        return self._type
    
    type = property(__get_type, __set_type,
                    doc="""Gets or sets the partition type.""")
    
    @classmethod
    def decode_partition_type(cls, partition_type):
        """
        Given a string indicating the type of a partition, such as 'L' for
        Linux Native or '0xc' for FAT32, returns a friendly name, such as 
        'Linux Native' or 'FAT32'.
        """
        
        friendly_type = cls.TYPE_UNKNOWN
        
        if partition_type == cls.TYPE_FAT32:
            friendly_type = 'W95 FAT32 (LBA)'
        elif partition_type == cls.TYPE_LINUX_NATIVE:
            friendly_type = 'Linux Native'
        
        return friendly_type
    
    def __set_filesystem(self, filesystem):
        """
        Sets the filesystem.
        
        Most common filesystems:
            - Partition.FILESYSTEM_VFAT
            - Partition.FILESYSTEM_EXT3
        """
        
        self._filesystem = filesystem
        
    def __get_filesystem(self):
        """
        Gets the filesystem. See set_filesystem() documentation for more info
        on common filesystems.
        """
        
        return self._filesystem
    
    filesystem = property(__get_filesystem, __set_filesystem,
                          doc="""Gets or sets the partition filesystem.""")
    
    def __set_bootable(self, bootable):
        """
        Sets the bootable property on the partition.
        """
        
        self._bootable = bootable
        
    def __get_bootable(self):
        """
        Gets the bootable property on the partition.
        """
        
        return self._bootable
    
    bootable = property(__get_bootable, __set_bootable,
                        doc="""Gets or sets the bootable property on
                        the partition.""")
    
    def is_bootable(self):
        """
        Returns true if the partition is bootable, false otherwise.
        """
        
        return self._bootable
    
    def __set_components(self, components):
        """
        Sets the list of components that will be installed on this partition.
        """
        self._components = components
        
    def __get_components(self):
        """
        Gets the list of components that will be installed on this partition.
        """
        
        return self._components
    
    components = property(__get_components, __set_components,
                          doc="""Gets or sets the list of components that
                          will be installed on this partition.""")
    
    def __str__(self):
        """
        To string.
        """
        
        _str  = ''
        _str += 'Name:       ' + self._name + '\n'
        _str += 'Start:      ' + str(self._start) + '\n'
        _str += 'Size:       ' + str(self._size) + '\n'
        _str += 'Bootable:   ' + ('Yes' if self._bootable else 'No') + '\n'
        _str += 'Type:       ' + self._type + '\n'
        _str += 'Filesystem: ' + self._filesystem + '\n'
        if self._components:
            _str += 'Components:\n'
            for comp in self._components:
                _str += '  - ' + comp + '\n'
            _str += '\n'
        else:
            _str += 'Components: none\n'
        return _str

# ==========================================================================
# Test cases
# ==========================================================================        

if __name__ == '__main__':
    
    import common
    
    p = Partition('test-partition')
    
    print p.name
    
    p.size = 100
    
    print p.size
    print common.hex_format(p.size)
    
    p.size = '-'
    print p.size
    
    p.start = 100
    print p.start
    print common.hex_addr(p.start)
    
    p.bootable = True
    if p.is_bootable:
        print "Partition " + p.name + " is bootable"
    else:
        print "Partition " + p.name + " is not bootable"
        
    p.type = Partition.TYPE_FAT32
    p.filesystem = Partition.FILESYSTEM_VFAT
    
    p.components = [Partition.COMPONENT_BOOTLOADER,
                    Partition.COMPONENT_KERNEL,
                    Partition.COMPONENT_ROOTFS]
    
    print p.__str__()
