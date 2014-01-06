#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Tests for the partition module.
#
# ==========================================================================

import os, sys
import unittest

sys.path.insert(1, os.path.abspath('..'))

import rrutils
from sdcard import Partition

class PartitionTestCase(unittest.TestCase):
    
    def setUp(self):
        self._p = Partition('test-partition')
        
    def tearDown(self):
        pass
        
    def test_properties(self):
                
        components = [Partition.COMPONENT_BOOTLOADER,
                      Partition.COMPONENT_KERNEL,
                      Partition.COMPONENT_ROOTFS]
                
        self._p.size = 100
        self._p.start = 100
        self._p.bootable = True
        self._p.type = Partition.TYPE_FAT32
        self._p.filesystem = Partition.FILESYSTEM_VFAT
        self._p.components = components
        
        self.assertEqual(self._p.name, 'test-partition')
        self.assertEqual(self._p.size, 100)
        self.assertEqual(self._p.start, 100)
        self.assertEqual(self._p.bootable, True)
        self.assertEqual(self._p.type, Partition.TYPE_FAT32)
        self.assertEqual(self._p.filesystem, Partition.FILESYSTEM_VFAT)
        self.assertEqual(self._p.components, components)

        print self._p.__str__()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(PartitionTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
