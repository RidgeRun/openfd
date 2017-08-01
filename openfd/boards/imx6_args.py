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
# CLI arguments parsing support.
#
# ==========================================================================

from openfd.utils import ArgChecker
from openfd.utils import ArgCheckerError
from openfd.methods.board import TftpRamLoader

class Imx6ArgsParser(object):
    
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
        self.add_args_tftp(parser)

        parser.add_argument('--work-dir',
                           help='Directory to perform temporary operations',
                           metavar='<dir>',
                           dest='workdir',
                           required=True)
        
        self.add_args_sd_fs(parser)
        self.add_args_sd_min_fs(parser)
        
    def check_args_sd(self, args):
        self.checker.is_file(args.mmap_file, '--mmap-file')
        self.check_args_sd_bootloader(args)
        self.check_args_sd_kernel(args)
        self.checker.is_dir(args.workdir, '--work-dir')
        args.workdir = args.workdir.rstrip('/')
        self.check_args_sd_fs(args)
        self.check_args_sd_min_fs(args) 
        
    def add_args_sd_kernel(self, parser):
        parser.add_argument('--kernel-file',
                           help='Path to the Kernel file to be installed.',
                           metavar='<file>',
                           dest='kernel_file',
                           required=True)
	parser.add_argument('--kernel-file-type',
                           help='The type of kernel image.',
                           metavar='<type>',
                           dest='kernel_file_type',
                           default='uImage',
                           required=False)
        parser.add_argument('--kernel-devicetree',
                           help='Path to the Kernel devicetree file.',
                           metavar='<file>',
                           dest='kernel_devicetree',
                           required=False)
        parser.add_argument('--kernel-tftp',
                           help='Sets the kernel to be loaded to ram from a ' 
                                'tftp server every time the board starts.',
                           dest='kernel_tftp',
                           action='store_true',
                           default=False,
                           required=False)
    
    def check_args_sd_kernel(self, args):
        self.checker.is_file(args.kernel_file, '--kernel-file')
        if args.kernel_tftp:
            self.check_args_tftp(args)

    def add_args_sd_bootloader(self, parser):
        parser.add_argument('--uboot-file',
                           help='Path to the U-Boot file',
                           metavar='<file>',
                           dest='uboot_file',
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

        parser.add_argument('--uboot-bootscript',
                            help="U-Boot bootscript file",
                            metavar='<file>',
                            dest='uboot_bootscript',
                            required=False)

	parser.add_argument('--uboot-bs',
			    help="bs argument of the 'dd' command",
			    metavar='<value>',
			    dest='uboot_bs',
                default='512',
			    required=False)

	parser.add_argument('--uboot-seek',
			    help="seek argument of the 'dd' command",
			    metavar='<value>',
			    dest='uboot_seek',
                default='2',
			    required=False)

	parser.add_argument('--spl-file',
			    help="Path to the U-Boot SPL file",
			    metavar='<file>',
			    dest='uboot_spl',
			    required=False)

    def check_args_sd_bootloader(self, args):
        self.checker.is_file(args.uboot_file, '--uboot-file')
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
            
    def add_args_sd_min_fs(self, parser):
        parser.add_argument('--min-rootfs',
                           help='Path to the minimal rootfs that will be installed.',
                           metavar='<dir>',
                           dest='min_rootfs',
                           default=None)
        
    def check_args_sd_min_fs(self, args):
        if args.min_rootfs:
            self.checker.is_dir(args.min_rootfs, '--min-rootfs')
        
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
        self.add_args_tftp(parser)
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

    # ==========================================================================
    # General args
    # ==========================================================================

    def add_args_serial(self, parser):
        parser.add_argument('--serial-port',
                           help="Device name or port number for serial communica"
                           "tion with U-Boot (i.e. '/dev/ttyS0')",
                           metavar='<port>',
                           dest='serial_port')
        
        parser.add_argument('--serial-baud',
                           help="Baud rate (default: 115200)",
                           metavar='<baud>',
                           dest='serial_baud',
                           default=115200)
        
    def check_args_serial(self, args):
        self.checker.is_int(args.serial_baud, '--serial-baud')
    
    def add_args_termnet(self, parser):
        parser.add_argument('--termnet-host',
                           help="Device name for termnet communica"
                           "tion with U-Boot (i.e. '127.0.0.1')",
                           metavar='<addr>',
                           dest='termnet_host')

        
        parser.add_argument('--termnet-port',
                           help="Termnet port (default: 3000)",
                           metavar='<port>',
                           dest='termnet_port')

    def check_args_termnet(self, args):
        self.checker.is_dir(args.termnet_host, '--termnet-host')
        self.checker.is_int(args.termnet_port,'--termnet-port')

    def add_args_uboot_comm(self, parser):
        uboot_modes = ['serial', 'termnet']

        parser.add_argument('--uboot-comm-mode',
                           help="Uboot Communication Mode: %s (default: serial)" %
                           ''.join('%s|' % mode for mode in uboot_modes).rstrip('|'),
                           metavar='<mode>',
                           choices=uboot_modes,
                           dest='uboot_comm_mode',
                           default='serial')


    def add_args_tftp(self, parser):
        net_modes = [TftpRamLoader.MODE_STATIC, TftpRamLoader.MODE_DHCP]
        
        parser.add_argument('--board-net-mode',
                           help="Networking mode: %s (default: dhcp)" %
                           ''.join('%s|' % mode for mode in net_modes).rstrip('|'),
                           metavar='<mode>',
                           choices=net_modes,
                           dest='board_net_mode',
                           default=TftpRamLoader.MODE_DHCP)
    
        parser.add_argument('--board-ip-addr',
                           help="Board IPv4 address (only required in --board-net-"
                           "mode=static)",
                           metavar='<addr>',
                           dest='board_ip_addr')
        
        parser.add_argument('--host-ip-addr',
                           help="Host IPv4 address",
                           metavar='<addr>',
                           dest='host_ip_addr',
                           required=False)
    
        parser.add_argument('--tftp-dir',
                           help="TFTP server root directory",
                           metavar='<dir>',
                           dest='tftp_dir',
                           required=False)
    
        parser.add_argument('--tftp-port',
                           help="TFTP server port (default: 69)",
                           metavar='<port>',
                           dest='tftp_port',
                           default=69)
        
    def check_args_tftp(self, args):
        if args.tftp_dir is None:
            raise ArgCheckerError('error: No TFTP server root directory specified, '
                                  '--tftp-dir is required')
        if args.host_ip_addr is None:
            raise ArgCheckerError('error: No TFTP host IPv4 address specified, '
                                  '--host-ip-addr is required')

        self.checker.is_dir(args.tftp_dir, '--tftp-dir')
        self.checker.is_int(args.tftp_port, '--tftp-port')
        args.tftp_port = int(args.tftp_port)
        self.checker.is_valid_ipv4(args.host_ip_addr, '--host-ip-addr')
        if args.board_net_mode == TftpRamLoader.MODE_STATIC:
            self.checker.is_valid_ipv4(args.board_ip_addr, '--board-ip-addr')
    
    # ==========================================================================
    # NAND args
    # ==========================================================================
    
    def add_args_nand_dimensions(self, parser):
        parser.add_argument('--nand-blk-size',
                           help="NAND block size (bytes)",
                           metavar='<size>',
                           dest='nand_blk_size')
        
        parser.add_argument('--nand-page-size',
                           help="NAND page size (bytes)",
                           metavar='<size>',
                           dest='nand_page_size')
        
    def check_args_nand_dimensions(self, args):
        if args.nand_blk_size:
            self.checker.is_int(args.nand_blk_size, '--nand-blk-size')
            args.nand_blk_size = int(args.nand_blk_size)
        if args.nand_page_size:
            self.checker.is_int(args.nand_page_size, '--nand-page-size')
            args.nand_page_size = int(args.nand_page_size)
        
    def add_args_nand(self, parser):
        parser.add_argument('--mmap-file',
                           help='Memory map config file',
                           metavar='<file>',
                           dest='mmap_file',
                           required=True)
        
        self.add_args_nand_dimensions(parser)
	self.add_args_uboot_comm(parser)
        self.add_args_serial(parser)
	self.add_args_termnet(parser)
	
        
        parser.add_argument('--ram-load-addr',
                           help='RAM address to load components (decimal or hex)',
                           metavar='<addr>',
                           dest='ram_load_addr',
                           required=True)
        
        parser.add_argument('--uboot-file',
                           help='Path to a U-Boot file that can be loaded to RAM '
                           'and drive the installation',
                           metavar='<file>',
                           dest='nand_uboot_file')
      
        self.add_args_tftp(parser)
    
    def check_args_nand(self, args):
        self.check_args_nand_dimensions(args)
        self.checker.is_file(args.mmap_file, '--mmap-file')
        if args.nand_uboot_file:
            self.checker.is_file(args.nand_uboot_file, '--uboot-file')
        self.checker.is_valid_addr(args.ram_load_addr, '--ram-load-addr')
        self.check_args_serial(args)
        self.check_args_tftp(args)
    
    def add_args_nand_ipl(self, parser):
        parser.add_argument('--force',
                           help='Force component installation',
                           dest='ipl_force',
                           action='store_true',
                           default=False)
        
    def add_args_nand_bootloader(self, parser):
        pass
    
    def add_args_nand_kernel(self, parser):
        parser.add_argument('--force',
                           help='Force component installation',
                           dest='kernel_force',
                           action='store_true',
                           default=False)
    
    def add_args_nand_fs(self, parser):
        parser.add_argument('--force',
                           help='Force component installation',
                           dest='fs_force',
                           action='store_true',
                           default=False)
    

    
    # ==========================================================================
    # RAM args
    # ==========================================================================
    
    def add_args_ram(self, parser):
        parser.add_argument('--file',
                           help='Path to the file to load in RAM (at --load-addr)',
                           metavar='<file>',
                           dest='ram_file',
                           required=True)
        
        parser.add_argument('--load-addr',
                           help='RAM address to load the file (decimal or hex)',
                           metavar='<addr>',
                           dest='ram_load_addr',
                           required=True)
        
        parser.add_argument('--boot-line',
                           help="Line to expect in the serial port to determine "
                           "that boot is complete",
                           metavar='<line>',
                           dest='ram_boot_line',
                           required=True)
        
        parser.add_argument('--boot-timeout',
                           help="Max time in seconds to wait for --boot-line",
                           metavar='<s>',
                           dest='ram_boot_timeout',
                           required=True)
       
        self.add_args_serial(parser)
        self.add_args_tftp(parser)
    
    def check_args_ram(self, args):
        self.checker.is_file(args.ram_file, '--file')
        self.checker.is_valid_addr(args.ram_load_addr, '--load-addr')
        self.checker.is_int(args.ram_boot_timeout, '--boot-timeout')
        args.ram_boot_timeout = int(args.ram_boot_timeout)
        self.check_args_serial(args)
        self.check_args_tftp(args)
    
    # ==========================================================================
    # Env args
    # ==========================================================================
    
    def add_args_env(self, parser):
        parser.add_argument('--variable',
                           help="U-Boot's environment variable",
                           metavar='<var>',
                           dest='env_variable',
                           required=True)
    
        parser.add_argument('--value',
                           help="Value to set in --variable",
                           metavar='<value>',
                           dest='env_value',
                           required=True)
        
        parser.add_argument('--force',
                           help='Force variable installation',
                           dest='env_force',
                           action='store_true',
                           default=False)
        
        self.add_args_serial(parser)
        self.add_args_uboot_comm(parser)
        self.add_args_termnet(parser)

    def check_args_env(self, args):
        self.check_args_serial(args)
