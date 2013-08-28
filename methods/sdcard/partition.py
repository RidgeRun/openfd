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

# ==========================================================================
# Imports
# ==========================================================================

import rrutils.hexutils as hexutils

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
    COMPONENT_BLANK = 'blank'
    
    def __init__(self, name, start_addr=0, size=0, bootable=False,
                 part_type='', filesystem='', components=[]):
        """    
        :param name: Partition name.
        :param start_addr: Partition start addres (decimal).
        :param size: Partition size in cylinders. Size can be '-' to indicate
            the max size available.
        :param bootable: Enables the bootable flag on this partition.
        :type bootable: boolean
        :param part_type: Partition type. Possible values:
            :const:`TYPE_LINUX_NATIVE`, :const:`TYPE_FAT32`,
            :const:`TYPE_UNKNOWN`.
        :param filesystem: Partition filesystem. Possible values:
            :const:`FILESYSTEM_VFAT`, :const:`FILESYSTEM_EXT3`, 
            :const:`FILESYSTEM_UNKNOWN`.
        :param components: A list of partition components. Possile Values:
            :const:`COMPONENT_BOOTLOADER`, :const:`COMPONENT_KERNEL`,
            :const:`COMPONENT_ROOTFS`, :const:`COMPONENT_BLANK`
        """
        
        self._name = name
        self._start = start_addr
        self._size = size
        self._bootable = bootable
        self._type = part_type
        self._filesystem = filesystem
        self._components = components
    
    @classmethod
    def decode_partition_type(cls, partition_type):
        """
        Given a partition type, like :const:`TYPE_LINUX_NATIVE`, returns
        a friendly name, such as 'Linux Native'.
        
        :param partition_type: Partition type.
        :returns: Partition type friendly name.
        """
        
        friendly_type = cls.TYPE_UNKNOWN
        
        if partition_type == cls.TYPE_FAT32:
            friendly_type = 'W95 FAT32 (LBA)'
        elif partition_type == cls.TYPE_LINUX_NATIVE:
            friendly_type = 'Linux Native'
        
        return friendly_type
    
    @property
    def name(self):
        """
        Partition name (read-only).
        """
        
        return self._name
       
    def __set_start(self, start):
        self._start = start
        
    def __get_start(self):
        return self._start
        
    start = property(__get_start, __set_start,
                     doc="""Partition start address (decimal).""")
        
    def __set_size(self, size):
        self._size = size
        
    def __get_size(self):
        return self._size
    
    size = property(__get_size, __set_size,
                    doc="""Partition size in cylinders (decimal). Size can
                    be '-' to indicate the max size available.""")
    
    def __set_type(self, partition_type):
        self._type = partition_type
        
    def __get_type(self):
        return self._type
    
    type = property(__get_type, __set_type,
                    doc="""Partition type.""")
    
    def __set_filesystem(self, filesystem):
        self._filesystem = filesystem
        
    def __get_filesystem(self):
        return self._filesystem
    
    filesystem = property(__get_filesystem, __set_filesystem,
                          doc="""Partition filesystem.""")
    
    def __set_bootable(self, bootable):
        self._bootable = bootable
        
    def __get_bootable(self):
        return self._bootable
    
    bootable = property(__get_bootable, __set_bootable,
                        doc="""Partition bootable flag.""")

    is_bootable = bootable
    
    def __set_components(self, components):
        self._components = components
        
    def __get_components(self):
        return self._components
    
    components = property(__get_components, __set_components,
                          doc="""List of components that
                          will be installed on this partition.""")
    
    def __str__(self):
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
    
    p = Partition('test-partition')
    
    print p.name
    
    p.size = 100
    
    print p.size
    print hexutils.hex_format(p.size)
    
    p.size = '-'
    print p.size
    
    p.start = 100
    print p.start
    print hexutils.hex_addr(p.start)
    
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
