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
# Definitions for the DM36x LeopardBoard.
#
# ==========================================================================

from board import Board

class Dm36xLeopard(Board):
    mach_description = "Leopard Board DM36x"
    ipl_name = "ubl"
    ipl_nand_write_cmd = "nand write.ubl"
    ipl_nand_erase_cmd = "nand erase"
