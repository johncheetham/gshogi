#
#   load_save.py
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
import os
from datetime import date
import constants
from . import gv
if gv.installed:
    from gshogi import engine
else:
    import engine
from . import move_list
from . import comments
from . import psn
from .constants import WHITE, BLACK


class Load_Save:

    load_save_ref = None

    def __init__(self):
        self.move_list = move_list.get_ref()
        self.psn = psn.get_ref()
        self.comments = comments.get_ref()

    # Load game from a previously saved game
    def load_game(self, b):

        dialog = Gtk.FileChooserDialog(
            _("Load.."), gv.gui.get_window(), Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        #dialog.set_current_folder(os.path.expanduser("~"))
        dialog.set_current_folder(gv.gui.lastdir)
        filter = Gtk.FileFilter()
        filter.set_name("psn files")
        filter.add_pattern("*.psn")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("gshog files")
        filter.add_pattern("*.gshog")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            dialog.destroy()
            return

        fname = dialog.get_filename()
        gv.gui.lastdir = os.path.dirname(fname)
        #if self.verbose == True:       
        #       print ("beim รถffnen " + os.path.dirname(fname))
        gv.gui.window.set_title(constants.NAME + " " + constants.VERSION + "  " + os.path.basename(fname))
        dialog.destroy()

        if fname.endswith(".psn"):
            self.psn.load_game_psn(fname)
            return

        if fname.endswith(".gshog"):
            self.load_game_gshog(fname)
            return

         #loads filename from 1st argument in commandline

    def load_game_parm(self,fname):        
    
        gv.gui.lastdir = os.path.basename(fname)
        gv.gui.window.set_title(constants.NAME + " " + constants.VERSION + "  " + os.path.basename(fname))
        #self.gui.set_status_bar_msg("File: " +os.path.basename(fname)) #!!
        #if self.verbose == True:NAME
                #print("1. Parameter ", fname)
              
        
        if fname.endswith(".psn"):
            self.psn.load_game_psn(fname)
            return

        if fname.endswith(".gshog"):
            self.load_game_gshog(fname)
            return

    # this routine is called from utils.py (when doing paste position)
    # and from gui.py (when ending an edit board session).
    def init_game(self, sfen):
        engine.setfen(sfen)
        startpos = sfen
        sfenlst = sfen.split()
        if sfenlst[1] == "b":
            if gv.verbose:
                print("setting stm to black")
            stm = BLACK
        elif sfenlst[1] == "w":
            stm = WHITE
        else:
            stm = BLACK
        engine.setplayer(stm)

        gv.usib.set_newgame()
        gv.usiw.set_newgame()
        gv.gui.set_status_bar_msg(_("ready"))
        self.gameover = False

        gv.gshogi.set_movelist([])
        gv.gshogi.set_redolist([])
        gv.gshogi.set_startpos(startpos)

        gv.board.update()

        # update move list in move list window
        self.move_list.update()

        stm = gv.gshogi.get_side_to_move()
        gv.gshogi.set_side_to_move(stm)
        gv.gui.set_side_to_move(stm)
        gv.gshogi.set_lastmove("")

        gv.tc.reset_clock()

    def load_game_gshog(self, fname):
        rc = engine.loadgame(fname)
        if (rc > 0):
            gv.gui.set_status_bar_msg(
                "Error 1 loading game - not a valid gshog file")
            return

        self.comments.clear_comments()

        # get movelist
        f = open(fname)
        startmoves = False
        movelist = []
        redolist = []
        startpos = "startpos"
        while 1:
            line = f.readline()
            if not line:
                break
            if line.startswith("startpos"):
                startpos = line[9:].strip()
                if gv.verbose:
                    print("startpos set to", startpos)
                continue
            if startmoves:
                l = line.strip()
                sl = l.split()
                m = sl[0]
                if m.startswith("+"):
                    m = m[1:]
                if m.find("*") != -1:
                    move = m
                else:
                    move = m[1:]
                movelist.append(move)
            if line.startswith("  move   score depth"):
                startmoves = True
        f.close()

        gv.usib.set_newgame()
        gv.usiw.set_newgame()
        gv.gui.set_status_bar_msg("game loaded:  " + fname)
        self.gameover = False

        gv.gshogi.set_movelist(movelist)
        gv.gshogi.set_redolist(redolist)
        gv.gshogi.set_startpos(startpos)

        gv.board.update()
        # update move list in move list window
        self.move_list.update()
        stm = gv.gshogi.get_side_to_move()
        gv.gshogi.set_side_to_move(stm)
        gv.gui.set_side_to_move(stm)
        gv.gshogi.set_lastmove("")
        utils.get_gamelist_ref().set_game_list([])

        gv.tc.reset_clock()

    # called from utils.py as well as from this module
    def get_game(self):

        gamestr = ""
        startpos = gv.gshogi.get_startpos()
        # properties
        dat = str(date.today())
        dat = dat.replace("-", "/")

        zstr = '[Date "' + dat + '"]\n'
        gamestr += zstr

        zstr = '[Sente "' + gv.gshogi.get_player(BLACK).strip() + '"]\n'
        gamestr += zstr

        zstr = '[Gote "' + gv.gshogi.get_player(WHITE).strip() + '"]\n'
        gamestr += zstr

        # sfen
        if startpos == "startpos":
            zstr = '[SFEN "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP' \
                   '/1B5R1/LNSGKGSNL b - 1"]\n'
            gamestr += zstr
        else:
            zstr = '[SFEN "' + startpos + '"]\n'
            gamestr += zstr

        # add comment if present
        comment = self.comments.get_comment(0)
        if comment != "":
            gamestr = gamestr + "{\n" + comment + "\n}\n"

        # if the movelist is positioned part way through the game then
        # we must redo all moves so the full game will be saved
        redo_count = len(gv.gshogi.get_redolist())
        for i in range(0, redo_count):
            gv.gshogi.redo_move()

        # moves
        moveno = 1
        # ml = self.movelist
        mvstr = engine.getmovelist()

        # if we did any redo moves then undo them now to get things back
        # the way they were
        for i in range(0, redo_count):
            gv.gshogi.undo_move()

        if mvstr != "":
            mlst = mvstr.split(",")

            for m in mlst:

                (capture, ispromoted, move) = m.split(";")

                if move.find("*") == -1:
                    m1 = move[0:3]
                    m2 = move[3:]
                    move = m1 + capture + m2
                    if ispromoted == "+":
                        move = "+" + move
                zstr = str(moveno) + "." + move + "\n"
                gamestr += zstr
                # add comment for this move if present
                comment = self.comments.get_comment(moveno)
                if comment != "":
                    gamestr = gamestr + "{" + comment + "}\n"
                moveno += 1
        return (gamestr)

    # Save game to a file
    def save_game(self, b):

        dialog = Gtk.FileChooserDialog(
            _("Save.."), gv.gui.get_window(), Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_current_folder(gv.gui.lastdir)

        filter = Gtk.FileFilter()
        filter.set_name("psn files")
        filter.add_pattern("*.psn")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("gshog files")
        filter.add_pattern("*.gshog")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:

            startpos = gv.gshogi.get_startpos()

            #
            # filename must end with .gshog or .psn
            #
            filename = dialog.get_filename()
            gv.lastdir = os.path.dirname(filename) # !!
            #if self.verbose == True:
                #print("beim Schliessen " + os.path.dirname(filename))
            gv.gui.window.set_title(constants.NAME + " " + constants.VERSION + "  " + os.path.basename(filename))
           
            if not filename.endswith('.gshog') and not filename.endswith('.psn'):
                if dialog.get_filter().get_name() == "psn files":
                    filename = filename + ".psn"
                else:
                    filename = filename + ".gshog"

            # If file already exists then ask before overwriting
            if os.path.isfile(filename):
                resp = gv.gui.ok_cancel_box(
                    _("Warning - file already exists and will be replaced.\n"
                      "Press Cancel if you do not want to overwrite it."))
                if resp == Gtk.ResponseType.CANCEL:
                    dialog.destroy()
                    return

            if filename.endswith(".psn"):
                # save in psn format
                gamestr = self.get_game()
                f = open(filename, "w")
                f.write(gamestr)
                f.close()
            else:
                # save in gshog format
                # engine.command("save " + filename)

                # comments cannot be saved in gshog format
                # if there are comments warn the user
                if self.comments.has_comments():
                    msg = "Warning. This Game has comments which will be " \
                          "lost if you save in this format."
                    msg += "\nTo save the comments save in PSN format instead."
                    gv.gui.info_box(msg)

                # if the movelist is positioned part way through the game then
                # we must redo all moves so the full game will be saved
                redo_count = len(gv.gshogi.get_redolist())
                for i in range(0, redo_count):
                    gv.gshogi.redo_move()

                engine.savegame(filename, "startpos " + startpos + "\n")

                # if we did any redo moves then undo them now to get things
                # back the way they were
                for i in range(0, redo_count):
                    gv.gshogi.undo_move()

            gv.gui.set_status_bar_msg(_("game saved:  " + filename))

        dialog.destroy()


def get_ref():
    if Load_Save.load_save_ref is None:
        Load_Save.load_save_ref = Load_Save()
    return Load_Save.load_save_ref
