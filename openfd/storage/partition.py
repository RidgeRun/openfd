#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Representation of a partition in a storage device.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import ConfigParser

# ==========================================================================
# Functions
# ==========================================================================

def read_nand_partitions(filename):
    """
    Reads the NAND partitions information from the given file.
    
    :param filename: Path to the file with the partitions information.
    :returns: Returns the list of partitions read from the given file.  
    """
    
    partitions = []
    config = ConfigParser.RawConfigParser()
    config.readfp(open(filename))
    for section in config.sections():
        if config.has_option(section, 'name'):
            part = NandPartition(config.get(section, 'name'))
            if config.has_option(section, 'start_blk'):
                part.start_blk = int(config.get(section, 'start_blk'))
            if config.has_option(section, 'size_blks'):
                part.size_blks = int(config.get(section, 'size_blks'))
            if config.has_option(section, 'filesystem'):
                part.filesystem = config.get(section, 'filesystem')
            if config.has_option(section, 'image'):
                part.image = config.get(section, 'image')
            # insert ordered by start blk
            inserted = False
            for i in range(0, len(partitions)):
                if partitions[i].start_blk > part.start_blk:
                    partitions.insert(i, part)
                    inserted = True
                    break
            if not inserted:
                partitions.append(part)
    return partitions

def read_sdcard_partitions(filename):
    """
    Reads the partitions information from the given file.
    
    :param filename: Path to the file with the partitions information.
    :returns: Returns the list of partitions read from the given file.  
    """
    
    partitions = []
    config = ConfigParser.RawConfigParser()
    config.readfp(open(filename))
    for section in config.sections():
        part = None
        if config.has_option(section, 'name'):
            part = SDCardPartition(config.get(section, 'name'))
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
            partitions.append(part)
    return partitions

def read_loopdevice_partitions(filename):
    """
    Reads the partitions information from the given file.
    
    :param filename: Path to the file with the partitions information.
    :returns: Returns the list of partitions read from the given file.  
    """
    
    partitions = []
    config = ConfigParser.RawConfigParser()
    config.readfp(open(filename))
    for section in config.sections():
        part = None
        if config.has_option(section, 'name'):
            part = LoopDevicePartition(config.get(section, 'name'))
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
            partitions.append(part)
    return partitions

# ==========================================================================
# Classes
# ==========================================================================

class Partition(object):
    """ Base class for a partition. """

class NandPartition(Partition):
    """ Class that represents a NAND partition. """
    
    # Common partition filesystems
    
    FILESYSTEM_UNKNOWN = 'unknown'
    FILESYSTEM_UBIFS = 'ubifs'
    
    # Common partition components
    
    COMPONENT_IPL = 'ipl'
    COMPONENT_BOOTLOADER = 'bootloader'
    COMPONENT_KERNEL = 'kernel'
    COMPONENT_ROOTFS = 'rootfs'
    COMPONENT_BLANK = 'blank'
    
    def __init__(self, name, start_blk=0, size_blks=0, filesystem='',
                 image='', components=[]):
        """    
        :param name: Partition name.
        :param start_blk: Partition start block in NAND (decimal).
        :param size_blks: Partition size in NAND blocks (decimal).
        :param filesystem: Partition filesystem. Possible values:
            :const:`FILESYSTEM_VFAT`, :const:`FILESYSTEM_EXT3`, 
            :const:`FILESYSTEM_UNKNOWN`.
        :param components: A list of partition components. Possible values:
            :const:`COMPONENT_IPL`, :const:`COMPONENT_BOOTLOADER`,
            :const:`COMPONENT_KERNEL`, :const:`COMPONENT_ROOTFS`,
            :const:`COMPONENT_BLANK`.
        :param image: Image filename associated with this partition.
        """
        
        self._name = name
        self._start_blk = start_blk
        self._size_blks = size_blks
        self._filesystem = filesystem
        self._image= image
    
    @property
    def name(self):
        """
        Partition name (read-only).
        """
        
        return self._name
       
    def __set_start_blk(self, start):
        self._start_blk = start
        
    def __get_start_blk(self):
        return self._start_blk
        
    start_blk = property(__get_start_blk, __set_start_blk,
                     doc="""Partition start block in NAND.""")
        
    def __set_size_blks(self, size):
        self._size_blks = size
        
    def __get_size_blks(self):
        return self._size_blks
    
    size_blks = property(__get_size_blks, __set_size_blks,
                    doc="""Partition size in NAND blocks (decimal).""")
    
    def __set_filesystem(self, filesystem):
        self._filesystem = filesystem
        
    def __get_filesystem(self):
        return self._filesystem
    
    filesystem = property(__get_filesystem, __set_filesystem,
                          doc="""Partition filesystem. Possible values: 
                          :const:`FILESYSTEM_UBIFS`,
                          :const:`FILESYSTEM_UNKNOWN`.""")
    
    def __set_image(self, img):
        self._image = img
        
    def __get_image(self):
        return self._image
    
    image = property(__get_image, __set_image,
                    doc="""Image filename associated with this partition.""") 

class SDCardPartition(Partition):
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
        :param start_addr: Partition start address (decimal).
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
        :param components: A list of partition components. Possible values:
            :const:`COMPONENT_BOOTLOADER`, :const:`COMPONENT_KERNEL`,
            :const:`COMPONENT_ROOTFS`, :const:`COMPONENT_BLANK`.
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
                    doc="""Partition type. Possible values:
                    :const:`TYPE_LINUX_NATIVE`, :const:`TYPE_FAT32`,
                    :const:`TYPE_UNKNOWN`.""")
    
    def __set_filesystem(self, filesystem):
        self._filesystem = filesystem
        
    def __get_filesystem(self):
        return self._filesystem
    
    filesystem = property(__get_filesystem, __set_filesystem,
                          doc="""Partition filesystem. Possible values: 
                          :const:`FILESYSTEM_VFAT`, :const:`FILESYSTEM_EXT3`,
                          :const:`FILESYSTEM_UNKNOWN`.""")
    
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
                          will be installed on this partition. Possible values:
                          :const:`COMPONENT_BOOTLOADER`,
                          :const:`COMPONENT_KERNEL`,
                          :const:`COMPONENT_ROOTFS`,
                          :const:`COMPONENT_BLANK`.""")

class LoopDevicePartition(SDCardPartition):
    
    def __init__(self, name, start_addr=0, size=0, bootable=False,
                 part_type='', filesystem='', components=[]):
        """    
        :param name: Partition name.
        :param start_addr: Partition start address (decimal).
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
        :param components: A list of partition components. Possible values:
            :const:`COMPONENT_BOOTLOADER`, :const:`COMPONENT_KERNEL`,
            :const:`COMPONENT_ROOTFS`, :const:`COMPONENT_BLANK`.
        """

        SDCardPartition.__init__(self, name, start_addr, size, bootable,
                                 part_type, filesystem, components)
        self._device = None
    
    def __set_device(self, device):
        self._device = device
        
    def __get_device(self):
        return self._device
    
    device = property(__get_device, __set_device,
                    doc="""Loop device (string) which this partition is
                    associated to.""")
    