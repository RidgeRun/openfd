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
# Setup installation script.
#
# ==========================================================================

from distutils.core import setup

setup(name='openfd',
      version='0.0.1',
      description='Open Firmware Installer',
      url='https://github.com/RidgeRun/u-boot-installer',
      packages=['openfd', 'openfd/boards', 'openfd/utils', 'openfd/methods',
                'openfd/methods.board', 'openfd/methods.sdcard',
                'openfd/storage'],
      scripts=['openfd/openfd'])
