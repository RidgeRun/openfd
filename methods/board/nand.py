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
# Serial communication operations to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import time
import rrutils
import rrutils.hexutils as hexutils

# ==========================================================================
# Constants
# ==========================================================================

# TFTP settings
DEFAULT_TFTP_DIR = '/srv/tftp'
DEFAULT_TFTP_PORT = 69

# NAND
DEFAULT_NAND_TIMEOUT = 60

# ==========================================================================
# Public Classes
# ==========================================================================

class NandInstaller(object):
    
    def __init__(self, uboot, ram_load_addr=None, dryrun=False):
        """
        :param uboot: :class:`Uboot` instance.
        :param ram_load_addr: RAM address to load components, in decimal or
            hexadecimal (`'0x'` prefix).
        :param dryrun: Enable dryrun mode. System commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._executer.logger = self._logger
        self._uboot = uboot
        self._ram_load_addr = None
        if hexutils.is_valid_addr(ram_load_addr):
            self._ram_load_addr = hexutils.str_to_hex(str(ram_load_addr))
        self._dryrun = dryrun
        
    def __set_ram_load_addr(self, ram_load_addr):
        if hexutils.is_valid_addr(ram_load_addr):
            self._ram_load_addr = hexutils.to_hex(str(ram_load_addr))
        else:
            self._logger.error('Invalid RAM load address: %s' %
                               ram_load_addr)
            self._ram_load_addr = None
        
    def __get_ram_load_addr(self):
        return self._ram_load_addr
    
    ram_load_addr = property(__get_ram_load_addr, __set_ram_load_addr,
                               doc="""Uboot RAM load address, in decimal or
                                hexadecimal (`'0x'` prefix).""")
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._executer.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System commands will be
                     logged, but not executed.""")
    
    def _check_icache(self):
        """
        Checks availability of the 'icache' uboot command.
        """
        
        ret = self._uboot.cmd('icache', prompt_timeout=None)
        if ret is False: return False
        
        ret = self._uboot.expect('Instruction Cache is')[0]
        if ret is False:
            self._logger.error("Your uboot doesn't have icache command, "
               "refusing to continue due to the risk of hanging, you can "
               "update your bootloader by other means like an SD card.")
            return False
        return True    

    def _load_file_to_ram(self, filename, load_addr):
        raise NotImplementedError

    def load_uboot_to_ram(self, image_filename, load_addr):
        """
        Loads an uboot image to RAM and executes it. This uboot will drive
        the installation.
        
        :param image_filename: Path to the uboot image file.
        :param load_addr: Load address in RAM where to load the uboot image.
        """
        
        if not os.path.isfile(image_filename):
            self._logger.error("Uboot image '%s' doesn't exist" %
                               image_filename)
            return False
        
        ret = self._uboot.sync()
        if ret is False: return False
        
        ret = self._check_icache()
        if ret is False: return False
        
        self._logger.info("Storing the current uboot's bootcmd")
        prev_bootcmd = self._uboot.get_env('bootcmd')
        ret = self._uboot.set_env('bootcmd', '')
        if ret is False: return False
        ret = self._uboot.cmd('saveenv')
        if ret is False: return False
        
        self._logger.info('Loading new uboot to RAM')
        ret = self._load_file_to_ram(image_filename, load_addr)
        if ret is False: return False
        
        self._logger.info('Running the new uboot')
        ret = self._uboot.cmd('icache off')
        if ret is False: return False
        ret = self._uboot.cmd('go %s' % load_addr)
        if ret is False: return False
        time.sleep(2) # Give time to uboot to restart
        ret = self._uboot.sync()
        if ret is False:
            self._logger.error('Failed to detect the new uboot starting')
            return False
        
        if prev_bootcmd:
            self._logger.info('Restoring the previous uboot bootcmd')
            ret = self._uboot.set_env('bootcmd', prev_bootcmd)
            if ret is False: return False
        
        ret = self._uboot.cmd('saveenv')
        if ret is False: return False
        
        return True
    
    def install_ubl(self, image_filename, start_block):
        """
        Installs the UBL (initial program loader) image to NAND.
        
        :param image_filename: Path to the UBL image file.
        :param start_block: Start block in NAND for the UBL image.
        :type start_block: integer
        :returns: Returns true on success; false otherwise.
        """
        
        if not os.path.isfile(image_filename):
            self._logger.error("UBL image '%s' doesn't exist" % image_filename)
            return False
        
        self._logger.info("Loading UBL image to RAM")
        ret = self._load_file_to_ram(image_filename, self._ram_load_addr)
        if ret is False: return False
        
        # Offset in blocks
        ubl_offset_addr = start_block * self._uboot.nand_block_size
        
        # Size in blocks
        ubl_size_b = os.path.getsize(image_filename)
        ubl_size_blk = (ubl_size_b / self._uboot.nand_block_size) + 1
        ubl_size_aligned = ubl_size_blk * self._uboot.nand_block_size
        
        self._logger.info("Erasing UBL NAND space")
        cmd = 'nand erase %s %s' % (hex(ubl_offset_addr),
                                    hex(ubl_size_aligned))
        ret = self._uboot.cmd(cmd, echo_timeout=None,
                             prompt_timeout=DEFAULT_NAND_TIMEOUT)
        if ret is False: return False
        
        self._logger.info("Writing UBL image from RAM to NAND")
        cmd = 'nand write.ubl %s %s %s' % (self._ram_load_addr,
                                   hex(ubl_offset_addr), hex(ubl_size_aligned))
        ret = self._uboot.cmd(cmd, echo_timeout=DEFAULT_NAND_TIMEOUT,
                             prompt_timeout=None)
        if ret is False: return False
        
        return True
    
    def install_uboot(self, image_filename, start_block):
        """
        Installs the uboot image to NAND.
        
        :param image_filename: Path to the uboot image file.
        :param start_block: Start block in NAND for the uboot image.
        :type start_block: integer
        :returns: Returns true on success; false otherwise.
        """
    
        if not os.path.isfile(image_filename):
            self._logger.error("Uboot image '%s' doesn't exist" %
                               image_filename)
            return False
        
        self._logger.info("Loading uboot image to RAM")
        ret = self._load_file_to_ram(image_filename, self._ram_load_addr)
        if ret is False: return False

        # Offset in blocks
        uboot_offset_addr = start_block * self._uboot.nand_block_size
        
        # Size in blocks
        uboot_size_b = os.path.getsize(image_filename)
        uboot_size_blk = (uboot_size_b / self._uboot.nand_block_size) + 1
        uboot_size_aligned = uboot_size_blk * self._uboot.nand_block_size

        self._logger.info("Erasing uboot NAND space")
        cmd = 'nand erase %s %s' % (hex(uboot_offset_addr),
                                    hex(uboot_size_aligned))
        ret = self._uboot.cmd(cmd, echo_timeout=None,
                             prompt_timeout=DEFAULT_NAND_TIMEOUT)
        if ret is False: return False
        
        self._logger.info("Writing uboot image from RAM to NAND")
        cmd = 'nand write.ubl %s %s %s' % (self._ram_load_addr,
                                           hex(uboot_offset_addr),
                                           hex(uboot_size_aligned))
        ret = self._uboot.cmd(cmd, echo_timeout=DEFAULT_NAND_TIMEOUT,
                             prompt_timeout=None)
        if ret is False: return False
        
        self._logger.info("Restarting to use the uboot in NAND")
        ret = self._uboot.cmd('reset', prompt_timeout=None)
        uboot_reset_str = 'U-Boot'
        found_reset_str = self._uboot.expect(uboot_reset_str, timeout=10)[0]
        if not found_reset_str:
            self._logger.error("Failed to detect the uboot in NAND restarting")
            return False
        time.sleep(4) # Give uboot time to initialize
        ret = self._uboot.sync()
        if ret is False:
            self._logger.error("Failed synchronizing with the uboot in NAND")
            return False
        
        return True

class NandInstallerTFTP(NandInstaller):
    
    #: Static networking mode.
    MODE_STATIC = 'static'
    
    #: DHCP networking mode.
    MODE_DHCP = 'dhcp'
    
    def __init__(self, uboot, host_ipaddr='', target_ipaddr='',
                 tftp_dir=DEFAULT_TFTP_DIR, tftp_port=DEFAULT_TFTP_PORT,
                 net_mode=None, ram_load_addr=None, dryrun=False):
        """
        :param uboot: :class:`Uboot` instance.
        :param host_ipaddr: Host IP address.
        :param target_ipaddr: Target IP address, only necessary
            in :const:`MODE_STATIC`.
        :param tftp_dir: TFTP root directory.
        :param tftp_port: TFTP server port.
        :type tftp_port: integer
        :param net_mode: Networking mode. Possible values:
            :const:`MODE_STATIC`, :const:`MODE_DHCP`.
        :param ram_load_addr: RAM address to load components, in decimal or
            hexadecimal (`'0x'` prefix).
        :param dryrun: Enable dryrun mode. System commands will be logged,
            but not executed.
        :type dryrun: boolean
        """    
        NandInstaller.__init__(self, uboot, ram_load_addr, dryrun)
        self._tftp_dir = tftp_dir
        self._tftp_port = tftp_port
        self._net_mode = net_mode
        self._host_ipaddr = host_ipaddr
        self._target_ipaddr = target_ipaddr
        self._is_network_setup = False
        
    def __set_tftp_port(self, port):
        self._tftp_port = port
    
    def __get_tftp_port(self):
        return self._tftp_port
    
    tftp_port = property(__get_tftp_port, __set_tftp_port,
                     doc="""TFTP server port.""")
    
    def __set_tftp_dir(self, directory):
        self._tftp_dir = directory
    
    def __get_tftp_dir(self):
        return self._tftp_dir
    
    tftp_dir = property(__get_tftp_dir, __set_tftp_dir,
                     doc="""TFTP root directory.""")

    def __set_net_mode(self, mode):
        self._net_mode = mode
    
    def __get_net_mode(self):
        return self._net_mode
    
    net_mode = property(__get_net_mode, __set_net_mode,
                     doc="""Networking mode. Possible values:
                     :const:`MODE_STATIC`, :const:`MODE_DHCP`.""")

    def __set_target_ipaddr(self, ipaddr):
        self._target_ipaddr = ipaddr
    
    def __get_target_ipaddr(self):
        return self._target_ipaddr
    
    target_ipaddr = property(__get_target_ipaddr, __set_target_ipaddr,
                     doc="""Target IP address, only necessary in
                     :const:`MODE_STATIC`.""")

    def __set_host_ipaddr(self, ipaddr):
        self._host_ipaddr = ipaddr
    
    def __get_host_ipaddr(self):
        return self._host_ipaddr
    
    host_ipaddr = property(__get_host_ipaddr, __set_host_ipaddr,
                     doc="""Host IP address.""")

    def _check_tftp_settings(self):
        """
        Checks TFTP settings in the host (dir and port).
        """
        
        if not os.path.isdir(self._tftp_dir):
            self._logger.error("Can't deploy firmware to '%s', the directory "
                               "doesn't exist" % self._tftp_dir)
            return False
        
        if not os.access(self._tftp_dir, os.W_OK):
            self._logger.error("Can't deploy firmware to '%s', the directory "
                               "is not writable" % self._tftp_dir)
            return False
        
        cmd = 'netstat -an | grep udp | grep -q :%d' % self._tftp_port
        ret = self._executer.check_call(cmd)
        if ret != 0:
            self._logger.error("Seems like you aren't running tftp udp server "
                               "on port %d, please check your server settings"
                               % self._tftp_port)
            return False
        
        return True

    def _load_file_to_ram(self, filename, load_addr):
        """
        Loads the given file through TFTP to the given load address in RAM.
        """
        
        if not hexutils.is_valid_addr(load_addr):
            self._logger.error("Invalid address '%s'" % load_addr)
            return False
        
        if not self._is_network_setup:
            self._logger.error("Please setup uboot's network prior to any "
                               "TFTP transfer")
            return False
        
        # Copy the file to the host's TFTP directory
        basename = os.path.basename(filename)
        tftp_filename = '%s/%s' % (self._tftp_dir, basename)
        cmd = 'cp %s %s' % (filename, tftp_filename)
        ret, output = self._executer.check_output(cmd)
        if ret != 0:
            self._logger.error(output)
            return False
        
        # Estimate a transfer timeout - 10 seconds per MB
        size_b = os.path.getsize(tftp_filename)
        one_mb = 1 << 20
        transfer_timeout = ((size_b/one_mb) + 1) * 10
        
        # Transfer
        hex_load_addr = hexutils.to_hex(load_addr)
        self._logger.debug("Starting TFTP transfer from file '%s' to "
                          "address '%s'" % (tftp_filename, hex_load_addr))
        cmd = 'tftp %s %s' % (hex_load_addr, basename)
        ret = self._uboot.cmd(cmd, prompt_timeout=transfer_timeout)
        if ret is False:
            self._uboot.cancel_cmd()
            self._logger.error("TFTP transfer failed from '%s:%s'." %
                               (self._host_ipaddr, self._tftp_port))
            return False
        
        filesize = self._uboot.get_env('filesize')
        if filesize:
            filesize = int(filesize, base=16)
        else:
            filesize = 0
        if size_b != filesize:
            self._logger.error("Something went wrong during the transfer, the "
                "size of file '%s' (%s) differs from the transferred "
                "bytes (%s)" % (tftp_filename, size_b, filesize))
            return False
        
        return True
        
    def setup_uboot_network(self):
        """
        Setup networking for uboot, based on the specified :func:`net_mode`.
        
        Returns true on success; false otherwise.
        """
        
        if not self._net_mode:
            self._logger.error('Please provide a networking mode')
            return False
        
        self._logger.info('Checking TFTP settings')
        ret = self._check_tftp_settings()
        if ret is False: return False
        
        self._logger.info('Configuring uboot network')
        if self._net_mode == NandInstallerTFTP.MODE_STATIC:
            if not self._target_ipaddr:
                self._logger.error('No IP address specified for the target')
                return False
            ret = self._uboot.set_env('ipaddr', self._target_ipaddr)
            if ret is False: return False
        elif self._net_mode == NandInstallerTFTP.MODE_DHCP:
            ret = self._uboot.set_env('autoload', 'no')
            if ret is False: return False
            ret = self._uboot.set_env('autostart', 'no')
            if ret is False: return False
            ret = self._uboot.cmd('dhcp', prompt_timeout=None)
            if ret is False: return False
            # If dhcp failed at retry 3, stop and report the error
            dhcp_error_line = 'BOOTP broadcast 3'
            found_error, line = self._uboot.expect(dhcp_error_line, timeout=6)
            if found_error:
                self._uboot.cancel_cmd()
                msg = ("Looks like your network doesn't have dhcp enabled or "
                       "you don't have an ethernet link. ")
                if line:
                    msg += "This is the log of the last line: %s" % line
                self._logger.error(msg)
                return False

        ret = self._uboot.set_env('serverip', self._host_ipaddr)
        if ret is False: return False
        
        self._is_network_setup = True
        
        return True
