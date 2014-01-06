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
# CLI arguments parsing support for openfd.methods.sdcard.
#
# ==========================================================================

from openfd.utils import ArgChecker
from openfd.boards import BoardFactory

class SdCardArgs(object):
    
    def __init__(self):
        self.checker = ArgChecker()
    
    # ==========================================================================
    # Mode sd args
    # ==========================================================================
    
    def add_args_sd(self, parser):
        
        parser.add_argument('--device',
                           help="Device to install",
                           metavar='<dev>',
                           dest='device',
                           required=True)
    
        parser.add_argument('--mmap-file',
                           help='Memory map config file',
                           metavar='<file>',
                           dest='mmap_file',
                           required=True)
    
        self.add_args_sd_bootloader(parser)
        self.add_args_sd_kernel(parser)
        
        parser.add_argument('--work-dir',
                           help='Directory to perform temporary operations',
                           metavar='<dir>',
                           dest='workdir',
                           required=True)
        
        self.add_args_sd_fs(parser)
        
    def check_args_sd(self, args):
        self.checker.is_file(args.mmap_file, '--mmap-file')
        self.check_args_sd_bootloader(args)
        self.check_args_sd_kernel(args)
        self.checker.is_dir(args.workdir, '--work-dir')
        args.workdir = args.workdir.rstrip('/')
        self.check_args_sd_fs(args) 
        
    def add_args_sd_kernel(self, parser):
        
        parser.add_argument('--kernel-file',
                           help='Path to the Kernel file to be installed.',
                           metavar='<file>',
                           dest='kernel_file',
                           required=True)
    
    def check_args_sd_kernel(self, args):
        self.checker.is_file(args.kernel_file, '--kernel-file')
    
    def add_args_sd_bootloader(self, parser):
        
        parser.add_argument('--uflash-bin',
                           help='Path to the uflash tool',
                           metavar='<file>',
                           dest='uflash_bin',
                           required=True)
        
        parser.add_argument('--ubl-file',
                           help='Path to the UBL file',
                           metavar='<file>',
                           dest='ubl_file',
                           required=True)
        
        parser.add_argument('--uboot-file',
                           help='Path to the U-Boot file',
                           metavar='<file>',
                           dest='uboot_file',
                           required=True)
        
        parser.add_argument('--uboot-entry-addr',
                           help='U-Boot entry address (decimal or hex)',
                           metavar='<addr>',
                           dest='uboot_entry_addr',
                           required=True)
        
        parser.add_argument('--uboot-load-addr',
                           help='U-Boot load address (decimal or hex)',
                           metavar='<addr>',
                           dest='uboot_load_addr',
                           required=True)
        
        parser.add_argument('--uboot-bootargs',
                           help="U-Boot bootargs environment variable",
                           metavar='<bootargs>',
                           dest='uboot_bootargs',
                           required=True)
        
    def check_args_sd_bootloader(self, args):
        self.checker.is_file(args.uflash_bin, '--uflash-bin')
        self.checker.x_ok(args.uflash_bin, '--uflash-bin')
        self.checker.is_file(args.ubl_file, '--ubl-file')
        self.checker.is_file(args.uboot_file, '--uboot-file')
        self.checker.is_valid_addr(args.uboot_entry_addr, '--uboot-entry-addr')
        self.checker.is_valid_addr(args.uboot_load_addr, '--uboot-load-addr')
        
    def add_args_sd_fs(self, parser):
        
        parser.add_argument('--rootfs',
                           help='Path to the rootfs that will be installed.',
                           metavar='<dir>',
                           dest='rootfs',
                           default=None)
        
    def check_args_sd_fs(self, args):
        if args.rootfs:
            self.checker.is_dir(args.rootfs, '--rootfs')
        
    # ==========================================================================
    # Mode sd-img args
    # ==========================================================================
    
    def add_args_sd_img(self, parser):
        
        parser.add_argument('--mmap-file',
                           help='Memory map config file',
                           metavar='<file>',
                           dest='mmap_file',
                           required=True)
    
        self.add_args_sd_kernel(parser)
        self.add_args_sd_bootloader(parser)
        
        parser.add_argument('--work-dir',
                           help='Directory to perform temporary operations',
                           metavar='<dir>',
                           dest='workdir',
                           required=True)
        
        self.add_args_sd_fs(parser)
    
        parser.add_argument('--image',
                           help="Filename of the SD card image to create",
                           metavar='<file>',
                           dest='image',
                           required=True)
        
        parser.add_argument('--image-size-mb',
                           help="Size in MB of the SD card image file to create",
                           metavar='<size>',
                           dest='imagesize_mb',
                           required=True)

    def check_args_sd_img(self, args):
        self.checker.is_file(args.mmap_file, '--mmap-file')
        self.check_args_sd_bootloader(args)
        self.check_args_sd_kernel(args)
        self.checker.is_dir(args.workdir, '--work-dir')
        args.workdir = args.workdir.rstrip('/')
        self.check_args_sd_fs(args)
        self.checker.is_int(args.imagesize_mb, '--image-size-mb')
        args.imagesize_mb = int(args.imagesize_mb)

    # ==========================================================================
    # Mode sd-script args
    # ==========================================================================

    def add_args_sd_script_board(self, parser):
        boards = BoardFactory().supported_boards()
        parser.add_argument('--board',
                           help="Board name. Supported: %s" % 
                           ''.join('%s, ' % b for b in boards).rstrip(', '),
                           metavar='<board>',
                           dest='board',
                           choices=boards,
                           required=True)

    def add_args_sd_script_files(self, parser):
        
        parser.add_argument('--sd-mmap-file',
                           help='SD card memory map config file',
                           metavar='<file>',
                           dest='sd_mmap_file',
                           required=True)
        
        parser.add_argument('--flash-mmap-file',
                           help='Flash memory map config file',
                           metavar='<file>',
                           dest='flash_mmap_file',
                           required=True)
        
        parser.add_argument('--template-file',
                           help='Template file for flash installer script',
                           metavar='<file>',
                           dest='template_file',
                           required=True)
        
        parser.add_argument('--output-file',
                           help='Output file generated from --template-file',
                           metavar='<file>',
                           dest='output_file',
                           required=True)

        parser.add_argument('--work-dir',
                           help='Directory to perform temporary operations',
                           metavar='<dir>',
                           dest='workdir',
                           required=True)
        
        parser.add_argument('--mkimage-bin',
                           help='Path to the mkimage tool',
                           metavar='<file>',
                           dest='mkimage_bin',
                           required=True)
        
    def check_args_sd_script_files(self, args):
        self.checker.is_file(args.flash_mmap_file, '--flash-mmap-file')
        self.checker.is_file(args.template_file, '--template-file')
        self.checker.is_file(args.sd_mmap_file, '--sd-mmap-file')
        self.checker.is_dir(args.workdir, '--work-dir')
        args.workdir = args.workdir.rstrip('/')
        self.checker.is_file(args.mkimage_bin, '--mkimage-bin')
        self.checker.x_ok(args.mkimage_bin, '--mkimage-bin')

    def add_args_sd_script(self, parser):
        self.add_args_sd_script_board(parser)
        self.add_args_sd_script_files(parser)
        parser.add_argument('--device',
                           help="Device to install",
                           metavar='<dev>',
                           dest='device',
                           required=True)
        self.add_args_sd_bootloader(parser)
    
    def check_args_sd_script(self, args):
        self.check_args_sd_script_files(args)      
        self.check_args_sd_bootloader(args)

    def add_args_sd_script_img(self, parser):
        self.add_args_sd_script_board(parser)
        self.add_args_sd_script_files(parser)
        self.add_args_sd_bootloader(parser)
        parser.add_argument('--image',
                           help="Filename of the SD card image to create",
                           metavar='<file>',
                           dest='image',
                           required=True)
        parser.add_argument('--image-size-mb',
                           help="Size in MB of the SD card image file to create",
                           metavar='<size>',
                           dest='imagesize_mb',
                           required=True)

    def check_args_sd_script_img(self, args):
        self.check_args_sd_script_files(args)      
        self.check_args_sd_bootloader(args)
        self.checker.is_int(args.imagesize_mb, '--image-size-mb')
        args.imagesize_mb = int(args.imagesize_mb)
