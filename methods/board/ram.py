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
# RAM loading operations to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import rrutils
from rrutils import hexutils
from rrutils import UbootTimeoutException

# ==========================================================================
# Constants
# ==========================================================================

DEFAULT_TFTP_DIR = '/srv/tftp'
DEFAULT_TFTP_PORT = 69

# ==========================================================================
# Public Classes
# ==========================================================================

class TftpException(Exception):
    """TFTP related exceptions."""
    pass

class TftpLoader(object):
    
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
        self._l = rrutils.logger.get_global_logger()
        self._e = rrutils.executer.get_global_executer()
        self._u = uboot
        self._tftp_dir = DEFAULT_TFTP_DIR
        self._tftp_port = DEFAULT_TFTP_PORT
        self._net_mode = net_mode
        self._host_ipaddr = ''
        self._board_ipaddr = ''
        self._dryrun = False

    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        self._u.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System and uboot commands will
                     be logged, but not executed.""")

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

    def _check_tftp_settings(self):
        cmd = 'netstat -an | grep udp | grep -q :%d' % self._tftp_port
        ret = self._e.check_call(cmd)
        if ret != 0:
            raise TftpException("Seems like you aren't running tftp udp server "
              "on port %d, please check your server settings" % self._tftp_port)
    
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
            raise TftpException(msg)
        
    def setup_uboot_network(self):
        """
        Setup networking for uboot, based on the specified :func:`net_mode`.
        
        :exception TftpException: Error configuring UBoot's network.
        """
        
        self._l.info('Configuring uboot network')
        if self._net_mode == TftpLoader.MODE_STATIC and not self._board_ipaddr:
            raise TftpException('No IP address specified for the board.')
        self._check_tftp_settings()
        # Don't configure the network if we have an IP address and we can reach
        # the host already
        board_ipaddr = self._u.get_env('ipaddr')
        self._u.cmd('ping %s' % self._host_ipaddr, prompt_timeout=None)
        host_is_reachable = self._u.expect('is alive', timeout=2)[0]
        if not host_is_reachable or not board_ipaddr:
            self._u.cancel_cmd()
            if self._net_mode == TftpLoader.MODE_STATIC:
                self._setup_static()
            elif self._net_mode == TftpLoader.MODE_DHCP:
                self._setup_dhcp()
        if self._u.get_env('serverip') != self._host_ipaddr:
            self._u.set_env('serverip', self._host_ipaddr)

    def load_file_to_ram(self, filename, load_addr):
        """
        Loads a file to RAM via TFTP.
        
        :param filename: File to load.
        :param load_addr: RAM address where to load the file.
        :exception TftpException: Error configuring UBoot's network.
        """
        
        # Copy the file to the host's TFTP directory
        basename = os.path.basename(filename)
        tftp_filename = '%s/%s' % (self._tftp_dir, basename)
        cmd = 'cp %s %s' % (filename, tftp_filename)
        ret, output = self._e.check_output(cmd)
        if ret != 0:
            raise TftpException(output)
        
        # Estimate a transfer timeout - 10 seconds per MB
        size_b = os.path.getsize(tftp_filename)
        one_mb = 1 << 20
        transfer_timeout = ((size_b/one_mb) + 1) * 10
        if size_b == 0:
            raise TftpException("Size of file %s is 0" % filename)
        
        # Transfer
        hex_load_addr = hexutils.to_hex(load_addr)
        self._l.debug("Starting TFTP transfer from file '%s' to RAM address "
                      "'%s'" % (tftp_filename, hex_load_addr))
        cmd = 'tftp %s %s' % (hex_load_addr, basename)
        try:
            self._u.cmd(cmd, prompt_timeout=transfer_timeout)
        except UbootTimeoutException:
            self._u.cancel_cmd()
            raise TftpException("TFTP transfer failed from '%s:%s'." %
                               (self._host_ipaddr, self._tftp_port))
        
        filesize = self._u.get_env('filesize')
        if filesize:
            env_size_b = int(filesize, base=16)
        else:
            env_size_b = 0
        if size_b != env_size_b and not self._dryrun:
            raise TftpException("Something went wrong during the transfer, the size "
                "of file '%s' (%s) differs from the transferred bytes (%s)"
                % (tftp_filename, size_b, env_size_b))
