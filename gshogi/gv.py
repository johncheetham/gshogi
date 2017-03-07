#
#   gv.py
#
#   This file is part of gshogi
#
#   gshogi is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   gshogi is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with gshogi.  If not, see <http://www.gnu.org/licenses/>.
#

import sys

# Global variables

# gettext/locale translation domain
domain = "gshogi"

# set in run.py
installed = True

# set in gshogi.py
verbose = False
verbose_usi = False
lastdir = ""
event = ""
gamedate = ""
gote = ""
sente = ""

# references to classes that have one instance
gshogi = None
gui = None
pieces = None
tc = None
board = None
usib = None
usiw = None
engine_manager = None
set_board_colours = None

# Make sure no gv global variables have been created elsewhere
# Only those above should be present

modulename = sys.modules[__name__]  # gshogi.gv


def testnames():
    names = dir(modulename)
    for n in names:
        if n not in initial_namelist:
            print("unknown global variable in gv.py:  ",  n  )
initial_namelist = None     # don't remove this line
initial_namelist = dir()
