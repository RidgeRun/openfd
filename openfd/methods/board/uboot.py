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
# Serial communication with Uboot to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import time
import re
import serial
import openfd.utils as utils

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

class UbootException(serial.SerialException):
    """Base class for uboot related exceptions."""
    
class UbootTimeoutException(UbootException):
    """Uboot timeouts give an exception."""

class Uboot(object):
    """
    Class that abstracts the communication with uboot over a serial port.
    Based on pySerial.
    """
    
    def __init__(self, dryrun=False):
        """
        :param l: :class:`Logger` instance.
        :param dryrun: Enable dryrun mode. System and uboot commands will be
            logged, but not executed.
        :type dryrun: boolean
        """
        
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._l_serial = None
        self._log_prefix = '  Uboot'  
        self._port = None
        self._prompt = ''
        self._dryrun = dryrun
        self._e.dryrun = dryrun

    @classmethod
    def comm_error_msg(cls, port):
        """
        Standard error message to report a failure communicating with uboot
        in the given port.
             Default: "  Uboot" 
        
        :param port: The port for which communication failed (i.e.
            `/dev/ttyS0`).
        :return: A string with the standard message.
        """
        
        return ('Failed to handshake with uboot.\n'
               'Be sure uboot is active on port %s and you have terminal '
               'programs like minicom closed.' % port)
    
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

    def __set_serial_logger(self, logger):
        self._l_serial = logger
    
    def __get_serial_logger(self):
        return self._l_serial
    
    serial_logger = property(__get_serial_logger, __set_serial_logger,
             doc=""":class:`Logger` instance to log the serial port's output.
             Output will be logged on DEBUG level.""")

    def _check_open_port(self):
        if self._port is None and not self._dryrun:
            self._l.error('No opened port.')
            return False
        else:
            return True

    def open_comm(self, port=DEFAULT_PORT,
                  baud=DEFAULT_BAUDRATE,
                  timeout=DEFAULT_READ_TIMEOUT):
        """
        Opens the communication with the Serial port where uboot is active.
        It's a good practice to call :func:`sync` after opening the port.
        
        :param port: Device name or port number (i.e. '/dev/ttyS0')
        :type port: string
        :param baud: Baud rate such as 9600 or 115200 etc
        :param timeout: Set a read timeout value
        :return: Returns true on success; false otherwise.
        :exception SerialException: On error while opening the serial port.
        """
        
        self._l.debug("Starting communication with uboot")
        
        if self._dryrun: return True
        
        # Terminal line settings
        cmd = ('stty -F %s %s intr ^C quit ^D erase ^H kill ^U eof ^Z '
               'eol ^J start ^Q stop ^S -echo echoe echok -echonl echoke '
               '-echoctl -istrip -icrnl -ocrnl -igncr -inlcr onlcr -opost '
               '-isig -icanon cs8 -cstopb clocal -crtscts -ixoff -ixon '
               '-parenb -parodd -inpck' % (port, baud))
        ret, output = self._e.check_output(cmd)
        if ret != 0:
            self._l.error(output)
            return False
        
        try:
            self._port = serial.Serial(port=port,
                                       baudrate=baud,
                                       timeout=timeout)
        except serial.SerialException as e:
            self._l.error(e)
            raise e
        
        return True

    def close_comm(self):
        """
        Closes the communication with the Serial port immediately.
        """
        
        if self._port:
            self._port.close()
            self._port = None

    def expect(self, response, timeout=DEFAULT_UBOOT_TIMEOUT,
               log_serial_output=False):
        """
        Expects a response from Uboot for no more than timeout seconds.
        The lines read from the serial port will be stripped before being
        compared with response.
        
        :param response: A string to expect in the serial port.
        :param timeout: Timeout in seconds to wait for the response.
        :param log_serial_output: Logs (debug level INFO) the output from
            the serial port while expecting the response.
        :return: Returns a tuple with two items. The first item is true if the
            response was found; false otherwise. The second item is the
            complete line where the response was found, or the last line read
            if the response wasn't found and the timeout reached. The line is
            returned stripped.
        """
        
        if self._check_open_port() is False: return False, ''
        if self._dryrun: return True, ''
        
        found = False
        line = ''
        start_time = time.time()
        
        while not found and (time.time() - start_time) < timeout:
            try:
                line = self._port.readline().strip(' \r\n')
                if self._l_serial:
                    msg = "%s => '%s'" % (self._log_prefix, line)
                    if log_serial_output:
                        self._l_serial.info(msg)
                    else:
                        self._l_serial.debug(msg)
            except (serial.SerialException, OSError) as e:
                self._l.error(e)
                return False, ''
            if response in line:
                found = True
            
        return found, line

    def _identify_prompt(self, line):
        m = re.match('(?P<prompt>.*) $', line)
        if m:
            self._prompt = m.group('prompt').strip()
            self._l.debug('Uboot prompt: %s' % self._prompt)
        else:
            self._l.error("Couldn't identify the uboot prompt.")
            return False
        
        return True

    def sync(self):
        """
        Synchronizes with uboot. If successful, uboot's prompt will be ready 
        to receive commands after this call.
        
        :return: Returns true on success; false otherwise.
        """
        
        self._l.debug("Synchronizing with uboot")
        
        if self._check_open_port() is False: return False
        
        port_name = ''
        if not self._dryrun:
            self._port.flush()
            port_name = self._port.port
        
        # Use an echo command to sync
        err_msg = Uboot.comm_error_msg(port_name)
        try:
            self.cmd('echo sync', prompt_timeout=False)
        except UbootTimeoutException as e:
            self._l.error(err_msg)
            return False
        
        found_echo = self.expect('sync', timeout=1)[0]
        if not found_echo:
            self._l.error(err_msg)
            return False
        
        # Identify the prompt in the following line
        if not self._dryrun:
            try:
                line = self._port.readline().strip('\r\n')
                if self._l_serial:
                    self._l_serial.debug("%s => '%s'" % (self._log_prefix,
                                                         line))
            except (serial.SerialException, OSError) as e:
                self._l.error(e)
                return False
            
            ret = self._identify_prompt(line)
            if ret is False: return False

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
        
        if cmd == CTRL_C:
            self._l.info("%s <= '<ctrl_c>'" % self._log_prefix)
        else:
            self._l.info("%s <= '%s'" % (self._log_prefix, cmd.strip()))
        
        if not self._dryrun:
        
            self._port.write('%s\n' % cmd)
            time.sleep(0.1)
            
            # Wait for the echo
            if echo_timeout:
                found_echo, line = self.expect(cmd.strip(), echo_timeout)
                if not found_echo:
                    msg = ("Uboot didn't echo the '%s' command, maybe it "
                        "froze. " % cmd.strip())
                    if line:
                        msg += "This is the log of the last line: %s" % line
                    raise UbootTimeoutException(msg)
            
            # Wait for the prompt
            if self._prompt and prompt_timeout:
                found_prompt, line = self.expect(self._prompt, timeout=prompt_timeout)
                if not found_prompt:
                    msg = ("Didn't get the uboot prompt back  after "
                           "executing the '%s' command." % cmd.strip())
                    if line:
                        msg += "This is the log of the last line: %s" % line
                    raise UbootTimeoutException(msg)
    
    def cancel_cmd(self):
        """
        Cancels the command being executed by uboot (equivalent to CTRL+C).
        
        :exception UbootTimeoutException: When a timeout is reached.
        """
        
        self.cmd(CTRL_C, echo_timeout=None, prompt_timeout=None)

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
        
        if ' ' in value or ';' in value:
            self.cmd("setenv %s '%s'" % (variable, value))
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
