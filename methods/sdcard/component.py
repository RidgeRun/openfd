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

"""
Components operations to support the installer. Current components are:
  - Bootloader (includes pre-bootloader)
  - Kernel
  - Filesystem

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
import common

# ==========================================================================
# Public Classes
# ==========================================================================

class ComponentInstaller(object):
    """
    Class to handle components-related operations.
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
        self._bootargs = None
        self._kernel_image = None
        self._rootfs = None
        self._executer.set_logger(self._logger)

    def __set_dryrun(self, dryrun):
        """
        Sets on/off the dryrun mode. In dryrun mode any commands will
        not be executed (just logged).
        """
        
        self._dryrun = dryrun
        self._executer.set_dryrun(dryrun)
    
    def __get_dryrun(self):
        """
        Returns true if the dryrun mode is on; false otherwise.
        """
        
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                      doc="""Gets or sets the dryrun mode.""")
        
    def __set_uflash_bin(self, uflash_bin):
        """
        Sets the path to the uflash tool.
        """
        
        self._uflash_bin = uflash_bin
        
    def __get_uflash_bin(self):
        """
        Gets the path to the uflash tool.
        """
        
        return self._uflash_bin
    
    uflash_bin = property(__get_uflash_bin, __set_uflash_bin,
                          doc="""Gets or sets the path to the uflash tool""")
    
    def __set_ubl_file(self, ubl_file):
        """
        Sets the path to the ubl file.
        """
        
        self._ubl_file = ubl_file
        
    def __get_ubl_file(self):
        """
        Gets the path to the ubl file.
        """
        
        return self._ubl_file
    
    ubl_file = property(__get_ubl_file, __set_ubl_file,
                        doc="""Gets or sets the path to the ubl file.""")
    
    def __set_uboot_file(self, uboot_file):
        """
        Sets the path to the uboot file.
        """
        
        self._uboot_file = uboot_file
        
    def __get_uboot_file(self):
        """
        Gets the path to the uboot file.
        """
        
        return self._uboot_file
    
    uboot_file = property(__get_uboot_file, __set_uboot_file,
                          doc="""Gets or sets the path to the uboot file.""")
    
    def __set_uboot_entry_addr(self, uboot_entry_addr):
        """
        Sets the uboot entry address.
        """
        
        self._uboot_entry_addr = uboot_entry_addr
        
    def __get_uboot_entry_addr(self):
        """
        Gets the path to the uboot entry address.
        """
        
        return self._uboot_entry_addr
    
    uboot_entry_addr = property(__get_uboot_entry_addr, __set_uboot_entry_addr,
                                doc="""Gets or sets the uboot entry
                                address.""")
    
    def __set_uboot_load_addr(self, uboot_load_addr):
        """
        Sets the path to the ubootload address.
        """
        self._uboot_load_addr = uboot_load_addr
        
    def __get_uboot_load_addr(self):
        """
        Gets the path to the uboot load address.
        """
        
        return self._uboot_load_addr
    
    uboot_load_addr = property(__get_uboot_load_addr, __set_uboot_load_addr,
                               doc="""Gets or sets the uboot load address.""")
    
    def __set_bootargs(self,bootargs):
        """
        Sets the uboot environment variable "bootargs".
        """
        self._bootargs = bootargs
    
    def __get_bootargs(self):
        """
        Gets the uboot environment variable "bootargs".
        """
        
        return self._bootargs
    
    bootargs = property(__get_bootargs, __set_bootargs,
                        doc="""Gets or sets the uboot environment variable
                        'bootargs'.""")
    
    def __set_kernel_image(self, kernel_image):
        """
        Sets the path to the kernel image.
        """
        
        self._kernel_image = kernel_image
        
    def __get_kernel_image(self):
        """
        Gets the path to the kernel image.
        """
        
        return self._kernel_image
    
    kernel_image = property(__get_kernel_image, __set_kernel_image,
                            doc="""Gets or sets the path to the kernel
                            image.""")
    
    def __set_rootfs(self, rootfs):
        """
        Sets the path to rootfs. Set to None if this installation does not
        require a rootfs, i.e. NFS will be used.
        """
        
        self._rootfs = rootfs

    def __get_rootfs(self):
        """
        Gets the path to rootfs. If None, a rootfs was not specified, more
        likely because this installation does not require rootfs, i.e. NFS
        will be used. 
        """
        
        return self._rootfs
    
    rootfs = property(__get_rootfs, __set_rootfs,
                      doc="""Gets or sets the path to rootfs.""")
    
    def __set_workdir(self, workdir):
        """
        Sets the path to the workdir - a directory where this installer can 
        write to files and perform other temporary operations.
        """
        
        self._workdir = workdir
        
    def __get_workdir(self):
        """
        Gets the path to the workdir - a directory where this installer can 
        write to files and perform other temporary operations.
        """
        
        return self._workdir
    
    workdir = property(__get_workdir, __set_workdir,
                       doc="""Gets or sets the path to the workdir.""")
    
    def install_uboot(self, device):
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
            return False

        if not self._uboot_load_addr:
            self._logger.error('No uboot load address specified')
            return False
        
        uboot_entry_addr = common.str_to_hex(self._uboot_entry_addr)
        if not uboot_entry_addr:
            self._logger.error('Invalid value given to uboot entry address: %s'
                               % self._uboot_entry_addr)
            return False
        
        uboot_load_addr = common.str_to_hex(self._uboot_load_addr)
        if not uboot_load_addr:
            self._logger.error('Invalid value given to uboot load address: %s'
                               % self._uboot_load_addr)
            return False
        
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
        Installs the U-Boot environment to the given mount point. Assumes
        a valid uboot load address and workdir.
        """
        
        if not os.path.isdir(mount_point) and not self._dryrun:
            self._logger.error('Mount point %s does not exist.' %
                               mount_point)
            return False
        
        if not self._uboot_load_addr:
            self._logger.error('No uboot load address specified')
            return False
        
        if not self._workdir:
            self._logger.error('No workdir specified')
            return False
        
        # Uboot env file preparation
        
        uenv_file = os.path.join(self._workdir, "uEnv.txt")
        
        uboot_load_addr = common.str_to_hex(self._uboot_load_addr)
        if not uboot_load_addr:
            self._logger.error('Invalid u-boot load address: %s' %
                               uboot_load_addr)
            return False
        
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
        Installs the Kernel on the given mount point.
        
        Returns true on success, false otherwise.
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
        If any, installs the rootfs to the given mount point.
        
        Returns true on success, false otherwise.
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
    comp_installer.dryrun = True
    
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
    
    comp_installer.set_ubl_file = ubl_file
    comp_installer.set_uboot_file = uboot_file
    comp_installer.set_uboot_entry_addr = uboot_entry_addr
    comp_installer.set_uboot_load_addr = uboot_load_addr
    comp_installer.set_workdir = workdir
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
