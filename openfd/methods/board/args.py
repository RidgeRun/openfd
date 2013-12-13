#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# CLI arguments parsing support for openfd.methods.board.
#
# ==========================================================================

from openfd.utils import ArgChecker
from openfd.methods.board import TftpRamLoader

class BoardArgs():
    
    def __init__(self):
        self.checker = ArgChecker()

    # ==========================================================================
    # General args
    # ==========================================================================

    def add_args_serial(self, parser):
        
        parser.add_argument('--serial-port',
                           help="Device name or port number for serial communica"
                           "tion with U-Boot (i.e. '/dev/ttyS0')",
                           metavar='<port>',
                           dest='serial_port',
                           required=True)
        
        parser.add_argument('--serial-baud',
                           help="Baud rate (default: 115200)",
                           metavar='<baud>',
                           dest='serial_baud',
                           default=115200)
    
    def check_args_serial(self, args):
        self.checker.is_int(args.serial_baud, '--serial-baud')
    
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
        self.add_args_serial(parser)
        
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

    def check_args_env(self, args):
        self.check_args_serial(args)
