#!/usr/bin/python

#
# start gshogi from within the source folder
# you must run "python setup.py build" to build the engine before this will run
#

import sys
import sysconfig
import os

assert sys.version_info >= (3,0)

import gshogi.gv

build_lib = "lib.%s-%s" % (sysconfig.get_platform(), sysconfig.get_python_version())
pypath = os.path.join("build", build_lib, "gshogi")

sys.path.append(pypath)
gshogi.gv.installed = False

import gshogi.gshogi
gshogi.gshogi.run()
