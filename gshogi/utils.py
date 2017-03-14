#
#   utils.py
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

from gi.repository import Gtk
from gi.repository import Gdk
import os
import sys
import pickle

from . import load_save
from . import psn
from . import gv
from .constants import VERSION


# Copy the board position to the clipboard in std SFEN format
def copy_SFEN_to_clipboard(action):
    sfen = gv.board.get_sfen()
    copy_text_to_clipboard(sfen)


# paste a position from the clipboard
def paste_clipboard_to_SFEN(action):
    sfen = get_text_from_clipboard()
    if sfen is None:
        gv.gui.info_box("Error: invalid sfen")
        return
    if not validate_sfen(sfen):
        gv.gui.info_box("Error: invalid sfen")
        return
    load_save_ref = load_save.get_ref()
    load_save_ref.init_game(sfen)


# lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1
def validate_sfen(sfen):
    sfenlst = sfen.split()
    num_words = len(sfenlst)
    if num_words != 3 and num_words != 4:
        return False

    if num_words == 3:
        board_state, side_to_move, pieces_in_hand = sfenlst
        move_count = "1"
    else:
        board_state, side_to_move, pieces_in_hand, move_count = sfenlst

    # board_state
    ranks = board_state.split("/")
    if len(ranks) != 9:
        print("board state does not have 9 ranks")
        return False

    # side_to_move
    if side_to_move != "w" and side_to_move != "b":
        print("invalid side to move")
        return False

    # pieces in hand

    # Move Count
    try:
        mc = int(move_count)
    except ValueError:
        print("invalid move count")
        return False

    return True


def copy_game_to_clipboard(action):
    load_save_ref = load_save.get_ref()
    gamestr = load_save_ref.get_game()
    copy_text_to_clipboard(gamestr)


def paste_game_from_clipboard(action):
    gamestr = get_text_from_clipboard()
    if gamestr is None:
        print("Error invalid game data")
        return
    psn_ref = psn.get_ref()
    psn_ref.load_game_psn_from_str(gamestr)


def copy_text_to_clipboard(text):
    # get the clipboard
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    # put the FEN data on the clipboard
    clipboard.set_text(text, -1)
    # make our data available to other applications
    clipboard.store()


def get_text_from_clipboard():
    # get the clipboard
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    # read the text from the clipboard
    text = clipboard.wait_for_text()
    return text


def get_settings_from_file(filepath):
    s = ""
    try:
        settings_file = os.path.join(filepath, "settings")
        f = open(settings_file, "rb")
        s = pickle.load(f)
        f.close()
    except EOFError as eofe:
        print("eof error:", eofe)
    except pickle.PickleError as pe:
        print("pickle error:", pe)
    except IOError as ioe:
        # Normally this error means it is the 1st run and the settings file
        # does not exist
        pass
    except Exception as exc:
        print("Cannot restore settings:", exc)
    #if gv.verbose:
    #    print "values read from settings file"
    #    print "colour_settings:",s.colour_settings
    return s


def get_prefix():
    # prefix to find package files/folders
    prefix = os.path.abspath(os.path.dirname(__file__))
    if gv.verbose:
        print("base directory (prefix) =", prefix)
    return prefix


def create_settings_dir():
    # set up gshogi directory under home directory
    home = os.path.expanduser("~")
    gshogipath = os.path.join(home, ".gshogi")
    if not os.path.exists(gshogipath):
        try:
            os.makedirs(gshogipath)
        except OSError as exc:
            raise
    return gshogipath


def get_verbose():
    verbose = False
    verbose_usi = False
    showmoves = False
    showheader = False
    for arg in sys.argv:
        if arg == "-v" or arg == "--verbose":
            verbose = True
        if arg == "-vusi":
            verbose_usi = True
        if arg == "-m":
            showmoves = True
        if arg == "-h":
            showheader = True
        if arg == "-mh" or arg == "-hm":
            showmoves = True
            showheader = True           
    return verbose, verbose_usi, showmoves, showheader
