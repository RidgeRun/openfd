#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2016 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Diego Chaverri Masis <diego.chaverri@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Definitions for the Xilinx ZCU102 Board.
#
# ==========================================================================

from board import Board
from ultrascale_zcu102_args import Ultrascale_Zcu102ArgsParser
from ultrascale_zcu102_sd_comp import Ultrascale_Zcu102SdCompInstaller
from openfd.methods.board import TftpRamLoader

BOARD_NAME = 'ultrascale_zcu102'

# Supported modes
MODE_SD = 'sd'
MODE_SD_IMG = 'sd-img'
MODE_RAM = 'ram'
MODE_ENV = 'env'

# Supported modes uboot communication
MODE_UBOOT = 'uboot_comm'

# Supported components
COMP_IPL = 'ipl'
COMP_BOOTLOADER = 'bootloader'
COMP_KERNEL = 'kernel'
COMP_FS = 'fs'

class Ultrascale_Zcu102(Board):
    
    MODES = [MODE_SD, MODE_SD_IMG, MODE_RAM, MODE_ENV]
    COMPONENTS = [COMP_IPL, COMP_BOOTLOADER, COMP_KERNEL, COMP_FS]
    
    mach_description = "Ultrascale ZCU102 Board"
    mkimage_arch = 'arm'

    def __init__(self, dryrun=False):
        """
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        self._parser = Ultrascale_Zcu102ArgsParser()
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
        if comp is COMP_IPL: return 'ubl'
        elif comp is COMP_BOOTLOADER: return 'uboot'
        elif comp is COMP_KERNEL: return 'kernel'
        elif comp is COMP_FS: return 'rootfs'

    def add_args(self, parser):
	subparsers = parser.add_subparsers(help="installation mode (help available)", dest="mode")

        parser_sd = subparsers.add_parser(MODE_SD)
        parser_sd_img = subparsers.add_parser(MODE_SD_IMG)
        parser_ram = subparsers.add_parser(MODE_RAM)
        parser_env = subparsers.add_parser(MODE_ENV)

        self._parser.add_args_sd(parser_sd)
        self._parser.add_args_sd_img(parser_sd_img)
        self._parser.add_args_ram(parser_ram)
        self._parser.add_args_env(parser_env)

    def check_args(self, args):
        if args.mode == MODE_SD:
            self._parser.check_args_sd(args)
        elif args.mode == MODE_SD_IMG:
            self._parser.check_args_sd_img(args)
        elif args.mode == MODE_RAM:
            self._parser.check_args_ram(args)
        elif args.mode == MODE_ENV:
            self._parser.check_args_env(args)

    def _get_tftp_loader(self, args):
        tftp_loader = TftpRamLoader(None, args.board_net_mode)
        tftp_loader.dir = args.tftp_dir
        tftp_loader.port = args.tftp_port
        tftp_loader.host_ipaddr = args.host_ip_addr
        tftp_loader.net_mode = args.board_net_mode
        if args.board_net_mode == TftpRamLoader.MODE_STATIC:
            tftp_loader.board_ipaddr = args.board_ip_addr
            tftp_loader.dryrun = args.dryrun
        return tftp_loader

    def sd_init_comp_installer(self, args):
        self._comp_installer = Ultrascale_Zcu102SdCompInstaller()
        self._comp_installer.dryrun = self._dryrun
        self._comp_installer.uboot_file = args.uboot_file
        self._comp_installer.uboot_load_addr = args.uboot_load_addr
        self._comp_installer.bootargs = args.uboot_bootargs
        if hasattr(args, 'kernel_file'): # sd-script mode doesn't need this
            self._comp_installer.kernel_image = args.kernel_file
	if hasattr(args, 'kernel_file_type'):
	    self._comp_installer.kernel_file_type = args.kernel_file_type
        if hasattr(args, 'kernel_devicetree'):
            self._comp_installer.kernel_devicetree = args.kernel_devicetree
        if hasattr(args, 'kernel_tftp'):
            self._comp_installer.kernel_tftp = args.kernel_tftp
        if hasattr(args, 'rootfs'): # sd-script mode doesn't need this
            self._comp_installer.rootfs = args.rootfs
        self._comp_installer.workdir = args.workdir
        if args.kernel_tftp:
            self._comp_installer.tftp_loader = self._get_tftp_loader(args)
            self._comp_installer.tftp_loader.check_tftp_settings()


    def sd_install_components(self, sd):
        self._comp_installer.install_sd_components(sd)

    def ld_install_components(self, ld):
        self._comp_installer.install_ld_components(ld)
        
    def sd_install_components_external(self, sd):
        self._comp_installer.install_sd_components_external(sd)

    def ld_install_components_external(self, ld):
        self._comp_installer.install_ld_components_external(ld)
