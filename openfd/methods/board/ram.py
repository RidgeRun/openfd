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
# RAM loading operations to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import openfd.utils as utils
import openfd.utils.hexutils as hexutils
from openfd.utils.hexutils import to_hex
from uboot import UbootTimeoutException

# ==========================================================================
# Constants
# ==========================================================================

DEFAULT_TFTP_DIR = '/srv/tftp'
DEFAULT_TFTP_PORT = 69

# ==========================================================================
# Public Classes
# ==========================================================================

class RamLoader(object):
    """Interface for objects that load images to RAM memory."""
    
    def load_file_to_ram(self):
        raise NotImplementedError
    
    def load_file_to_ram_and_boot(self):
        raise NotImplementedError

    def get_load_file_to_ram_env(self):
        raise NotImplementedError

class RamLoaderException(Exception):
    """RAM loader exceptions."""

class TftpRamLoader(RamLoader):
    """Load images to RAM via TFTP."""
    
    #: Static networking mode.
    MODE_STATIC = 'static'
    
    #: DHCP networking mode.
    MODE_DHCP = 'dhcp'
    
    def __init__(self, uboot, net_mode):
        """
        :param uboot: :class:`Uboot` instance.
        :param net_mode: Networking mode. Possible values:
            :const:`MODE_STATIC`, :const:`MODE_DHCP`.
        """
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._u = uboot
        self._dir = DEFAULT_TFTP_DIR
        self._port = DEFAULT_TFTP_PORT
        self._net_mode = net_mode
        self._host_ipaddr = ''
        self._board_ipaddr = ''
        self._dryrun = False

    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        if self._u is not None:
            self._u.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System and uboot commands will
                     be logged, but not executed.""")

    def __set_port(self, port):
        self._port = port
    
    def __get_port(self):
        return self._port
    
    port = property(__get_port, __set_port, doc="""TFTP server port.""")
    
    def __set_dir(self, directory):
        self._dir = directory
    
    def __get_dir(self):
        return self._dir
    
    dir = property(__get_dir, __set_dir, doc="""TFTP root directory.""")

    def __set_net_mode(self, mode):
        self._net_mode = mode
    
    def __get_net_mode(self):
        return self._net_mode
    
    net_mode = property(__get_net_mode, __set_net_mode,
                     doc="""Networking mode. Possible values:
                     :const:`MODE_STATIC`, :const:`MODE_DHCP`.""")

    def __set_board_ipaddr(self, ipaddr):
        self._board_ipaddr = ipaddr
    
    def __get_board_ipaddr(self):
        return self._board_ipaddr
    
    board_ipaddr = property(__get_board_ipaddr, __set_board_ipaddr,
                     doc="""Board IP address, only necessary in
                     :const:`MODE_STATIC`.""")

    def __set_host_ipaddr(self, ipaddr):
        self._host_ipaddr = ipaddr
    
    def __get_host_ipaddr(self):
        return self._host_ipaddr
    
    host_ipaddr = property(__get_host_ipaddr, __set_host_ipaddr,
                     doc="""Host IP address.""")

    def check_tftp_settings(self):
        cmd = 'netstat -an | grep udp | grep -q :%d' % self._port
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise RamLoaderException("Seems like you aren't running tftp udp server "
              "on port %d, please check your server settings" % self._port)
    
    def _setup_static(self):
        self._u.set_env('ipaddr', self._board_ipaddr)
    
    def _setup_dhcp(self):
        self._u.set_env('autoload', 'no')
        self._u.set_env('autostart', 'no')
        self._u.cmd('dhcp', prompt_timeout=None)
        # If dhcp failed at retry 3, stop and report the error
        dhcp_error_line = 'BOOTP broadcast 3'
        found_error, line = self._u.expect(dhcp_error_line, timeout=6)
        if found_error and not self.dryrun:
            self._u.cancel_cmd()
            msg = ("Looks like your network doesn't have dhcp enabled "
                   "or you don't have an ethernet link. ")
            if line:
                msg += "This is the log of the last line: '%s'" % line
            raise RamLoaderException(msg)
        
    def setup_uboot_network(self):
        """
        Setup networking for uboot, based on the specified :func:`net_mode`.
        
        :exception RamLoaderException: Error configuring UBoot's network.
        """
        
        self._l.info('Configuring uboot network')
        if self._net_mode == TftpRamLoader.MODE_STATIC and not self._board_ipaddr:
            raise RamLoaderException('No IP address specified for the board.')
        self.check_tftp_settings()
        # Don't configure the network if we have an IP address and we can reach
        # the host already
        board_ipaddr = self._u.get_env('ipaddr')
        self._u.cmd('ping %s' % self._host_ipaddr, prompt_timeout=None)
        host_is_reachable = self._u.expect('is alive', timeout=8)[0]
        if not host_is_reachable or not board_ipaddr:
            self._u.cancel_cmd()
            if self._net_mode == TftpRamLoader.MODE_STATIC:
                self._setup_static()
            elif self._net_mode == TftpRamLoader.MODE_DHCP:
                self._setup_dhcp()
        if self._u.get_env('serverip') != self._host_ipaddr:
            self._u.set_env('serverip', self._host_ipaddr)

    def _transfer_timeout(self, size_b):
        # 15 secs per mb
        one_mb = 1 << 20
        return ((size_b/one_mb) + 1) * 15

    def load_file_to_ram(self, filename, load_addr):
        """
        Loads a file to RAM via TFTP.
        
        :param filename: File to load.
        :param load_addr: RAM address where to load the file.
        :exception RamLoaderException: Error loading to RAM.
        """
        
        # Copy the file to the host's TFTP directory
        basename = os.path.basename(filename)
        tftp_filename = '%s/%s' % (self._dir, basename)
        cmd = 'cp -f %s %s' % (filename, tftp_filename)
        ret, output = self._e.check_output(cmd)
        if ret != 0:
            raise RamLoaderException(output)
        
        # Transfer
        size_b = os.path.getsize(tftp_filename)
        if size_b == 0:
            raise RamLoaderException("Size of file %s is 0" % filename)
        hex_load_addr = hexutils.to_hex(load_addr)
        self._l.debug("Starting TFTP transfer from file '%s' to RAM address "
                      "'%s'" % (tftp_filename, hex_load_addr))
        cmd = 'tftp %s %s' % (to_hex(hex_load_addr), basename)
        try:
            self._u.cmd(cmd, prompt_timeout=self._transfer_timeout(size_b))
        except UbootTimeoutException:
            self._u.cancel_cmd()
            raise RamLoaderException("TFTP transfer failed from '%s:%s'." %
                               (self._host_ipaddr, self._port))
        
        filesize = self._u.get_env('filesize')
        if filesize:
            env_size_b = int(filesize, base=16)
        else:
            env_size_b = 0
        if size_b != env_size_b and not self._dryrun:
            raise RamLoaderException("Something went wrong during the transfer, the size "
                "of file '%s' (%s) differs from the transferred bytes (%s)"
                % (tftp_filename, size_b, env_size_b))

    def load_file_to_ram_and_boot(self, filename, load_addr, boot_line,
                                  boot_timeout=0):
        """
        Loads a file to RAM via TFTP.
        
        :param filename: File to load.
        :param load_addr: RAM address where to load the file.
        :param boot_line: Line to expect in the serial port to determine that
            boot has been reached.
        :param boot_timeout: Timeout (in seconds) to wait for
            :const:`boot_line`.
        :exception RamLoaderException: Error loading to RAM or booting.
        """
        
        # Copy the file to the host's TFTP directory
        basename = os.path.basename(filename)
        tftp_filename = '%s/%s' % (self._dir, basename)
        cmd = 'cp %s %s' % (filename, tftp_filename)
        ret, output = self._e.check_output(cmd)
        if ret != 0:
            raise RamLoaderException(output)
        
        self._u.set_env('autostart', 'yes')
        
        # Transfer
        size_b = os.path.getsize(tftp_filename)
        if size_b == 0:
            raise RamLoaderException("Size of file %s is 0" % filename)
        hex_load_addr = hexutils.to_hex(load_addr)
        self._l.debug("Starting TFTP transfer from file '%s' to RAM address "
                      "'%s'" % (tftp_filename, hex_load_addr))
        cmd = 'tftp %s %s' % (hex_load_addr, basename)
        self._u.cmd(cmd, prompt_timeout=None)
        autobooting = self._u.expect("Automatic boot of image at addr",
                                  timeout=self._transfer_timeout(size_b))[0]
        if not autobooting:
            raise RamLoaderException("Didn't detect Autoboot from addr "
                                         "%s" % hex_load_addr)
        self._l.info("Booting from %s" % hex_load_addr)
        self._u.log_prefix = "  Serial"
        booted = self._u.expect(boot_line, timeout=boot_timeout,
                                log_serial_output=True)[0]
        if not booted:
            raise RamLoaderException("Didn't encountered boot line '%s' "
                                "after %s seconds" %(boot_line, boot_timeout))
        
    def get_env_load_file_to_ram(self, filename, load_addr):
        """
        Set the tftp file to be transfer and returns the loadtftp 
        uboot enviroment variable
        
        :param filename: File to load.
        :param load_addr: RAM address where to load the file.
        :exception RamLoaderException: Error loading to RAM.
        """
        
        # Copy the file to the host's TFTP directory
        basename = os.path.basename(filename)
        tftp_filename = '%s/%s' % (self._dir, basename)

        if self._net_mode == TftpRamLoader.MODE_STATIC:
            ip_method = 'setenv ipaddr'
        elif self._net_mode == TftpRamLoader.MODE_DHCP:
            ip_method = 'setenv autoload no;dhcp'

        cmd = 'cp -f %s %s' % (filename, tftp_filename)
        ret, output = self._e.check_output(cmd)
        if ret != 0:
            raise RamLoaderException(output)
        
        size_b = os.path.getsize(tftp_filename)
        if size_b == 0:
            raise RamLoaderException("Size of file %s is 0" % filename)

        hex_load_addr = hexutils.to_hex(load_addr)        
        cmd = '%s;setenv serverip %s; setenv loadaddr %s;tftp %s' % (ip_method,
                                                                     self._host_ipaddr,
                                                                     hex_load_addr,
                                                                     basename)
        self._l.debug("Setting TFTP transfer from file '%s' to RAM address "
                      "'%s'" % (tftp_filename, hex_load_addr))

        return cmd
