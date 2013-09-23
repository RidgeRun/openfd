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
import check_env

sys.path.insert(1, os.path.abspath('..'))

import rrutils
import time
from serial_comm import SerialInstaller
from serial_comm import SerialInstallerTFTP

# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

test_host_ip_addr = '10.251.101.24'
#test_host_ip_addr = '192.168.1.108'
test_uboot_load_addr = '0x82000000'
test_ram_load_addr = '0x82000000'

class SerialInstallerTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('SerialInstaller')
        logger.setLevel(rrutils.logger.DEBUG)
    
    def setUp(self):
        self._inst = SerialInstaller()
        ret = self._inst.open_comm(port='/dev/ttyUSB0', baud=115200)
        self.assertTrue(ret)
        ret = self._inst.uboot_sync()
        self.assertTrue(ret)
        
    def tearDown(self):
        self._inst.close_comm()
        
    def test_nand_block_size(self):
        
        test_nbs = False
        if test_nbs:
            # Set a value manually
            self._inst.nand_block_size = 15
            self.assertEqual(self._inst.nand_block_size, 15)
            
            # Force to query uboot - block size = 128 KB for a leo dm368
            self._inst.nand_block_size = 0
            self.assertEqual(self._inst.nand_block_size, 131072)
        
    def test_nand_page_size(self):
        
        # Set a value manually
        test_nps = False
        if test_nps:
            self._inst.nand_page_size = 15
            self.assertEqual(self._inst.nand_page_size, 15)
            
            # Force to query uboot - page size = 0x800 (2048) for a leo dm368
            self._inst.nand_page_size = 0
            self.assertEqual(self._inst.nand_page_size, 2048)

    def test_uboot_env(self):
        
        test_env = False
        if test_env:
            
            value = self._inst._uboot_get_env('kerneloffset')
            self.assertEqual(value, '0x400000')
            
            value = self._inst._uboot_get_env('importbootenv')
            self.assertEqual(value, 'echo Importing environment from mmc ...; env import -t ${loadaddr} ${filesize}')

    def test_uboot_cmd(self):
        
        test_cmd = False
        if test_cmd:
            
            ret = self._inst.uboot_cmd('nand info')
            self.assertTrue(ret)

class SerialInstallerTFTPTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('SerialInstallerTFTP')
        logger.setLevel(rrutils.logger.DEBUG)
    
    def setUp(self):
        self._inst = SerialInstallerTFTP()
        self._inst.host_ipaddr = test_host_ip_addr
        self._inst.net_mode = SerialInstallerTFTP.MODE_DHCP
        self._inst.ram_load_addr = test_ram_load_addr
        ret = self._inst.open_comm(port='/dev/ttyUSB0', baud=115200)
        self.assertTrue(ret)
        ret = self._inst.uboot_sync()
        self.assertTrue(ret)

    def tearDown(self):
        self._inst.close_comm()
        
    def test_tftp_settings(self):
        
        test_tftp = False
        if test_tftp:
            self._inst.tftp_dir = '/srv/tftp'
            self._inst.tftp_port = 69
            ret = self._inst._check_tftp_settings()
            self.assertTrue(ret)
        
    def test_tftp_dhcp(self):
        
        test_dhcp = False
        if test_dhcp:
            ret = self._inst._setup_uboot_network()
            self.assertTrue(ret)

    def test_load_file_to_ram(self):
        
        test_load_to_ram = False
        if test_load_to_ram:
            boot_img = "%s/images/bootloader" % devdir
            ret = self._inst._load_file_to_ram(boot_img)
            self.assertTrue(ret)
    
    def test_install_bootloader(self):
        
        test_install_boot = True
        if test_install_boot:
            
            # Load to RAM the uboot that will make the installation
            uboot_img = "%s/images/bootloader" % devdir
            ret = self._inst.load_uboot_to_ram(uboot_img, test_uboot_load_addr)
            self.assertTrue(ret)
            
            # Install the Initial Program Loader (UBL) 
            ubl_nand_img = "%s/images/ubl_nand.nandbin" % devdir
            ubl_nand_start_block = 1
            ret = self._inst.install_ubl(ubl_nand_img, ubl_nand_start_block)
            self.assertTrue(ret)

            # Install the Bootloader (uboot) 
            uboot_nand_img = "%s/images/bootloader.nandbin" % devdir
            uboot_nand_start_block = 25
            ret = self._inst.install_uboot(uboot_nand_img,
                                           uboot_nand_start_block)
            self.assertTrue(ret)

if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(SerialInstallerTestCase)
    suite.addTests(loader.loadTestsFromTestCase(SerialInstallerTFTPTestCase))
    unittest.TextTestRunner(verbosity=2).run(suite)
