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
# Tests for the sdcard module.
#
# ==========================================================================

import os, sys
import unittest
import check_env

sys.path.insert(1, os.path.abspath('..'))

import rrutils
from sdcard import SDCardInstaller
from component import ComponentInstaller

# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

# Default variables for test cases - Leo DM368

uboot = 'u-boot-2010.12-rc2-psp03.01.01.39'
uflash_bin = '%s/bootloader/%s/src/tools/uflash/uflash' % (devdir, uboot)
ubl_file = '%s/images/ubl_DM36x_sdmmc.bin' % devdir
uboot_file = '%s/images/bootloader' % devdir
uboot_entry_addr = '0x82000000' # 2181038080
uboot_load_addr = '2181038080' # 0x82000000
kernel_image = '%s/images/kernel.uImage' % devdir
rootfs = '%s/fs/fs' % devdir
workdir = "%s/images" % devdir

# IMPORTANT: Main test device (be careful!)
test_device = '/dev/ttyUSB0'

class SDCardInstallerTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('sd_card-test')
        logger.setLevel(rrutils.logger.DEBUG)
        
    def setUp(self):
        
        # Component installer
        self._comp_installer = ComponentInstaller()        
        self._comp_installer.uflash_bin = uflash_bin
        self._comp_installer.ubl_file = ubl_file
        self._comp_installer.uboot_file = uboot_file
        self._comp_installer.uboot_entry_addr = uboot_entry_addr
        self._comp_installer.uboot_load_addr = uboot_load_addr
        self._comp_installer.kernel_image = kernel_image
        self._comp_installer.rootfs = rootfs
        self._comp_installer.workdir = workdir
        
        # SDCard Installer
        
        self._sd_installer = SDCardInstaller(self._comp_installer)
        
    def tearDown(self):
        pass
        
    def test_first(self):
        self._sd_installer.mode = SDCardInstaller.MODE_SD
        self._sd_installer.device = test_device
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(SDCardInstallerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
