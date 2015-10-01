#!/usr/bin/python

#
# start gshogi from within the source folder
# you must run 'python setup.py build' to build the engine before this will run
#

import sys, os, string

(osname, host, release, version, machine) = os.uname()
osname = string.lower(osname)
osname = string.replace(osname, '/', '')
machine = string.replace(machine, ' ', '_')
machine = string.replace(machine, '/', '-')
plat_name = "%s-%s" % (osname, machine)
plat_specifier = ".%s-%s" % (plat_name, sys.version[0:3])
build_lib = "lib" + plat_specifier
pypath = os.path.join("build", build_lib)
pypath = os.path.join(pypath, "gshogi")
sys.path.append(pypath)

import gshogi.gshogi
gshogi.gshogi.run()
