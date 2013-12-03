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
# Common logic to obtain variables from the environment
#
# ==========================================================================

import os

def get_devdir():
    """
    Returns a string with the contents of the DEVDIR environment variable.
    """
    
    devdir = ''
    try:
        devdir = os.environ['DEVDIR'] 
    except KeyError:
        print 'Unable to obtain $DEVDIR from the environment.'
    return devdir
