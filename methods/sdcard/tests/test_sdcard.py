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

# IMPORTANT: Main test device (be careful!)
test_device = '/dev/sdb'

class SDCardInstallerTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('sd_card-test')
        logger.setLevel(rrutils.logger.DEBUG)
        
    def setUp(self):

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
        self._inst = SDCardInstaller(self._comp_installer)
        
    def tearDown(self):
        pass
        
    def test_device(self):
        
        # Change these booleans to enable/disable tests that assume some
        # preconditions (i.e. we know in advance the device is mounted,
        # we know the device size, etc.)
        test_all = False         # Force all tests
        test_mounted = False
        test_sizes = False
        
        # Device information
        is_mounted = True
        #mounted_partitions = ['/media/rootfs_', '/media/boot'] # 'mount | grep /dev/sdb  | cut -f 3 -d " "
        mounted_partitions = ['/media/boot'] # 'mount | grep /dev/sdb  | cut -f 3 -d " "
        size_b = 2002780160 # sudo fdisk -l <device> | grep <device> | grep Disk | cut -f 5 -d " "
        size_gb = 1
        size_cyl = 243
        
        #   --------- Don't edit below -----------
        
        self._inst.mode = SDCardInstaller.MODE_SD
        self._inst.dryrun = False
        self._inst.interactive = False
        
        # Device existence
        self._inst.device = '/dev/sdbX'
        self.assertFalse(self._inst._device_exists())
        self._inst.device = test_device
        self.assertTrue(self._inst._device_exists())
        
        # Device mounted
        if test_mounted or test_all:
            self.assertEqual(self._inst._device_is_mounted(), is_mounted)
            partitions = self._inst._get_device_mounted_partitions()
            self.assertEqual(partitions, mounted_partitions)
        
        # Device sizes
        if test_sizes or test_all:
            self.assertEqual(self._inst._get_device_size_b(), size_b)
            self.assertEqual(self._inst._get_device_size_gb(), size_gb)
            self.assertEqual(self._inst._get_device_size_cyl(), size_cyl)
        
    def test_partitions(self):
        
        self._inst.mode = SDCardInstaller.MODE_SD
        self._inst.dryrun = False
        self._inst.interactive = False
        self._inst.device = test_device
        
        # Auto-unmount_partitions
        if self._inst._device_is_mounted():
            ret = self._inst._auto_unmount_partitions()
            self.assertTrue(ret, 'Can\'t unmount partitions on %s' 
                            % self._inst.device)
            
        # Read_partitions
        sdcard_mmap_filename = '%s/images/sd-mmap.config' % devdir
        ret = self._inst._read_partitions(sdcard_mmap_filename)
        self.assertTrue(ret)
        
        # Create partitions
        ret = self._inst._create_partitions()
        self.assertTrue(ret, 'Failed to create partitions on %s'
                        % self._inst.device)
        
    def test_interactive(self):
        
        self._inst.mode = SDCardInstaller.MODE_SD
        self._inst.dryrun = False
        self._inst.interactive = True
        self._inst.device = test_device
        
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(SDCardInstallerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
