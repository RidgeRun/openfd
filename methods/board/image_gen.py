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
# NAND images generator to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import rrutils
import rrutils.hexutils as hexutils

# ==========================================================================
# Public Classes
# ==========================================================================

class NandImageGenerator(object):
    """
    NAND images generator.
    
    Based on the TI Binary Creator (BC) tool for DM36x; the images produced by
    this utility are expected to be used within the uboot environment and
    to be flashed using the uboot NAND commands.
    """
    
    def __init__(self, bc_bin=None, image_dir=None, verbose=False,
                 dryrun=False):
        """
        :param bc_bin: Path to the TI DM36x Binary Creator (BC) tool.
        :param verbose: Enable verbose mode to display the BC tool output.
        :type verbose: boolean
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        self._bc_bin = bc_bin
        self._image_dir = image_dir
        self._l = rrutils.logger.get_global_logger()
        self._e = rrutils.executer.Executer()
        self._e.logger = self._l
        self._verbose = verbose
        self._dryrun = dryrun
        self._e.dryrun = dryrun

    def __set_bc_bin(self, bc_bin):
        if os.path.isfile(bc_bin) and os.access(bc_bin, os.X_OK):
            self._bc_bin = bc_bin
        
    def __get_bc_bin(self):
        return self._bc_bin
    
    bc_bin = property(__get_bc_bin, __set_bc_bin,
                      doc="""Path to the TI DM36x Binary Creator (BC) tool.""")
    
    def __set_verbose(self, verbose):
        self._verbose = verbose
    
    def __get_verbose(self):
        return self._verbose
    
    verbose = property(__get_verbose, __set_verbose,
                      doc="""Enable verbose mode to display the BC tool
                      output.""")
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                      doc="""Enable dryrun mode. Systems commands will be
                     logged, but not executed.""")
    
    def _check_args(self, input_img, output_img, entry_addr='', load_addr=''):
        """
        Helper to check the validity of the received arguments for image
        generation methods.
        """
    
        if not self._bc_bin:
            self._l.error("Please provide the path to the TI Binary Creator "
                          "tool.")
            return False
        
        if not os.path.isfile(input_img):
            self._l.error("File '%s' doesn't exist." % input_img)
            return False
        
        output_dir = os.path.dirname(output_img)
        if not os.access(output_dir, os.W_OK):
            self._l.error("Can't write to '%s'." % output_dir)
            return False
        
        if entry_addr and not hexutils.is_valid_addr(entry_addr):
            self._l.error("Invalid uboot entry address '%s'" % entry_addr)
            return False
        
        if load_addr and not hexutils.is_valid_addr(load_addr):
            self._l.error("Invalid uboot load address '%s'" % load_addr)
            return False
        
        return True
    
    def gen_uboot_img(self, page_size, start_block, entry_addr, load_addr,
                      input_img, output_img):
        """
        Generates an uboot binary image for NAND.
        
        :param page_size: NAND page size (bytes).
        :param start_block: Start block in NAND for the uboot image (decimal).
        :param entry_addr: Uboot entry address, in decimal or hexadecimal
            (`'0x'` prefix).
        :param load_addr: Uboot load address, in decimal or hexadecimal
            (`'0x'` prefix).
        :param input_img: Path to the uboot binary input image.
        :param output_img: Path where to place the generated NAND uboot
            binary image.
        :returns: Returns true on success; false otherwise.
        """
        
        ret = self._check_args(input_img, output_img, entry_addr, load_addr)
        if ret is False: return False
        
        entry_addr_hex = hexutils.to_hex(str(entry_addr))
        load_addr_hex = hexutils.to_hex(str(load_addr))
        
        self._l.info("Generating uboot image for NAND: %s" % output_img)
        
        cmd = ('mono %s -uboot -pageSize %s -blockNum %s -startAddr %s '
               '-loadAddr %s %s -o %s' % (self._bc_bin, page_size,
                  start_block, entry_addr_hex, load_addr_hex, input_img,
                  output_img))
        if self._verbose:
            ret = self._e.call(cmd)
        else:
            ret = self._e.check_call(cmd)
        if ret != 0:
            self._l.error('Failed generating uboot image for NAND')
            return False
        
        return True

    def gen_ubl_img(self, page_size, start_block, input_img, output_img):
        """
        Generates an UBL binary image for NAND.
        
        :param page_size: NAND page size (bytes).
        :param start_block: Start block in NAND for the UBL image (decimal).
        :param input_img: Path to the UBL binary input image.
        :param output_img: Path where to place the generated NAND UBL
            binary image.
        :returns: Returns true on success; false otherwise.
        """
        
        ret = self._check_args(input_img, output_img)
        if ret is False: return False
        
        self._l.info("Generating UBL image for NAND: %s" % output_img)
        
        cmd = ('mono %s -pageSize %s -blockNum %s %s -o %s' % (self._bc_bin,
                page_size, start_block, input_img, output_img))
        if self._verbose:
            ret = self._e.call(cmd)
        else:
            ret = self._e.check_call(cmd)
        if ret != 0:
            self._l.error('Failed generating UBL image for NAND')
            return False
        
        return True
