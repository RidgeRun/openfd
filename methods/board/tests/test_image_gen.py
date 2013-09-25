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

sys.path.insert(1, os.path.abspath('..'))

import rrutils
from image_gen import NandImageGenerator

class NandImageGeneratorTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        rrutils.logger.basic_config(verbose=True)
        logger = rrutils.logger.get_global_logger('SerialInstaller')
        logger.setLevel(rrutils.logger.DEBUG)
    
    def setUp(self):
        self._gen = NandImageGenerator()
        
    def tearDown(self):
        pass
        
if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(NandImageGeneratorTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
