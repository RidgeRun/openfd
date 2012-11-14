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

import subprocess
import rrutils

# ==========================================================================
# Private Functions
# ==========================================================================

def device_exists(device):
    """
    Returns true if the device exists, false otherwise.
    """
    
    exists = True
    
    cmd = 'sudo fdisk -l ' + device + ' 2>/dev/null'
    
    output = subprocess.check_output(cmd, shell=True)
    if output == "":
        exists = False
        
    return exists
    
    
def is_mounted(device):
    pass

# ==========================================================================
# Public Functions
# ==========================================================================

def format_sd():
    pass


if __name__ == '__main__':

    # Check device existence (positive test case)
    
    device = "/dev/sdb1"    
    if device_exists(device):
        print "Device " + device + " exists."
    else:
        print "Device " + device + " doesn't exist."
    
    # Check device existence (negative test case)
        
    device = "/dev/sdbX"    
    if device_exists(device):
        print "Device " + device + " exists."
    else:
        print "Device " + device + " doesn't exist."
