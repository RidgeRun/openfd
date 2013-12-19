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
# Tests for the device module.
#
# ==========================================================================

import os, sys
import logging
import unittest
import check_env

sys.path.insert(1, os.path.abspath('..'))

import openfd.utils as utils
from device import SDCard
from device import LoopDevice
from device import DeviceException

# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

test_device = '/dev/sdb' # CAREFUL!
test_mmap_file = '%s/images/sd-mmap.config' % devdir
test_work_dir = "%s/images/" % devdir
test_img = "%s/images/sdcard-test.img" % devdir
test_img_size_mb = 128

class DeviceTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        verbose = True
        dryrun = False
        logger = utils.logger.init_global_logger('Device')
        logger.setLevel(logging.DEBUG)
        streamhandler = logging.StreamHandler()
        streamhandler.setFormatter(logging.Formatter('%(msg)s'))
        if verbose:
            streamhandler.setLevel(logging.DEBUG)
        else:
            streamhandler.setLevel(logging.INFO)
        logger.addHandler(streamhandler)
        utils.executer.init_global_executer(dryrun=dryrun,
                                    enable_colors=False, verbose=verbose)
            
    def setUp(self):
        pass
  
    def tearDown(self):
        pass
    
    def testSDCard(self):
        test_sd = False
        if test_sd:
            print "---- Testing SDCard ----"
            self.sd = SDCard(device=test_device)
            self.sd.read_partitions(test_mmap_file)
            self.assertTrue(self.sd.exists)
            self.assertTrue(self.sd.size_cyl >= self.sd.min_cyl_size())
            self.sd.unmount()
            self.sd.create_partitions()
            self.sd.format_partitions()
            self.sd.mount(test_work_dir)
            self.sd.unmount()
            self.sd.check_filesystems()
    
    def testLoopDevice(self):
        test_ld = True
        if test_ld:
            self.ld = LoopDevice()
            self.ld.read_partitions(test_mmap_file)
            self.ld.check_img_size(test_img_size_mb)
            self.assertRaises(DeviceException, self.ld.check_img_size, 1)
            self.ld.attach_device(test_img, test_img_size_mb)
            self.ld.detach_device()

if __name__ == '__main__':
    unittest.main()