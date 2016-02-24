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
# CLI arguments parsing support.
#
# ==========================================================================

from openfd.utils import ArgChecker
from openfd.utils import ArgCheckerError

class Am5728ArgsParser(object):
    
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
                           dest='kernel_file')
        parser.add_argument('--kernel-file-type',
                           help='The type of kernel image.',
                           metavar='<type>',
                           dest='kernel_file_type',
                           required=True)
        parser.add_argument('--kernel-devicetree',
                           help='Path to the Kernel devicetree file.',
                           metavar='<file>',
                           dest='kernel_devicetree',
                           required=False)
    
    def check_args_sd_kernel(self, args):
        if args.kernel_file:
            self.checker.is_file(args.kernel_file, '--kernel-file')
    
    def add_args_sd_bootloader(self, parser):
        
        parser.add_argument('--uboot-MLO-file',
                           help='Path to the U-Boot MLO file',
                           metavar='<file>',
                           dest='uboot_MLO_file')
        
        parser.add_argument('--uboot-file',
                           help='Path to the U-Boot file',
                           metavar='<file>',
                           dest='uboot_file')
        
        parser.add_argument('--uboot-bootargs',
                           help="U-Boot bootargs environment variable",
                           metavar='<bootargs>',
                           dest='uboot_bootargs')
        
    def check_args_sd_bootloader(self, args):
        if args.uboot_mlo_file:
            self.checker.is_file(args.uboot_mlo_file, '--uboot-MLO-file')
        if args.uboot_file:
            self.checker.is_file(args.uboot_file, '--uboot-file')
        
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
    # General args
    # ==========================================================================
