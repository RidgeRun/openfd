#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Authors: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# SD Component-related operations
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import openfd.utils as utils
from openfd.storage import SDCardPartition
from openfd.storage import LoopDevicePartition
from board import BoardError

# ==========================================================================
# Public Classes
# ==========================================================================

class Dm816xSdCompInstaller(object):
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
        self._uboot_min_file = None
        self._uboot_file = None
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
  
    def __set_uboot_min_file(self, uboot_min_file):
        self._uboot_min_file = uboot_min_file
        
    def __get_uboot_min_file(self):
        return self._uboot_min_file
    
    uboot_min_file = property(__get_uboot_min_file, __set_uboot_min_file,
                          doc="""Path to the uboot min file.""")
  
    def __set_uboot_file(self, uboot_file):
        self._uboot_file = uboot_file
        
    def __get_uboot_file(self):
        return self._uboot_file
    
    uboot_file = property(__get_uboot_file, __set_uboot_file,
                          doc="""Path to the uboot file.""")
    
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
    
    def install_uboot(self, mount_point):
        """
        Copies the uboot min and uboot images to the given mount point.
        
        :param mount_point: Path where to install the uboot images.
        :exception BoardError: On error.
        """
        
        self._l.info('Installing uboot')
        cmd = 'sudo cp %s %s/MLO' % (self._uboot_min_file, mount_point)
        if self._e.check_call(cmd) != 0:
            raise BoardError('Failed copying %s to %s' %
                               (self._uboot_min_file, mount_point))
        cmd = 'sudo cp %s %s/u-boot.bin' % (self._uboot_file, mount_point)
        if self._e.check_call(cmd) != 0:
            raise BoardError('Failed copying %s to %s' %
                               (self._uboot_file, mount_point))
    
    def install_uboot_env(self, mount_point):
        """
        Installs the uboot environment (uEnv.txt) to the given mount point.
        
        :param mount_point: Path where to install the uboot environment.
        :exception BoardError: On error.
        """
        
        self._l.info('Installing uboot environment')
        uenv_file = os.path.join(self._workdir, "uEnv.txt")
        if not self._dryrun:
            with open(uenv_file, "w") as uenv:
                bootargs = 'bootargs=%s' % self._bootargs.strip()
                uenvcmd = ('uenvcmd=echo Running uenvcmd ...; run loaduimage; '
                           'bootm ${loadaddr}')
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

    def install_sd_components(self, sd):
        """
        Installs the specified components for each partition.
        
        :exception BoardError: On failure installing the components.
        """
        
        i = 1
        for part in sd.partitions:
            cmd = 'mount | grep %s  | cut -f 3 -d " "' % sd.partition_name(i)
            output = self._e.check_output(cmd)[1]
            mount_point = output.replace('\n', '')
            for comp in part.components:
                if comp == SDCardPartition.COMPONENT_BOOTLOADER:
                    self.install_uboot(mount_point)
                    self.install_uboot_env(mount_point)
                elif comp == SDCardPartition.COMPONENT_KERNEL:
                    self.install_kernel(mount_point)
                elif comp == SDCardPartition.COMPONENT_ROOTFS:
                    self.install_rootfs(mount_point)
                else:
                    raise BoardError('Invalid component: %s' % comp)
            i += 1

    def install_ld_components(self, ld):
        """
        Installs the specified components for each partition.
        
        :exception BoardError: On failure installing the components.
        """
        
        for part in ld.partitions:
            cmd = 'mount | grep %s  | cut -f 3 -d " "' % part.device
            output = self._e.check_output(cmd)[1]
            mount_point = output.replace('\n', '')
            for comp in part.components:
                if comp == LoopDevicePartition.COMPONENT_BOOTLOADER:
                    self.install_uboot(mount_point)
                    self.install_uboot_env(mount_point)
                elif comp == LoopDevicePartition.COMPONENT_KERNEL:
                    self.install_kernel(mount_point)
                elif comp == LoopDevicePartition.COMPONENT_ROOTFS:
                    self.install_rootfs(mount_point)
                else:
                    raise BoardError('Invalid component: %s' % comp)

    def install_sd_components_external(self, sd):
        """
        Installs the specified components for each partition, as required
        in external (sd-script) mode.
        
        :exception BoardError: On failure installing the components.
        """
        
        i = 1
        for part in sd.partitions:
            cmd = 'mount | grep %s  | cut -f 3 -d " "' % sd.partition_name(i)
            output = self._e.check_output(cmd)[1]
            mount_point = output.replace('\n', '')
            for comp in part.components:
                if comp == SDCardPartition.COMPONENT_BOOTLOADER:
                    self.install_uboot(mount_point)
                else:
                    raise BoardError('Invalid component: %s' % comp)
            i += 1

    def install_ld_components_external(self, ld):
        """
        Installs the specified components for each partition, as required
        in external (sd-script) mode.
        
        :exception BoardError: On failure installing the components.
        """
        
        for part in ld.partitions:
            cmd = 'mount | grep %s  | cut -f 3 -d " "' % part.device
            output = self._e.check_output(cmd)[1]
            mount_point = output.replace('\n', '')
            for comp in part.components:
                if comp == LoopDevicePartition.COMPONENT_BOOTLOADER:
                    self.install_uboot(mount_point)
                else:
                    raise BoardError('Invalid component: %s' % comp)
    