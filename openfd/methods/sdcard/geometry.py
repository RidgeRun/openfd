#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
#
# Author: Jose Pablo Carballo <jose.carballo@ridgerun.com>
#
# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of 
# RidgeRun, LLC.
#
# Geometry associated definitions.
#
# ==========================================================================

"""
Geometry associated definitions.
"""

# ==========================================================================
# Constants
# ==========================================================================

# Geometry

#: Heads in the unit.
HEADS              = 255.0

#: Sectors in the unit.
SECTORS            = 63.0

#: Sector byte size.
SECTOR_BYTE_SIZE   = 512.0

#: Cylinder byte size: 255 * 63 * 512 = 8225280 bytes.
CYLINDER_BYTE_SIZE = 8225280.0

#: String used to represent the max available size of a given storage device.
FULL_SIZE          = "-"
