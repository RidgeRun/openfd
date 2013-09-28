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
        self._uboot.dryrun = False
        ret = self._uboot.open_comm(port='/dev/ttyUSB0', baud=115200)
        self.assertTrue(ret)
        ret = self._uboot.sync()
        self.assertTrue(ret)
        
    def tearDown(self):
        self._uboot.close_comm()
 
    def test_uboot_env(self):
        if self._uboot.dryrun:
            ret = self._uboot.set_env('test_env','yes')
            self.assertTrue(ret)
            value = self._uboot.get_env('test_env')
            self.assertEqual(value, '') # empty because of dryrun
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
