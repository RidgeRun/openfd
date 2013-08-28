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
# Components operations to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import rrutils
import rrutils.hexutils as hexutils
import sys

# ==========================================================================
# Public Classes
# ==========================================================================

class ComponentInstaller(object):
    """
    Class to handle components-related operations.
    """
    
    def __init__(self, uflash_bin=None, ubl_file=None, uboot_file=None,
                 uboot_entry_addr=None, uboot_load_addr=None, bootargs=None,
                 kernel_image=None, rootfs=None, workdir=None, dryrun=False):
        """
        :param uflash_bin: Path to the uflash tool.
        :param ubl_file: Path to the UBL file.
        :param uboot_file: Path the Uboot file.
        :param uboot_entry_addr: Uboot entry address, in decimal or hexadecimal
            (`'0x'` prefix).
        :param uboot_load_addr: Uboot load address, in decimal or hexadecimal
            (`'0x'` prefix).
        :param bootargs: Uboot environment variable 'bootargs'.
        :param kernel_image: Path to the kernel image.
        :param rootfs: Path to the rootfs directory. Set to None if this
            installation does not require a rootfs, i.e. NFS will be used.
        :param workdir: Path to the workdir - a directory where this installer
            can write files and perform other temporary operations.
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        
        self._logger = rrutils.logger.get_global_logger()
        self._executer = rrutils.executer.Executer()
        self._executer.logger = self._logger
        self._workdir = workdir
        self._uflash_bin = uflash_bin
        self._ubl_file = ubl_file
        self._uboot_file = uboot_file
        self._uboot_entry_addr = uboot_entry_addr
        self._uboot_load_addr = uboot_load_addr
        self._bootargs = bootargs
        self._kernel_image = kernel_image
        self._rootfs = rootfs
        self._dryrun = dryrun

    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._executer.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                      doc="""Enable dryrun mode. Systems commands will be
                     logged, but not executed.""")
        
    def __set_uflash_bin(self, uflash_bin):
        self._uflash_bin = uflash_bin
        
    def __get_uflash_bin(self):
        return self._uflash_bin
    
    uflash_bin = property(__get_uflash_bin, __set_uflash_bin,
                          doc="""Path to the uflash tool.""")
    
    def __set_ubl_file(self, ubl_file):
        self._ubl_file = ubl_file
        
    def __get_ubl_file(self):
        return self._ubl_file
    
    ubl_file = property(__get_ubl_file, __set_ubl_file,
                        doc="""Path to the UBL file.""")
    
    def __set_uboot_file(self, uboot_file):
        self._uboot_file = uboot_file
        
    def __get_uboot_file(self):
        return self._uboot_file
    
    uboot_file = property(__get_uboot_file, __set_uboot_file,
                          doc="""Path to the uboot file.""")
    
    def __set_uboot_entry_addr(self, uboot_entry_addr):
        if self._is_valid_addr(uboot_entry_addr):
            self._uboot_entry_addr = uboot_entry_addr
        else:
            self._logger.error('Invalid u-boot entry address: %s' %
                               uboot_entry_addr)
            self._uboot_entry_addr = None
        
    def __get_uboot_entry_addr(self):
        return self._uboot_entry_addr
    
    uboot_entry_addr = property(__get_uboot_entry_addr, __set_uboot_entry_addr,
                                doc="""Uboot entry address, in decimal or
                                hexadecimal (`'0x'` prefix).""")
    
    def __set_uboot_load_addr(self, uboot_load_addr):
        if self._is_valid_addr(uboot_load_addr):
            self._uboot_load_addr = uboot_load_addr
        else:
            self._logger.error('Invalid u-boot load address: %s' %
                               uboot_load_addr)
            self._uboot_load_addr = None
            
        
    def __get_uboot_load_addr(self):
        return self._uboot_load_addr
    
    uboot_load_addr = property(__get_uboot_load_addr, __set_uboot_load_addr,
                               doc="""Uboot load address, in decimal or
                                hexadecimal (`'0x'` prefix).""")
    
    def __set_bootargs(self,bootargs):
        self._bootargs = bootargs
    
    def __get_bootargs(self):
        return self._bootargs
    
    bootargs = property(__get_bootargs, __set_bootargs,
                        doc="""Uboot environment variable 'bootargs'.""")
    
    def __set_kernel_image(self, kernel_image):
        self._kernel_image = kernel_image
        
    def __get_kernel_image(self):
        return self._kernel_image
    
    kernel_image = property(__get_kernel_image, __set_kernel_image,
                            doc="""Path to the kernel image.""")
    
    def __set_rootfs(self, rootfs):
        self._rootfs = rootfs

    def __get_rootfs(self):
        return self._rootfs
    
    rootfs = property(__get_rootfs, __set_rootfs,
                      doc="""Path to the rootfs directory. Set to None if this
            installation does not require a rootfs, i.e. NFS will be used.""")
    
    def __set_workdir(self, workdir):
        self._workdir = workdir
        
    def __get_workdir(self):
        return self._workdir
    
    workdir = property(__get_workdir, __set_workdir,
                       doc="""Path to the workdir - a directory where this
                       installer can write files and perform other temporary
                       operations.""")
    
    def _is_valid_addr(self, addr):
        """
        Returns true if the address is valid; false otherwise.
        """
        
        return True if hexutils.str_to_hex(addr) else False
    
    def install_uboot(self, device):
        """
        Flashes UBL and uboot to the given device, using the uflash tool.
        
        This method needs :attr:`uflash_bin`, :attr:`ubl_file`, 
        :attr:`uboot_file`, :attr:`uboot_entry_addr`, and  
        :attr:`uboot_load_addr` to be already set.
        
        :param device: Device where to flash UBL and uboot (i.e. '/dev/sdb').
        :returns: Returns true on success; false otherwise.
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
            return False

        if not self._uboot_load_addr:
            self._logger.error('No uboot load address specified')
            return False
        
        uboot_load_addr = hexutils.str_to_hex(self._uboot_load_addr)
        uboot_entry_addr = hexutils.str_to_hex(self._uboot_entry_addr)
        
        cmd = 'sudo ' + self._uflash_bin + \
              ' -d ' + device + \
              ' -u ' + self._ubl_file + \
              ' -b ' + self._uboot_file + \
              ' -e ' + uboot_entry_addr + \
              ' -l ' + uboot_load_addr

        self._logger.info('Installing uboot')
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Failed to flash UBL and U-Boot into %s' %
                               device)
            return False

        return True
    
    def install_uboot_env(self, mount_point):
        """
        Installs the uboot environment (uEnv.txt) to the given mount point.
        
        This methods needs :attr:`uboot_load_addr` and :attr:`workdir`
        to be already set.
        
        :param mount_point: Path where to install the uboot environment.
        :returns: Returns true on success; false otherwise.
        """
        
        if not os.path.isdir(mount_point) and not self._dryrun:
            self._logger.error('Mount point %s does not exist' %
                               mount_point)
            return False
        
        if not self._uboot_load_addr:
            self._logger.error('No uboot load address specified')
            return False
        
        if not self._workdir:
            self._logger.error('No workdir specified')
            return False
        
        uboot_load_addr = hexutils.str_to_hex(self._uboot_load_addr)
        
        # Uboot env file preparation
        
        uenv_file = os.path.join(self._workdir, "uEnv.txt")
        
        if not self._dryrun:
            uenv = open(uenv_file, "w")
            
            uenv.write('bootargs=%s\n' % self._bootargs)
            uenv.write('uenvcmd=echo Running uenvcmd ...; '
                       'run loaduimage; '
                       'bootm %s\n' % uboot_load_addr)
            uenv.close()
        
        cmd = 'sudo cp ' + uenv_file + ' ' + mount_point
        
        self._logger.info('Installing uboot environment')
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Failed to install uboot env file.')
            return False
        
        return True
        
    def install_kernel(self, mount_point):
        """
        Installs the kernel image on the given mount point.
        
        This methods needs :attr:`kernel_image` to be already set.
        
        :param mount_point: Path to where install the kernel image.
        :returns: Returns true on success, false otherwise.
        """
        
        if not self._kernel_image:
            self._logger.error('No kernel image specified')
            return False
        
        cmd = 'sudo cp ' + self._kernel_image + ' ' + mount_point + '/uImage'
        
        self._logger.info('Installing kernel')
        if self._executer.check_call(cmd) != 0:
            self._logger.error('Failed copying %s to %s' %
                               (self._kernel_image, mount_point))
            return False
        
        return True
    
    def install_rootfs(self, mount_point):
        """
        If any, installs :attr:`rootfs` to the given mount point.
        
        :param mount_point: Path to where install rootfs.
        :returns: Returns true on success, false otherwise.
        """
        
        if self._rootfs:
        
            cmd = 'cd ' + self._rootfs + ' ; find . | sudo cpio -pdum ' + \
                    mount_point
            
            self._logger.info('Installing rootfs')
            if self._executer.check_call(cmd) != 0:
                self._logger.error('Failed installing rootfs into %s' %
                                   mount_point)
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
    
    comp_installer = ComponentInstaller()
    
    # The following test cases will be run over the following device,
    # in the given dryrun mode, unless otherwise specified in the test case.
    
    # WARNING: Dryrun mode is set by default, but be careful
    # you don't repartition or flash a device you don't want to.
    
    device = "/dev/sdb"
    comp_installer.dryrun = False
    
    uflash_bin = devdir + \
       '/bootloader/u-boot-2010.12-rc2-psp03.01.01.39/src/tools/uflash/uflash'
    
    comp_installer.uflash_bin = uflash_bin

# ==========================================================================
# Test cases - Unit tests
# ==========================================================================

    # --------------- TC 1 ---------------
    
    tc_start(1, sleep_time=0)
    
    # Initial setup
    
    ubl_file = devdir + '/images/ubl_DM36x_sdmmc.bin'
    uboot_file = devdir + '/images/bootloader'
    workdir = devdir + "/images/"
    uboot_entry_addr = '0x82000000' # 2181038080 
    uboot_load_addr = '2181038080' # 0x82000000
    
    comp_installer.ubl_file = ubl_file
    comp_installer.uboot_file = uboot_file
    comp_installer.uboot_entry_addr = uboot_entry_addr
    comp_installer.uboot_load_addr = uboot_load_addr
    comp_installer.workdir = workdir
    comp_installer.bootargs = ("davinci_enc_mngr.ch0_output=COMPONENT "
                          "davinci_enc_mngr.ch0_mode=1080I-30  "
                          "davinci_display.cont2_bufsize=13631488 "
                          "vpfe_capture.cont_bufoffset=13631488 "
                          "vpfe_capture.cont_bufsize=12582912 "
                          "video=davincifb:osd1=0x0x8:osd0=1920x1080x16,4050K@0,0:vid0=off:vid1=off "
                          "console=ttyS0,115200n8  dm365_imp.oper_mode=0  vpfe_capture.interface=1 "
                          "mem=83M root=/dev/mmcblk0p2 rootdelay=2 "
                          "rootfstype=ext3")
    
    # Flash the device
    
    if comp_installer.install_uboot(device):
        print "Uboot successfully installed on " + device
    else:
        print "Error installing uboot in " + device
    
    # --------------- TC 2 ---------------
    
    tc_start(2)
    
    # Uboot env installation
    
    mount_point = '/media/boot'
    
    if comp_installer.install_uboot_env(mount_point):
        print "Uboot env successfully installed on " + mount_point
    else:
        print "Error installing uboot env on " + mount_point

    # --------------- TC 3 ---------------
    
    tc_start(3)
    
    # Kernel  installation
    
    kernel_image = devdir + '/images/kernel.uImage'
    
    comp_installer.kernel_image = kernel_image
    
    if comp_installer.install_kernel(mount_point):
        print "Kernel successfully installed on " + mount_point
    else:
        print "Error installing kernel " + kernel_image + " on " + mount_point

    # --------------- TC 4 ---------------
    
    tc_start(4)
    
    comp_installer.rootfs = devdir + "/fs/fs"
    mount_point = "/media/rootfs"

    if comp_installer.install_rootfs(mount_point):
        print "Rootfs successfully installed on " + mount_point
    else:
        print "Error installing rootfs on " + mount_point
        sys.exit(-1)
    
    print "Test cases finished"
