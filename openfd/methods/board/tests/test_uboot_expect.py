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
# Tests for the uboot_expect module.
#
# ==========================================================================

import os, sys
import unittest
import logging

sys.path.insert(1, os.path.abspath('..'))

import openfd.utils as utils
from uboot_expect import UbootExpect

test_telnet_host = '10.251.101.24'
test_telnet_port = '3001'

class UbootExpectTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        verbose = True
        dryrun = False
        logger = utils.logger.init_global_logger('UbootExpect')
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
        self.uboot = UbootExpect()
        self.uboot.dryrun = dryrun
        cmd = 'telnet %s %s' % (test_telnet_host, test_telnet_port)
        ret = self.uboot.open_comm(cmd)
        self.assertTrue(ret)
    
    def tearDown(self):
        self.uboot.close_comm()

    def test_comm(self):
        pass

if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(UbootExpectTestCase)
    unittest.TextTestRunner(verbosity=1).run(suite)
