#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
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
    ipl_name = "ubl"
    ipl_erase_cmd = "nand erase"
    ipl_pre_write_cmd = ""
    ipl_write_cmd = "nand write.ubl"
    ipl_post_write_cmd = ""
    bootloader_name = "uboot"
    bootloader_erase_cmd = "nand erase"
    bootloader_pre_write_cmd = ""
    bootloader_write_cmd = "nand write.ubl"
    bootloader_post_write_cmd = ""
    kernel_name = "kernel"
    kernel_erase_cmd = "nand erase"
    kernel_pre_write_cmd = ""
    kernel_write_cmd = "nand write"
    kernel_post_write_cmd = ""
    fs_name = "rootfs"
    fs_erase_cmd = "nand erase"
    fs_pre_write_cmd = ""
    fs_write_cmd = "nand write"
    fs_post_write_cmd = ""

    def comp_name(self, comp):
        if comp not in self.COMPONENTS:
            raise AttributeError('Unknown component: %s' % comp)
        if comp is 'ipl': return 'ubl'
        elif comp is 'bootloader': return 'uboot'
        elif comp is 'kernel': return 'kernel'
        elif comp is 'filesystem': return 'rootfs'

    def erase_cmd(self, comp):
        if comp not in self.COMPONENTS:
            raise AttributeError('Unknown component: %s' % comp)
        return 'nand erase'
    
    def write_cmd(self, comp):
        if comp not in self.COMPONENTS:
            raise AttributeError('Unknown component: %s' % comp)
        if comp is 'ipl' or comp is 'bootloader':
            return 'nand write.ubl'
        else:
            return 'nand write'
