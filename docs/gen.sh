#!/bin/sh
# 
# Copyright (C) 2013 RidgeRun (http://www.ridgerun.com)
#
# Documentation generator
#

if [ -z "$DEVDIR" ] ; then
  echo " ====== DEVDIR variable is empty, invoke this Makefile from the BSP root, or provide the path to it ====="
  exit -1
fi

echo "Documentation generator"
echo "Copyright (C) 2013 RidgeRun (http://www.ridgerun.com)" 

DOCS_DIR=$DEVDIR/installer/new/installer/docs
SRC_DIR=$DEVDIR/installer/new/installer/

# Generate .rst files
sphinx-apidoc -o $DOCS_DIR $SRC_DIR

# Build the html docs
make clean html

# Open it up
if [ -z "$BROWSER"  ] ; then
  firefox $DOCS_DIR/_build/html/index.html
else
  $BROWSER $DOCS_DIR/_build/html/index.html
fi

