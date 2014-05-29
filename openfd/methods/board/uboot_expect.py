#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Communication with Uboot using pexpect to support the installer.
#
# ==========================================================================

import pexpect
import openfd.utils as utils

# Serial settings
DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUDRATE = 115200
DEFAULT_READ_TIMEOUT = 2 # seconds

# Uboot communication timeouts (seconds)
DEFAULT_UBOOT_TIMEOUT = 5

class UbootExpect(object):
    """
    Class that abstracts the communication with uboot using a console.
    Based on pexpect.
    """
    
    def __init__(self, dryrun=False):
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._child = None
        self._dryrun = dryrun
        self._e.dryrun = dryrun
    
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System and uboot commands will
                     be logged, but not executed.""")
    
    def open_comm(self, cmd, timeout=DEFAULT_READ_TIMEOUT):
        """
        Opens the communication with the console where uboot is active.
        It's a good practice to call :func:`sync` after opening the port.
        
        :param cmd: Command to spawn
        :param timeout: Set a read timeout value
        :return: Returns true on success; false otherwise.
        :exception ?: On error while spawning the child program.
        """
        
        self._child = pexpect.spawn(cmd)
        return True
        
    def close_comm(self):
        """
        Closes the communication with the Serial port immediately.
        """
        
        if self._child:
            self._child.close(force=True)
            self._child = None
        
    

    