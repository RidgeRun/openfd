#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
# Author: Diego Benavides <diego.benavides@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# Filesystem related operations to support the installer.
#
# ==========================================================================

"""
Bootloader related operations to support the installer.

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

import os
import rrutils
import sys

# ==========================================================================
# Public Classes
# ==========================================================================

class FilesystemInstaller(object):
    """
    Class to handle Filesystem-related operations.
    """
    
    def __init__(self):
        """
        Constructor.
        """
        
        self._logger      = rrutils.logger.get_global_logger()
        self._executer    = rrutils.executer.Executer()
        self._dryrun      = False
        self._workdir     = None
        self._rootfs      = None
        self._executer.set_logger(self._logger)
        
    def set_dryrun(self, dryrun):
        """
        Sets on/off the dryrun mode. In dryrun mode any commands will
        not be executed (just logged).
        """
        
        self._dryrun = dryrun
        self._executer.set_dryrun(dryrun)
    
    def get_dryrun(self):
        """
        Returns true if the dryrun mode is on; false otherwise.
        """
        
        return self._dryrun
    
    def set_workdir(self, workdir):
        """
        Sets the path to the workdir.
        """
        self._workdir = workdir
        
    def get_workdir(self):
        """
        Gets the path to the kernel_image.
        """
        
        return self._workdir
    
    def set_rootfs(self, rootfs):
        """
        Sets the path to the directory that contains the rootfs that will be
        installed. Set to None if this installation does not require a rootfs.
        """
        self._rootfs = rootfs

    def get_rootfs(self):
        """
        Gets the path to the directory that contains the rootfs that will be
        installed. If None, a rootfs was not specified, more likely because
        this installation does not require rootfs, i.e. NFS will be used. 
        """
        return self._rootfs
    
    def generate_rootfs_partition(self, mount_point):
        """
        If any, installs the filesystem on the mount point given.
        Returns True on success, False otherwise.
        """
        
        if self._rootfs:
        
            cmd = "cd " + self._rootfs + " ; find . | sudo cpio -pdum " + mount_point
            
            if self._executer.check_call(cmd) != 0:
                err_msg = 'Failed installing rootfs into ' +  mount_point
                self._logger.error(err_msg)
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

    # Devdir info
    devdir = ''
    
    try:
        if os.environ['DEVDIR']:
            devdir = os.environ['DEVDIR'] 
    except KeyError:
        print 'Unable to obtain $DEVDIR from the environment.'
        exit(-1)

    # Initialize the logger
    rrutils.logger.basic_config(verbose=True)
    logger = rrutils.logger.get_global_logger('sdcard-test')
    
    fs_installer = FilesystemInstaller()
    
    # The following test cases will be run over the following device,
    # in the given dryrun mode, unless otherwise specified in the test case.
    
    # WARNING: Dryrun mode is set by default, but be careful
    # you don't repartition or flash a device you don't want to.
    
    fs_installer.set_dryrun(True)
    
# ==========================================================================
# Test cases - Unit tests
# ==========================================================================

    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0) 
    
    rootfs = devdir + "/fs/fs"
    fs_installer.set_rootfs(rootfs)
    mount_point = "/media/rootfs"
        
    if fs_installer. generate_rootfs_partition(mount_point):
        print "Fs successfully installed on " + mount_point
    else:
        print "Error installing fs on " + mount_point
        sys.exit(-1)
    
    print "Test cases finished"
