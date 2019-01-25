#
# build the opening book
#

import os
import sysconfig
import sys

build_lib = "lib.%s-%s" % (sysconfig.get_platform(), sysconfig.get_python_version())
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
