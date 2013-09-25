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
        self._gen.dryrun = False
        
    def tearDown(self):
        pass
        
if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(NandImageGeneratorTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
