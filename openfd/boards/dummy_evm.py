#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2013 RidgeRun, LLC (http://www.ridgerun.com)
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Definitions for a Dummy board used for testing.
#
# ==========================================================================

from board import Board

BOARD_NAME = 'dummy-evm'

class DummyEvm(Board):
    mach_description = "Dummy Board"
