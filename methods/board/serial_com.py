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
import serial
import rrutils

# ==========================================================================
# Public Classes
# ==========================================================================

class SerialInstaller(object):
    """
    Serial communication operations to support the installer. Based on
    pySerial.
    
    Attributes:
        _port: A Serial port instance for serial communication. 
    """
    
    def __init__(self, port='/dev/ttyS0', baud=115200, timeout=2):
        """
        Constructor.
        
        Args:
            port: Device name or port number (i.e. /dev/ttyS0)
            baud: Baud rate such as 9600 or 115200 etc
            timeout: Set a read timeout value
        
        Raises:
            SerialException: On error while opening the serial port.
        """
        
        self._logger = rrutils.logger.get_global_logger()
        
        # Open the serial port
        try:
            self._port = serial.Serial(port=port,
                                       baudrate=baud,
                                       timeout=timeout)
        except serial.SerialException as e:
            self._logger.error(e)
            raise e

    @classmethod
    def com_error_msg(cls, port):
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

    def __expect(self, response, timeout=5):
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
        
        start_time = time.time()
        
        found = False
        line = ''
        
        while not found:
            
            try:
               msg = line = self._port.readline().strip('\s\r\n')
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
    
        self._port.flush()
        self._port.write('echo resync\n')
        
        ret = self.__expect('resync')[0]
        
        if not ret:
            msg = SerialInstaller.com_error_msg(self._port.port)
            self._logger.error(msg)
            return False
        
        return True 

    def get_nand_block_size(self):
        
        self._port.write('nand info\n')
        ret, line = self.__expect('Device 0')
        
        if not ret:
            self._logger.error('Can\'t find Device 0')
            return False
        
        self._logger.debug('NAND info: %s' % line)
        
        # Two versions of uboot output:
        # old: Device 0: Samsung K9K1208Q0C at 0x2000000 (64 MB, 16 kB sector)
        # new: Device 0: NAND 256MiB 1,8V 16-bit, sector size 128 KiB
        
        # Old - not necessary for now
        
        # New - TODO
        
 
        
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
        inst = SerialInstaller(port, 115200)
        print "Port %s opened" % port
    except:
        print 'Failed to open %s' % port
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

    inst.get_nand_block_size()
