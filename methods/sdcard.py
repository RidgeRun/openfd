# ==========================================================================
#
# Copyright (C) 2012 Ridgerun (http://www.ridgerun.com).
#
# SD-card operations to support the installer.
#
# ==========================================================================

"""
SD-card operations to support the installer.

Copyright (C) 2012 Ridgerun (http://www.ridgerun.com).
"""

# ==========================================================================
# Imports
# ==========================================================================

import rrutils

# ==========================================================================
# Public Classes
# ==========================================================================

class SDCardInstaller:
    """
    Class to handle SD-card operations.
    """

    def __init__(self):
        """
        Constructor.
        """
        
        self._config   = rrutils.config.get_global_config()
        self._logger   = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._dryrun   = False
        
    def set_logger(self, logger):
        """
        Sets the logger to use
        """
        
        self._logger = logger
        self._executer.set_logger(logger)
        
    def set_dryrun(self, dryrun):
        """
        Sets on/off the dryrun mode. In dryrun mode any commands will
        not be executed.
        """
        
        self._dryrun = dryrun
        self._executer.set_dryrun(dryrun)
        
    def device_exists(self, device):
        """
        Returns true if the device exists, false otherwise.
        """
        
        ret     = 0
        output  = ''
        exists  = True
        
        cmd = 'sudo fdisk -l ' + device + ' 2>/dev/null'
        
        ret, output = self._executer.check_output(cmd)
        
        if output == "":
            exists = False
            
        return exists
    
    def device_is_mounted(self, device):
        """
        Returns true if the device is mounted or if it's part of RAID array,
        false otherwise.
        """
        
        is_mounted = False
        
        cmd1 = 'grep --quiet ' + device + ' /proc/mounts'
        cmd2 = 'grep --quiet ' + device + ' /proc/mdstat'
        
        if self._executer.check_call(cmd1) == 0: is_mounted = True
        if self._executer.check_call(cmd2) == 0: is_mounted = True
        
        return is_mounted

if __name__ == '__main__':

    # Initialize global config and logger
    
    rrutils.logger.basic_config()
    logger = rrutils.logger.get_global_logger('sdcard-test')
    
    sd_installer = SDCardInstaller()
    sd_installer.set_logger(logger)
    

    # Check device existence (positive test case)
    
    device = "/dev/sdb1"    
    if sd_installer.device_exists(device):
        print "Device " + device + " exists."
    else:
        print "Device " + device + " doesn't exist."
    
    # Check device existence (negative test case)
        
    device = "/dev/sdbX"    
    if sd_installer.device_exists(device):
        print "Device " + device + " exists."
    else:
        print "Device " + device + " doesn't exist."

    # Check if the device is mounted (positive test case)
    
    device = "/dev/sdb1"
    if sd_installer.device_is_mounted(device):
        print "Device " + device + " is mounted."
    else:
        print "Device " + device + " isn't mounted."
        
    # Check if the device is mounted (negative test case)
    
    device = "/dev/sdbX"
    if sd_installer.device_is_mounted(device):
        print "Device " + device + " is mounted."
    else:
        print "Device " + device + " isn't mounted."
    
