#
#   constants.py
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

NAME = "gshogi"
VERSION = "0.5.1"

# Beep after move - not implemented yet
BEEP = False

# Specify a minimum move time in seconds for engines.
# A value of say 1.0 will mean that there will be
# at least 1 second between moves being displayed.
# This makes it easier to follow when the engines are moving
# very quickly
MIN_MOVETIME = 0.5

# These values match those used in the engine
BLACK = 0
WHITE = 1
NEUTRAL = 2

# Drag and Drop
TARGET_TYPE_TEXT = 1180
