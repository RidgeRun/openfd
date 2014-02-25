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
from dm36x_leopard_args import Dm36xLeopardArgsParser

BOARD_NAME = 'dm36x-leopard'

# Supported modes
MODE_SD = 'sd'
MODE_SD_IMG = 'sd-img'
MODE_SD_SCRIPT = 'sd-script'
MODE_SD_SCRIPT_IMG = 'sd-script-img'
MODE_NAND = 'nand'
MODE_RAM = 'ram'
MODE_ENV = 'env'

# Supported components
COMP_IPL = 'ipl'
COMP_BOOTLOADER = 'bootloader'
COMP_KERNEL = 'kernel'
COMP_FS = 'fs'

class Dm36xLeopard(Board):
    
    MODES = [MODE_SD, MODE_SD_IMG, MODE_SD_SCRIPT, MODE_SD_SCRIPT_IMG,
             MODE_NAND, MODE_RAM, MODE_ENV]
    COMPONENTS = [COMP_IPL, COMP_BOOTLOADER, COMP_KERNEL, COMP_FS]
    
    mach_description = "Leopard Board DM36x"
    nand_block_size = 131072
    nand_page_size = 2048

    def __init__(self):
        self._parser = Dm36xLeopardArgsParser()
        
    @property
    def parser(self):
        """CLI args parser."""
        return self._parser

    def _check_comp(self, comp):
        if comp not in self.COMPONENTS:
            raise AttributeError('Unknown component: %s' % comp)

    def comp_name(self, comp):
        self._check_comp(comp)
        if comp is COMP_IPL: return 'ubl'
        elif comp is COMP_BOOTLOADER: return 'uboot'
        elif comp is COMP_KERNEL: return 'kernel'
        elif comp is COMP_FS: return 'rootfs'

    def erase_cmd(self, comp):
        self._check_comp(comp)
        return 'nand erase'
    
    def pre_write_cmd(self, comp):
        self._check_comp(comp)
        return ''
    
    def write_cmd(self, comp):
        self._check_comp(comp)
        if comp is COMP_IPL or comp is COMP_BOOTLOADER:
            return 'nand write.ubl'
        else:
            return 'nand write'
    
    
    def post_write_cmd(self, comp):
        self._check_comp(comp)
        return ''

    def add_args(self, parser):
        subparsers = parser.add_subparsers(help="installation mode (--help available)", dest="mode")

        parser_sd = subparsers.add_parser(MODE_SD)
        parser_sd_img = subparsers.add_parser(MODE_SD_IMG)
        parser_sd_script = subparsers.add_parser(MODE_SD_SCRIPT)
        parser_sd_script_img = subparsers.add_parser(MODE_SD_SCRIPT_IMG)
        parser_ram = subparsers.add_parser(MODE_RAM)
        parser_env = subparsers.add_parser(MODE_ENV)
        parser_nand = subparsers.add_parser(MODE_NAND)
        
        subparsers_nand = parser_nand.add_subparsers(help="component (--help available)", dest="component")
        parser_nand_ipl = subparsers_nand.add_parser(COMP_IPL, help="Initial Program Loader (UBL)")
        parser_nand_bootloader = subparsers_nand.add_parser(COMP_BOOTLOADER, help="Bootloader (U-Boot)")
        parser_nand_kernel = subparsers_nand.add_parser(COMP_KERNEL, help="Kernel")
        parser_nand_fs = subparsers_nand.add_parser(COMP_FS, help="Filesystem")
        
        self._parser.add_args_sd(parser_sd)
        self._parser.add_args_sd_img(parser_sd_img)
        self._parser.add_args_sd_script(parser_sd_script)
        self._parser.add_args_sd_script_img(parser_sd_script_img)
        self._parser.add_args_nand(parser_nand)
        self._parser.add_args_nand_ipl(parser_nand_ipl)
        self._parser.add_args_nand_bootloader(parser_nand_bootloader)
        self._parser.add_args_nand_kernel(parser_nand_kernel)
        self._parser.add_args_nand_fs(parser_nand_fs)
        self._parser.add_args_ram(parser_ram)
        self._parser.add_args_env(parser_env)
