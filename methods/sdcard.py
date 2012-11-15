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
        self._executer = rrutils.Executer()
        
    def device_exists(self, device):
        """
        Returns true if the device exists, false otherwise.
        """
        
        retcode = 0
        output  = ''
        exists = True
        cmd = 'sudo fdisk -l ' + device + ' 2>/dev/null'
        
        retcode, output = self._executer.check_output(cmd)
        
        if output == "":
            exists = False
            
        return exists

if __name__ == '__main__':

    # Initialize global config and logger
    
    rrutils.logger.get_global_logger('sdcard-test')
    
    sd_installer = SDCardInstaller()
    

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


