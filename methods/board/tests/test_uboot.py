#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# Tests for the uboot module.
#
# ==========================================================================

import os, sys
import unittest
import rrutils

sys.path.insert(1, os.path.abspath('..'))

from uboot import Uboot

class UbootTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('Uboot')
        logger.setLevel(rrutils.logger.DEBUG)
    
    def setUp(self):
        self._uboot = Uboot()
        self._uboot.uboot_dryrun = False
        self._uboot.dryrun = False
        ret = self._uboot.open_comm(port='/dev/ttyUSB0', baud=115200)
        self.assertTrue(ret)
        ret = self._uboot.sync()
        self.assertTrue(ret)
        
    def tearDown(self):
        self._uboot.close_comm()
 
    def test_nand_block_size(self):
        if self._uboot.uboot_dryrun:
            self.assertEqual(self._uboot.nand_block_size, 0)
            self._uboot.nand_block_size = 131072
            self.assertEqual(self._uboot.nand_block_size, 131072)
        else:
            # Set a value manually
            self._uboot.nand_block_size = 15
            self.assertEqual(self._uboot.nand_block_size, 15)
            # Force to query uboot - block size = 128 KB for a leo dm368
            self._uboot.nand_block_size = 0
            self.assertEqual(self._uboot.nand_block_size, 131072)
 
    def test_nand_page_size(self):
        if self._uboot.uboot_dryrun:
            self.assertEqual(self._uboot.nand_page_size, 0)
            self._uboot.nand_page_size = 2048
            self.assertEqual(self._uboot.nand_page_size, 2048)
        else:
            # Set a value manually
            self._uboot.nand_page_size = 15
            self.assertEqual(self._uboot.nand_page_size, 15)
            # Force to query uboot - page size = 0x800 (2048) for a leo dm368
            self._uboot.nand_page_size = 0
            self.assertEqual(self._uboot.nand_page_size, 2048)
 
    def test_uboot_env(self):
        if self._uboot.uboot_dryrun:
            ret = self._uboot.set_env('test_env','yes')
            self.assertTrue(ret)
            value = self._uboot.get_env('test_env')
            self.assertEqual(value, '') # empty because of uboot_dryrun
        else:
            # Get
            value = self._uboot.get_env('kerneloffset')
            self.assertEqual(value, '0x400000')
            value = self._uboot.get_env('importbootenv')
            self.assertEqual(value, 'echo Importing environment from mmc ...; env import -t ${loadaddr} ${filesize}')
            # Set
            ret = self._uboot.set_env('test_env','yes')
            self.assertTrue(ret)
            value = self._uboot.get_env('test_env')
            self.assertEqual(value, 'yes')

    def test_uboot_cmd(self):
        ret = self._uboot.cmd('nand info')
        self.assertTrue(ret)
        ret = self._uboot.cancel_cmd()
        self.assertTrue(ret)
 
if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(UbootTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
