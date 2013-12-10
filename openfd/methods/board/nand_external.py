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
import openfd.utils as utils
from string import Template
from openfd.storage.partition import read_nand_partitions  

# ==========================================================================
# Public Classes
# ==========================================================================

class ExternalInstaller(object):
    """
    Install components to NAND memory.
    """

    def __init__(self, board, dryrun=False):
        self._subs = {}
        self._board = board
        self._partitions = []
        self._e = utils.executer.get_global_executer()
        self._e.dryrun = dryrun
        self._dryrun = dryrun
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System commands will be logged,
                     but not executed.""")
    
    def _general_substitutions(self):
        self._subs['mach_desc'] = self._board.mach_description
    
    def write(self, in_file, out_file):
        self._general_substitutions()
        with open(in_file, 'r') as in_f:
            t = Template(in_f.read())
            with open(out_file, 'w') as out_f: 
                out_f.write(t.safe_substitute(self._subs))
                
    def _bytes_to_blks(self, size_b):
        size_blks = (size_b / self._board.nand_block_size)
        if (size_b % self._board.nand_block_size != 0):
            size_blks += 1
        return size_blks
    
    def _md5sum(self, filename):
        cmd = "md5sum %s | cut -f1 -d' '" % filename
        ret, md5sum = self._e.check_output(cmd)
        return md5sum.strip() if ret == 0 else ''
    
    def _install_img(self, filename, comp, comp_name, comp_nick, cmds, start_blk,
                     size_blks=0):
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
        self._subs['%s_name' % comp] = comp_name
        self._subs['%s_image' % comp] = os.path.basename(filename)
        self._subs['%s_erase_cmd' % comp] = cmds['erase']
        self._subs['%s_erase_offset' % comp] = hex(offset)
        self._subs['%s_erase_size' % comp] = hex(part_size)
        self._subs['%s_pre_write_cmd' % comp] = cmds['pre_write']
        self._subs['%s_write_cmd' % comp] = cmds['write']
        self._subs['%s_write_offset' % comp] = hex(offset)
        self._subs['%s_write_size' % comp] = hex(img_size_aligned)
        self._subs['%s_post_write_cmd' % comp] = cmds['post_write']
        self._subs['%smd5sum' % comp_nick] = self._md5sum(filename)
        self._subs['%soffset' % comp_nick] = hex(offset)
        self._subs['%ssize' % comp_nick] = hex(img_size_aligned)
        self._subs['%spartitionsize' % comp_nick] = hex(part_size)
    
    def install_ipl(self):
        for part in self._partitions:
            if part.name == self._board.ipl_name:
                cmds = {
                    'erase': self._board.ipl_erase_cmd,
                    'pre_write': self._board.ipl_pre_write_cmd,
                    'write': self._board.ipl_write_cmd,
                    'post_write': self._board.ipl_post_write_cmd
                }
                name = self._board.ipl_name 
                self._install_img(part.image, 'ipl', name, 'ipl', cmds,
                                  part.start_blk, part.size_blks)

    def install_bootloader(self):
        for part in self._partitions:
            if part.name == self._board.bootloader_name:
                cmds = {
                    'erase': self._board.bootloader_erase_cmd,
                    'pre_write': self._board.bootloader_pre_write_cmd,
                    'write': self._board.bootloader_write_cmd,
                    'post_write': self._board.bootloader_post_write_cmd
                }
                name = self._board.bootloader_name
                self._install_img(part.image, 'bootloader', name, name, cmds,
                                  part.start_blk, part.size_blks)
                
    def install_kernel(self):
        for part in self._partitions:
            if part.name == self._board.kernel_name:
                cmds = {
                    'erase': self._board.kernel_erase_cmd,
                    'pre_write': self._board.kernel_pre_write_cmd,
                    'write': self._board.kernel_write_cmd,
                    'post_write': self._board.kernel_post_write_cmd
                }
                name = self._board.kernel_name
                self._install_img(part.image, 'kernel', name, 'k', cmds,
                                  part.start_blk, part.size_blks)
    def install_fs(self):
        for part in self._partitions:
            if part.name == self._board.fs_name:
                cmds = {
                    'erase': self._board.fs_erase_cmd,
                    'pre_write': self._board.fs_pre_write_cmd,
                    'write': self._board.fs_write_cmd,
                    'post_write': self._board.fs_post_write_cmd
                }
                name = self._board.fs_name
                self._install_img(part.image, 'fs', name, 'fs', cmds,
                                  part.start_blk, part.size_blks)

    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        :returns: Returns true on success; false otherwise.  
        """
        
        self._partitions[:] = []
        self._partitions = read_nand_partitions(filename)
