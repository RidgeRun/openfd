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
# Tests for the image_gen module.
#
# ==========================================================================


import os, sys
import unittest
import rrutils
import check_env

sys.path.insert(1, os.path.abspath('..'))

from image_gen import NandImageGenerator


# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

class NandImageGeneratorTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('SerialInstaller')
        logger.setLevel(rrutils.logger.DEBUG)
    
    def setUp(self):
        self._gen = NandImageGenerator()
        self._gen.bc_bin = ('%s/bootloader/u-boot-2010.12-rc2-psp03.01.01.39'
                    '/ti-flash-utils/src/DM36x/GNU/bc_DM36x.exe' % devdir)
        self._gen.image_dir = '%s/images' % devdir
        self._gen.verbose = True
        self._gen.dryrun = False
 
    def tearDown(self):
        pass
 
    def test_gen_ubl_img(self):
        
        # BC info for UBL image:
        #   Intended NAND device has 2048 byte pages.
        #   Image intended for block 1.
        #   Image entry point is 0x00000100. (ignore)
        #   Image load address is 0x00000020. (ignore)
        
        page_size = 2048
        start_block = 1
        input_img = '%s/images/ubl_DM36x_nand.bin' % devdir
        output_img = '%s/images/ubl_nand.nandbin' % devdir
        ret = self._gen.gen_ubl_img(page_size, start_block, input_img,
                                    output_img)
        self.assertTrue(ret)
 
    def test_gen_uboot_img(self):
        
        # BC info for uboot image:
        #   Intended NAND device has 2048 byte pages.
        #   Image intended for block 25.
        #   Image entry point is 0x82000000.
        #   Image load address is 0x82000000.

        page_size = 2048
        start_block = 25
        entry_addr = '0x82000000'
        load_addr = '0x82000000'
        input_img = '%s/images/bootloader' % devdir
        output_img = '%s/images/bootloader.nandbin' % devdir
        ret = self._gen.gen_uboot_img(page_size, start_block, entry_addr, load_addr,
                                input_img, output_img)
        self.assertTrue(ret)
        
if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(NandImageGeneratorTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
