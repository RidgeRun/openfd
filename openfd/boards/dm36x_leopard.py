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
# Definitions for the DM36x LeopardBoard.
#
# ==========================================================================

from board import Board

BOARD_NAME = 'dm36x-leopard'

class Dm36xLeopard(Board):
    
    COMPONENTS = ['ipl', 'bootloader', 'kernel', 'filesystem']
    
    mach_description = "Leopard Board DM36x"
    nand_block_size = 131072
    nand_page_size = 2048

    def _check_comp(self, comp):
        if comp not in self.COMPONENTS:
            raise AttributeError('Unknown component: %s' % comp)

    def comp_name(self, comp):
        self._check_comp(comp)
        if comp is 'ipl': return 'ubl'
        elif comp is 'bootloader': return 'uboot'
        elif comp is 'kernel': return 'kernel'
        elif comp is 'filesystem': return 'rootfs'

    def erase_cmd(self, comp):
        self._check_comp(comp)
        return 'nand erase'
    
    def pre_write_cmd(self, comp):
        self._check_comp(comp)
        return ''
    
    def write_cmd(self, comp):
        self._check_comp(comp)
        if comp is 'ipl' or comp is 'bootloader':
            return 'nand write.ubl'
        else:
            return 'nand write'
    
    def post_write_cmd(self, comp):
        self._check_comp(comp)
        return ''
