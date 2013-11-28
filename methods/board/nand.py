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
# Operations on NAND to support the installer.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import re
import time
import ConfigParser
import rrutils
import rrutils.hexutils as hexutils
from partition import NandPartition
import tftp

# ==========================================================================
# Constants
# ==========================================================================

# TFTP settings
DEFAULT_TFTP_DIR = '/srv/tftp'
DEFAULT_TFTP_PORT = 69

# NAND
DEFAULT_NAND_TIMEOUT = 60 # seconds
DEFAULT_NAND_BLK_SIZE = 131072 # bytes
DEFAULT_NAND_PAGE_SIZE = 2048 # bytes

# ==========================================================================
# Public Classes
# ==========================================================================

class NandInstaller(object):
    
    names = {
        'ipl': 'ubl',
        'bootloader': 'uboot',
        'kernel': 'kernel',
        'filesystem': 'rootfs'
    }
    
    erase_cmd = {
        'ipl': 'nand erase',
        'bootloader': 'nand erase',
        'kernel': 'nand erase',
        'filesystem': 'nand erase'
    }
    
    write_cmd = {
        'ipl': 'nand write.ubl',
        'bootloader': 'nand write.ubl',
        'kernel': 'nand write',
        'filesystem': 'nand write'
    }
    
    def __init__(self, uboot, loader, nand_block_size=0, nand_page_size=0,
                 ram_load_addr=None, dryrun=False, interactive=True):
        """
        :param uboot: :class:`Uboot` instance.
        :param nand_block_size: NAND block size (bytes). If not given, the
            value will be obtained from uboot (once).
        :param nand_page_size: NAND page size (bytes). If not given, the
            value will be obtained from uboot (once).
        :param ram_load_addr: RAM address to load components, in decimal or
            hexadecimal (`'0x'` prefix).
        :param dryrun: Enable dryrun mode. System commands will be logged,
            but not executed.
        :type dryrun: boolean
        :param interactive: Enable interactive mode. The user will
            be prompted before executing dangerous commands.
        :type interactive: boolean
        """
        
        self._l = rrutils.logger.get_global_logger()
        self._e = rrutils.executer.get_global_executer()
        self._u = uboot
        self._loader = loader
        self._nand_block_size = nand_block_size
        self._nand_page_size = nand_page_size
        self._ram_load_addr = None
        if hexutils.is_valid_addr(ram_load_addr):
            self._ram_load_addr = hexutils.str_to_hex(str(ram_load_addr))
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        self._u.dryrun = dryrun
        self._loader.dryrun = dryrun
        self._interactive = interactive
        self._partitions = []

    def __set_nand_block_size(self, size):
        self._nand_block_size = int(size)

    def __get_nand_block_size(self):
        
        # Don't query uboot if already set
        if self._nand_block_size != 0:
            return self._nand_block_size
        
        self._l.info("Identifying NAND block size")
        
        self._u.cmd('nand info', prompt_timeout=None)
        
        if self._dryrun: # no need to go further in this mode
            self.nand_block_size = DEFAULT_NAND_BLK_SIZE
            return self._nand_block_size
        
        device_found, line = self._u.expect('Device 0')
        if not device_found:
            self._l.error('Can\'t find Device 0')
            return 0
        
        # Two versions of uboot output:
        # old: Device 0: Samsung K9K1208Q0C at 0x2000000 (64 MB, 16 kB sector)
        # new: Device 0: NAND 256MiB 1,8V 16-bit, sector size 128 KiB
        m = re.match('.* (?P<size_kb>\d+) (kb|kib).*', line, re.IGNORECASE)
        if m:
            self._nand_block_size = int(m.group('size_kb')) << 10 # to bytes
        else:
            self._l.error('Unable to determine the NAND block size')
        self._l.info("NAND block size ... %s" % hex(self._nand_block_size))
        return self._nand_block_size
    
    nand_block_size = property(__get_nand_block_size, __set_nand_block_size, 
                           doc="""NAND block size (bytes). The value will be
                           obtained from uboot (once), unless manually
                           specified.""")
    
    def __set_nand_page_size(self, size):
        self._nand_page_size = int(size)
    
    def __get_nand_page_size(self):
        
        # Don't query uboot if already set
        if self._nand_page_size != 0:
            return self._nand_page_size
        
        self._l.info("Identifying NAND page size")
        
        page_size = 0
        possible_sizes=['0200', '0400', '0800', '1000']
        
        if self._dryrun:
            for size in possible_sizes:
                self._u.cmd('nand dump.oob %s' % size, prompt_timeout=None)
            self._nand_page_size = DEFAULT_NAND_PAGE_SIZE
            return self._nand_page_size
        
        for size in possible_sizes:
            
            self._u.cmd('nand dump.oob %s' % size, prompt_timeout=None)
            found, line = self._u.expect('Page 0000')
            if not found: continue
            
            # Detect the page size upon a change on the output
            m = re.match('^Page 0000(?P<page_size>\d+) .*', line)
            if m:
                page_size = int(m.group('page_size'), 16)
                if page_size != 0:
                    break
                
        if page_size == 0:
            self._l.error('Unable to determine the NAND page size')
        else:
            self._nand_page_size = page_size
            
        self._l.info("NAND page size ... %s" % hex(self._nand_page_size))
        return self._nand_page_size
    
    nand_page_size = property(__get_nand_page_size, __set_nand_page_size,
                          doc="""NAND page size (bytes). The value will be
                           obtained from uboot (once), unless manually
                           specified.""")

    def __set_ram_load_addr(self, ram_load_addr):
        if hexutils.is_valid_addr(ram_load_addr):
            self._ram_load_addr = hexutils.to_hex(str(ram_load_addr))
        else:
            self._l.error('Invalid RAM load address: %s' %
                               ram_load_addr)
            self._ram_load_addr = None
        
    def __get_ram_load_addr(self):
        return self._ram_load_addr
    
    ram_load_addr = property(__get_ram_load_addr, __set_ram_load_addr,
                               doc="""Uboot RAM load address, in decimal or
                                hexadecimal (`'0x'` prefix).""")
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        self._u.dryrun = dryrun
        self._loader.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System commands will be
                     logged, but not executed.""")
    
    def __set_interactive(self, interactive):
        self._interactive = interactive
    
    def __get_interactive(self):
        return self._interactive
    
    interactive = property(__get_interactive, __set_interactive,
                           doc="""Enable interactive mode. The user will
                           be prompted before executing dangerous commands.""")
    
    def _bytes_to_blks(self, size_b):
        size_blks = (size_b / self.nand_block_size)
        if (size_b % self.nand_block_size != 0):
            size_blks += 1
        return size_blks
    
    def _check_icache(self):
        self._u.cmd('icache', prompt_timeout=None)
        found_icache = self._u.expect('Instruction Cache is')[0]
        if not found_icache:
            self._l.error("Your uboot doesn't have icache command, refusing "
               "to continue due to the risk of hanging, you can update your "
               "bootloader by other means like an SD card.")
            return False
        return True    

    def _load_file_to_ram(self, filename, load_addr):
        try:
            self._loader.load_file_to_ram(filename, load_addr)
        except tftp.TftpException as e:
            self._l.error(e)
            return False

    def load_uboot_to_ram(self, img_filename, load_addr):
        """
        Loads an uboot image to RAM and executes it. This uboot will drive
        the installation.
        
        :param img_filename: Path to the uboot image file.
        :param load_addr: Load address in RAM where to load the uboot image.
        """
        
        self._l.info('Loading uboot to RAM')
        
        ret = self._check_icache()
        if ret is False: return False
        
        self._l.debug("Storing the current uboot's bootcmd")
        prev_bootcmd = self._u.get_env('bootcmd')
        self._u.set_env('bootcmd', '')
        self._u.save_env()
        
        ret = self._load_file_to_ram(img_filename, load_addr)
        if ret is False: return False
        
        self._l.debug('Running the new uboot')
        self._u.cmd('icache off')
        self._u.cmd('go %s' % load_addr, echo_timeout=None, prompt_timeout=None)
        time.sleep(2) # Give time to uboot to restart
        ret = self._u.sync()
        if ret is False:
            self._l.error('Failed to detect the new uboot starting')
            return False
        
        if prev_bootcmd:
            self._l.debug('Restoring the previous uboot bootcmd')
            self._u.set_env('bootcmd', prev_bootcmd)
            self._u.save_env()
            
        return True
    
    def _md5sum(self, filename):
        cmd = "md5sum %s | cut -f1 -d' '" % filename
        ret, md5sum = self._e.check_output(cmd)
        return md5sum.strip() if ret == 0 else ''

    def _is_img_install_needed(self, comp_nick, img_env):
        md5sum_on_board = self._u.get_env('%smd5sum' % comp_nick)
        off_on_board = self._u.get_env('%soffset' % comp_nick)
        size_on_board = self._u.get_env('%ssize' % comp_nick)
        part_size_on_board = self._u.get_env('%spartitionsize' % comp_nick)
        if (img_env['md5sum'] != md5sum_on_board or
            img_env['offset'] != off_on_board or
            img_env['size'] != size_on_board or
            img_env['partitionsize'] != part_size_on_board):
            return True
        return False

    def _save_img_env(self, comp_nick, img_env):
        self._u.set_env('%smd5sum' % comp_nick, img_env['md5sum'])
        self._u.set_env('%soffset' % comp_nick, img_env['offset'])
        self._u.set_env('%ssize' % comp_nick, img_env['size'])
        self._u.set_env('%spartitionsize' % comp_nick, img_env['partitionsize'])

    def _install_img(self, filename, comp, comp_nick, start_blk, size_blks=0,
                     force=False):
        self._l.info('Installing %s' % comp)
        offset = start_blk * self.nand_block_size
        img_size_blks = self._bytes_to_blks(os.path.getsize(filename))
        img_size_aligned = img_size_blks * self.nand_block_size
        part_size = img_size_aligned
        if size_blks:
            if img_size_blks > size_blks:
                self._l.warning("Using %s NAND blocks instead of %s for the "
                            "%s partition" % (img_size_blks, size_blks, comp))
            else:
                part_size = size_blks * self.nand_block_size
        
        self._l.debug('Verifying if %s installation is needed' % comp)
        img_env = {'md5sum': self._md5sum(filename),
                   'offset': hex(offset),
                   'size': hex(img_size_aligned),
                   'partitionsize': hex(part_size)}
        if not force and not self._is_img_install_needed(comp_nick, img_env):
            self._l.info("%s doesn't need to be installed" % comp.capitalize())
            return True
        
        self._l.debug("Loading %s image to RAM" % comp)
        self._u.set_env('autostart', 'no')
        ret = self._load_file_to_ram(filename, self._ram_load_addr)
        if ret is False: return False
        self._u.set_env('autostart', 'yes')
        
        self._l.debug("Erasing %s NAND space" % comp)
        cmd = "%s %s %s" % \
                (NandInstaller.erase_cmd[comp], hex(offset), hex(part_size))
        self._u.cmd(cmd, echo_timeout=None, prompt_timeout=DEFAULT_NAND_TIMEOUT)
        
        self._l.debug("Writing %s image from RAM to NAND" % comp)
        cmd = "%s %s %s %s" % (NandInstaller.write_cmd[comp],
                       self._ram_load_addr, hex(offset), hex(img_size_aligned))
        self._u.cmd(cmd, echo_timeout=None, prompt_timeout=DEFAULT_NAND_TIMEOUT)
        
        self._l.debug("Saving %s partition info" % comp)
        self._save_img_env(comp_nick, img_env)
        self._u.save_env()
        
        self._l.info('%s installation complete' % comp.capitalize())
        return True
    
    def install_ipl(self, force=False):
        """
        Installs the UBL (initial program loader) image to NAND. After 
        installing the image it will save in uboot's environment the following
        variables:
        
        * `iploffset`: IPL offset address, hexadecimal.
        * `iplmd5sum`: IPL image md5sum.
        * `iplsize`: IPL size, in bytes.
        * `iplpartitionsize`: IPL partition size, block aligned, in bytes.
        
        This information is also used to avoid re-installing the image if it is
        not necessary, unless `force` is specified.
        
        :param force: Forces the IPL installation.
        :type force: boolean
        :returns: Returns true on success; false otherwise.
        """
        
        for part in self._partitions:
            if part.name == NandInstaller.names['ipl']:
                return self._install_img(part.image, 'ipl', 'ipl',
                             part.start_blk, part.size_blks, force)
        return True

    def install_bootloader(self):
        """
        Installs the uboot image to NAND.
        
        :returns: Returns true on success; false otherwise.
        """
        
        for part in self._partitions:
            if part.name == NandInstaller.names['bootloader']:
                
                self._l.info('Installing bootloader')
                
                self._l.debug("Loading uboot image to RAM")
                ret = self._load_file_to_ram(part.image, self._ram_load_addr)
                if ret is False: return False
        
                offset = part.start_blk * self.nand_block_size
                img_size_blk = self._bytes_to_blks(os.path.getsize(part.image))
                img_size_aligned = img_size_blk * self.nand_block_size
        
                self._u.set_env('autostart', 'no')
                self._u.save_env()
        
                self._l.debug("Erasing uboot NAND space")
                cmd = "%s %s %s" % (NandInstaller.erase_cmd['bootloader'],
                                        hex(offset), hex(img_size_aligned))
                self._u.cmd(cmd, echo_timeout=None, prompt_timeout=DEFAULT_NAND_TIMEOUT)
                
                self._l.debug("Writing uboot image from RAM to NAND")
                cmd = "%s %s %s %s" % (NandInstaller.write_cmd['bootloader'],
                        self._ram_load_addr, hex(offset), hex(img_size_aligned))
                self._u.cmd(cmd, echo_timeout=None, prompt_timeout=None)
                
                self._l.debug("Restarting to use the uboot in NAND")
                self._u.cmd('reset', prompt_timeout=None)
                found_reset_str = self._u.expect('U-Boot', timeout=10)[0]
                if not found_reset_str:
                    self._l.error("Failed to detect the uboot in NAND restarting")
                    return False
                time.sleep(4) # Give uboot time to initialize
                ret = self._u.sync()
                if ret is False:
                    self._l.error("Failed synchronizing with the uboot in NAND")
                    return False
                
                self._u.set_env('autostart', 'yes')
                self._u.save_env()
                
                self._l.info('Bootloader installation complete')
        return True

    def install_kernel(self, force=False):
        """
        Installs the kernel image to NAND. After installing the image it
        will save in uboot's environment the following variables:
        
        * `koffset`: Kernel offset address, hexadecimal.
        * `kmd5sum`: Kernel image md5sum.
        * `ksize`: Kernel size, in bytes.
        * `kpartitionsize`: Kernel partition size, block aligned, in bytes.
        
        This information is also used to avoid re-installing the image if it is
        not necessary, unless `force` is specified.
        
        :param force: Forces the kernel installation.
        :type force: boolean
        :returns: Returns true on success; false otherwise.
        """
        
        for part in self._partitions:
            if part.name == NandInstaller.names['kernel']:
                return self._install_img(part.image, 'kernel', 'k',
                                         part.start_blk, part.size_blks, force)
        return True
    
    def install_fs(self, force=False):
        """
        Installs the filesystem image to NAND. After installing the image it
        will save in uboot's environment the following variables:
        
        * `fsoffset`: Filesystem offset address, hexadecimal.
        * `fsmd5sum`: Filesystem image md5sum.
        * `fssize`: Filesystem size, in bytes.
        * `fspartitionsize`: Filesystem partition size, block aligned, in bytes.
        
        This information is also used to avoid re-installing the image if it is
        not necessary, unless `force` is specified.
        
        :param force: Forces the filesystem installation.
        :type force: boolean
        :returns: Returns true on success; false otherwise.
        """
        
        for part in self._partitions:
            if part.name == NandInstaller.names['filesystem']:
                return self._install_img(part.image, 'filesystem', 'fs',
                                         part.start_blk, part.size_blks, force)
        return True

    def install_cmdline(self, cmdline, force=False):
        """
        Installs the kernel command line to uboot's environment. If the same
        command line has already been installed it will avoid re-installing it, 
        unless `force` is specified.

        :param cmdline: Kernel command line.
        :param force: Forces the kernel command line installation.
        :type force: boolean
        :returns: Returns true on success; false otherwise.
        """
        
        self._l.info("Installing kernel cmdline")
        cmdline = cmdline.strip()
        self._l.debug("Verifying if cmdline installation is needed")
        if not force:
            cmdline_on_board = self._u.get_env('bootargs')        
            if cmdline == cmdline_on_board and not force:
                self._l.info("Kernel cmdline doesn't need to be installed")
                return True
        self._u.set_env('bootargs', "'%s'" % cmdline)
        self._u.save_env()
        self._l.info("Kernel cmdline installation complete")
        return True

    def install_bootcmd(self, bootcmd, force=False):
        """
        Installs the boot command (`bootcmd`) to uboot's environment. If the
        same boot command has already been installed it will avoid
        re-installing it, unless `force` is specified.

        :param bootcmd: Boot command.
        :param force: Forces the boot command installation.
        :type force: boolean
        :returns: Returns true on success; false otherwise.
        """
        
        self._l.info("Installing bootcmd")
        bootcmd = bootcmd.strip()
        if not force:
            self._l.debug("Verifying if bootcmd installation is needed")
            bootcmd_on_board = self._u.get_env('bootcmd')
            if bootcmd == bootcmd_on_board and not force:
                self._l.info("Uboot's bootcmd doesn't need to be installed")
                return True
        self._u.set_env('bootcmd', bootcmd)
        self._u.save_env()
        self._l.info("Bootcmd installation complete")
        return True
        
    def install_mtdparts(self, mtdparts, force=False):
        """
        Installs mtdparts to uboot's environment. If the same mtdparts has
        already been installed it will avoid re-installing it, unless `force`
        is specified.

        :param mtdparts: Mtdparts.
        :param force: Forces the mtdparts installation.
        :type force: boolean
        :returns: Returns true on success; false otherwise.
        """
        
        self._l.info("Installing mtdparts")
        mtdparts = mtdparts.strip()
        if not force:
            self._l.debug("Verifying if mtdparts installation is needed")
            mtdparts_on_board = self._u.get_env('mtdparts')
            if mtdparts == mtdparts_on_board and not force:
                self._l.info("Uboot's mtdparts doesn't need to be installed")
                return True
        self._u.set_env('mtdparts', mtdparts)
        self._u.save_env()
        self._l.info("Mtdparts installation complete")
        return True
        
    def read_partitions(self, filename):
        """
        Reads the partitions information from the given file.
        
        :param filename: Path to the file with the partitions information.
        :returns: Returns true on success; false otherwise.  
        """
        
        self._partitions[:] = []
        self._l.debug('Reading file %s' % filename)
        config = ConfigParser.RawConfigParser()
        config.readfp(open(filename))
        for section in config.sections():
            if config.has_option(section, 'name'):
                part = NandPartition(config.get(section, 'name'))
                if config.has_option(section, 'start_blk'):
                    part.start_blk = int(config.get(section, 'start_blk'))
                if config.has_option(section, 'size_blks'):
                    part.size_blks = int(config.get(section, 'size_blks'))
                if config.has_option(section, 'filesystem'):
                    part.filesystem = config.get(section, 'filesystem')
                if config.has_option(section, 'image'):
                    part.image = config.get(section, 'image')
                # insert ordered by start blk
                inserted = False
                for i in range(0, len(self._partitions)):
                    if self._partitions[i].start_blk > part.start_blk:
                        self._partitions.insert(i, part)
                        inserted = True
                        break
                if not inserted:
                    self._partitions.append(part)
        return True

class NandInstallerTFTP(NandInstaller):
    
    #: Static networking mode.
    MODE_STATIC = 'static'
    
    #: DHCP networking mode.
    MODE_DHCP = 'dhcp'
    
    def __init__(self, uboot, loader, nand_block_size=0, nand_page_size=0,
                 ram_load_addr=None, dryrun=False, interactive=True):
        """
        :param uboot: :class:`Uboot` instance.
        :param nand_block_size: NAND block size (bytes). If not given, the
            value will be obtained from uboot (once).
        :param nand_page_size: NAND page size (bytes). If not given, the
            value will be obtained from uboot (once).
        :param ram_load_addr: RAM address to load components, in decimal or
            hexadecimal (`'0x'` prefix).
        :param dryrun: Enable dryrun mode. System commands will be logged,
            but not executed.
        :type dryrun: boolean
        :param interactive: Enable interactive mode. The user will
            be prompted before executing dangerous commands.
        :type interactive: boolean
        :param host_ipaddr: Host IP address.
        :param target_ipaddr: Target IP address, only necessary
            in :const:`MODE_STATIC`.
        :param tftp_dir: TFTP root directory.
        :param tftp_port: TFTP server port.
        :type tftp_port: integer
        :param net_mode: Networking mode. Possible values:
            :const:`MODE_STATIC`, :const:`MODE_DHCP`.
        """    
        NandInstaller.__init__(self, uboot, nand_block_size, nand_page_size,
                               ram_load_addr, dryrun, interactive)
        self._loader = loader
        
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        self._e.dryrun = dryrun
        self._u.dryrun = dryrun
        self._loader.dryrun = dryrun
    
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                     doc="""Enable dryrun mode. System and uboot commands will
                     be logged, but not executed.""")
        
    def _load_file_to_ram(self, filename, load_addr):
        pass
        
