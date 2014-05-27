#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2014 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Definitions for the DM814x board.
#
# ==========================================================================

from dm816x import Dm816x

BOARD_NAME = 'dm814x'

class Dm814x(Dm816x):
    mach_description = "DM814x Board"
