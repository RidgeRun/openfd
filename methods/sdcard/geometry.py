#!/usr/bin/env python
# ==========================================================================
#
# Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.
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

Copyright (C) 2012 RidgeRun, LLC (http://www.ridgerun.com)
All Rights Reserved.

The contents of this software are proprietary and confidential to RidgeRun,
LLC.  No part of this program may be photocopied, reproduced or translated
into another programming language without prior written consent of 
RidgeRun, LLC.
"""

# ==========================================================================
# Constants
# ==========================================================================

# Geometry

# Unit: cylinders of 255 * 63 * 512 = 8225280 bytes
HEADS              = 255.0
SECTORS            = 63.0
SECTOR_BYTE_SIZE   = 512.0
CYLINDER_BYTE_SIZE = 8225280.0

# String used to represent the max available size of a given storage device.
FULL_SIZE          = "-"
