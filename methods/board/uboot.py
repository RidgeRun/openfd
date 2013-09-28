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
import rrutils

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

class Uboot(object):
    """
    Class that abstracts the communication with uboot over a serial port.
    Based on pySerial.
    """
    
    def __init__(self, dryrun=False):
        """
        :param dryrun: Enable dryrun mode. System and uboot commands will be
            logged, but not executed.
        :type dryrun: boolean
        """
        
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._executer.logger = self._logger
        self._port = None
        self._prompt = ''
        self._dryrun = dryrun

    @classmethod
    def comm_error_msg(cls, port):
        """
        Standard error message to report a failure communicating with uboot
        in the given port.
        
        :param port: The port for which communication failed (i.e.
            `/dev/ttyS0`).
        :return: A string with the standard message.
        """
        
        return ('Failed to handshake with uboot.\n'
               'Be sure uboot is active on port %s and you have terminal '
               'programs like minicom closed.' % port)
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._executer.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System and uboot commands will
                     be logged, but not executed.""")

    def _check_open_port(self):
        if self._port is None and not self._dryrun:
            self._logger.error('No opened port (try open_comm() first)')
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
        
        if self._dryrun: return True
        
        # Terminal line settings
        cmd = ('stty -F %s %s intr ^C quit ^D erase ^H kill ^U eof ^Z '
               'eol ^J start ^Q stop ^S -echo echoe echok -echonl echoke '
               '-echoctl -istrip -icrnl -ocrnl -igncr -inlcr onlcr -opost '
               '-isig -icanon cs8 -cstopb clocal -crtscts -ixoff -ixon '
               '-parenb -parodd -inpck' % (port, baud))
        ret, output = self._executer.check_output(cmd)
        if ret != 0:
            self._logger.error(output)
            return False
        
        try:
            self._port = serial.Serial(port=port,
                                       baudrate=baud,
                                       timeout=timeout)
        except serial.SerialException as e:
            self._logger.error(e)
            raise e
        
        return True

    def close_comm(self):
        """
        Closes the communication with the Serial port immediately.
        """
        
        if self._port:
            self._port.close()
            self._port = None

    def expect(self, response, timeout=DEFAULT_UBOOT_TIMEOUT):
        """
        Expects a response from Uboot for no more than timeout seconds.
        The lines read from the serial port will be stripped before being
        compared with response.
        
        :param response: A string to expect in the serial port.
        :param timeout: Timeout in seconds to wait for the response.
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
            except (serial.SerialException, OSError) as e:
                self._logger.error(e)
                return False, ''
            if response in line:
                found = True
            
        return found, line

    def _identify_prompt(self, line):
        m = re.match('(?P<prompt>.*) $', line)
        if m:
            self._prompt = m.group('prompt').strip()
            self._logger.debug('Uboot prompt: %s' % self._prompt)
        else:
            self._logger.error("Couldn't identify the uboot prompt.")
            return False
        
        return True

    def sync(self):
        """
        Synchronizes with uboot. If successful, uboot's prompt will be ready 
        to receive commands after this call.
            False
        :return: Returns true on success; false otherwise.
        """
        
        if self._check_open_port() is False: return False
        
        if not self._dryrun:
            self._port.flush()
        
        # Use an echo command to sync
        if (not self.cmd('echo sync', prompt_timeout=False) or
            not self.expect('sync', timeout=1)[0]):
            msg = Uboot.comm_error_msg(self._port.port)
            self._logger.error(msg)
            return False
        
        # Identify the prompt in the following line
        if not self._dryrun:
            try:
                line = self._port.readline().strip('\r\n')
            except (serial.SerialException, OSError) as e:
                self._logger.error(e)
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
        :returns: Returns true on success; false otherwise.
        """
        
        if self._check_open_port() is False: return False
        
        self._logger.info("Uboot: '%s'" % cmd.strip())
        
        if not self._dryrun:
        
            self._port.write('%s\n' % cmd)
            time.sleep(0.1)
            
            # Wait for the echo
            if echo_timeout:
                ret, line = self.expect(cmd.strip(), echo_timeout)
                if ret is False:
                    msg = ("Uboot didn't echo the '%s' command, maybe it "
                        "froze. " % cmd.strip())
                    if line:
                        msg += "This is the log of the last line: %s" % line
                    self._logger.error(msg)
                    return False
        
            # Wait for the prompt
            if self._prompt and prompt_timeout:
                ret, line = self.expect(self._prompt, timeout=prompt_timeout)
                if ret is False:
                    msg = ("Didn't get the uboot prompt back  after "
                           "executing the '%s' command. " % cmd.strip())
                    if line:
                        msg += "This is the log of the last line: %s" % line
                    self._logger.error(msg)
                    return False
        
        return True
    
    def cancel_cmd(self):
        """
        Cancels the command being executed by uboot (equivalent to CTRL+C).
        
        :returns: Returns true on success; false otherwise.
        """
        
        return self.cmd(CTRL_C, echo_timeout=None, prompt_timeout=None)
    
    def set_env(self, variable, value):
        """
        Sets an uboot env variable.
        
        :returns: Returns true on success; false otherwise.
        """
        
        return self.cmd('setenv %s %s' % (variable, value))
    
    def get_env(self, variable):
        """
        Obtains a string with the value of the uboot env variable if found;
        an empty string otherwise.
        """
        
        value=''
        
        ret = self.cmd('printenv %s' % variable, prompt_timeout=None)
        if ret is False: return ''
        
        ret, line = self.expect('%s=' % variable)
        if ret:
            m = re.match('.*=(?P<value>.*)', line)
            if m:
                value = m.group('value').strip()
                
        return value
