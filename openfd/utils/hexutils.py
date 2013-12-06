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
# The hexutils module provides useful utilities for hex numbers manipulation.
#
# ==========================================================================

"""
The hexutils module provides useful utilities for hex numbers and hex
addresses manipulation.
"""

# ==========================================================================
# Functions
# ==========================================================================

def hex_format(decimal_value, width=8, upper=True):
    """
    Converts the given decimal value as hex of given width (left zeros
    will be appended if needed). After meeting the width requirement, the
    prefix '0x' will be added. Use the upper switch to have the hexadecimal
    value all in upper case.
    
    For a width example, suppose the decimal value 3:
    ::
        width = 0 -> returns 0x3
        width = 1 -> returns 0x3
        width = 2 -> returns 0x03
        ...
        width = 8 -> returns 0x00000003
        
    :param decimal_value: Decimal value to convert.
    :type decimal_value: string or integer
    :param width: Width of the resulting hexadecimal number.
    :param upper: Converts all hexadecimal digits to upper case.
    :returns: The converted hex string, prefixed with `0x`. 
    """
    
    hex_value = hex(int(decimal_value))[2:] # remove the '0x' prefix
    if width:
        hex_value = hex_value.zfill(width)
    if upper:
        hex_value = hex_value.upper()
    return '0x%s' % hex_value

#: Alias for :func:`hex_format` 
hex_addr = hex_format

def str_to_hex(value, upper=True):
    """
    Converts the string that may contain a decimal number (like '12'), or
    a hexadecimal number (like '0xC', or 'c'), into a hexadecimal number
    (like '0xc'). Use the upper switch to have the hexadecimal value all in
    upper case.
    
    :param value: Decimal or hexadecimal value to convert.
    :type value: string
    :param upper: Converts all hexadecimal digits to upper case.
    :returns: The converted hex string, prefixed with `0x`, or empty if
        that given value is not decimal nor hexadecimal.
    """
    
    if not value: return ''
    
    hex_value = value
    try:
        hex_value = hex(int(value))
    except ValueError:
        try:
            hex_value = hex(int(value, base=16))
        except ValueError:
            # This is not a valid value
            return ''
    if upper:
        hex_value = '0x%s' % hex_value.upper().replace('0X', '')
    return hex_value

#: Alias for :func:`str_to_hex`
to_hex = str_to_hex

def is_valid_addr(addr):
    """
    Returns true if the given address in decimal or hexadecimal (`'0x'` prefix)
    is valid.
    
    :param addr: Address to verify (i.e. `'0x82000000'`).
    :type addr: string
    :returns: Returns true if the address is valid; false otherwise. 
    """
    
    return True if str_to_hex(addr) else False
