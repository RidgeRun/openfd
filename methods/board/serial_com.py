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

import serial

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
        """
        
        self._port = serial.Serial(port=port, baudrate=baud, timeout=timeout)

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
        
        while self._port.readline().strip('\s\r\n') != response:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                return False
            
        return True

# ==========================================================================
# Test cases
# ==========================================================================

if __name__ == '__main__':

# ==========================================================================
# Test cases  - Support functions
# ==========================================================================

    import time

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

    inst = SerialInstaller('/dev/ttyUSB0', 115200)
