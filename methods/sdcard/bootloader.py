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
import rrutils
import sys

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
        self._sd_installer = sdcard.SDCardInstaller()
        # This flags will tell the methods to continue only if
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
        
    def set_uflash_bin(self, uflash_bin):
        """
        Sets the path to the uflash tool.
        """
        if os.path.isfile(uflash_bin):
            self._uflash_bin = uflash_bin
            return True
        else:
            self._logger.error(uflash_bin+' Does not exist.')
        
    def get_uflash_bin(self):
        """
        Gets the path to the uflash tool.
        """
        
        return self._uflash_bin
        
    def flash(self, device, ubl_file, uboot_file, uboot_entry_addr,
              uboot_load_addr,partition_index):
        """
        Flashes UBL and U-Boot to the given device, using the uflash tool.
        
        Returns true on success; false otherwise.
        """
        # Let's check that sd info was set.
        if not self._sd_info_set:
            self._logger.error("Set SD Info!")
            return False
        # Now let's check that there is a workdir.
        if self.get_workdir() == None:
            self._logger.error("Set a Workdir!")
        # We should get sure that the device exists.
        if not self._sd_installer.device_exists(device):
            return False
        # Now that we know that the device exist let's get the device info.
        dev_info = self._sd_installer.get_dev_info(device)
        # Now it is convenient to get the real partition suffix.
        part_suffix = self._sd_installer.get_partition_suffix(device, partition_index)
        # Now that we have this info, let's create a mount point for the partition.
        # For this we will use self._workdir and the real label of the partition.
        m_point = os.path.join( self._workdir, dev_info[device+part_suffix]["label"])
        # Here we check if the device is mounted, if not we mount it.
        if not self._check_sd_mounted(device,part_suffix, m_point):
            return False
        
        if not self._uflash_bin:
            self._logger.error('No path to uflash specified')
            return False
        
        uboot_entry_addr = self._get_str_hex(uboot_entry_addr)
        if uboot_entry_addr == None:
            self._logger.error("Invalid value given to uboot entry address")
            return False
        uboot_load_addr = self._get_str_hex(uboot_load_addr)
        if uboot_load_addr == None:
            self._logger.error("Invalid value given to uboot load address")
            return False
        
        cmd = 'sudo ' + self._uflash_bin + \
              ' -d ' + device + \
              ' -u ' + ubl_file + \
              ' -b ' + uboot_file + \
              ' -e ' + uboot_entry_addr + \
              ' -l ' + uboot_load_addr

        self._logger.info('Flashing UBL and U-Boot to ' + device)
        if self._executer.check_call(cmd) != 0:
                self._logger.error('Failed to flash UBL and U-Boot into ' +
                                   device)
                return False

        return True
    
    def _get_str_hex(self,value_str):
        """
        Returns a string with the hex number of the string number passed.
        Otherwise returns None.
        """
        if (value_str.find('0x') or value_str.find('0X')):
            try:
                value = int(value_str,0)
            except:
                return None
        else:
            try:
                value = int(value_str)
            except:
                return None
        ret_value = hex(value)
        return str(ret_value)
    
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
        if os.path.isdir(workdir):
            self._workdir = workdir
            return True
        else:
            self._logger.error("Error! "+workdir+" is not a directory.")
            return False
    
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

    def install_uboot_env(self, device, partition_index,uboot_load_addr):
        """
        Install the U-Boot environment to the given file. 
        """
        # Let's check that sd info was set.
        if not self._sd_info_set:
            self._logger.error("Set SD Info!")
            return False
        # Now let's check that there is a workdir.
        if self.get_workdir() == None:
            self._logger.error("Set a Workdir!")
        # We should get sure that the device exists.
        if not self._sd_installer.device_exists(device):
            return False
        # Now that we know that the device exist let's get the device info.
        dev_info = self._sd_installer.get_dev_info(device)
        # Now it is convenient to get the real partition suffix.
        part_suffix = self._sd_installer.get_partition_suffix(device, partition_index)
        # Now that we have this info, let's create a mount point for the partition.
        # For this we will use self._workdir and the real label of the partition.
        m_point = os.path.join( self._workdir, dev_info[device+part_suffix]["label"])
        # Here we check if the device is mounted, if not we mount it.
        if not self._check_sd_mounted(device,part_suffix, m_point):
            return False
        
        # Here we prepare the uboot env file.
        # but write it only if we are not in dryrun.
        uenv_file = os.path.join(self._workdir,"uEnv.txt")
        uboot_load_addr = self._get_str_hex(uboot_load_addr)
        if not self.get_dryrun():
            uenv = open(uenv_file, "w")
            uenv.write("bootargs="+self._bootargs+"\n")
            uenv.write("uenvcmd=echo Running uenvcmd ...; run loaduimage;bootm " \
                       +uboot_load_addr+"\n")
            uenv.close()
        else:
            self._logger.info("You are running in dryrun, that's why uboot env file is not generated.")
        
        
        if self._executer.check_call("sudo cp " + uenv_file +" "+ m_point) != 0:
            self._logger.error('Failed to copy ' + uenv_file + " to " + m_point)
            return False
        
        return True
        
    def install_kernel(self, kernel_image, device, partition_index):
        """
        Install the Kernel on the given device.
        """
        # Let's check that sd info was set.
        if not self._sd_info_set:
            self._logger.error("Set SD Info!")
            return False
        # Now let's check that there is a workdir.
        if self.get_workdir() == None:
            self._logger.error("Set a Workdir!")
        # We should get sure that the device exists.
        if not self._sd_installer.device_exists(device):
            return False
        # Now that we know that the device exist let's get the device info.
        dev_info = self._sd_installer.get_dev_info(device)
        # Now it is convenient to get the real partition suffix.
        part_suffix = self._sd_installer.get_partition_suffix(device, partition_index)
        # Now that we have this info, let's create a mount point for the partition.
        # For this we will use self._workdir and the real label of the partition.
        m_point = os.path.join( self._workdir, dev_info[device+part_suffix]["label"])
        # Here we check if the device is mounted, if not we mount it.
        if not self._check_sd_mounted(device,part_suffix, m_point):
            return False
        
        if self._executer.check_call("sudo cp " + kernel_image +" "+ m_point+"/uImage") != 0:
            self._logger.error('Failed to copy ' + kernel_image + " to " +  m_point)
            return False
        
        return True
    
    def _check_sd_mounted(self,device,partition_index,m_point):
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
            partition = device+self._sd_installer.get_partition_suffix(device, partition_index)
            current_mpoint = self._sd_installer.get_mpoint(partition)
            if m_point != current_mpoint:
                self._logger.error('Device is mounted on '+ current_mpoint \
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
    
    bl_installer = BootloaderInstaller()
    
    # The following test cases will be run over the following device,
    # in the given dryrun mode, unless otherwise specified in the test case.
    
    # WARNING: Dryrun mode is set by default, but be careful
    # you don't repartition or flash a device you don't want to.
    
    device = "/dev/sdb"
    partition_index = 1
    bl_installer.set_dryrun(True)
    
    # Now it's important to set a workdir so that the logic know where to mount devices.
    workdir = devdir + '/images'
    bl_installer.set_workdir(workdir)
    
    bl_installer.set_uflash_bin(devdir +
       '/bootloader/u-boot-2010.12-rc2-psp03.01.01.39/src/tools/uflash/uflash')
    
    workdir = devdir + '/images'
    if not bl_installer.set_workdir(devdir + '/images'):
        print "Failed to set working directory"
        sys.exit(-1)

    # Try to set sd partitions info.
    
    sdcard_mmap_filename = devdir + '/images/sd-mmap.config'
    if not bl_installer.set_sd_info(sdcard_mmap_filename):
        print "SD partitions info could not be setted... Exiting"
        sys.exit(-1)
      
# ==========================================================================
# Test cases - Unit tests
# ==========================================================================

    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0)
    
    # Check device existence (positive test case)
    
    ubl_file         = devdir + '/images/ubl_DM36x_sdmmc.bin'
    uboot_file       = devdir + '/images/bootloader'
    uboot_entry_addr = '0x82000000' # 2181038080
    uboot_load_addr  = '2181038080' # 0x82000000
    
    if bl_installer.flash(device, ubl_file, uboot_file, uboot_entry_addr,
                          uboot_load_addr,partition_index):
        print "Device " + device + " correctly flashed"
    else:
        print "Error flashing " + device
    
    # Try to install uboot env on sd.
    
    bl_installer.set_bootargs(" davinci_enc_mngr.ch0_output=COMPONENT \
    davinci_enc_mngr.ch0_mode=1080I-30  davinci_display.cont2_bufsize=13631488 \
    vpfe_capture.cont_bufoffset=13631488 vpfe_capture.cont_bufsize=12582912 \
    video=davincifb:osd1=0x0x8:osd0=1920x1080x16,4050K@0,0:vid0=off:vid1=off  \
    console=ttyS0,115200n8  dm365_imp.oper_mode=0  vpfe_capture.interface=1  \
    mem=83M root=/dev/mmcblk0p2 rootdelay=2 rootfstype=ext3   ")
    
    if bl_installer.install_uboot_env(device,partition_index,uboot_load_addr):
        print "uboot env successfully installed on " + device + str(partition_index)
    else:
        print "Error installing uboot env on " + device + str(partition_index)
        sys.exit(-1)
    
    kernel_image = devdir + '/images/kernel.uImage'
    
    if bl_installer.install_kernel(kernel_image,device,partition_index):
        print "Kernel successfully installed on " + device + str(partition_index)
    else:
        print "Error installing kernel on " + device + str(partition_index)
        sys.exit(-1)
    
    # Let's check that the filesystem is ok.
    print "Checking fs..."
    bl_installer.check_fs(device)
    
    print "Test cases finished"
