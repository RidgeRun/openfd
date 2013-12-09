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

BOARD_NAME = 'dm36x-leopard'

class Dm36xLeopard(Board):
    mach_description = "Leopard Board DM36x"
    nand_block_size = 131072
    nand_page_size = 2048
    ipl_name = "ubl"
    ipl_erase_cmd = "nand erase"
    ipl_pre_write_cmd = ""
    ipl_write_cmd = "nand write.ubl"
    ipl_post_write_cmd = ""
    bootloader_name = "uboot"
    bootloader_erase_cmd = "nand erase"
    bootloader_pre_write_cmd = ""
    bootloader_write_cmd = "nand write.ubl"
    bootloader_post_write_cmd = ""
