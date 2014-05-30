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
# Communication with Uboot using pexpect to support the installer.
#
# ==========================================================================

import time
import pexpect
import openfd.utils as utils

# Serial settings
DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUDRATE = 115200
DEFAULT_READ_TIMEOUT = 2 # seconds

# Uboot communication timeouts (seconds)
DEFAULT_UBOOT_TIMEOUT = 5

class UbootTimeoutException(Exception):
    """Uboot timeouts give an exception."""

class UbootExpect(object):
    """
    Class that abstracts the communication with uboot using a console.
    Based on pexpect.
    """
    
    def __init__(self, dryrun=False):
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._open_cmd = None
        self._prompt = ''
        self._log_prefix = '  Uboot'
        self._child = None
        self._dryrun = dryrun
        self._e.dryrun = dryrun

    @classmethod
    def comm_error_msg(cls, cmd):
        """
        Standard error message to report a failure communicating with uboot
        in the given port.
             Default: "  Uboot" 
        
        :param port: The port for which communication failed (i.e.
            `/dev/ttyS0`).
        :return: A string with the standard message.
        """
        
        return ("Failed to handshake with uboot using '%s'.\n"
               "Be sure uboot is active and you have terminal "
               "programs like minicom or termnet closed." % cmd)
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System and uboot commands will
                     be logged, but not executed.""")

    def open_comm(self, cmd, timeout=DEFAULT_READ_TIMEOUT):
        """
        Opens the communication with the console where uboot is active.
        It's a good practice to call :func:`sync` after opening the port.
        
        :param cmd: Command to spawn
        :param timeout: Set a read timeout value
        :return: Returns true on success; false otherwise.
        :exception ExceptionPexpect: On error while spawning the child program.
        """
        
        self._child = pexpect.spawn(cmd)
        self._open_cmd = cmd
        return True
        
    def close_comm(self):
        """
        Closes the communication with the Serial port immediately.
        """
        
        if self._child:
            self._child.close(force=True)
            self._child = None
    
    def sync(self):
        """
        Synchronizes with uboot. If successful, uboot's prompt will be ready 
        to receive commands after this call.
        
        :return: Returns true on success; false otherwise.
        """
        
        self._l.debug("Synchronizing with uboot")
        
        err_msg = UbootExpect.comm_error_msg(self._open_cmd)
        if not self._child.isalive() and not self.dryrun:
            self._l.error(err_msg)
            return False
        
        # Use an echo command to sync
        try:
            self.cmd('echo sync', prompt_timeout=False)
        except UbootTimeoutException:
            self._l.error(err_msg)
            return False
        
        if not self._dryrun:
            try:
                self._child.expect('sync', timeout=1)
            except (pexpect.TIMEOUT, pexpect.EOF):
                self._l.error(err_msg)
                return False
        
        # Identify the prompt in the following line
        
            try:
                self._child.expect('(?P<prompt>.*)[ |$|#]')
            except pexpect.EOF:
                self._l.error(err_msg)
                return False
            except pexpect.TIMEOUT:
                self._l.error("Couldn't identify the uboot prompt.")
                return False
            self._prompt = self._child.match.group('prompt').strip()
            self._l.debug('Uboot prompt: %s' % self._prompt)
            
        return True
    
    def cmd(self, cmd, echo_timeout=DEFAULT_UBOOT_TIMEOUT,
                  prompt_timeout=DEFAULT_UBOOT_TIMEOUT):
        """
        Sends a command to uboot.
        
        :param cmd: Command.
        :param echo_timeout: Timeout to wait for the command to be echoed. Set
            to None to avoid waiting for the echo.
        :type echo_timeout: integer or none
        :param prompt_timeout: Timeout to wait for the prompt after sending
            the command. Set to None to avoid waiting for the prompt.
        :type prompt_timeout: integer or none
        :exception UbootTimeoutException: When a timeout is reached.
        """
        
        self._l.info("%s <= '%s'" % (self._log_prefix, cmd.strip()))
        
        if not self._dryrun:
        
            self._child.send('%s\n' % cmd)
            time.sleep(0.1)
            
            # Wait for the echo
            if echo_timeout:
                try:
                    self._child.expect(cmd.strip(), timeout=echo_timeout)
                except (pexpect.TIMEOUT, pexpect.EOF):
                    msg = ("Uboot didn't echo the '%s' command, maybe it "
                        "froze. " % cmd.strip())
                    raise UbootTimeoutException(msg)
            
            # Wait for the prompt
            if self._prompt and prompt_timeout:
                try:
                    self._child.expect(self._prompt, timeout=prompt_timeout)
                except (pexpect.TIMEOUT, pexpect.EOF):
                    msg = ("Didn't get the uboot prompt back  after "
                               "executing the '%s' command." % cmd.strip())
                    raise UbootTimeoutException(msg)
