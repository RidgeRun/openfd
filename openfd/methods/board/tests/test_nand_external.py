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
# Tests for the nand module.
#
# ==========================================================================

import os, sys
import logging
import unittest
import check_env
from openfd.boards import dm36x_leopard

sys.path.insert(1, os.path.abspath('..'))

import openfd.utils as utils
from openfd.methods.board.nand_external import ExternalInstaller
from openfd.boards.board_factory import BoardFactory

# DEVDIR environment variable
devdir = check_env.get_devdir()
if not devdir: sys.exit(-1)

test_mmap_file = '%s/images/nand-mmap.config' % devdir

class ExternalInstallerTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        verbose = True
        logger = utils.logger.init_global_logger('NandInstaller')
        logger.setLevel(logging.DEBUG)
        streamhandler = logging.StreamHandler()
        streamhandler.setFormatter(logging.Formatter('%(msg)s'))
        if verbose:
            streamhandler.setLevel(logging.DEBUG)
        else:
            streamhandler.setLevel(logging.INFO)
        logger.addHandler(streamhandler)
        
    def setUp(self):
        board = BoardFactory().make(dm36x_leopard.BOARD_NAME)
        self.inst = ExternalInstaller(board=board)
        self.inst.read_partitions(test_mmap_file)
        
    def tearDown(self):
        pass
        
    def test_write(self):
        print 'test_write'
        in_file = 'external.txt.in'
        out_file = 'external.txt.out'
        self.inst._general_substitutions()
        self.inst.write(in_file, out_file)
        self.inst.read_partitions(test_mmap_file)

    def test_install_ipl(self):
        self.inst.install_ipl()
        in_file = 'external.txt.in'
        out_file = 'external_ipl.txt.out'
        self.inst.write(in_file, out_file)
        


if __name__ == '__main__':
    loader = unittest.TestLoader() 
    suite = loader.loadTestsFromTestCase(ExternalInstallerTestCase)
    unittest.TextTestRunner(verbosity=1).run(suite)
