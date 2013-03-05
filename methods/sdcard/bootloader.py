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
# Bootloader related operations to support the installer.
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
import ConfigParser
import rrutils
import shutil

# ==========================================================================
# Public Classes
# ==========================================================================

class BootloaderInstaller:
    """
    Class to handle bootloader-related operations.
    
    Uses the uflash tool (Linux commmand tool specific to TI's Davinci
    platforms) for flashing UBL (User Boot Loader), u-boot and u-boot
    Environment in the MMC/SDcard.
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
        
    def set_uflash_bin(self, uflash_bin):
        """
        Sets the path to the uflash tool.
        """
        
        self._uflash_bin = uflash_bin
        
    def get_uflash_bin(self):
        """
        Gets the path to the uflash tool.
        """
        
        return self._uflash_bin
        
    def flash(self, device, ubl_file, uboot_file, uboot_entry_addr,
              uboot_load_addr):
        """
        Flashes UBL and U-Boot to the given device, using the uflash tool.
        
        Returns true on success; false otherwise.
        """
        
        if not self._uflash_bin:
            self._logger.error('No path to uflash specified')
            return False
        
        cmd = 'sudo ' + self._uflash_bin + \
              ' -d ' + device + \
              ' -u ' + ubl_file + \
              ' -b ' + uboot_file + \
              ' -e ' + str(hex(int(uboot_entry_addr))) + \
              ' -l ' + str(hex(int(uboot_load_addr)))

        self._logger.info('Flashing UBL and U-Boot to ' + device)
        if self._executer.check_call(cmd) != 0:
                self._logger.error('Failed to flash UBL and U-Boot into ' +
                                   device)
                return False

        return True
    
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
    
    def set_bootargs(self,bootargs):
        """
        Sets the boot args used when generating the uboot env file.
        """
        self._bootargs = bootargs
    
    def get_bootargs(self):
        """
        Gets the boot args.
        """
        return self._bootargs

    def install_uboot_env(self, uenv_file, device):
        """
        Install the U-Boot environment to the given file. 
        """
        uenv = open(uenv_file, "w")
        uenv.write("bootargs="+self._bootargs+"\n")
        uenv.write("uenvcmd=echo Running uenvcmd ...; run loaduimage;bootm " \
                   +str(hex(int(uboot_load_addr)))+"\n")
        uenv.close()
        m_point = self._workdir + "/boot"
        if not self._mount_partition('vfat', device, 1, m_point):
            self._logger.error('Failed to mount device')
            return False
        if self._executer.check_call("sudo cp " + uenv_file +" "+ m_point) != 0:
            self._logger.error('Failed to copy ' + uenv_file + " to " +  m_point)
            return False
        if not self._unmount_partition(m_point):
            self._logger.error('Failed to unmount ' + device)
            return False
        return True
    
    def install_kernel(self, kernel_image, device):
        """
        Install the Kernel on the given device.
        """
        m_point = self._workdir + "/boot"
        if not self._mount_partition('vfat', device, 1, m_point):
            self._logger.error('Failed to mount device')
            return False
        if self._executer.check_call("sudo cp " + kernel_image +" "+ m_point+"/uImage") != 0:
            self._logger.error('Failed to copy ' + uenv_file + " to " +  m_point)
            return False
        if not self._unmount_partition(m_point):
            self._logger.error('Failed to unmount ' + device)
            return False
        return True
    
    def _mount_partition(self,p_type,device,p_number,m_point):
        """
        Mounts vfat or ext3 partitions.
        """
        if not (p_type == 'vfat' or p_type == 'ext3'):
            self._logger.error('Unrecognized partition type')
            return False
        if self._executer.check_call("mkdir --parents "+ m_point) != 0:
            self._logger.error('Failed to create ' + m_point)
            return False
        if self._executer.check_call("sudo mount -t "+ p_type +" "+ device + \
                                     str(p_number) + " " +  m_point ) != 0:
            self._logger.error('Failed to mount ' + device + str(p_number) + \
                               " on "+ m_point)
            return False
        return True
    
    def _unmount_partition(self,m_point):
        """
        Unmount the given mount point.
        """
        time.sleep(0.1) # fails if it doesn't wait
        if self._executer.check_call("sudo umount "+ m_point) != 0:
            self._logger.error('Failed to unmount ' + m_point)
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
    
    bl_installer = BootloaderInstaller()
    
    # The following test cases will be run over the following device,
    # in the given dryrun mode, unless otherwise specified in the test case.
    
    # WARNING: Dryrun mode is set by default, but be careful
    # you don't repartition or flash a device you don't want to.
    
    device = "/dev/sdb"
    bl_installer.set_dryrun(True)
    bl_installer.set_uflash_bin(devdir +
       '/bootloader/u-boot-2010.12-rc2-psp03.01.01.39/src/tools/uflash/uflash')
    
# ==========================================================================
# Test cases - Unit tests
# ==========================================================================

    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0) 
    
    # Check device existence (positive test case)
    
    ubl_file         = devdir + '/images/ubl_DM36x_sdmmc.bin'
    uboot_file       = devdir + '/images/bootloader'
    uboot_entry_addr = '2181038080' # 0x82000000 
    uboot_load_addr  = '2181038080' # 0x82000000
    
    if bl_installer.flash(device, ubl_file, uboot_file, uboot_entry_addr,
                          uboot_load_addr):
        print "Device " + device + " correctly flashed"
    else:
        print "Error flashing " + device
    
    # Try to install uboot env on sd.
    
    bl_installer.set_workdir(devdir + '/images')
    bl_installer.set_bootargs(" davinci_enc_mngr.ch0_output=COMPONENT \
    davinci_enc_mngr.ch0_mode=1080I-30  davinci_display.cont2_bufsize=13631488 \
    vpfe_capture.cont_bufoffset=13631488 vpfe_capture.cont_bufsize=12582912 \
    video=davincifb:osd1=0x0x8:osd0=1920x1080x16,4050K@0,0:vid0=off:vid1=off  \
    console=ttyS0,115200n8  dm365_imp.oper_mode=0  vpfe_capture.interface=1  \
    mem=83M root=/dev/mmcblk0p2 rootdelay=2 rootfstype=ext3   ")
        
    uenv_file = devdir + '/images/uEnv.txt'
    
    if bl_installer.install_uboot_env(uenv_file,device):
        print "uboot env successfully installed on " + device + "1"
    else:
        print "Error installing uboot env on " + device + "1"
    
    kernel_image = devdir + '/images/kernel.uImage'
    
    if bl_installer.install_kernel(kernel_image,device):
        print "Kernel successfully installed on " + device + "1"
    else:
        print "Error installing kernel on " + device + "1"
    
    print "Test cases finished"
