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
# Tests for the sdcard module.
#
# ==========================================================================

import os, sys
import logging
import argparse
import unittest
import check_env

sys.path.insert(1, os.path.abspath('..'))

import openfd.utils as utils
from openfd.methods.sdcard import SDCardInstaller
from openfd.methods.sdcard import LoopDeviceInstaller 
from openfd.boards import BoardFactory

# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

# IMPORTANT: Main test device (be careful!)
test_device = '/dev/sdb'

#test_board = 'dm36x-leopard'
test_board = 'dm816x-z3'

class SDCardInstallerTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        verbose = True
        dryrun = False
        logger = utils.logger.init_global_logger('SDCardInstaller')
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

        # Default variables for test cases - Leo DM368
        if test_board == 'dm36x-leopard':
            uboot = 'u-boot-2010.12-rc2-psp03.01.01.39'
            uflash_bin = '%s/bootloader/%s/src/tools/uflash/uflash' % (devdir, uboot)
            ubl_file = '%s/images/ubl_DM36x_sdmmc.bin' % devdir
            uboot_file = '%s/images/bootloader' % devdir
            uboot_entry_addr = '0x82000000' # 2181038080
            uboot_load_addr = '2181038080' # 0x82000000
            kernel_image = '%s/images/kernel.uImage' % devdir
            rootfs = '%s/fs/fs' % devdir
            workdir = "%s/images" % devdir
            bootargs = ("davinci_enc_mngr.ch0_output=COMPONENT "
                      "davinci_enc_mngr.ch0_mode=1080I-30  "
                      "davinci_display.cont2_bufsize=13631488 "
                      "vpfe_capture.cont_bufoffset=13631488 "
                      "vpfe_capture.cont_bufsize=12582912 "
                      "video=davincifb:osd1=0x0x8:osd0=1920x1080x16,4050K@0,0:vid0=off:vid1=off "
                      "console=ttyS0,115200n8  dm365_imp.oper_mode=0  vpfe_capture.interface=1 "
                      "mem=83M root=/dev/mmcblk0p2 rootdelay=2 "
                      "rootfstype=ext3")
    
            # Component installer
            # TODO - Adapt to the new logic where SDCardInstaller receives a
            #        a Board object instead of a ComponentInstaller
#            self._comp_installer = ComponentInstaller()        
#            self._comp_installer.uflash_bin = uflash_bin
#            self._comp_installer.ubl_file = ubl_file
#            self._comp_installer.uboot_file = uboot_file
#            self._comp_installer.uboot_entry_addr = uboot_entry_addr
#            self._comp_installer.uboot_load_addr = uboot_load_addr
#            self._comp_installer.kernel_image = kernel_image
#            self._comp_installer.rootfs = rootfs
#            self._comp_installer.bootargs = bootargs
#            self._comp_installer.workdir = workdir
        
        if test_board == 'dm816x-z3':
            uboot = 'u-boot-2010.06'
            self.args = argparse.Namespace()
            self.args.mmap_file = '%s/images/sd-mmap.config' % devdir
            self.args.uboot_min_file = '%s/images/u-boot.min.sd' % devdir
            self.args.uboot_file = '%s/images/bootloader' % devdir
            self.args.uboot_load_addr = '0x82000000'
            self.args.uboot_bootargs = ('console=ttyO2,115200n8 '
               'notifyk.vpssm3_sva=0xBF900000 root=/dev/mmcblk0p2 rootdelay=2 '
               'rootfstype=ext4 mem=364M@0x80000000 mem=320M@0x9FC00000 '
               'vmalloc=512M vram=81M')
            self.args.kernel_file = '%s/images/kernel.uImage' % devdir
            self.args.rootfs = '%s/fs/fs' % devdir
            self.args.workdir = '%s/images' % devdir
            self.args.image = '%s/images/test-sdcard.img' % devdir
            #self.args.imagesize_mb = 256 * 8
            self.args.imagesize_mb = 1024 * 8
            self.board = BoardFactory().make(test_board)
            self.board.sd_init_comp_installer(self.args)
        
        dryrun = False
        interactive = False
        
        # SDCard Installer
        self._inst = SDCardInstaller(board=self.board)
        self._inst.enable_colors = False
        self._inst.dryrun = dryrun
        self._inst.interactive = interactive
        self._inst.device = test_device
        
        # LoopDevice Installer
        self._ld_inst = LoopDeviceInstaller(board=self.board)
        self._ld_inst.enable_colors = False
        self._ld_inst.dryrun = dryrun
        self._ld_inst.interactive = interactive
        self._ld_inst.device = test_device
        
    def tearDown(self):
        pass
        
    def test_install_sd(self, dryrun=False):
        test_sd = True
        if test_sd:
            self._inst.read_partitions(self.args.mmap_file)
            self._inst.format()
            self._inst.mount_partitions(self.args.workdir)
            self._inst.install_components()
            self._inst.release()

    def test_install_loopback(self, dryrun=False):
        test_ld = False
        if test_ld:
            self._ld_inst.read_partitions(self.args.mmap_file)
            self._ld_inst.format(self.args.image, self.args.imagesize_mb)
            self._ld_inst.mount_partitions(self.args.workdir)
            self._ld_inst.install_components()
            self._ld_inst.release()
        #ret = self._inst.format_loopdevice(image, image_size_mb=1)
        #self.assertFalse(ret) # Fail with small image size

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(SDCardInstallerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
