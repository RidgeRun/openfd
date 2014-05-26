#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Tests for the sdcard_external module.
#
# ==========================================================================

import os, sys
import logging
import argparse
import unittest
import check_env

sys.path.insert(1, os.path.abspath('..'))

import openfd.utils as utils
from openfd.methods.sdcard import SDCardExternalInstaller
from openfd.methods.sdcard import LoopDeviceExternalInstaller 
from openfd.boards import BoardFactory
from openfd.storage import DeviceException

# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

# IMPORTANT: Main test device (be careful!)
test_device = '/dev/sdb'

#test_board = 'dm36x-leopard'
test_board = 'dm816x'

class SDCardExternalInstallerTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        verbose = True
        dryrun = False
        logger = utils.logger.init_global_logger('SDCardExternalInstaller')
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

        if test_board == 'dm816x':
            uboot = 'u-boot-2010.06'
            self.args = argparse.Namespace()
            self.args.mmap_file = '%s/images/sd-script-mmap.config' % devdir
            self.args.mkimage_bin = ('%s/bootloader/%s/src/tools/mkimage' %
                                        (devdir, uboot))
            self.args.output_file = 'dm816x.external.txt'
            self.imgs = ['%s/images/u-boot.noxip.bin' % devdir,
                         '%s/images/fsimage.uImage' % devdir,
                         '%s/images/kernel.uImage' % devdir,
                         '%s/images/kernel.uImage' % devdir]
            self.args.uboot_min_file = '%s/images/u-boot.min.sd' % devdir
            self.args.uboot_file = '%s/images/bootloader' % devdir
            self.args.uboot_load_addr = '0x82000000'
            self.args.workdir = '%s/images/openfd' % devdir
            self.args.image = '%s/images/test-sdcard-external.img' % devdir
            self.args.imagesize_mb = 256
            self.board = BoardFactory().make(test_board)
            self.board.sd_init_comp_installer(self.args)
            
        dryrun = False
        interactive = False
        
        self._test_sd = False
        self._test_ld = True
        
        # SDCard Installer
        if self._test_sd:
            self._inst = SDCardExternalInstaller(board=self.board)
            self._inst.enable_colors = False
            self._inst.dryrun = dryrun
            self._inst.interactive = interactive
            self._inst.device = test_device
        
        # LoopDevice Installer
        if self._test_ld:
            self._ld_inst = LoopDeviceExternalInstaller(board=self.board)
            self._ld_inst.enable_colors = False
            self._ld_inst.dryrun = dryrun
            self._ld_inst.interactive = interactive
            self._ld_inst.device = test_device
            
    def tearDown(self):
        pass
        
    def test_install_sd(self, dryrun=False):
        if self._test_sd:
            self._inst.read_partitions(self.args.mmap_file)
            self._inst.format()
            self._inst.mount_partitions(self.args.workdir)
            self._inst.install_components(self.args.workdir, self.imgs,
                                self.args.mkimage_bin, self.args.output_file)
            self._inst.release()

    def test_install_loopback(self, dryrun=False):
        if self._test_ld:
            self._ld_inst.read_partitions(self.args.mmap_file)
            self.assertRaises(DeviceException, self._ld_inst.format,
                              self.args.image, 1)
            self._ld_inst.format(self.args.image, self.args.imagesize_mb)
            self._ld_inst.mount_partitions(self.args.workdir)
            self._ld_inst.install_components(self.args.workdir, self.imgs,
                                self.args.mkimage_bin, self.args.output_file)
            self._ld_inst.release()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(SDCardExternalInstallerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
