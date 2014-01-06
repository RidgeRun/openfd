#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# CLI arguments checking support.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import hexutils
import socket

# ==========================================================================
# Checks
# ==========================================================================

class ArgCheckerError(Exception):
    """ArgChecker exceptions."""

class ArgChecker(object):
    """Class to verify CLI arguments."""
    
    def is_dir(self, dirname, arg):
        if not os.path.isdir(dirname):
            raise ArgCheckerError('Unable to find %s: %s' % (arg, dirname))
    
    def is_file(self, filename, arg):
        if not os.path.isfile(filename):
            raise ArgCheckerError('Unable to find %s: %s' % (arg, filename))
    
    def x_ok(self, filename, arg):
        if not os.access(filename, os.X_OK):
            raise ArgCheckerError('No execution permissions on %s: %s' %
                                (arg, filename))
    
    def is_int(self, val, arg):
        try:
            int(val)
        except ValueError:
            raise ArgCheckerError('%s must be an integer (%s)' % (arg, val))
    
    def is_valid_addr(self, addr, arg):
        if not hexutils.is_valid_addr(addr):
            raise ArgCheckerError('Invalid address on %s: %s' % (arg, addr))
    
    def is_valid_ipv4(self, ip, arg):
        try:
            socket.inet_aton(ip)
        except socket.error:
            raise ArgCheckerError('Invalid IP address on %s: %s' % (arg, ip))
