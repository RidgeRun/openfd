#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013-2014 RidgeRun, LLC (http://www.ridgerun.com)
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Setup installation script.
#
# ==========================================================================

from distutils.core import setup

setup(name='openfd',
      version='0.0.1',
      description='Open Firmware Deployer',
      url='https://github.com/RidgeRun/openfd',
      packages=['openfd', 'openfd/boards', 'openfd/utils', 'openfd/methods',
                'openfd/methods.board', 'openfd/methods.sdcard',
                'openfd/storage'],
      scripts=['openfd/openfd'])
