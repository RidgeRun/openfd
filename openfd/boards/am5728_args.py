#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2014 RidgeRun, LLC (http://www.ridgerun.com)
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

class AM5728ArgsParser(object):
    
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
        if args.uboot_MLO_file:
            self.checker.is_file(args.uboot_MLO_file, '--uboot-MLO-file')
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

    def add_args_comm(self, parser):
        self.add_args_serial(parser)
        self.add_args_telnet(parser)

    def check_args_comm(self, args): 
        if args.serial_port:
            self.check_args_serial(args)
        elif args.telnet_host:
            self.check_args_telnet(args)
        else:
            raise ArgCheckerError('No communication method specified, use ' 
                'either --serial-* or --telnet-* settings')

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

    def add_args_telnet(self, parser):
        
        parser.add_argument('--telnet-host',
                           help="Telnet host IPv4 address where the board is"
                           "connected",
                           metavar='<telnet_host>',
                           dest='telnet_host')
        
        parser.add_argument('--telnet-port',
                           help="Telnet port number (default: 23)",
                           metavar='<telnet_port>',
                           dest='telnet_port',
                           default=23)

    def check_args_telnet(self, args):
        self.checker.is_valid_ipv4(args.telnet_host, '--telnet-host')
        self.checker.is_int(args.telnet_port, '--telnet-port')

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
                           required=True)
    
        parser.add_argument('--tftp-dir',
                           help="TFTP server root directory",
                           metavar='<dir>',
                           dest='tftp_dir',
                           required=True)
    
        parser.add_argument('--tftp-port',
                           help="TFTP server port (default: 69)",
                           metavar='<port>',
                           dest='tftp_port',
                           default=69)
        
    def check_args_tftp(self, args):
        self.checker.is_dir(args.tftp_dir, '--tftp-dir')
        self.checker.is_int(args.tftp_port, '--tftp-port')
        args.tftp_port = int(args.tftp_port)
        self.checker.is_valid_ipv4(args.host_ip_addr, '--host-ip-addr')
        if args.board_net_mode == TftpRamLoader.MODE_STATIC:
            self.checker.is_valid_ipv4(args.board_ip_addr, '--board-ip-addr')
    
