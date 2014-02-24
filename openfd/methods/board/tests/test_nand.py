#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013-2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Tests for the nand module.
#
# ==========================================================================

import os, sys
import logging
import unittest
import check_env

sys.path.insert(1, os.path.abspath('..'))

import openfd.utils as utils
from openfd.methods.board.nand import NandInstaller
from openfd.methods.board.ram import TftpRamLoader
from openfd.methods.board.env import EnvInstaller
from openfd.methods.board.uboot import Uboot
from openfd.boards import BoardFactory

# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

test_host_ip_addr = '10.251.101.24'
#test_host_ip_addr = '192.168.1.110'
test_uboot_load_addr = '0x82000000'
test_ram_load_addr = '0x82000000'
test_mmap_file = '%s/images/nand-mmap.config' % devdir
test_tftp_dir = '/srv/tftp'
test_port = '/dev/ttyUSB0'

class NandInstallerTFTPTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        verbose = True
        dryrun = False
        logger = utils.logger.init_global_logger('NandInstaller')
        logger.setLevel(logging.DEBUG)
        streamhandler = logging.StreamHandler()
        streamhandler.setFormatter(logging.Formatter('%(msg)s'))
        if verbose:
            streamhandler.setLevel(logging.DEBUG)
        else:
            streamhandler.setLevel(logging.INFO)
        logger.addHandler(streamhandler)
        utils.executer.init_global_executer(dryrun=dryrun, enable_colors=False,
                                            verbose=verbose)
    
    def setUp(self):
        dryrun = False
        self.uboot = Uboot()
        self.uboot.serial_logger = utils.logger.get_global_logger()
        self.uboot.dryrun = dryrun
        ret = self.uboot.open_comm(port=test_port, baud=115200)
        self.assertTrue(ret)
        ret = self.uboot.sync()
        self.assertTrue(ret)
        
        self.loader = TftpRamLoader(self.uboot, TftpRamLoader.MODE_DHCP)
        self.loader.dir = test_tftp_dir
        self.loader.port = 69
        self.loader.host_ipaddr = test_host_ip_addr
        self.loader.dryrun = dryrun
        
        self.env_inst = EnvInstaller(uboot=self.uboot)
        self.env_inst.dryrun = dryrun
        
        self.board = BoardFactory().make('dm36x-leopard')
        
        self.inst = NandInstaller(uboot=self.uboot, board=self.board,
                                  loader=self.loader)
        self.inst.ram_load_addr = test_ram_load_addr
        self.inst.verbose = True
        self.inst.dryrun = dryrun
        self.inst.read_partitions(test_mmap_file)
        
    def tearDown(self):
        self.uboot.close_comm()
    
# ==========================================================================
# Test cases - Others 
# ==========================================================================
    
    def test_nand_block_size(self):
        print "---- test_nand_block_size ----"
        test_nbs = False
        if test_nbs:
            # Set a value manually
            self.inst.nand_block_size = 15
            self.assertEqual(self.inst.nand_block_size, 15)
            # Force to query uboot - block size = 128 KB for a leo dm368
            self.inst.nand_block_size = 0
            self.assertEqual(self.inst.nand_block_size, 131072)
        
    def test_nand_page_size(self):
        print "---- test_nand_page_size ----"
        test_nps = False
        if test_nps:
            # Set a value manually
            self.inst.nand_page_size = 15
            self.assertEqual(self.inst.nand_page_size, 15)
            # Force to query uboot - page size = 0x800 (2048) for a leo dm368
            self.inst.nand_page_size = 0
            self.assertEqual(self.inst.nand_page_size, 2048)
    
    def test_tftp_settings(self):
        print "---- test_tftp_settings ----"
        test_tftp = False
        if test_tftp:
            ret = self.inst._check_tftp_settings()
            self.assertTrue(ret)

    def test_tftp_dhcp(self):
        print "---- test_dhcp ----"
        test_dhcp = False
        if test_dhcp:
            ret = self.inst.setup_uboot_network()
            self.assertTrue(ret)

    def test_load_file_to_ram(self):
        print "---- test_load_to_ram ----"
        test_load_to_ram = False
        if test_load_to_ram:
            ret = self.inst.setup_uboot_network()
            self.assertTrue(ret)
            boot_img = "%s/images/bootloader" % devdir
            ret = self.inst._load_file_to_ram(boot_img, test_uboot_load_addr)
            self.assertTrue(ret)
    
    def test_read_partitions(self):
        print "---- test_nand_block_size ----"
        test_read_part = False
        if test_read_part:
            self.inst.read_partitions('%s/images/nand-mmap.config' % devdir)
    
    def test_mtdparts(self):
        print "---- test_mtdparts ----"
        test_mtd_parts = False
        if test_mtd_parts:
            self.inst._generate_mtdparts('davinci_nand.0')
    
# ==========================================================================
# Install methods
# ==========================================================================
            
    def setup_network(self):
        print "---- Setting up network ----"
        self.loader.setup_uboot_network()
        self.uboot.set_env('autostart', 'yes')
        self.uboot.save_env()
    
    def load_uboot(self):
        print "---- Loading uboot to RAM ----"
        uboot_img = "%s/images/bootloader" % devdir
        self.inst.load_uboot_to_ram(uboot_img, test_uboot_load_addr)
            
    def install_bootloader(self):
        print "---- Installing bootloader ----"
        self.inst.install_ipl()
        self.inst.install_bootloader()
    
    def install_kernel(self):
        print "---- Installing kernel ----"
        self.inst.install_kernel(force=True)
    
    def install_fs(self):
        print "---- Installing fs ----"
        self.inst.install_fs(force=True)
    
    def install_cmdline(self):
        print "---- Installing cmdline ----"
        # cmdline for ubifs
        cmdline = "davinci_enc_mngr.ch0_output=COMPONENT davinci_enc_mngr.ch0_mode=1080I-30 davinci_display.cont2_bufsize=13631488 vpfe_capture.cont_bufoffset=13631488 vpfe_capture.cont_bufsize=12582912 video=davincifb:osd1=0x0x8:osd0=1920x1080x16,4050K@0,0:vid0=off:vid1=off console=ttyS0,115200n8 dm365_imp.oper_mode=0 mem=83M ubi.mtd=ROOTFS root=ubi0:rootfs rootfstype=ubifs mtdparts=davinci_nand.0:128k@128k(UBL),384k@3200k(UBOOT),4736k@4096k(KERNEL),204800k@8832k(ROOTFS)"
        self.env_inst.install_variable('bootargs', cmdline)
        
    def install_bootcmd(self):
        print "---- Installing bootcmd ----"
        bootcmd = "'nboot 0x82000000 0 ${koffset}'"
        self.env_inst.install_variable('bootcmd', bootcmd)
        
    def install_mtdparts(self):
        print "---- Installing mtdparts ----"
        mtdparts = "mtdparts=davinci_nand.0:128k@128k(UBL),384k@3200k(UBOOT),4736k@4096k(KERNEL),204800k@8832k(ROOTFS)"
        self.env_inst.install_variable('mtdparts', mtdparts, force=True)

# ==========================================================================
# Test cases - Install methods 
# ==========================================================================

    def test_install_bootloader(self):
        test_install_uboot = False
        if test_install_uboot:
            self.setup_network()
            self.load_uboot()
            self.install_bootloader()
            
    def test_install_kernel(self):
        test_install_k = False
        if test_install_k:
            self.setup_network()
            self.load_uboot()
            self.install_kernel()

    def test_install_fs(self):
        test_fs = False
        if test_fs:
            self.setup_network()
            self.load_uboot()
            self.install_fs()

    def test_install_cmdline(self):
        test_cmdline = False
        if test_cmdline:
            self.install_cmdline()
            
    def test_install_bootcmd(self):
        test_bootcmd = False
        if test_bootcmd:
            self.install_bootcmd()
            
    def test_install_mtdparts(self):
        test_mtdparts = False
        if test_mtdparts:
            self.install_mtdparts()
            
    def test_install_all(self):
        install_all = True
        if install_all:
            self.setup_network()
            self.load_uboot()
            self.install_bootloader()
            self.install_kernel()
            self.install_fs()
            self.install_cmdline()
            self.install_bootcmd()
            self.install_mtdparts()
            self.uboot.set_env('autostart', 'yes')
            self.uboot.save_env()
            self.uboot.cmd('echo Installation complete')

if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(NandInstallerTFTPTestCase)
    unittest.TextTestRunner(verbosity=1).run(suite)
