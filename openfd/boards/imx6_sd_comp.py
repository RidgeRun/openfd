
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
from openfd.storage import LoopDevicePartition
from board import BoardError

# ==========================================================================
# Public Classes
# ==========================================================================

class Imx6SdCompInstaller(object):
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
        self._uboot_file = None
        self._uboot_load_addr = None
        self._bootargs = None
        self._bootscript = None
        self._kernel_image = None
        self._kernel_tftp = False
        self._tftp_loader = None
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

    def __set_tftp_loader(self, loader):
        self._tftp_loader = loader
    
    def __get_tftp_loader(self):
        return self._tftp_loader
    
    tftp_loader = property(__get_tftp_loader, __set_tftp_loader)

    def __set_uboot_file(self, uboot_file):
        self._uboot_file = uboot_file
        
    def __get_uboot_file(self):
        return self._uboot_file
    
    uboot_file = property(__get_uboot_file, __set_uboot_file,
                          doc="""Path to the uboot file.""")
        
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

    def __set_bootscript(self,bootscript):
        self._bootscript = bootscript
    
    def __get_bootscript(self):
        return self._bootscript
    
    bootscript = property(__get_bootscript, __set_bootscript,
                        doc="""Path to the bootscript file.""")

    def __set_kernel_image(self, kernel_image):
        self._kernel_image = kernel_image
        
    def __get_kernel_image(self):
        return self._kernel_image
    
    kernel_image = property(__get_kernel_image, __set_kernel_image,
                            doc="""Path to the kernel image.""")
    
    def __set_kernel_tftp(self, kernel_tftp):
        self._kernel_tftp = kernel_tftp
        
    def __get_kernel_tftp(self):
        return self._kernel_tftp
    
    kernel_tftp = property(__get_kernel_tftp, __set_kernel_tftp,
                            doc="""Enable kernel tftp.""")
    
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
        Flashes  uboot to the given device, using dd.
        
        This method needs`, 
        :attr:`uboot_file` to be already set.
        
        :param device: Device where to flash UBL and uboot (i.e. '/dev/sdb').
        :exception BoardError: On error.
        """
        
        self._l.info('Installing uboot')
        cmd = ('sudo dd' + 
              ' if=' + self._uboot_file + 
              ' of=' + device +
               ' seek=2 bs=512' )
        if self._e.check_call(cmd) != 0:
            raise BoardError('Failed to flash uboot into %s' % device)
    
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
                if self._kernel_tftp:
                    loadtftpimage = 'loadtftpimage=%s'% self._tftp_loader.get_env_load_file_to_ram(
                        self._kernel_image, uboot_load_addr)
                    self._l.debug("  uEnv.txt <= '%s'" % loadtftpimage)
                    uenv.write("%s\n" % loadtftpimage)
                    kernel_load = 'run loadtftpimage'
                else:
                    kernel_load = 'run loaduimage'
                uenvcmd = ('uenvcmd=echo Running uenvcmd ...; %s; '
                           'bootm %s' % (kernel_load, uboot_load_addr))
                self._l.debug("  uEnv.txt <= '%s'" % bootargs)
                uenv.write("%s\n" % bootargs)
                self._l.debug("  uEnv.txt <= '%s'" % uenvcmd)
                uenv.write("%s\n" % uenvcmd)
        cmd = 'sudo cp %s %s' % (uenv_file, mount_point)
        if self._e.check_call(cmd) != 0:
            raise BoardError('Failed to install uboot env file.')

    def install_uboot_bootscript(self, mount_point):
        """
        Installs the uboot script (bootscript) to the given mount point.
        
        This methods needs :attr:`uboot_bootscript` to be already set.
        
        :param mount_point: Path where to install the uboot script.
        :exception BoardError: On error.
        """

        if self._bootscript:
            self._l.info('Installing uboot script')

            cmd = 'sudo cp %s %s/' % (self._bootscript, mount_point)
            if self._e.check_call(cmd) != 0:
                raise BoardError('Failed copying %s to %s' %
                                 (self._bootscript, mount_point))
        else:
            self._l.warning('No bootscript file, omitting...')


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
                    self.install_uboot(sd.name)
                    self.install_uboot_env(mount_point)
                    self.install_uboot_bootscript(mount_point)
                elif comp == SDCardPartition.COMPONENT_KERNEL:
                    if not self._kernel_tftp:
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
                    self.install_uboot(ld.name)
                    self.install_uboot_env(mount_point)
                    self.install_uboot_bootscript(mount_point)
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
        
        for part in sd.partitions:
            for comp in part.components:
                if comp == SDCardPartition.COMPONENT_BOOTLOADER:
                    self.install_uboot(sd.name)
                else:
                    raise BoardError('Invalid component: %s' % comp)

    def install_ld_components_external(self, ld):
        """
        Installs the specified components for each partition, as required
        in external (sd-script) mode.
        
        :exception BoardError: On failure installing the components.
        """
        
        for part in ld.partitions:
            for comp in part.components:
                if comp == LoopDevicePartition.COMPONENT_BOOTLOADER:
                    self.install_uboot(ld.name)
                else:
                    raise BoardError('Invalid component: %s' % comp)
