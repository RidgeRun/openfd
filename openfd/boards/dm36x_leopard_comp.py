#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013-2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#          Diego Benavides <diego.benavides@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Component-related operations
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import openfd.utils as utils
import openfd.utils.hexutils as hexutils
from openfd.storage import SDCardPartition
from board import BoardError

# ==========================================================================
# Public Classes
# ==========================================================================

class Dm36xLeopardSdCompInstaller(object):
    """
    Class to handle components-related operations.
    """
    
    def __init__(self, dryrun=False):
        """
        :param dryrun: Enable dryrun mode. Systems commands will be logged,
            but not executed.
        :type dryrun: boolean
        """
        
        self._l = utils.logger.get_global_logger()
        self._e = utils.executer.get_global_executer()
        self._workdir = None
        self._uflash_bin = None
        self._ubl_file = None
        self._uboot_file = None
        self._uboot_entry_addr = None
        self._uboot_load_addr = None
        self._bootargs = None
        self._kernel_image = None
        self._rootfs = None
        self._dryrun = dryrun
        self._e.dryrun = dryrun

    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
    
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
        if hexutils.is_valid_addr(uboot_entry_addr):
            self._uboot_entry_addr = uboot_entry_addr
        else:
            self._l.error('Invalid u-boot entry address: %s' % uboot_entry_addr)
            self._uboot_entry_addr = None
        
    def __get_uboot_entry_addr(self):
        return self._uboot_entry_addr
    
    uboot_entry_addr = property(__get_uboot_entry_addr, __set_uboot_entry_addr,
                                doc="""Uboot entry address, in decimal or
                                hexadecimal (`'0x'` prefix).""")
    
    def __set_uboot_load_addr(self, uboot_load_addr):
        if hexutils.is_valid_addr(uboot_load_addr):
            self._uboot_load_addr = uboot_load_addr
        else:
            self._l.error('Invalid u-boot load address: %s' % uboot_load_addr)
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
               doc="""Path to the workdir - a directory where this installer
               can write files and perform other temporary operations.""")
    
    def install_uboot(self, device):
        """
        Flashes UBL and uboot to the given device, using the uflash tool.
        
        This method needs :attr:`uflash_bin`, :attr:`ubl_file`, 
        :attr:`uboot_file`, :attr:`uboot_entry_addr`, and  
        :attr:`uboot_load_addr` to be already set.
        
        :param device: Device where to flash UBL and uboot (i.e. '/dev/sdb').
        :exception BoardError: On error.
        """
        
        uboot_load_addr = hexutils.str_to_hex(self._uboot_load_addr)
        uboot_entry_addr = hexutils.str_to_hex(self._uboot_entry_addr)
        self._l.info('Installing uboot')
        cmd = ('sudo ' + self._uflash_bin +
              ' -d ' + device +
              ' -u ' + self._ubl_file + 
              ' -b ' + self._uboot_file + 
              ' -e ' + uboot_entry_addr + 
              ' -l ' + uboot_load_addr)
        if self._e.check_call(cmd) != 0:
            raise BoardError('Failed to flash UBL and uboot into %s' % device)
        return True
    
    def install_uboot_env(self, mount_point):
        """
        Installs the uboot environment (uEnv.txt) to the given mount point.
        
        This methods needs :attr:`uboot_load_addr` and :attr:`workdir`
        to be already set.
        
        :param mount_point: Path where to install the uboot environment.
        :exception BoardError: On error.
        """
        
        self._l.info('Installing uboot environment')
        uboot_load_addr = hexutils.str_to_hex(self._uboot_load_addr)
        uenv_file = os.path.join(self._workdir, "uEnv.txt")
        if not self._dryrun:
            with open(uenv_file, "w") as uenv:
                bootargs = 'bootargs=%s' % self._bootargs.strip()
                uenvcmd = ('uenvcmd=echo Running uenvcmd ...; run loaduimage; '
                           'bootm %s' % uboot_load_addr)
                self._l.debug("  uEnv.txt <= '%s'" % bootargs)
                uenv.write("%s\n" % bootargs)
                self._l.debug("  uEnv.txt <= '%s'" % uenvcmd)
                uenv.write("%s\n" % uenvcmd)
        cmd = 'sudo cp %s %s' % (uenv_file, mount_point)
        if self._e.check_call(cmd) != 0:
            raise BoardError('Failed to install uboot env file.')
        
    def install_kernel(self, mount_point):
        """
        Installs the kernel image on the given mount point.
        
        This methods needs :attr:`kernel_image` to be already set.
        
        :param mount_point: Path to where install the kernel image.
        :exception BoardError: On error.
        """

        self._l.info('Installing kernel')
        cmd = 'sudo cp %s %s/uImage' % (self._kernel_image, mount_point)
        if self._e.check_call(cmd) != 0:
            raise BoardError('Failed copying %s to %s' %
                               (self._kernel_image, mount_point))
    
    def install_rootfs(self, mount_point):
        """
        If any, installs :attr:`rootfs` to the given mount point.
        
        :param mount_point: Path to where install rootfs.
        :exception BoardError: On error.
        """
                                 
        if self._rootfs:
            self._l.info('Installing rootfs (this may take a while)')
            cmd = 'cd %s ; find . | sudo cpio -pdum %s' % (self._rootfs,
                                                           mount_point)
            if self._e.check_call(cmd) != 0:
                raise BoardError('Failed installing rootfs '
                                              'into %s' % mount_point)
            if self._e.check_call('sync') != 0:
                raise BoardError('Unable  to sync')
        else:
            self._l.warning('No directory for "%s", omitting...'
                                        % (SDCardPartition.COMPONENT_ROOTFS))

