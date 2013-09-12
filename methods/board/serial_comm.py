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

import time
import os
import re
import serial
import rrutils

# ==========================================================================
# Constants
# ==========================================================================

DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUDRATE = 115200
DEFAULT_READ_TIMEOUT = 2
DEFAULT_TFTP_DIR = '/srv/tftp'
DEFAULT_TFT_PORT = 69

# ==========================================================================
# Public Classes
# ==========================================================================

class SerialInstaller(object):
    """
    Serial communication operations to support the installer. Based on
    pySerial.
    """
    
    def __init__(self, nand_block_size=0, nand_page_size=0,
                 force_install=False, uboot_dryrun=False, dryrun=False):
        """
        :param nand_block_size: NAND block size (bytes). If not given, the
            value will be obtained from uboot (once).
        :param nand_page_size: NAND page size (bytes). If not given, the
            value will be obtained from uboot (once).
        :param uboot_dryrun: Enable uboot dryrun mode. Uboot commands will be
            logged, but not executed.
        :type uboot_dryrun: boolean
        :param dryrun: Enable dryrun mode. System commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._executer.logger = self._logger
        self._port = None
        self._nand_block_size = nand_block_size
        self._page_page_size = nand_page_size
        self._force_install = force_install
        self._uboot_prompt = ''
        self._uboot_dryrun = uboot_dryrun
        self._dryrun = dryrun

    @classmethod
    def uboot_comm_error_msg(cls, port):
        """
        Standard error message to report a failure communicating with uboot
        in the given port.
        
        :param port: The port for which communication failed.
        :return: A string with the standard message.
        """
        
        return ('Failed to handshake with uboot.\n'
               'Be sure u-boot is active on port %s and you have terminal '
               'programs like minicom closed.' % port)
    
    @property
    def port(self):
        """
        Serial port instance. It may be None if no serial port
        has been opened using open_comm().
        """
        
        return self._port
    
    def __set_force_install(self, force_install):
        self._force_install = force_install
        
    def __get_force_install(self):
        return self._force_install
    
    force_install = property(__get_force_install, __set_force_install,
                     doc="""Forces the requested installation.""")
    
    def __set_uboot_dryrun(self, dryrun):
        self._uboot_dryrun = dryrun
    
    def __get_uboot_dryrun(self):
        return self._uboot_dryrun
    
    uboot_dryrun = property(__get_uboot_dryrun, __set_uboot_dryrun,
                     doc="""Enable uboot dryrun mode. Uboot commands will be
                     logged, but not executed.""")
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._executer.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System commands will be
                     logged, but not executed.""")

    def __set_nand_block_size(self, size):
        self._nand_block_size = int(size)

    def __get_nand_block_size(self):
        
        # Don't query uboot if already set
        
        if self._nand_block_size != 0:
            return self._nand_block_size
        
        # Ask uboot
        
        if self._check_open_port() is False: return 0
        
        ret = self.uboot_cmd('nand info')
        if ret is False: return False
            
        ret, line = self.expect('Device 0')
        if not ret:
            self._logger.error('Can\'t find Device 0')
            return self._nand_block_size
        
        self._logger.debug('NAND info: %s' % line)
        
        # Two versions of uboot output:
        # old: Device 0: Samsung K9K1208Q0C at 0x2000000 (64 MB, 16 kB sector)
        # new: Device 0: NAND 256MiB 1,8V 16-bit, sector size 128 KiB
        
        m = re.match('.* (?P<size_kb>\d+) (kb|kib).*', line, re.IGNORECASE)
        if m:
            size_kb = int(m.group('size_kb'))
        else:
            self._logger.error('Unable to determine the NAND block size')
        self._nand_block_size = size_kb << 10
        self._logger.debug('NAND block size: %d bytes' % self._nand_block_size)
        return self._nand_block_size
    
    nand_block_size = property(__get_nand_block_size, __set_nand_block_size, 
                           doc="""NAND block size (bytes). The value will be
                           obtained from uboot (once), unless manually
                           specified.""")
    
    def __set_nand_page_size(self, size):
        self._nand_page_size = int(size)
    
    def __get_nand_page_size(self):
        
        # Don't query uboot if already set
        
        if self._nand_page_size != 0:
            return self._nand_page_size
        
        # Ask uboot
        
        if self._check_open_port() is False: return 0
        
        page_size = 0
        possible_sizes=['0200', '0400', '0800', '1000']
        
        for size in possible_sizes:
            
            ret = self.uboot_cmd('nand dump.oob %s' % size)
            if ret is False: return False
            
            ret, line = self.expect('Page 0000')
            if not ret: continue
            
            # Detect the page size upon a change on the output
            m = re.match('^Page 0000(?P<page_size>\d+) .*', line)
            if m:
                page_size = int(m.group('page_size'), 16)
                if page_size != 0:
                    break

        if page_size == 0:
            self._logger.error('Unable to determine the NAND page size')
        else:
            self._nand_page_size = page_size
            self._logger.debug('NAND page size: %d bytes' %
                               self._nand_page_size)
        return self._nand_page_size
    
    nand_page_size = property(__get_nand_page_size, __set_nand_page_size,
                          doc="""NAND page size (bytes). The value will be
                           obtained from uboot (once), unless manually
                           specified.""")

    def _check_open_port(self):
        """
        Checks if the port is opened.
        """
        
        if self._port is None:
            self._logger.error('No opened port (try open_comm() first)')
            return False
        else:
            return True

    def open_comm(self, port=DEFAULT_PORT,
                  baud=DEFAULT_BAUDRATE,
                  timeout=DEFAULT_READ_TIMEOUT):
        """
        Opens the communication with the Serial port.
        
        :param port: Device name or port number (i.e. '/dev/ttyS0')
        :type port: string
        :param baud: Baud rate such as 9600 or 115200 etc
        :param timeout: Set a read timeout value
        :return: Returns true on success; false otherwise.
        :exception SerialException: On error while opening the serial port.
        """
        
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
        
        # Open the serial port
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

    def expect(self, response, timeout=5):
        """
        Expects a response from the serial port for no more than timeout
        seconds.
        
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
        
        found = False
        line = ''
        start_time = time.time()
        
        if self._check_open_port() is False: return False, ''
        
        while not found:
            
            try:
                line = self._port.readline().strip(' \r\n')
            except (serial.SerialException, OSError) as e:
                self._logger.error(e)
                return False, ''
            
            if response in line:
                found = True
                break
            
            if (time.time() - start_time) > timeout:
                break

        return found, line

    def uboot_sync(self):
        """
        Synchronizes with uboot. If successful, uboot's prompt will 
        be ready to receive commands after this call.
            
        :return: Returns true on success; false otherwise.
        """
    
        if self._check_open_port() is False: return False
    
        self._port.flush()
        self._port.write('echo resync\n')
        self.expect('echo resync') # Ignore the echo
        ret = self.expect('resync', timeout=1)[0]
        if not ret:
            msg = SerialInstaller.uboot_comm_error_msg(self._port.port)
            self._logger.error(msg)
            return False
        
        # Identify the prompt in the following line
        try:
            line = self._port.readline().strip(' \r\n')
        except (serial.SerialException, OSError) as e:
            self._logger.error(e)
            return False, ''
        
        m = re.match('(?P<prompt>.*) $', line)
        if m:
            self._uboot_prompt = m.group('prompt').strip()
            self._logger.debug('Uboot prompt: %s' % self._uboot_prompt)

        return True
    
    def uboot_cmd(self, cmd, echo_timeout=5, prompt_timeout=5):
        """
        Sends a command to uboot.
        
        :param cmd: Command.
        :param echo_timeout: Timeout to wait for the command to be echoed. Set
            to None to avoid waiting for the echo.
        :type echo_timeout: integer or none
        :param prompt_timeout: Timeout to wait for the prompt after sending
            the command. Set to None to avoid waiting for the prompt.
        :type prompt_timeout: integer or none
        :returns: Returns true on sucess; false otherwise.
        """
        
        self._logger.info("Uboot: '%s'" % cmd.strip())
        
        if not self._uboot_dryrun and self._port:
        
            self._port.write('%s\n' % cmd)
            time.sleep(0.1)
            
            # Wait for the echo
            if echo_timeout:
                ret, line = self.expect(cmd, echo_timeout)
                if ret is False:
                    self._logger.error("Uboot didn't echo the command, maybe "
                        "it froze. This is the log of the last command: %s" %
                        line)
                    return False
        
            # Wait for the prompt
            if self._uboot_prompt and prompt_timeout:
                ret = self.expect(self._uboot_prompt, timeout=prompt_timeout)
                if ret is False:
                    self._logger.error("Didn't get the uboot prompt back. "
                       "This is the log of the last command: %s" % line)
                    return False
        
        return True

    def _check_icache(self):
        """
        Checks availability of the 'icache' uboot command.
        """
        
        ret = self.uboot_cmd('icache')
        if ret is False: return False 
        
        ret = self.expect('Instruction Cache is')[0]
        if ret is False:
            self._logger.error("Your uboot doesn't have icache command, "
               "refusing to continue due risk of hanging.\nYou can update "
               "your bootloader by other means like SD card or use"
               " --force_install=yes")
            return False
        return True
    
    def _uboot_env(self, variable):
        """
        Reads the value of the u-boot env variable.
        """
        
        value=''
        
        if not self.uboot_cmd('printenv', prompt_timeout=None): return ''
        
        ret, line = self.expect('%s=' % variable)
        if ret:
            m = re.match('.*=(?P<value>.*)', line)
            if m:
                value = m.group('value').strip()

        return value

    def _load_file_to_ram(self, filename):
        raise NotImplementedError

    def install_bootloader(self):
        
        ret = self._uboot_sync()
        if ret is False: return False
        
        ret = self._check_icache()
        if ret is False and not self._force_install: return False
        
        prev_bootcmd = self._uboot_env('bootcmd')
        
        ret = self.uboot_cmd('setenv bootcmd')
        if ret is False: return False
        
        ret = self.uboot_cmd('saveenv')
        if ret is False: return False
        
        self._load_file_to_ram()
        
        return True

class SerialInstallerTFTP(SerialInstaller):
    
    """
    Serial communication operations to support the installer using TFTP.
    """
    
    #: Static networking mode.
    MODE_STATIC = 'static'
    
    #: DHCP networking mode.
    MODE_DHCP = 'dhcp'
    
    def __init__(self, nand_block_size=0, nand_page_size=0, host_ipaddr='',
                 target_ipaddr='', tftp_dir=DEFAULT_TFTP_DIR,
                 tftp_port=DEFAULT_TFT_PORT, net_mode=MODE_DHCP,
                 force_install=False, uboot_dryrun=False, dryrun=False):
        """
        :param nand_block_size: NAND block size (bytes). If not given, the
            value will be obtained from uboot (once).
        :param nand_page_size: NAND page size (bytes). If not given, the
            value will be obtained from uboot (once).
        :param host_ipaddr: Host IP address.
        :param target_ipaddr: Target IP address, only necessary
            in :const:`MODE_STATIC`.
        :param tftp_dir: TFTP root directory.
        :param tftp_port: TFTP server port.
        :type tftp_port: integer
        :param net_mode: Networking mode. Possible values:
            :const:`MODE_STATIC`, :const:`MODE_DHCP`. 
        :param force_install: Forces the requested installation.
        :type force_install: boolean
        :param uboot_dryrun: Enable uboot dryrun mode. Uboot commands will be
            logged, but not executed.
        :type uboot_dryrun: boolean
        :param dryrun: Enable dryrun mode. System commands will be logged,
            but not executed.
        :type dryrun: boolean
        """    
        SerialInstaller.__init__(self, nand_block_size, nand_page_size,
                                 force_install, uboot_dryrun, dryrun)
        self._tftp_dir = tftp_dir
        self._tftp_port = tftp_port
        self._net_mode = net_mode
        self._host_ipaddr = host_ipaddr
        self._target_ipaddr = target_ipaddr
        
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
        Checks TFTP settings (dir and port).
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

    def _load_file_to_ram(self):
        pass
    
    def _setup_uboot_network(self):
        """
        Setup networking for uboot.
        
        Returns true on success; false otherwise.
        """
        
        self._logger.info('Configuring uboot network')
        if self._net_mode == SerialInstallerTFTP.MODE_STATIC:
            if not self._target_ipaddr:
                self._logger.error('No IP address specified for the target')
                return False
            ret = self.uboot_cmd('setenv ipaddr %s' % self._target_ipaddr)
            if ret is False: return False
        elif self._net_mode == SerialInstallerTFTP.MODE_DHCP:
            ret = self.uboot_cmd('setenv autoload no')
            if ret is False: return False
    
        ret = self.uboot_cmd('setenv serverip %s' % self._host_ipaddr)
        if ret is False: return False
        
        return True
