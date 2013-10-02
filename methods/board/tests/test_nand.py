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
from uboot import Uboot
from nand import NandInstaller
from nand import NandInstallerTFTP
from image_gen import NandImageGenerator

# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

test_host_ip_addr = '10.251.101.24'
#test_host_ip_addr = '192.168.1.108'
test_uboot_load_addr = '0x82000000'
test_ram_load_addr = '0x82000000'

class NandInstallerTFTPTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('SerialInstaller')
        logger.setLevel(rrutils.logger.DEBUG)
    
    def setUp(self):
        
        dryrun = False
        
        self._uboot = Uboot()
        self._uboot.dryrun = dryrun
        ret = self._uboot.open_comm(port='/dev/ttyUSB0', baud=115200)
        self.assertTrue(ret)
        ret = self._uboot.sync()
        self.assertTrue(ret)
        
        self._inst = NandInstallerTFTP(uboot=self._uboot)
        self._inst.net_mode = NandInstallerTFTP.MODE_DHCP
        self._inst.host_ipaddr = test_host_ip_addr
        self._inst.tftp_dir = '/srv/tftp'
        self._inst.tftp_port = 69
        self._inst.ram_load_addr = test_ram_load_addr
        self._inst.dryrun = dryrun
        
    def tearDown(self):
        self._uboot.close_comm()
    
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
        test_nps = False
        if test_nps:
            # Set a value manually
            self._inst.nand_page_size = 15
            self.assertEqual(self._inst.nand_page_size, 15)
            # Force to query uboot - page size = 0x800 (2048) for a leo dm368
            self._inst.nand_page_size = 0
            self.assertEqual(self._inst.nand_page_size, 2048)
    
    def test_tftp_settings(self):
        test_tftp = False
        if test_tftp:
            ret = self._inst._check_tftp_settings()
            self.assertTrue(ret)

    def test_tftp_dhcp(self):
        test_dhcp = False
        if test_dhcp:
            ret = self._inst.setup_uboot_network()
            self.assertTrue(ret)

    def test_load_file_to_ram(self):
        test_load_to_ram = False
        if test_load_to_ram:
            ret = self._inst.setup_uboot_network()
            self.assertTrue(ret)
            boot_img = "%s/images/bootloader" % devdir
            ret = self._inst._load_file_to_ram(boot_img, test_uboot_load_addr)
            self.assertTrue(ret)
    
    def test_install_bootloader(self):
        
        test_install_uboot = False
        if test_install_uboot:
            
            # Setup networking
            ret = self._inst.setup_uboot_network()
            self.assertTrue(ret)
            
            # Load to RAM the uboot that will make the installation
            uboot_img = "%s/images/bootloader" % devdir
            ret = self._inst.load_uboot_to_ram(uboot_img, test_uboot_load_addr)
            self.assertTrue(ret)
            
            # Image generator
            gen = NandImageGenerator()
            gen.bc_bin = ('%s/bootloader/u-boot-2010.12-rc2-psp03.01.01.39'
                      '/ti-flash-utils/src/DM36x/GNU/bc_DM36x.exe' % devdir)
            gen.image_dir = '%s/images' % devdir
            gen.dryrun = self._inst.dryrun
            
            # Generate the UBL nand image
            ubl_img = '%s/images/ubl_DM36x_nand.bin' % devdir
            ubl_nand_img = "%s/images/ubl_nand.nandbin" % devdir
            ubl_nand_start_block = 1
            ret = gen.gen_ubl_img(page_size=self._inst.nand_page_size,
                                        start_block=ubl_nand_start_block,
                                        input_img=ubl_img,
                                        output_img=ubl_nand_img)
            self.assertTrue(ret)
            
            # Install UBL to NAND 
            ret = self._inst.install_ubl(ubl_nand_img, ubl_nand_start_block)
            self.assertTrue(ret)
            
            # Generate the uboot nand image
            uboot_img = "%s/images/bootloader" % devdir
            uboot_nand_img = "%s/images/bootloader.nandbin" % devdir
            uboot_nand_start_block = 25
            uboot_entry_addr = '0x82000000'
            uboot_load_addr = '0x82000000'
            ret = gen.gen_uboot_img(page_size=self._inst.nand_page_size,
                                    start_block=uboot_nand_start_block,
                                    entry_addr=uboot_entry_addr,
                                    load_addr=uboot_load_addr,
                                    input_img=uboot_img,
                                    output_img=uboot_nand_img)
            self.assertTrue(ret)
            
            # Install uboot
            ret = self._inst.install_uboot(uboot_nand_img,
                                           uboot_nand_start_block)
            self.assertTrue(ret)

    def test_install_kernel(self):
        test_install_k = False
        if test_install_k:
            
            # Setup networking
            ret = self._inst.setup_uboot_network()
            self.assertTrue(ret)
            
            # Load to RAM the uboot that will make the installation
            uboot_img = "%s/images/bootloader" % devdir
            ret = self._inst.load_uboot_to_ram(uboot_img, test_uboot_load_addr)
            self.assertTrue(ret)
            
            # Install kernel
            kernel_img = "%s/images/kernel.uImage" % devdir
            kernel_start_block = 32
            ret = self._inst.install_kernel(kernel_img, kernel_start_block)
            self.assertTrue(ret)

    def test_install_cmdline(self):
        test_cmdline = True
        if test_cmdline:
            cmdline = "davinci_enc_mngr.ch0_output=COMPONENT davinci_enc_mngr.ch0_mode=1080I-30 davinci_display.cont2_bufsize=13631488 vpfe_capture.cont_bufoffset=13631488 vpfe_capture.cont_bufsize=12582912 video=davincifb:osd1=0x0x8:osd0=1920x1080x16,4050K@0,0:vid0=off:vid1=off console=ttyS0,115200n8 dm365_imp.oper_mode=0 vpfe_capture.interface=1 mem=83M rootfstype=jffs2 root=/dev/mtdblock2 mtdparts=davinci_nand.0:4096k(UBOOT),4736k(KERNEL),204800k(FS)"
            ret = self._inst.install_cmdline(cmdline)
            self.assertTrue(ret)

if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(NandInstallerTFTPTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
