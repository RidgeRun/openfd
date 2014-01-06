#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012-2013 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# The Executer module is in charge of executing commands in the shell.
#
# ==========================================================================

# ==========================================================================
# Imports
# ==========================================================================

import os
import subprocess
import termcolor
import openfd.utils.logger

# ==========================================================================
# Globals
# ==========================================================================

_executer = None

# ==========================================================================
# Functions
# ==========================================================================

def init_global_executer(dryrun=False, enable_colors=True,
                 verbose=True):
    """
    Inits the global `Executer` instance.
    
    :param name: Name for the global executer instance.
    :returns: The global executer instance.
    """
    
    global _executer
    if not _executer:
        _executer = Executer(dryrun=dryrun, enable_colors=enable_colors,
                             verbose=verbose)
    return _executer

def get_global_executer():
    """
    Returns the global `Executer` instance.
    
    :returns: The global executer instance.
    """
    
    return _executer

# ==========================================================================
# Public classes
# ==========================================================================

class Executer(object):
    """
    Class to execute system commands; based on `subprocess`. Features:

    * Quiet execution - ability to suppress `stdout` and/or `stderr`.
    * Colors - colored output for warning messages (based on `termcolor`).
    * Uniform user prompt - when confirmation from the user is needed.
    * Dryrun mode - system commands will be logged, but not executed.
    """
    
    def __init__(self, dryrun=False, enable_colors=True,
                 verbose=True):    
        """
        :param dryrun: Enable dryrun mode. System commands will be logged,
            but not executed.
        :type dryrun: boolean
        :param enable_colors: Enabled colored messages.
        :type enable_colors: boolean
        :param verbose: Enable verbose mode. System commands will be
                     logged as INFO instead of DEBUG.
        :type verbose: boolean
        """
        
        self._l = openfd.utils.logger.get_global_logger()
        self._dryrun = dryrun
        self._enable_colors = enable_colors
        self._verbose = verbose
    
    def __set_verbose(self, verbose):
        self._verbose = verbose
        
    def __get_verbose(self):
        return self._verbose
    
    verbose = property(__get_verbose, __set_verbose,
                      doc="""Enable verbose mode. System commands will be
                     logged as INFO instead of DEBUG.""")
    
    def __set_dryrun(self, dryrun):
        self._dryrun = dryrun
        
    def __get_dryrun(self):
        return self._dryrun
    
    dryrun = property(__get_dryrun, __set_dryrun,
                      doc="""Enable dryrun mode. System commands will be
                     logged, but not executed.""")
    
    def __set_enable_colors(self, enable):
        self._enable_colors = enable
        
    def __get_enable_colors(self):
        return self._enable_colors
    
    enable_colors = property(__get_enable_colors, __set_enable_colors,
                             doc="""Enable colored messages.""")

    def _log(self, msg):
        if self._l:
            self._l.info(msg) if self._verbose else self._l.debug(msg)

    def _log_cmd(self, cmd):
        self._log("  System <= '%s'" % cmd)
    
    def prompt_sudo(self):
        """
        Prompts the user to enter the sudo password if needed.
        
        :returns: Returns true if the user was authenticated for superuser
            access; false otherwise.
        """
        
        retcode = 0
        if os.geteuid() != 0:
            msg = "[sudo] password for %u: "
            retcode = self.call("sudo -v -p '%s'" % msg)
        return retcode
    
    def prompt_user(self, message, color=''):
        """
        Prints a message to the user and prompts for confirmation.
        
        :param message: Message for the user.
        :type message: string
        :param color: Color for the message, as supported by the `termcolor`
            library: "red", "green", "yellow", "blue", "magenta", "cyan",
            "white". Subject to the value of :func:`enable_colors`.
        :type color: string
        :returns: Returns true if the user confirmed; false otherwise.
        """
        
        if color and self._enable_colors:
            try:
                termcolor.cprint(message, color)
            except KeyError:
                print message
        else:
            print message
        confirmation = ''
        try:
            confirmation = raw_input('Do you want to continue [Y/n]: ')
        except (EOFError, KeyboardInterrupt):
            pass
        return confirmation.strip().upper() == 'Y'

    def check_output(self, cmd, logoutput=False):
        """
        Executes a system command, with the ability to return both the
        output and the return code of the command execution. The output
        will also contain information about the failure of the command
        execution, if any.
        
        :param cmd: Command.
        :type cmd: string
        :param logoutput: Enables logging of both the return code and the
            output of the command.
        :type logoutput: boolean
        :returns: Returns a tuple with two items. The first item is the 
            return code after the command execution. For most commands,
            a return code of 0 represents success. The second item is the
            output of the command. Upon failure, the output will also contain
            information about the exception raised during the command
            execution.
        """
       
        retcode = 0
        output  = ""
        self._log_cmd(cmd)
        if not self._dryrun:
            try:
                output = subprocess.check_output(cmd, shell=True,
                                                 stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                retcode = e.returncode
                output += e.output
        if logoutput and not self._dryrun:
            self._log(output)
        return retcode, output
                        
    def call(self, cmd):
        """
        Executes a system command. For a quiet version use :func:`check_call`.
        
        :param cmd: Command.
        :type cmd: string
        :returns: The return code after the command execution. For most
            commands, a return code of 0 represents success.
        """
        
        retcode = 0
        self._log_cmd(cmd)
        if not self._dryrun:
            try:
                retcode = subprocess.check_call(cmd, shell=True)
            except subprocess.CalledProcessError as e:
                retcode = e.returncode
        return retcode
    
    def check_call(self, cmd):
        """
        Executes a system command redirecting `stdout` and `stderr` to
        `/dev/null`. This is a quiet version of :func:`call`.
        
        :param cmd: Command.
        :type cmd: string
        :returns: The return code after the command execution. For most
            commands, a return code of 0 represents success. 
        """
       
        retcode = 0
        self._log_cmd(cmd)
        if not self._dryrun:
            try:
                retcode = subprocess.check_call(cmd, shell=True,
                                                stdout=open(os.devnull, 'wb'),
                                                stderr=open(os.devnull, 'wb'))
            except subprocess.CalledProcessError as e:
                retcode = e.returncode
        return retcode
