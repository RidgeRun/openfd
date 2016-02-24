#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2016 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Daniel Garbanzo Hidalgo <daniel.garbanzo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Definitions for the AM4728 EVM.
#
# ==========================================================================

from board import Board
from am5728_args import AM5728ArgsParser
from am5728_sd_comp import AM5728SdCompInstaller

BOARD_NAME = 'am5728'

# Supported modes
MODE_SD = 'sd'
MODE_SD_IMG = 'sd-img'

# Supported components
COMP_IPL = 'ipl'
COMP_BOOTLOADER = 'bootloader'
COMP_KERNEL = 'kernel'
COMP_FS = 'fs'

class AM5728(Board):
    
    MODES = [MODE_SD, MODE_SD_IMG]
    COMPONENTS = [COMP_BOOTLOADER, COMP_KERNEL, COMP_FS]
    
    mach_description = "AM5728 EVM"
    mkimage_arch = 'arm'

    def __init__(self, dryrun=False):
        """
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        self._parser = AM5728ArgsParser()
        self._comp_installer = None
        self._dryrun = dryrun 
    
    @property
    def parser(self):
        """CLI args parser."""
        return self._parser

    @property
    def sd_comp_installer(self):
        """Component installer for sdcard method."""
        return self._comp_installer

    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        if self._comp_installer:
            self._comp_installer.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                      doc="""Enable dryrun mode. Systems commands will be
                     logged, but not executed.""")

    def _check_comp(self, comp):
        if comp not in self.COMPONENTS:
            raise AttributeError('Unknown component: %s' % comp)

    def comp_name(self, comp):
        self._check_comp(comp)
        if comp is COMP_IPL: return 'uboot-MLO'
        elif comp is COMP_BOOTLOADER: return 'uboot'
        elif comp is COMP_KERNEL: return 'kernel'
        elif comp is COMP_FS: return 'rootfs'


    def add_args(self, parser):
        subparsers = parser.add_subparsers(help="installation mode (--help available)", dest="mode")

        parser_sd = subparsers.add_parser(MODE_SD)
        parser_sd_img = subparsers.add_parser(MODE_SD_IMG)

        self._parser.add_args_sd(parser_sd)
        self._parser.add_args_sd_img(parser_sd_img)

    def check_args(self, args):
        if args.mode == MODE_SD:
            self._parser.check_args_sd(args)
        elif args.mode == MODE_SD_IMG:
            self._parser.check_args_sd_img(args)

    def sd_init_comp_installer(self, args):
        self._comp_installer = AM5728SdCompInstaller()
        self._comp_installer.dryrun = self._dryrun
        self._comp_installer.uboot_MLO_file = args.uboot_MLO_file
        self._comp_installer.uboot_file = args.uboot_file
        if hasattr(args, 'uboot_bootargs'): # sd-script mode doesn't need this
            self._comp_installer.bootargs = args.uboot_bootargs
        if hasattr(args, 'kernel_file'): # sd-script mode doesn't need this
            self._comp_installer.kernel_image = args.kernel_file
        if hasattr(args, 'kernel_file_type'):
			self._comp_installer.kernel_file_type = args.kernel_file_type
        if hasattr(args, 'kernel_devicetree'):
            self._comp_installer.kernel_devicetree = args.kernel_devicetree
        if hasattr(args, 'rootfs'): # sd-script mode doesn't need this
            self._comp_installer.rootfs = args.rootfs
        self._comp_installer.workdir = args.workdir

    def sd_install_components(self, sd):
        self._comp_installer.install_sd_components(sd)

    def ld_install_components(self, ld):
        self._comp_installer.install_ld_components(ld)
    
    def sd_install_components_external(self, sd):
        self._comp_installer.install_sd_components_external(sd)

    def ld_install_components_external(self, ld):
        self._comp_installer.install_ld_components_external(ld)
    
