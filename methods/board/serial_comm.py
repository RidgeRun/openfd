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

"""
Serial communication operations to support the installer.

Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
All Rights Reserved.

The contents of this software are proprietary and confidential to RidgeRun,
LLC.  No part of this program may be photocopied, reproduced or translated
into another programming language without prior written consent of 
RidgeRun, LLC.
"""

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

DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUDRATE = 115200
DEFAULT_READ_TIMEOUT = 2

# ==========================================================================
# Public Classes
# ==========================================================================

class SerialInstaller(object):
    """
    Serial communication operations to support the installer. Based on
    pySerial.
    
    Attributes:
        port: A Serial port instance for serial communication. None if no
            serial port has been opened using open_comm().
        nand_block_size: The NAND block size will be retrieved from uboot
            by default. But if this property was manually set, uboot will
            not be queried, unless it is manually set back to the value 0.
        nand_page_size: The NAND page size will be retrieved from uboot
            by default. But if this property was manually set, uboot will
            not be queried, unless it is manually set back to the value 0.
        dryrun: When dryrun mode is set, all commands will be logged, but not
            executed.
    """
        
    def __init__(self):
        """
        Constructor.
        """
        
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._executer.logger = self._logger
        self._dryrun = False
        self._port = None
        self._nand_block_size = 0
        self._page_block_size = 0

    @classmethod
    def uboot_comm_error_msg(cls, port):
        """
        Standard error message to report a failure communicating with the given
        port.
        
        Args:
            port: The port for which communication failed.
            
        Returns:
            A string with the standard message.
        """
        
        return ('Failed to handshake with uboot.\n'
               'Be sure u-boot is active on port %s and you have terminal '
               'programs like minicom closed.' % port)
    
    @property
    def port(self):
        """
        Gets the Serial port instance. It may be None if no
        serial port has been opened using open_comm().
        """
        
        return self._port
    
    def check_open_port(self):
        """
        Checks if the serial port has been successfully opened.
        
        Returns:
            Returns true if the port is opened; false otherwise.
        """
        
        if self._port is None:
            self._logger.error('No opened port (try open_comm() first)')
            return False
        else:
            return True
    
    def __set_dryrun(self, dryrun):
        """
        Sets on/off the dryrun mode. In dryrun mode any commands will
        not be executed (just logged).
        """
        
        self._dryrun = dryrun
        self._executer.dryrun = dryrun
    
    def __get_dryrun(self):
        """
        Returns true if the dryrun mode is on; false otherwise.
        """
        
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Gets or sets the dryrun mode.""")

    def __set_nand_block_size(self, size):
        """
        Sets the NAND block size (bytes). When this value is manually set,
        uboot will not be queried. Set it back to 0 to obtain the NAND block
        size from uboot.
        """
        
        self._nand_block_size = int(size)

    def __get_nand_block_size(self):
        """
        Gets the NAND block size (bytes). The value will be obtained from
        uboot, unless it was manually specified through the nand_block_size
        property, and would return such value.
        
        Returns:
            The size in bytes of the NAND block size; 0 if it was unable
            to obtain it. 
        """
        
        # If specified, return the value set by the user
        if self._nand_block_size != 0:
            return self._nand_block_size
        
        # Ask uboot
        
        if self.check_open_port() is False: return 0
        
        self._port.write('nand info\n')
        ret, line = self.expect('Device 0')
        if not ret:
            self._logger.error('Can\'t find Device 0')
            return False
        
        self._logger.debug('NAND info: %s' % line)
        
        # Two versions of uboot output:
        # old: Device 0: Samsung K9K1208Q0C at 0x2000000 (64 MB, 16 kB sector)
        # new: Device 0: NAND 256MiB 1,8V 16-bit, sector size 128 KiB
        
        m = re.match('.* (?P<size_kb>\d+) (kb|kib).*', line, re.IGNORECASE)
        if m:
            size_kb = int(m.group('size_kb'))
        else:
            self._logger.error('Unable to determine the NAND block size')
        
        return size_kb << 10 
    
    nand_block_size = property(__get_nand_block_size, __set_nand_block_size, 
                           doc="""Gets or sets the NAND block size (bytes)""")
    
    def __set_nand_page_size(self, size):
        """
        Sets the NAND page size (bytes). When this value is manually set,
        uboot will not be queried. Set it back to 0 to obtain the NAND page
        size from uboot.
        """
        
        self._nand_page_size = int(size)
    
    def __get_nand_page_size(self):
        """
        Gets the NAND page size (bytes). The value will be obtained from
        uboot, unless it was manually specified through the nand_page_size
        property, and would return such value.
        
        Returns:
            The size in bytes of the NAND page size; 0 if it was unable
            to obtain it. 
        """
        
        # If specified, return the value set by the user
        if self._nand_page_size != 0:
            return self._nand_page_size
        
        # Ask uboot
        
        if self.check_open_port() is False: return 0
        
        page_size = 0
        possible_sizes=['0200', '0400', '0800', '1000']
        
        for size in possible_sizes:
            
            self._port.write('nand dump.oob %s\n' % size)
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

        return page_size
    
    nand_page_size = property(__get_nand_page_size, __set_nand_page_size,
                          doc="""Gets or sets the NAND page size (bytes)""")
    
    def open_comm(self, port=DEFAULT_PORT,
                  baud=DEFAULT_BAUDRATE,
                  timeout=DEFAULT_READ_TIMEOUT):
        """
        Opens the communication with the Serial port.
        
        Args:
            port: Device name or port number (i.e. /dev/ttyS0)
            baud: Baud rate such as 9600 or 115200 etc
            timeout: Set a read timeout value
            
        Returns:
            Returns true on success; false otherwise.
            
        Raises:
            SerialException: On error while opening the serial port.
        """
        
        # Terminal line settings
        cmd = ('stty -F %s %s intr ^C quit ^D erase ^H kill ^U eof ^Z '
               'eol ^J start ^Q stop ^S -echo echoe echok -echonl echoke '
               '-echoctl -istrip -icrnl -ocrnl -igncr -inlcr onlcr -opost '
               '-isig -icanon cs8 -cstopb clocal -crtscts -ixoff -ixon '
               '-parenb -parodd -inpck' % (port, baud))
        
        ret = self._executer.check_call(cmd)
        if ret != 0:
            self._logger.error('Couldn\'t change terminal line settings')
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

    def expect(self, response, timeout=5):
        """
        Expects a response from the serial port for no more than timeout
        seconds.
        
        The lines read from the serial port will be stripped (\s\r\n) before
        being compared with response.
        
        Args:
            response: A string to expect in the serial port.
            timeout: Timeout in seconds to wait for the response. 
            
        Returns:
            Returns a tuple with two items. The first one is true if the
            response was found; false otherwise. The second is the complete
            line where the response was found, or the last line read if the
            response wasn't found and the timeout reached. The line is
            returned stripped (\s\r\n).
        """
        
        found = False
        line = ''
        start_time = time.time()
        
        if self.check_open_port() is False: return False, ''
        
        while not found:
            
            try:
                line = self._port.readline().strip('\s\r\n')
            except serial.SerialException as e:
                self._logger.error(e)
                return False, ''
            
            if line.find(response) != -1:
                found = True
            
            if (time.time() - start_time) > timeout:
                break

        return found, line

    def uboot_sync(self):
        """
        Synchronizes with uboot. If successful, uboot's prompt will 
        be ready to receive commands.
            
        Returns:
            Returns true on success; false otherwise.
        """
    
        if self.check_open_port() is False: return False
    
        self._port.flush()
        self._port.write('echo resync\n')
        
        ret = self.expect('resync')[0]
        
        if not ret:
            msg = SerialInstaller.uboot_comm_error_msg(self._port.port)
            self._logger.error(msg)
            return False
        
        return True
    
# ==========================================================================
# Test cases
# ==========================================================================

if __name__ == '__main__':

# ==========================================================================
# Test cases  - Support functions
# ==========================================================================

    import sys

    def tc_start(tc_id, sleep_time=1):
        """
        Sleeps for 'sleep_time' and then prints the given test case header.
        """
        
        tc_header  = '=' * 20
        tc_header += 'TEST CASE ' + str(tc_id)
        tc_header += '=' * 20
        
        time.sleep(sleep_time)
        print tc_header

# ==========================================================================
# Test cases  - Initialization
# ==========================================================================

    # Initialize the logger
    rrutils.logger.basic_config(verbose=True)
    logger = rrutils.logger.get_global_logger('serial_com-test')
    logger.setLevel(rrutils.logger.DEBUG)

# ==========================================================================
# Test cases - Unit tests
# ==========================================================================
    
    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0) 
    
    # Open port (positive test case)

    inst = None
    port = '/dev/ttyUSB0'
    try:
        inst = SerialInstaller()
        if inst.open_comm(port='/dev/ttyUSB0', baud=115200):
            print 'Port %s opened' % port
        else:
            print 'Failed to open port %s' % port
            sys.exit(-1)
            
    except:
        print 'SerialException: Failed to open %s' % port
        sys.exit(-1)
    
    # --------------- TC 2 ---------------
    
    tc_start(2)
    
    # Handshake with uboot
    
    if inst.uboot_sync():
        print 'Synchronized with uboot'
    else:
        print 'Failed to sync with uboot'
    
    # --------------- TC 3 ---------------
    
    tc_start(3)
    
    # Get NAND dimensions

    # NAND block size

    inst.nand_block_size = 15
    size = inst.nand_block_size
    if size != 0:
        print "NAND block size (manual): 0x%x" % size
    else:
        print "Failed to obtain the NAND block size"
        
    inst.nand_block_size = 0 # Force to query uboot
    size = inst.nand_block_size
    if size != 0:
        print "NAND block size (uboot): 0x%x" % size
    else:
        print "Failed to obtain the NAND block size"
    
    # NAND page size
    
    inst.nand_page_size = 15
    size = inst.nand_page_size
    if size != 0:
        print "NAND page size (manual): %d" % size
    else:
        print "Failed to obtain the NAND page size"
        
    inst.nand_page_size = 0 # Force to query uboot
    size = inst.nand_page_size
    if size != 0:
        print "NAND page size (uboot): %d" % size
    else:
        print "Failed to obtain the NAND page size"
    