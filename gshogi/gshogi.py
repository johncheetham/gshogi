#
#   gshogi 0.5.0
#
#   Copyright (C) 2010-2016 John Cheetham
#
#   web   : http://www.johncheetham.com/projects/gshogi
#   email : developer@johncheetham.com
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
#/home/bernd/Downloads/gshogi-0.5.0/B_3f gegen Spearing the sparrow-Quest.psn
#   You should have received a copy of the GNU General Public License
#   along with gshogi.  If not, see <http://www.gnu.org/licenses/>.
#

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GLib
import _thread
import traceback
import os
import sys
import pickle
import time
from datetime import date

from . import gv
if gv.installed:
   from gshogi import engine
else:
   import engine
from . import utils
from . import gui
from . import usi
#from . import  sys
from . import engine_manager
from . import time_control
from . import set_board_colours
from . import move_list
from . import comments
from . import board
from . import pieces
from . import engine_output
from .constants import WHITE, BLACK, NEUTRAL, NAME, VERSION, BEEP, MIN_MOVETIME


class Game:

    def __init__(self):

        gv.gshogi = self
        self.xname = ""
        
        Filefound = False
        # set global variables for debug messages
        gv.verbose, gv.verbose_usi, gv.show_moves, gv.show_header = utils.get_verbose()
    
        # prefix to find package files/folders
        self.prefix = utils.get_prefix()
        # set up .gshogi directory in the home directory
        self.gshogipath = utils.create_settings_dir()
        self.glade_dir = os.path.join(self.prefix, "glade")
        # get settings saved from previous game
        self.settings = utils.get_settings_from_file(self.gshogipath)
        # Filename from command line
        Startfilename = False
        for arg in range(1, len(sys.argv)):
                 if (sys.argv[arg] != '-v' and sys.argv[arg] != '-vusi' and sys.argv[arg] !=""):
                        if (sys.argv[arg].find(":")!= -1 or sys.argv[arg].startswith("/")) :
                                Startfilename = True
                        if Startfilename == True:
                                self.xname = self.xname + " " + sys.argv[arg] #single file from command-line
                                #print (sys.argv[arg] + "   "+ str(arg) +"    "+ self.xname)
                                if sys.argv[arg].find(".psn") != -1:
                                        Filefound = True
                                        break
                                if sys.argv[arg].find(".gshog") != -1:
                                        Filefound = True
                                        break
        self.xname = self.xname.strip()
        if gv.verbose == True :
                print("Filename read:  " + self.xname + "  File:"+ str(Filefound) +"   "+VERSION)
        self.ask_before_promoting = False
       
        self.gameover = False
        self.time_limit = "00:10"
        self.stopped = True
        self.quitting = False
        self.src = ""
        self.src_x = ""
        self.src_y = ""
        self.startpos = "startpos"
        self.start_stm = BLACK

        self.search_depth = 39
        self.thinking = False
        self.cmove = "none"
        self.movelist = []
        self.lastmove = ""
        self.redolist = []
        self.player = ["Human", "gshogi"]
        self.pondermove = [None, None]

        opening_book_path = os.path.join(self.prefix, "data/opening.bbk")
        engine.init(opening_book_path, gv.verbose)

        gv.gui = gui.Gui()

        gv.pieces = pieces.Pieces()
        # custom pieceset path
        if self.settings != "":
            gv.pieces.set_custom_pieceset_path(
                self.settings.custom_pieceset_path)
        gv.pieces.load_pieces(self.prefix)

        # usiw is the instance that plays white (gote)
        # usib is the instance that plays black (sente)
        gv.usib = usi.Usi("b")
        gv.usiw = usi.Usi("w")

        # instantiate board, gui, classes
        gv.tc = time_control.Time_Control()
        gv.engine_manager = engine_manager.Engine_Manager()
        gv.board = board.Board()

        gv.set_board_colours = set_board_colours.Set_Board_Colours(self.prefix)
        # set colours to previous game (if any)
        if self.settings != "":
            gv.set_board_colours.restore_colour_settings(
                self.settings.colour_settings)
        gv.gui.build_gui()
        gv.board.build_board()
        self.engine_output = engine_output.get_ref()

        # set level
        command = "level 0 " + self.time_limit
        engine.command(command)
        # turn off beeps
        if not BEEP:
            engine.command("beep")

        # restore users settings to values from previous game
        self.restore_settings(self.settings)

        gv.usib.set_engine(self.player[BLACK], None)
        gv.usiw.set_engine(self.player[WHITE], None)
        gv.gui.update_toolbar(self.player)

        self.move_list = move_list.get_ref()

        gv.tc.reset_clock()

        gv.gui.enable_go_button()
        gv.gui.disable_stop_button()

        self.stm = self.get_side_to_move()
        self.timer_active = False
        gv.set_board_colours.apply_colour_settings()
        if Filefound==True:
            gv.lastdir = os.path.dirname(self.xname)
            # single file from command-line
            gv.gui.load_save.load_game_parm(self.xname)

    #
    # Process Human move
    #
    def square_clicked(self, widget, event, data):
        # if in edit board mode then call routine in gui.py to show the edit
        # popup menu
        if gv.gui.get_edit_mode():
            (x, y) = data
            gv.gui.show_edit_popup(event, x, y)
            return

        if self.gameover or self.thinking or self.stopped:
            return

        self.stm = self.get_side_to_move()
        if self.player[self.stm] != "Human":
            return
        gv.gui.set_side_to_move(self.stm)

        # get x,y co-ords of square clicked on (0, 0 is top left)
        (x, y) = data

        # convert the x, y co-ords into the shogi representation
        # (e.g. 8, 6 is 1g)
        sq = gv.board.get_square_posn(x, y)

        # if the square clicked on is a valid source square
        # then set this square as the source square
        if gv.board.valid_source_square(x, y, self.stm):
            self.src = sq
            if gv.verbose:
                print("source square: (x, y) = (", x, ",",  y, ") ", sq)
            self.src_x = x
            self.src_y = y
            self.piece = gv.board.get_piece(x, y)
            # hilite square clicked on
            gv.board.update(squares_to_hilite=(self.src,))
            return

        # must have a valid source square before checking dest square
        if self.src == "":
            return

        # Not a valid source square, assume destination square
        dst = sq

        move = self.get_move(self.piece, self.src, dst, self.src_x,
                             self.src_y, x, y)
        if move is None:
            return

        # display the move
        self.human_move(move)

    # format human move
    def get_move(self, piece, src, dst, src_x, src_y, dst_x, dst_y):
        if gv.verbose:
            print("in get move")
            print("src=", src)
            print("dst=", dst)
            print("src_x=", src_x)
            print("src_y=", src_y)
            print("dst_x=", dst_x)
            print("dst_y=", dst_y)

        move = self.src + dst
        # check for promotion
        if self.promotion_zone(src, dst, self.stm):
            promote = gv.board.promote(piece, src_x, src_y, dst_x, dst_y,
                                       self.stm)
            if (promote == 2):
                # must promote
                move = move + "+"
            elif (promote == 1):
                # promotion is optional
                #
                # But always prompt before promoting a silver since it
                # can be valuable to have an unpromoted silver on the
                # opposite side of the board.
                if self.ask_before_promoting or piece == " s" or piece == " S":
                    response = gv.gui.promote_popup()
                    if (response == Gtk.ResponseType.CANCEL):
                        return None
                    if (response == Gtk.ResponseType.YES):
                        move = move + "+"
                else:
                    move = move + "+"

        if gv.verbose:
            print("move=", move)

        engine.setplayer(self.stm)
        validmove = engine.hmove(move)
        if (not validmove):
            # illegal move
            gv.gui.set_status_bar_msg(_("Illegal Move"))
            return None
        return move

    def human_move(self, move):
        self.movelist.append(move)
        self.redolist = []
        self.lastmove = move

        gv.board.update()

        # update move list in move list window
        self.move_list.update()

        if gv.verbose:
            engine.command("bd")
        self.src = ""

        self.gameover, msg = self.check_for_gameover()
        if (self.gameover):
            self.stop()
            gv.gui.set_status_bar_msg(msg)         
            self.automatic_comment( msg,len(self.movelist))
            self.thinking = False
            return

        self.stm = self.get_side_to_move()
        gv.gui.set_side_to_move(self.stm)
        if gv.verbose:
            print("#")
            print("# " + self.get_side_to_move_string(self.stm) + _(" to move"))
            print("#")
        gv.gui.set_status_bar_msg(" ")

        self.src = ""

        # update time for last move
        gv.tc.update_clock()

        gv.gui.apply_drag_and_drop_settings(self.player[self.stm], self.stm)

        if self.player[self.stm] == "Human":

            # set clock ready for move to come
            gv.tc.start_clock(self.stm)

            if not self.timer_active:
                GObject.timeout_add(1000, gv.tc.show_time)

            return

        self.thinking = True
        # disable some functionality while the computer is thinking
        # gv.gui.disable_menu_items()

        # it's the computers turn to move. Kick off a separate thread for
        # computers move so that gui is still useable
        self.ct = _thread.start_new_thread(self.computer_move, ())

        return
     
    def automatic_comment(self,text,moveno):
       maxm = moveno
       # extend comment list if it is shorter than movelist
       while len(self.move_list.comments.comment_list) <= moveno:
          self.move_list.comments.comment_list.append("")
       text1 = self.move_list.comments.comment_list[moveno]
       self.move_list.comments.comment_list[moveno] = text1 + text  #append comments
       #print("Update")
       #self.move_list.update()
       #Do not call update here: leads to segfault from errors deep inside PyGtk

    def stop_clicked(self, widget):
        self.stop()

    def stop(self):
        self.stopped = True
        gv.gui.enable_menu_items()
        gv.gui.enable_go_button()
        gv.gui.disable_stop_button()
        gv.gui.unset_all_drag_and_drop_squares()

        # update time
        gv.tc.stop_clock()

        # stop engines
        gv.usib.stop_engine()
        gv.usiw.stop_engine()
        engine.movenow()
        gv.gui.set_status_bar_msg(_("stopped"))

    def go_clicked(self, widget):

        # update time control prior to move
        gv.tc.update_gui_time_control(self.stm)

        # side to move
        self.stm = self.get_side_to_move()

        # start a timer to display the time left while the player is thinking
        gv.tc.start_clock(self.stm)

        if not self.timer_active:
            GObject.timeout_add(1000, gv.tc.show_time)

        gv.gui.disable_menu_items()
        gv.gui.disable_go_button()
        gv.gui.enable_stop_button()

        self.stopped = False

        if gv.verbose:
            print("#")
            print("# " + self.get_side_to_move_string(self.stm) + " to move")
            print("#")

        gv.gui.apply_drag_and_drop_settings(self.player[self.stm], self.stm)

        # gv.board.reduce_board_history(self.movelist)
        self.engine_output.clear("w", " ")
        self.engine_output.clear("b", " ")

        if self.player[self.stm] == "Human":
            gv.gui.set_status_bar_msg(_("ready"))
            return

        gv.gui.set_status_bar_msg(_("Thinking ..."))
        # it's the computers turn to move. kick off a separate thread for
        # computers move so that gui is still useable
        self.ct = _thread.start_new_thread(self.computer_move, ())

    def cap_square_clicked(self, widget, event, data):

        # if in edit board mode then call routines in board.py to change the
        # piece count in the komadai
        if gv.gui.get_edit_mode():
            x, y, colour = data
            if event.button == 1:
                # left click - decrement count for the piece clicked on
                gv.board.decrement_cap_piece(y, colour)
            elif event.button == 3:
                # right click - increment count for the piece clicked on
                gv.board.increment_cap_piece(y, colour)
            return

        if self.gameover or self.thinking:
            return

        x, y, colour = data

        # If user clicked in the black capture area and it's white to move or
        # vice versa then ignore
        stm = self.get_side_to_move()
        if stm != colour:
            return

        self.src_x = x
        self.src_y = y
        self.piece = gv.board.get_cap_piece(y, stm)

        if (self.piece != "-"):
            self.src = self.piece + "*"
        else:
            self.src = ""

    def get_prefix(self):
        return self.prefix

    def get_glade_dir(self):
        return self.glade_dir

    def computer_move(self):
        try:
            self.thinking = True

            while True:
                self.thinking = True
                self.stm = self.get_side_to_move()

                # update time for last move
                # gv.tc.update_clock()
                GLib.idle_add(gv.gui.set_side_to_move, self.stm)
                # set clock ready for move to come
                # gv.tc.start_clock(self.stm)

                if gv.verbose:
                    print("#")
                    print(("# " + self.get_side_to_move_string(self.stm) +
                          " to move"))
                    print("#")

                if self.player[self.stm] == "Human":
                    GLib.idle_add(gv.gui.apply_drag_and_drop_settings,
                        self.player[self.stm], self.stm)
                    self.thinking = False
                    gv.tc.start_clock(self.stm)
                    return

                t_start = time.time()
                if self.player[self.stm] != "gshogi":
                    if self.stm == BLACK:
                        self.usi = gv.usib
                        # usi_opponent = self.usiw
                        # opponent_stm = WHITE
                    else:
                        self.usi = gv.usiw
                        # usi_opponent = self.usib
                        # opponent_stm = BLACK

                    ponder_enabled = gv.engine_manager.get_ponder()

                    if not ponder_enabled:
                        # get engines move
                        self.cmove, self.pondermove[self.stm] = self.usi.cmove(
                            self.movelist, self.stm)
                    else:
                        # pondering
                        ponderhit = False
                        if (self.pondermove[self.stm] is not None and
                                len(self.movelist) > 0):
                            if (self.movelist[-1] ==
                                    self.pondermove[self.stm]):
                                ponderhit = True

                        if ponderhit:
                            # ponderhit, wait for return of bestmove and
                            # pondermove
                            self.cmove, self.pondermove[self.stm] = \
                                self.usi.send_ponderhit(self.stm)
                        else:
                            if self.pondermove[self.stm] is not None:
                                # stop ponder, wait for return of bestmove and
                                # pondermove from ponder
                                bm, pm = self.usi.stop_ponder()
                            # get engines move
                            self.cmove, self.pondermove[self.stm] = \
                                self.usi.cmove(self.movelist, self.stm)

                        # start pondering
                        if self.pondermove[self.stm] is not None:
                            # send position and ponder command,
                            # return immediately
                            self.usi.start_ponder(
                                self.pondermove[self.stm],
                                self.movelist, self.cmove)

                    if self.stopped or self.cmove is None:
                        self.thinking = False
                        return

                    if gv.verbose:
                        print("computer move is", self.cmove)
                    # check if player resigned
                    if self.cmove == "resign":
                        if gv.verbose:
                            print("computer resigned")
                        self.gameover = True
                        self.thinking = False
                        colour = self.get_side_to_move_string(self.stm)
                        msg = _("  game over - ") + colour + _(" resigned")
                        GLib.idle_add(self.stop)
                        GLib.idle_add(gv.gui.set_status_bar_msg, msg)
                        self.automatic_comment(self.cmove + ":  "+ _(msg),len(self.movelist))
                        self.thinking = False
                        return

                    # engine.setplayer(WHITE)
                    engine.setplayer(self.stm)
                    validmove = engine.hmove(self.cmove)
                    if (not validmove):
                        GLib.idle_add(self.stop)
                        GLib.idle_add(gv.gui.set_status_bar_msg,
                            self.cmove + _(" - computer made illegal Move!"))
                        self.gameover = True
                        self.thinking = False
                        self.automatic_comment(self.cmove + _(" - computer made illegal Move!"),len(self.movelist))
                        return
                    if gv.verbose:
                        engine.command("bd")
                else:

                    if gv.verbose:
                        print("using gshogi builtin engine")
                    #
                    # We are using the builtin gshogi engine (not a USI engine)
                    #

                    if self.player[self.stm ^ 1] == "Human":
                        GLib.idle_add(gv.gui.set_status_bar_msg,
                             _("Thinking ..."))

                    # set the computer to black or white
                    engine.setplayer(self.stm ^ 1)

                    # start the clock
                    # print "starting clock from gshogi.py"
                    gv.tc.start_clock(self.stm)

                    # set time limit/level for move in gshogi engine
                    gv.tc.set_gshogi_time_limit(self.stm)

                    # call the gshogi engine to do the move
                    self.cmove = engine.cmove()

                    # update time for last move
                    # print "updating clock from gshogi.py"
                    GLib.idle_add(gv.tc.update_clock)

                    # if the engine moved very fast then wait a bit
                    # before displaying the move. The time to wait
                    # is in MIN_MOVETIME in constants.py
                    t_end = time.time()
                    move_t = t_end - t_start
                    if move_t < MIN_MOVETIME:
                        diff = MIN_MOVETIME - move_t
                        time.sleep(diff)

                    GLib.idle_add(gv.gui.set_side_to_move, self.stm)

                    if self.quitting:
                        return

                    if self.stopped:
                        self.thinking = False
                        GLib.idle_add(gv.gui.set_status_bar_msg, _("stopped"))
                        engine.command("undo")
                        return

                if self.cmove != "":
                    self.movelist.append(self.cmove)
                    self.redolist = []
                    self.lastmove = self.cmove
                else:
                    # empty move is returned by gshogi engine when it is in
                    # checkmate
                    if gv.verbose:
                        print("empty move returned by engine")

                # if program is exitting then quit this thread asap
                if self.quitting:
                    return

                # gv.board.save_board(len(self.movelist))
                # show computer move
                GLib.idle_add(gv.board.update)
                GLib.idle_add(self.move_list.update)
        
                # if self.player[self.stm] != "gshogi"
                #     and gv.engine_manager.get_ponder():
                #     self.usi.send_ponder()
                #     # self.ctp= thread.start_new_thread(
                #     self.usi.send_ponder, () )

                if gv.verbose:
                    engine.command("bd")

                if gv.verbose:
                    print("move=", self.cmove)
                msg = self.cmove

                self.gameover, gmsg = self.check_for_gameover()
                if (self.gameover):
                    msg = self.get_side_to_move_string(self.stm) + ": " 
                    msg = msg + gmsg
                    self.thinking = False
                    self.stm = self.get_side_to_move()
                    GLib.idle_add(self.stop)
                    GLib.idle_add(gv.gui.set_side_to_move, self.stm)
                    GLib.idle_add(gv.gui.set_status_bar_msg, msg)
                    self.automatic_comment(msg,len(self.movelist))
                    return

                msg = self.get_side_to_move_string(self.stm) + ": " + str(len(self.movelist)) + ". " + msg                             
                GLib.idle_add(gv.gui.set_status_bar_msg, msg)
                # give gui time to update the board
                time.sleep(0.1)
            self.thinking = False
        except:
            traceback.print_exc()
            return

    def check_for_gameover(self):
        gameover = False
        msg = ""
        winner = engine.getwinner()
        if (winner):
            gameover = True
            winner -= 1
            if (winner == BLACK):
                msg = _("game over - black wins")
            elif (winner == WHITE):
                msg = _("game over - white wins")
            elif (winner == NEUTRAL):
                msg = _("game over - match drawn")
            else:
                print("invalid value returned from engine getwinner function")
        return gameover, msg

    def set_promotion_mode(self, mode):
        self.ask_before_promoting = mode
    
    

    def promotion_zone(self, src, dst, stm):
        srclet = src[1:2]
        dstlet = dst[1:2]

        # can't promote dropped pieces
        if srclet == "*":
            return False

        if stm == BLACK:
            if (srclet < "d" and srclet != "*") or dstlet < "d":
                return True
            else:
                return False
        else:
            if (srclet > "f" and srclet != "*") or dstlet > "f":
                return True
            else:
                return False

    #
    # Callback Functions
    #

    def quit_game(self, b):
        if gv.verbose:
            gv.testnames()
        self.quit()
        return False

    # This callback quits the program
    def delete_event(self, widget, event, data=None):
        if gv.verbose:
            gv.testnames()
        self.quit()
        return False

    def quit(self):
        self.stopped = True
        self.quitting = True
        engine.movenow()
        self.save_settings()
        gv.usib.stop_engine()
        gv.usiw.stop_engine()
        Gtk.main_quit()
        return False

    def quitting(self):
        return self.quitting

    #
    # called from menu by new game and new handicap game
    #
    def new_game_cb(self, action):
        menu_name = action.get_name()
        self.new_game(menu_name)

    # called from new_game_cb in this module and from load_game_psn_from_str
    # in psn.py
    def new_game(self, menu_name):

        self.gameover = False
        engine.command("new")

        if menu_name == "NewGame":
            # Normal Game (No handicap)
            self.startpos = "startpos"
            self.start_stm = BLACK
        else:
            # Handicap Game
            self.start_stm = WHITE
            if menu_name == "LanceHandicap":
                sfen = "lnsgkgsn1/1r5b1/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "BishopHandicap":
                sfen = "lnsgkgsnl/1r7/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "RookHandicap":
                sfen = "lnsgkgsnl/7b1/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "RookandLanceHandicap":
                sfen = "lnsgkgsn1/7b1/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "TwoPieceHandicap":
                sfen = "lnsgkgsnl/9/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "FourPieceHandicap":
                sfen = "1nsgkgsn1/9/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "SixPieceHandicap":
                sfen = "2sgkgs2/9/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "EightPieceHandicap":
                sfen = "3gkg3/9/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "TenPieceHandicap":
                sfen = "4k4/9/ppppppppp/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            elif menu_name == "ThreePawnHandicap":
                sfen = "4k4/9/9/9/9/9/" \
                       "PPPPPPPPP/1B5R1/LNSGKGSNL w 3p - 1"
            else:
                gv.gui.info_box("Error. Invalid menu name:" + menu_name)
                return

            engine.setfen(sfen)
            self.startpos = sfen

        gv.board.update()
        # update move list in move list window
        self.move_list.update()
        # clean comments (bugfix)
        self.move_list.comments.clear_comments()
        if not BEEP:
            engine.command("beep")

        gv.usib.set_newgame()
        gv.usiw.set_newgame()
        self.movelist = []
        self.redolist = []
        self.lastmove = ""
        #clear comment-and move windows
        #self.move_list.comments.automatic_comment("") # just a  Test
        #print("test")
        if gv.show_moves == True:
           start, end =gv.gui.comment_view.get_buffer().get_bounds()
           gv.gui.comment_view.get_buffer().delete(start,end)
           gv.gui.comment_view.get_buffer().insert(start,"-")        
           gv.gui.move_view.get_model().clear()
        gv.gui.set_status_bar_msg("")
        self.stm = self.get_side_to_move()
        gv.gui.set_side_to_move(self.stm)
        gv.tc.reset_clock()
        gv.event = "##"
        gv.gamedate = str(date.today().day) +"."+str(date.today().month)+"."+str(date.today().year)
        gv.gote = self.player[BLACK]
        gv.sente = self.player[WHITE]
        if gv.show_header == True:
         GLib.idle_add(gv.gui.header_lblsente.set_text, "")
         GLib.idle_add(gv.gui.header_lblgote.set_text,"")
         GLib.idle_add(gv.gui.header_lblevent.set_text, "")
         GLib.idle_add(gv.gui.header_lbldate.set_text, "")
    #
    # save users settings at program termination
    #

    def save_settings(self):

        # get settings
        s = Settings()
        s.name = NAME
        s.version = VERSION
        s.engine_list = gv.engine_manager.get_engine_list()
        s.pieceset = gv.pieces.get_pieceset()
        s.custom_pieceset_path = gv.pieces.get_custom_pieceset_path()
        s.player_white = self.player[WHITE]
        s.player_black = self.player[BLACK]
        s.clock_settings = gv.tc.get_clock_settings()
        s.colour_settings = gv.set_board_colours.get_settings()
        s.hash_value = gv.engine_manager.get_hash_value()
        s.ponder = gv.engine_manager.get_ponder()
        s.show_coords = gv.gui.get_show_coords()
        s.highlight_moves = gv.gui.get_highlight_moves()
        s.lastdir = gv.lastdir # last dir used
        # Header not saved
        s.event = "##"       #gv.event, mark for not read
        s.gamedate = ""  #gv.gamedate
        s.gote = "" #gv.gote
        s.sente ="" #gv.sente
        if gv.verbose == True:
                print(gv.lastdir + "  saved")
        # pickle and save settings
        try:
            settings_file = os.path.join(self.gshogipath, "settings")
            f = open(settings_file, "wb")
            pickle.dump(s, f)
            f.close()
        except AttributeError as ae:
            print("attribute error:", ae)
        except pickle.PickleError as pe:
            print("PickleError:", pe)
        except pickle.PicklingError as pe2:
            print("PicklingError:", pe2)
        except Exception as exc:
            print("cannot save settings:", exc)

    #
    # restore users settings at program start-up
    #
    def restore_settings(self, x):
        if x:
            # engine list
            try:
                if x.engine_list:
                    # if old format of [(engine, path), ...] 
                    # then reformat to [[engine, path, {}], ...]                    
                    if len(x.engine_list[0]) != 3:
                        print("reformatting engine list")
                        new_engine_list = []
                        for olde in x.engine_list:
                            newe = [olde[0], olde[1], {}]
                            new_engine_list.append(newe)
                        x.engine_list = new_engine_list
                gv.engine_manager.set_engine_list(x.engine_list)
            except Exception as e:
                if gv.verbose:
                    print(e, ". engine list not restored")

            try:
                gv.gamedate = x.gamedate
                if gv.verbose == True:
                    print("date read: " + gv.gamedate)
            except Exception as e:
                if gv.verbose: 
                    print (e, ". date not restored")

            # pieceset "eastern", "western" or "custom"
            try:
                gv.pieces.set_pieceset(x.pieceset)
            except Exception as e:
                if gv.verbose:
                    print(e, ". pieceset setting not restored")

            # set the engine or human for each player
            try:
                self.player[WHITE] = x.player_white
                self.player[BLACK] = x.player_black
            except Exception as e:
                if gv.verbose:
                    print(e, ". player setting not restored")

            # time controls
            try:
                cs = x.clock_settings
                gv.tc.restore_clock_settings(cs)
            except Exception as e:
                if gv.verbose:
                    print(e, ". time controls not restored")

            # hash value
            try:
                hash_value = x.hash_value
                gv.engine_manager.set_hash_value(hash_value)
            except Exception as e:
                if gv.verbose:
                    print(e, ". hash value not restoself.player[side]:red")

            # ponder (true/false)
            try:
                ponder = x.ponder
                gv.engine_manager.set_ponder(ponder)
            except Exception as e:
                if gv.verbose:
                    print(e, ". ponder not restored")

            # show coordinates (true/false)
            try:
                show_coords = x.show_coords
                gv.gui.set_show_coords(show_coords)
            except Exception as e:
                if gv.verbose:
                    print(e, ". show_coords not restored")

            # highlight moves (true/false)
            try:
                highlight_moves = x.highlight_moves
                gv.gui.set_highlight_moves(highlight_moves)
            except Exception as e:
                if gv.verbose:
                    print(e, ". highlight_moves not restored")
            # lastdir
            try: 
                gv.lastdir = x.lastdir
                if gv.verbose == True:
                        print("path read: " + gv.lastdir)
            except Exception as e:
                if gv.verbose: 
                        print (e, ". lastdir not restored")
            #header : werden nicht gelesen
            gv.gamedate = ""
            gv.event = "##"
            gv.gote = ""
            gv.sente = ""
                
    def goto_move(self, move_idx):
        try:
            gv.usib.stop_engine()
            gv.usiw.stop_engine()
        except:
            pass
        self.gameover = False
        if move_idx < len(self.movelist):
            while move_idx < len(self.movelist):
                self.undo_move()
        else:
            while move_idx > len(self.movelist):
                self.redo_move()

        self.stm = self.get_side_to_move()
        gv.gui.set_side_to_move(self.stm)

        gv.board.update()
        # gv.gui.set_status_bar_msg(" ")
        move = None
        try:
            move = self.movelist[len(self.movelist) - 1]
            self.lastmove = move
            # print "move ",move
        except IndexError:
            pass

        if move is not None:
            gv.gui.set_status_bar_msg(str(move_idx) +"." +move)
            if gv.show_moves == True:
               nmoves = len(self.movelist)
               path =(nmoves-1,)
               sel = gv.gui.move_view.get_selection()
               sel.select_path(path)  
               self.move_list.set_move(nmoves)          
        else:
            gv.gui.set_status_bar_msg(" ")

    #
    # called from gui.py when undo button click on toolbar (passed widget is
    # Gtk.ToolButton object) and when undo move is selected from menu
    # (or ctrl-u is pressed) (passed widget is Gtk.Action object)
    #
    def undo_single_move(self, b):
        
        move = None
        nmove = len(self.movelist)
        try:
            move = self.movelist.pop()
            engine.command("undo")
            self.redolist.append(move)
            self.lastmove = move
            self.stm = self.get_side_to_move()
            gv.gui.set_side_to_move(self.stm)
        except IndexError:
            pass

        try:
            gv.usib.stop_engine()
            gv.usiw.stop_engine()
        except:
            pass
        self.gameover = False
        #gv.board.update()
        # set move list window to last move
        self.move_list.set_move(len(self.movelist))
        self.goto_move(len(self.movelist))
        if move is not None:
            squares_to_hilite=(move[0:2], move[2:4])
        else:
            squares_to_hilite=None
        self.lastmove = ""
        gv.board.update(squares_to_hilite=squares_to_hilite)
        if move is not None:
            gv.gui.set_status_bar_msg("back: (" + str(nmove) + ". " + move + ")")                   
                   
    # undo a move without updating the gui
    def undo_move(self):
        engine.command("undo")
        move = None
        try:
            move = self.movelist.pop()
            self.redolist.append(move)
                  
        except IndexError:
            pass

    def undo_all(self, toolbutton):
        try:
            gv.usib.stop_engine()
            gv.usiw.stop_engine()
        except:
            pass
        self.gameover = False
        while len(self.movelist) != 0:
            self.undo_move()
        self.lastmove = ""

        self.stm = self.get_side_to_move()
        gv.gui.set_side_to_move(self.stm)

        gv.board.update()
        # set move list window to initial position
        self.move_list.set_move(1)
        gv.gui.set_status_bar_msg(" ")
        if gv.show_moves == True:
            start, end =gv.gui.comment_view.get_buffer().get_bounds()
            gv.gui.comment_view.get_buffer().delete(start,end)
            gv.gui.comment_view.get_buffer().insert(start,"-")        
                  


    #
    # called from gui.py when redo button click on toolbar (passed widget is
    # Gtk.ToolButton object) and when redo move is selected from menu
    # (or ctrl-r is pressed) (passed widget is Gtk.Action object)
    #
    def redo_single_move(self, widget):
        move = None
        try:
            move = self.redolist.pop()
            # get side to move before appending to movelist
            self.stm = self.get_side_to_move()
            self.movelist.append(move)
            self.lastmove = move

            # do the move in gshogi engine
            engine.setplayer(self.stm)
            engine.hmove(move)

            # side to move changes to opponent
            self.stm = self.get_side_to_move()
            gv.gui.set_side_to_move(self.stm)
                    
        except IndexError:
            pass

        try:
            gv.usib.stop_engine()
            gv.usiw.stop_engine()
        except:
            pass
        gv.board.update()
        # set move list window to last move
        self.move_list.set_move(len(self.movelist))
        self.goto_move(len(self.movelist))
        nmove = len(self.movelist)
        if move is not None:
           gv.gui.set_status_bar_msg("forward: (" + str(nmove) + ". " + move + ")")
            
    # redo a move without updating the gui
    def redo_move(self):
        move = None
        try:
            move = self.redolist.pop()

            # get side to move before appending to movelist
            self.stm = self.get_side_to_move()
            self.movelist.append(move)
            
            # do the move in gshogi engine
            engine.setplayer(self.stm)
            engine.hmove(move)
        except IndexError:
            pass

    def redo_all(self, toolbutton):
        while len(self.redolist) != 0:
            self.redo_move()
        self.stm = self.get_side_to_move()
        gv.gui.set_side_to_move(self.stm)
        gv.board.update()
        # set move list window to last move
        self.move_list.set_move(len(self.movelist))                         
        self.goto_move(len(self.movelist))
        if gv.show_moves == True:
         startc, endc =gv.gui.comment_view.get_buffer().get_bounds()
         gv.gui.comment_view.get_buffer().delete(startc,endc)
         gv.gui.comment_view.get_buffer().insert(startc,"-")   
         if len(self.movelist) != 0:
            gv.gui.move_view.get_selection().select_path(str(len(self.movelist)-1))
        nmove = len(self.movelist)
        move = None
        try:
            move = self.movelist[len(self.movelist) - 1]
        except IndexError:
            pass
       
            

        if move is not None:
            gv.gui.set_status_bar_msg(" (" + str(nmove) + ". " + move + ")")
            self.lastmove = move
            #Lists?         

    def set_movelist(self, movelist):
        self.movelist = movelist

    def set_redolist(self, redolist):
        self.redolist = redolist

    def set_startpos(self, startpos):
        self.startpos = startpos

    def set_side_to_move(self, stm):
        self.stm = stm

    def get_stm(self):
        return self.stm

    def get_move_count(self):
        return len(self.movelist) + 1

    def get_side_to_move(self):

        # get side to move for the first move of the game
        # This is black in a normal game and white in a handicap game
        start_stm = self.get_stm_from_sfen(self.startpos)

        if len(self.movelist) % 2 == 0:
            return start_stm
        else:
            return start_stm ^ 1

    def get_side_to_move_string(self, stm):
        if stm == BLACK:
            return _("black")
        else:
            return _("white")

    def get_stm_from_sfen(self, sfen):
        if sfen == "startpos":
            # normal game
            stm = BLACK
        else:
            sp = sfen.split()
            try:
                if sp[1] == "w":
                    stm = WHITE
                else:
                    stm = BLACK
            except:
                    stm = BLACK
        return stm

    def get_player(self, side):
        return self.player[side]

    def set_player(self, side, player):
        self.player[side] = player
        gv.usib.set_engine(self.player[side], None)
        gv.gui.update_toolbar(self.player)

    def move_now(self, b):
        if self.player[self.stm] == "Human":
            return

        if not self.thinking:
            return

        # builtin gshogi engine
        if self.player[self.stm] == "gshogi":
            engine.movenow()
            return

        # USI engine
        try:
            if self.stm == BLACK:
                gv.usib.command("stop\n")
            else:
                gv.usiw.command("stop\n")
        except:
            pass

    def get_movelist(self):
        return self.movelist

    def get_redolist(self):
        return self.redolist

    def get_lastmove(self):
        return self.lastmove

    def set_lastmove(self, lastmove):
        self.lastmove = lastmove

    def set_players(self, b):
        dialog = Gtk.Dialog(
            _("Players"), gv.gui.get_window(), 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_title(_("Set Players"))

        elist = gv.engine_manager.get_engine_list()

        # White Player
        fr = Gtk.Frame.new(_("White"))
        dialog.vbox.pack_start(fr, True, True, 15)
        # dialog.vbox.set_spacing(20)
        vb = Gtk.VBox(False, 0)
        fr.add(vb)

        comboboxw = Gtk.ComboBoxText()
        comboboxw.append_text(_("Human"))

        if self.player[WHITE] == "Human":
            comboboxw.set_active(0)

        i = 1
        for (engine_name, path, ucioptions) in elist:
            comboboxw.append_text(engine_name)

            if engine_name == self.player[WHITE]:
                comboboxw.set_active(i)
            i += 1
        vb.pack_start(comboboxw, True, True, 15)

        # Black Player
        fr = Gtk.Frame.new(_("Black"))
        dialog.vbox.pack_start(fr, True, True, 15)
        vb = Gtk.VBox(False, 0)
        fr.add(vb)

        comboboxb = Gtk.ComboBoxText()
        comboboxb.append_text(_("Human"))
        if self.player[BLACK] == "Human":
            comboboxb.set_active(0)

        i = 1
        for (engine_name, path, ucioptions) in elist:
            comboboxb.append_text(engine_name)
            if engine_name == self.player[BLACK]:
                comboboxb.set_active(i)
            i += 1
        vb.pack_start(comboboxb, True, True, 15)

        dialog.show_all()

        # If user hasn't clicked on OK then exit now
        if dialog.run() != Gtk.ResponseType.OK:
            dialog.destroy()
            return

        self.player[BLACK] = comboboxb.get_active_text()
        self.player[WHITE] = comboboxw.get_active_text()

        gv.usib.set_engine(self.player[BLACK], None)
        gv.usiw.set_engine(self.player[WHITE], None)

        gv.gui.update_toolbar(self.player)

        dialog.destroy()

    def get_startpos(self):
        return self.startpos

    def get_stopped(self):
        return self.stopped


# class to save settings on program exit and restore on program start
class Settings:
    pass


def run():
    Game()
    GObject.threads_init()
    Gtk.main()
    return 0

if __name__ == "__main__":
    run()
