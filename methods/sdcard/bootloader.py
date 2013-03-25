#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#          Diego Benavides <diego.benavides@ridgerun.com>
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
import rrutils
import sys

# ==========================================================================
# Public Classes
# ==========================================================================

class BootloaderInstaller(object):
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
        
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._dryrun = False
        self._workdir = None
        self._uflash_bin = None
        self._ubl_file = None
        self._uboot_file = None
        self._uboot_entry_addr = None
        self._uboot_load_addr = None
        self._kernel_image = None
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
    
    def set_ubl_file(self, ubl_file):
        """
        Sets the path to the ubl file.
        """
        
        self._ubl_file = ubl_file
        
    def get_ubl_file(self):
        """
        Gets the path to the ubl file.
        """
        
        return self._ubl_file
    
    def set_uboot_file(self, uboot_file):
        """
        Sets the path to the uboot_file.
        """
        
        self._uboot_file = uboot_file
        
    def get_uboot_file(self):
        """
        Gets the path to the uboot_file.
        """
        
        return self._uboot_file
    
    def set_uboot_entry_addr(self, uboot_entry_addr):
        """
        Sets the path to the uboot_entry_addr.
        """
        self._uboot_entry_addr = uboot_entry_addr
        
    def get_uboot_entry_addr(self):
        """
        Gets the path to the uboot_entry_addr.
        """
        
        return self._uboot_entry_addr
    
    def set_uboot_load_addr(self, uboot_load_addr):
        """
        Sets the path to the uboot_load_addr.
        """
        self._uboot_load_addr = uboot_load_addr
        
    def get_uboot_load_addr(self):
        """
        Gets the path to the uboot_load_addr.
        """
        
        return self._uboot_load_addr
    
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
    
    def set_kernel_image(self, kernel_image):
        """
        Sets the path to the kernel_image.
        """
        
        self._kernel_image = kernel_image
        
    def get_kernel_image(self):
        """
        Gets the path to the kernel_image.
        """
        
        return self._kernel_image
    
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
    
    def flash(self, device):
        """
        Flashes UBL and U-Boot to the given device, using the uflash tool.
        This method needs that uflash_bin, ubl_file, uboot_file, 
        uboot_entry_addr and uboot_load_addr to be already set.
        Returns true on success; false otherwise.
        """
        
        if not self._uflash_bin:
            self._logger.error('No path to uflash specified')
            return False
        
        if not self._ubl_file:
            self._logger.error('No path to ubl file specified')
            return False
        
        if not self._uboot_file:
            self._logger.error('No path to uboot file specified')
            return False
        
        if not self._uboot_entry_addr:
            self._logger.error('No uboot entry address specified')

        if not self._uboot_load_addr:
            self._logger.error('No uboot load address specified')
        
        uboot_entry_addr = self._get_str_hex(self._uboot_entry_addr)
        if uboot_entry_addr == None:
            self._logger.error('Invalid value given to uboot entry address: %s'
                               % self._uboot_entry_addr)
            return False
        
        uboot_load_addr = self._get_str_hex(self._uboot_load_addr)
        if uboot_load_addr == None:
            self._logger.error('Invalid value given to uboot load address: %s'
                               % self._uboot_load_addr)
            return False
        
        cmd = 'sudo ' + self._uflash_bin + \
              ' -d ' + device + \
              ' -u ' + self._ubl_file + \
              ' -b ' + self._uboot_file + \
              ' -e ' + uboot_entry_addr + \
              ' -l ' + uboot_load_addr

        self._logger.info('Flashing UBL and U-Boot into %s' % device)
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Failed to flash UBL and U-Boot into %s' %
                               device)
            return False

        return True
    
    def _get_str_hex(self, value_str):
        """
        Converts the string that may contain a decimal number (like 12), or
        a hexadecimal number (like 0Xabcd), into an all-lowercase hexadecimal
        number (like 0xabcd).
        """
        
        if not value_str.upper().find('0X'):
            try:
                return hex(int(value_str))
            except:
                return ''
        else:
            return value_str.lower()
        
    def install_uboot_env(self, mount_point):
        """
        Install the U-Boot environment to the given mount point.
        This method needs that uboot_load_addr be already set.
        """
        
        if not os.path.isdir(mount_point):
            self._logger.error('Mount point %s does not exist.' % mount_point)
            return False
        
        if not self._uboot_load_addr:
            self._logger.error('No uboot load address specified')
            return False
        
        # Uboot env file preparation
        
        uenv_file = os.path.join(self._workdir, "uEnv.txt")
        
        uboot_load_addr = self._get_str_hex(self._uboot_load_addr)
        if not uboot_load_addr:
            self._logger.error('Invalid u-boot load address: %s' %
                               uboot_load_addr)
            return False
        
        uenv = open(uenv_file, "w")
        
        uenv.write('bootargs=%s\n' % self._bootargs)
        uenv.write('uenvcmd=echo Running uenvcmd ...; run loaduimage; '
                   'bootm %s\n' % uboot_load_addr)
        uenv.close()
        
        # Now we copy it to mount point
        cmd = 'sudo cp ' + uenv_file + ' ' + mount_point
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Failed to install uboot env file.')
            return False
        
        return True
        
    def install_kernel(self, mount_point):
        """
        Install the Kernel on the given device.
        This method needs the kernel_image to be set.
        """
        
        if not self._kernel_image:
            self._logger.error('No kernel image specified')
            return False
        
        cmd = 'sudo cp ' + self._kernel_image + ' ' + mount_point + '/uImage'
        
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Failed copying %s to %s' %
                               (self._kernel_image, mount_point))
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
    
    uflash_bin = devdir + \
       '/bootloader/u-boot-2010.12-rc2-psp03.01.01.39/src/tools/uflash/uflash'
    
    bl_installer.set_uflash_bin(uflash_bin)
      
# ==========================================================================
# Test cases - Unit tests
# ==========================================================================

    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0)
    
    # Check device existence (positive test case)
    
    ubl_file         = devdir + '/images/ubl_DM36x_sdmmc.bin'
    
    bl_installer.set_ubl_file(ubl_file)
    
    uboot_file       = devdir + '/images/bootloader'
    
    bl_installer.set_uboot_file(uboot_file)
    
    uboot_entry_addr = '0x82000000' # 2181038080
    
    bl_installer.set_uboot_entry_addr(uboot_entry_addr)
    
    uboot_load_addr  = '2181038080' # 0x82000000
    
    bl_installer.set_uboot_load_addr(uboot_load_addr)
    
    if bl_installer.flash(device):
        print "Device " + device + " correctly flashed"
    else:
        print "Error flashing " + device
    
    # Try to install uboot env on sd.
    
    mount_point = '/media/boot'
    
    bl_installer.set_bootargs(" davinci_enc_mngr.ch0_output=COMPONENT "
    + "davinci_enc_mngr.ch0_mode=1080I-30  " +
    "davinci_display.cont2_bufsize=13631488 " +
    "vpfe_capture.cont_bufoffset=13631488 vpfe_capture.cont_bufsize=12582912 "
    + "video=davincifb:osd1=0x0x8:osd0=1920x1080x16,4050K@0,0:vid0=off:vid1=off "
    + "console=ttyS0,115200n8  dm365_imp.oper_mode=0  vpfe_capture.interface=1"
    + " mem=83M root=/dev/mmcblk0p2 rootdelay=2 rootfstype=ext3   ")
    
    if bl_installer.install_uboot_env(mount_point):
        print "uboot env successfully installed on " + mount_point
    else:
        print "Error installing uboot env on " + mount_point
        sys.exit(-1)
    
    kernel_image = devdir + '/images/kernel.uImage'
    
    bl_installer.set_kernel_image(kernel_image)
    
    if bl_installer.install_kernel(mount_point):
        print "Kernel successfully installed on " + mount_point
    else:
        print "Error installing kernel "+ kernel_image + " on " + mount_point
        sys.exit(-1)
    
    print "Test cases finished"
