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
    Serial communication operations to support the installer.
    
    Attributes:
        _port: A Serial port instance for serial communication. 
    """
    
    def __init__(self, port='/dev/ttyS0', baud=115200, timeout=2):
        """
        Constructor.
        
        Raises:
            SerialException: On error while opening the serial port.
        """
        
        self._logger = rrutils.logger.get_global_logger()
        try:
            self._port = serial.Serial(port=port,
                                       baudrate=baud,
                                       timeout=timeout)
        except serial.SerialException as e:
            self._logger.debug(e)
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
            Returns true if the response is found; false otherwise.
        """
        
        start_time = time.time()
        
        try:
            while self._port.readline().strip('\s\r\n') != response:
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    return False
        except serial.SerialException as e:
            self._logger.debug(e)
            return False
            
        return True

    def uboot_sync(self):
        """
        Synchronizes with uboot. If successful, uboot's prompt will 
        be ready to receive commands.
            
        Returns:
            Returns true on success; false otherwise.
        """
    
        self._port.flush()
        self._port.write('echo resync\n')
        if not self.__expect('resync'):
            msg = SerialInstaller.com_error_msg(self._port.port)
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
        inst = SerialInstaller(port, 115200)
    except:
        print SerialInstaller.com_error_msg(port)
        sys.exit(-1)
    
    # --------------- TC 2 ---------------
    
    tc_start(2)
    
    # Handshake with uboot
    
    if inst.uboot_sync():
        print 'Synchronized with uboot'
    else:
        print 'Failed to sync with uboot'
    
