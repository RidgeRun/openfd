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
from imx6_args import Imx6ArgsParser
from imx6_sd_comp import Imx6SdCompInstaller
from openfd.methods.board import TftpRamLoader

BOARD_NAME = 'imx6'

# Supported modes
MODE_SD = 'sd'
MODE_SD_IMG = 'sd-img'
MODE_SD_SCRIPT = 'sd-script'
MODE_SD_SCRIPT_IMG = 'sd-script-img'
MODE_NAND = 'nand'
MODE_RAM = 'ram'
MODE_ENV = 'env'

# Supported modes uboot communication
MODE_UBOOT = 'uboot_comm'

# Supported components
COMP_IPL = 'ipl'
COMP_DTB = 'dtb'
COMP_BOOTLOADER = 'bootloader'
COMP_KERNEL = 'kernel'
COMP_FS = 'fs'

class Imx6(Board):
    
    MODES = [MODE_SD, MODE_SD_IMG, MODE_SD_SCRIPT, MODE_SD_SCRIPT_IMG,
             MODE_NAND, MODE_RAM, MODE_ENV]
    COMPONENTS = [COMP_IPL, COMP_BOOTLOADER, COMP_DTB, COMP_KERNEL, COMP_FS]
    
    mach_description = "IMX6 Board"
    nand_block_size = 131072
    nand_page_size = 2048
    mkimage_arch = 'arm'

    def __init__(self, dryrun=False):
        """
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        self._parser = Imx6ArgsParser()
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
        elif comp is COMP_DTB: return 'dtb'
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
	subparsers = parser.add_subparsers(help="installation mode (help available)", dest="mode")

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
        parser_nand_dtb = subparsers_nand.add_parser(COMP_DTB, help="DTB")
        parser_nand_kernel = subparsers_nand.add_parser(COMP_KERNEL, help="Kernel")
        parser_nand_fs = subparsers_nand.add_parser(COMP_FS, help="Filesystem")
        
        self._parser.add_args_sd(parser_sd)
        self._parser.add_args_sd_img(parser_sd_img)
        self._parser.add_args_sd_script(parser_sd_script)
        self._parser.add_args_sd_script_img(parser_sd_script_img)
        self._parser.add_args_nand(parser_nand)
        self._parser.add_args_nand_ipl(parser_nand_ipl)
        self._parser.add_args_nand_bootloader(parser_nand_bootloader)
        self._parser.add_args_nand_kernel(parser_nand_dtb)
        self._parser.add_args_nand_kernel(parser_nand_kernel)
        self._parser.add_args_nand_fs(parser_nand_fs)
        self._parser.add_args_ram(parser_ram)
        self._parser.add_args_env(parser_env)

    def check_args(self, args):
        if args.mode == MODE_SD:
            self._parser.check_args_sd(args)
        elif args.mode == MODE_SD_IMG:
            self._parser.check_args_sd_img(args)
        elif args.mode == MODE_SD_SCRIPT:
            self._parser.check_args_sd_script(args)
        elif args.mode == MODE_SD_SCRIPT_IMG:
            self._parser.check_args_sd_script_img(args)
        elif args.mode == MODE_NAND:
            self._parser.check_args_nand(args)
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
        self._comp_installer = Imx6SdCompInstaller()
        self._comp_installer.dryrun = self._dryrun
        self._comp_installer.uboot_file = args.uboot_file
	self._comp_installer.uboot_spl = args.uboot_spl
	self._comp_installer.uboot_bs = args.uboot_bs
	self._comp_installer.uboot_seek = args.uboot_seek
        self._comp_installer.uboot_load_addr = args.uboot_load_addr
        self._comp_installer.bootargs = args.uboot_bootargs
        self._comp_installer.bootscript = args.uboot_bootscript
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
