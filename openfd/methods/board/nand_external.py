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
# Support to generate an external installer for SD.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
from string import Template
from openfd.storage.partition import read_nand_partitions  

# ==========================================================================
# Public Classes
# ==========================================================================

class ExternalInstaller(object):
    """
    Install components to NAND memory.
    """

    def __init__(self, board):
        self._subs = {}
        self._board = board
        self._partitions = []
    
    def _general_substitutions(self):
        self._subs['mach_desc'] = self._board.mach_description
    
    def write(self, in_file, out_file):
        with open(in_file, 'r') as in_f:
            t = Template(in_f.read())
            with open(out_file, 'w') as out_f: 
                out_f.write(t.safe_substitute(self._subs))
                
    def _bytes_to_blks(self, size_b):
        size_blks = (size_b / self._board.nand_block_size)
        if (size_b % self._board.nand_block_size != 0):
            size_blks += 1
        return size_blks
                
    def _install_img(self, filename, comp, start_blk, size_blks=0):
        offset = start_blk * self._board.nand_block_size
        img_size_blks = self._bytes_to_blks(os.path.getsize(filename))
        img_size_aligned = img_size_blks * self._board.nand_block_size
        part_size = img_size_aligned
        if size_blks:
            if img_size_blks > size_blks:
                self._l.warning("Using %s NAND blocks instead of %s for the "
                            "%s partition" % (img_size_blks, size_blks, comp))
            else:
                part_size = size_blks * self._board.nand_block_size
        self._subs['%s_erase_cmd' % comp] = self._board.ipl_erase_cmd
        self._subs['%s_erase_offset' % comp] = hex(offset)
        self._subs['%s_erase_size' % comp] = hex(part_size)
        self._subs['%s_pre_write_cmd' % comp] = self._board.ipl_pre_write_cmd
        self._subs['%s_write_cmd' % comp] = self._board.ipl_write_cmd
        self._subs['%s_write_offset' % comp] = hex(offset)
        self._subs['%s_write_size' % comp] = hex(img_size_aligned)
        self._subs['%s_post_write_cmd' % comp] = self._board.ipl_post_write_cmd
    
    def install_ipl(self):
        self._subs['ipl_image'] = self._board.mach_description
        for part in self._partitions:
            if part.name == self._board.ipl_name:
                self._subs['ipl_image'] = os.path.basename(part.image)
                self._install_img(part.image, 'ipl', part.start_blk,
                                  part.size_blks)

    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        :returns: Returns true on success; false otherwise.  
        """
        
        self._partitions[:] = []
        self._partitions = read_nand_partitions(filename)
