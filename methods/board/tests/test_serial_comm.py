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
# Tests for the serial_comm module.
#
# ==========================================================================

import os, sys
import unittest

sys.path.insert(1, os.path.abspath('..'))

import rrutils
import serial_comm
import time

class SerialInstallerTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('serial_comm-test')
        logger.setLevel(rrutils.logger.DEBUG)
    
    def setUp(self):
        self._inst = serial_comm.SerialInstaller()
        ret = self._inst.open_comm(port='/dev/ttyUSB0', baud=115200)
        self.assertTrue(ret)
        
    def tearDown(self):
        self._inst.close_comm()
        
    def test_uboot_sync(self):
        ret = self._inst.uboot_sync()
        self.assertTrue(ret)
    
    def test_nand_block_size(self):
        
        # Set a value manually
        self._inst.nand_block_size = 15
        self.assertEqual(self._inst.nand_block_size, 15)
        
        # Force to query uboot - block size = 128 KB for a leo dm368
        self._inst.nand_block_size = 0
        self.assertEqual(self._inst.nand_block_size, 131072)
        
    def test_nand_page_size(self):
        
        # Set a value manually
        self._inst.nand_page_size = 15
        self.assertEqual(self._inst.nand_page_size, 15)
        
        # Force to query uboot - page size = 0x800 (2048) for a leo dm368
        self._inst.nand_page_size = 0
        self.assertEqual(self._inst.nand_page_size, 2048)

    def test_tftp_settings(self):

        self._inst.tftp_dir = '/srv/tftp'
        self._inst.tftp_port = 69
        ret = self._inst._check_tftp_settings()
        self.assertTrue(ret)

    def test_uboot_env(self):
        
        test_env = False
        if test_env:
            
            value = self._inst._uboot_env('kerneloffset')
            self.assertEqual(value, '0x400000')
            
            value = self._inst._uboot_env('importbootenv')
            self.assertEqual(value, 'echo Importing environment from mmc ...; env import -t ${loadaddr} ${filesize}')

    def test_uboot_cmd(self):
        
        test_cmd = False
        if test_cmd:
            
            ret = self._inst.uboot_cmd('nand info')
            self.assertTrue(ret)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(SerialInstallerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
