#!/usr/bin/python

#
# start gshogi from within the source folder
# you must run "python setup.py build" to build the engine before this will run
#

import sys
import os
import platform
import string

assert sys.version_info >= (3,0)

import gshogi.gv

def get_plat():
    if os.name == 'nt':
        prefix = " bit ("
        i = sys.version.find(prefix)
        if i == -1:
            return sys.platform
        j = sys.version.find(")", i)
        look = sys.version[i+len(prefix):j].lower()
        if look == 'amd64':
            return 'win-amd64'
        if look == 'itanium':
            return 'win-ia64'
        return sys.platform

    # linux
    (osname, host, release, version, machine) = os.uname()
    osname = osname.lower()
    osname = osname.replace("/", "")
    machine = machine.replace(" ", "_")
    machine = machine.replace("/", "-")
    if osname[:5] != "linux":
        print("OS not supported")
    plat_name = "%s-%s" % (osname, machine)
    return plat_name

plat_name = get_plat()
plat_specifier = ".%s-%s" % (plat_name, sys.version[0:3])
build_lib = "lib" + plat_specifier
pypath = os.path.join("build", build_lib, "gshogi")

sys.path.append(pypath)
gshogi.gv.installed = False

import gshogi.gshogi
gshogi.gshogi.run()
