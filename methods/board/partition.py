#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# Representation of a nand memory partition.
#
# ==========================================================================

# ==========================================================================
# Classes
# ==========================================================================

class NandPartition(object):
    """ Class that represents a file system partition. """
    
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
    