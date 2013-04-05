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
# Common utility functions used accross the installer. 
#
# ==========================================================================

"""
Common utility functions used accross the installer.

Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
All Rights Reserved.

The contents of this software are proprietary and confidential to RidgeRun,
LLC.  No part of this program may be photocopied, reproduced or translated
into another programming language without prior written consent of 
RidgeRun, LLC.
"""

# ==========================================================================
# Functions
# ==========================================================================

def hex_format(decimal_value, width=8, upper=True):
    """
    Returns the given decimal value as hex of given width (left zeros
    will be appended). After meeting the width requirement, the
    prefix '0x' will be added.
    
    Use the upper switch to have the hexadecimal value all in upper case.
    
    Example:
    
      Suppose the decimal value 3:
      
        width = 1 -> returns 0x3
        width = 2 -> returns 0x03
        ...
        width = 8 -> returns 0x00000003 
    """
    
    hex_value = hex(int(decimal_value))[2:] # remove the '0x' prefix
    hex_value = hex_value.zfill(width)
    if upper:
        hex_value = hex_value.upper()
   
    return '0x' + hex_value

hex_addr = hex_format

def str_to_hex(value, upper=True):
    """
    Converts the string that may contain a decimal number (like '12'), or
    a hexadecimal number (like '0xC', or 'c'), into a hexadecimal number
    (like '0xc').
    
    Use the upper switch to have the hexadecimal value all in upper case.
    """
    
    if not value: return ''
    
    hex_value = value
    if value.upper().find('0X') == -1:
        try:
            hex_value = hex(int(value))
        except ValueError:
            hex_value = hex(int(value, base=16))
        
    if upper:
        hex_value = '0x' + hex_value.upper().replace('0X', '')
        
    return hex_value
    
# ==========================================================================
# Test cases
# ==========================================================================
        
if __name__ == '__main__':
    
    print str_to_hex('12')
    print str_to_hex('0xC')
    print str_to_hex('C')
        