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
import re
import pexpect
import openfd.utils as utils
from openfd.utils.hexutils import to_hex

# ==========================================================================
# Constants
# ==========================================================================

CTRL_C = '\x03'

# Serial settings
DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUDRATE = 115200
DEFAULT_READ_TIMEOUT = 2 # seconds

# Uboot communication timeouts (seconds)
DEFAULT_UBOOT_TIMEOUT = 5

# ==========================================================================
# Public Classes
# ==========================================================================

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
        self._l_console = None
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
        
        :param cmd: The command used to communicate with u-boot.
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

    def __set_log_prefix(self, prefix):
        self._log_prefix = prefix
    
    def __get_log_prefix(self):
        return self._log_prefix
    
    log_prefix = property(__get_log_prefix, __set_log_prefix,
             doc="""String to prefix log messages for commands.
             Default: "  Uboot" """)

    def __set_console_logger(self, logger):
        self._l_console = logger
    
    def __get_console_logger(self):
        return self._l_console
    
    console_logger = property(__get_console_logger, __set_console_logger,
             doc=""":class:`Logger` instance to log the console's output.
             Output will be logged on DEBUG level.""")

    def _check_is_alive(self):
        if not self._dryrun and not self._child.isalive():
            self._l.error('No child program.')
            return False
        else:
            return True

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
        
        if self._check_is_alive() is False: return False
        
        # Use an echo command to sync
        err_msg = UbootExpect.comm_error_msg(self._open_cmd)
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
            to None to a_l_serialvoid waiting for the echo.
        :type echo_timeout: integer or none
        :param prompt_timeout: Timeout to wait for the prompt after sending
            the command. Set to None to avoid waiting for the prompt.
        :type prompt_timeout: integer or none
        :exception UbootTimeoutException: When a timeout is reached.
        """
        
        if cmd == CTRL_C:
            self._l.info("%s <= '<ctrl_c>'" % self._log_prefix)
        else:
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
                    msg = ("Didn't get the uboot prompt back after "
                               "executing the '%s' command." % cmd.strip())
                    raise UbootTimeoutException(msg)

    def expect(self, response, timeout=DEFAULT_UBOOT_TIMEOUT,
               log_console_output=False):
        """
        Expects a response from Uboot for no more than timeout seconds.
        The lines read from the console will be stripped before being
        compared with response.
        
        :param response: A string to expect in the console.
        :param timeout: Timeout in seconds to wait for the response.
        :param log_console_output: Logs (debug level INFO) the output from
            the console while expecting the response.
        :return: Returns a tuple with two items. The first item is true if the
            response was found; false otherwise. The second item is the
            complete line where the response was found, or the last line read
            if the response wasn't found and the timeout reached. The line is
            returned stripped.
        """
        
        if self._check_is_alive() is False: return False, ''
        if self._dryrun: return True, ''
        
        found = False
        line = ''
        start_time = time.time()
        
        while not found and (time.time() - start_time) < timeout:
            try:
                line = self._child.readline().strip(' \r\n')
                if self._l_console:
                    msg = "%s => '%s'" % (self._log_prefix, line)
                    if log_console_output:
                        self._l_console.info(msg)
                    else:
                        self._l_console.debug(msg)
            except (pexpect.TIMEOUT, pexpect.EOF) as e:
                self._l.error(e)
                return False, ''
            if response in line:
                found = True
            
        return found, line

    def save_env(self):
        """
        Saves the uboot environment to persistent storage.
        
        :exception UbootTimeoutException: When a timeout is reached.
        """
        
        self.cmd('saveenv')

    def set_env(self, variable, value):
        """
        Sets an uboot env variable.
        
        :exception UbootTimeoutException: When a timeout is reached.
        """
        
        value = value.strip()
        if ' ' in value or ';' in value:
            self.cmd("setenv %s '%s'" % (variable, value))
        else:
            if value.startswith('0x') and value.endswith('L'):
                self.cmd("setenv %s %s" % (variable, to_hex(value)))
            else:
                self.cmd("setenv %s %s" % (variable, value))
    
    def get_env(self, variable):
        """
        Obtains a string with the value of the uboot env variable if found;
        an empty string otherwise.
        
        :exception UbootTimeoutException: When a timeout is reached.
        """
        
        value=''
        self.cmd('printenv %s' % variable, prompt_timeout=None)
        found, line = self.expect('%s=' % variable)
        if found:
            m = re.match('.*?=(?P<value>.*)', line)
            if m:
                value = m.group('value').strip()   
        return value

    def cancel_cmd(self):
        """
        Cancels the command being executed by uboot (equivalent to CTRL+C).
        
        :exception UbootTimeoutException: When a timeout is reached.
        """
        
        self.cmd(CTRL_C, echo_timeout=None, prompt_timeout=None)
