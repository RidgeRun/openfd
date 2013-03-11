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
import sdcard
import rrutils
import sys

# ==========================================================================
# Public Classes
# ==========================================================================

class FilesystemInstaller:
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
        self._uflash_bin  = ''
        self._executer.set_logger(self._logger)
        self._sd_installer = sdcard.SDCardInstaller()
        # This flag will tell the methods to continue only if
        # partitions info is already set.
        self._sd_info_set = False 
        
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
    
    def set_sd_info(self,sdcard_mmap_filename):
        """
        Sets the sd partitions info. 
        """
        if self._sd_info_set:
            self._logger.info("SD partitions info was already set,\
                             try unsetting it next time.")
        if not os.path.isfile(sdcard_mmap_filename):
            self._logger.error('Unable to find ' + sdcard_mmap_filename)
            return False
        if not self._sd_installer.read_partitions(sdcard_mmap_filename):
            self._logger.error('Failed to read partitions info')
            return False
        self._logger.info("Sd partitions info successfully setted.")
        self._sd_info_set = True
        return True
    
    def unset_sd_info(self):
        """
        Unsets the _sd_info_set flag for setting new info.
        """
        self._sd_info_set = False
    
    def set_workdir(self,workdir):
        """
        Sets the path to the directory where to create temporary files
        and also mount devices.
        """
        self._workdir = workdir
    
    def get_workdir(self):
        """
        Gets the working directory.
        """
        return self._workdir
    
    def install_filesystem(self, fs_path, device, part_num):
        """
        Installs the filesystem on the device given.
        """
        # We should get sure that the device exists.
        if not self._sd_installer.device_exists(device):
            return False
        # Now that we know that the device exist let's get the device info.
        dev_info = self._sd_installer.get_dev_info(device)
        # Now it is convinient to get the real partition suffix.
        part_suffix = self._sd_installer.get_partition_suffix(device, part_num)
        # Now that we have this info, let's create a mount point for the partition.
        # For this we will use self._workdir and the real label of the partition.
        m_point = self._workdir + "/" + dev_info[device+part_suffix]["label"]
        
        if not self._check_sd_mounted(device,part_suffix, m_point):
            return False
        if self._executer.check_call("cd "+fs_path+" ; find . | sudo cpio -pdum "+m_point) != 0:
            self._logger.error('Failed to fs to ' +  m_point)
            return False
        return True
    
    def _check_sd_mounted(self,device,part_suffix,m_point):
        """
        Checks that the given device is mounted, if not it will try to mount
        it on self._workdir. 
        """
        if not self._sd_installer.device_is_mounted(device):
            if not self._sd_installer.mount_partitions(device, self._workdir):
                self._logger.error('Failed to mount '+device+" on "+self._workdir)
                return False
        
        # Now we check that the device is mounted where we want it to be.
        # This will only work if dryrun is setted to false.
        if not self._dryrun:
            partition = device + part_suffix
            current_mpoint = self._sd_installer.get_mpoint(partition)
            if m_point != current_mpoint:
                self._logger.error('Device is not mounted on '+ m_point \
                                   +' and not on '+m_point+' as expected.')
                return False
        else:
            pass
        return True
    
    def check_fs(self,device):
        self._sd_installer.check_fs(device)

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
    
    device = "/dev/sdb"
    fs_installer.set_dryrun(True)
    
# ==========================================================================
# Test cases - Unit tests
# ==========================================================================

    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0) 
    
    # Check device existence (positive test case)
    
    # Try to set sd partitions info.
    
    sdcard_mmap_filename = devdir + '/images/sd-mmap.config'
    if not fs_installer.set_sd_info(sdcard_mmap_filename):
        print "SD partitions info could not be setted... Exiting"
        sys.exit(-1)
    
    # Try to install filesystem on the sd.
    
    fs_installer.set_workdir(devdir + '/images')
    
    fs_path = devdir + "/fs/fs"
    part_num = 2
    
    if fs_installer.install_filesystem(fs_path,device,part_num):
        print "Fs successfully installed on " + device + str(part_num)
    else:
        print "Error installing fs on " + device + str(part_num)
        sys.exit(-1)
    
    # Let's check that the filesystem is ok.
    print "Checking fs..."
    fs_installer.check_fs(device)
    
    print "Test cases finished"
