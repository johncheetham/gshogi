#
# build the opening book
#

import os
import sys

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

import engine

text_opening_book = "data/gnushogi.tbk"
bin_opening_book = "gshogi/data/opening.bbk"
booksize = 8000
bookmaxply = 40

# check input file exists
if (not os.path.exists(text_opening_book)):
    print("Input file", text_opening_book, "not found")
    sys.exit()

# create data folder for bin book
data_folder = os.path.dirname(bin_opening_book)
if not os.path.exists(data_folder):
    try:
        os.makedirs(data_folder)
    except OSError as exc:
        print("Unable to create data folder", data_folder)
        sys.exit()

# delete the output file if it exists
try:
    os.remove(bin_opening_book)
except OSError as oe:
    pass

# initialise the engine
verbose = False
engine.init(bin_opening_book, verbose)

# call engine function to generate book file
engine.genbook(text_opening_book, bin_opening_book, booksize, bookmaxply)
