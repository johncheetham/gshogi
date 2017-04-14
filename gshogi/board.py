#
#   board.py
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
from gi.repository import GObject
from gi.repository import GdkPixbuf
from gi.repository import GLib
import cairo

from . import gv
if gv.installed:
    from gshogi import engine
else:
    import engine
from .constants import WHITE, BLACK

SCALE = 0.9      # scale the pieces so they occupy 90% of the board square
LINEWIDTH = 2    # width of lines on the board


class Board:

    def __init__(self):
        self.board_position = self.getboard()
        self.cap = [
            engine.getcaptured(BLACK),
            engine.getcaptured(WHITE)
        ]
        self.cap_label = [
            [Gtk.Label() for x in range(9)],
            [Gtk.Label() for x in range(9)]
        ]

    def get_cap_label(self, side):
        return self.cap_label[side]

    def build_board(self):
        # pieces captured by black (index 0) and white (index 1)
        self.cap2 = [
            ["-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-"]
        ]

        # pieces contains the list of possible pieces in self.board_position
        pieces = [
            " -", " p", " l", " n", " s", " g", " b", " r", " k", "+p", "+l",
            "+n", "+s", "+b", "+r", " P", " L", " N", " S", " G", " B", " R",
            " K", "+P", "+L", "+N", "+S", "+B", "+R"
        ]

        # initialise komadai (areas containing captured pieces)
        for y in range(7):
            for side in range(2):
                self.cap_label[side][y].set_text("   ")

        GObject.idle_add(self.update)

    def get_gs_loc(self, x, y):
        l = x + (8 - y) * 9
        return l

    # convert gshogi co-ordinates for square into
    # standard notation (e.g.  (2, 6) -> 7g)
    def get_square_posn(self, x, y):
        lets = "abcdefghi"
        sq = str(9 - x) + lets[y]
        return sq

    # convert standard notation for square into
    # gshogi co-ordinates (e.g.  7g -> (2, 6) )
    def get_gs_square_posn(self, sq):
        x = 9 - int(sq[0:1])
        lets = "abcdefghi"
        y = lets.index(sq[1:2])
        return x, y

    #
    # USI SFEN string
    #
    # uppercase letters for black pieces, lowercase letters for white pieces
    #
    # examples:
    #     "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
    #     "8l/1l+R2P3/p2pBG1pp/kps1p4/Nn1P2G2/P1P1P2PP/1PS6/1KSG3+r1/LN2+p3L w
    # Sbgn3p 124"
    def get_sfen(self):

        empty = 0
        sfen = ""

        # board state
        for y in range(9):
            for x in range(9):
                # convert the x, y square to the location value
                # used by the engine
                l = self.get_gs_loc(x, y)
                p = self.board_position[l]
                if p == " -":
                    empty += 1
                    continue
                if empty != 0:
                    sfen += str(empty)
                    empty = 0
                if p[1].isupper():
                    usi_p = p[1].lower()
                else:
                    usi_p = p[1].upper()
                if p[0] == "+":
                    usi_p = "+" + usi_p
                sfen += usi_p
            if empty != 0:
                sfen += str(empty)
                empty = 0
            if y != 8:
                sfen += "/"

        # side to move
        if gv.gshogi.get_stm() == BLACK:
            stm = "b"
        else:
            stm = "w"
        sfen = sfen + " " + stm

        # pieces in hand
        pih = ""

        # get list of captured pieces for black in the correct order
        # (rook, bishop, gold, silver, knight, lance, pawn)
        cap_list = []
        for p in ("R", "B", "G", "S", "N", "L", "P"):
            zcap = self.getcap(p, self.cap[BLACK])
            if zcap != "":
                cap_list.append(zcap)

        # get list captured pieces for white in the correct order
        # (rook, bishop, gold, silver, knight, lance, pawn)
        for p in ("R", "B", "G", "S", "N", "L", "P"):
            zcap = self.getcap(p, self.cap[WHITE])
            if zcap != "":
                # change to lower case for white
                zcap2 = zcap[0] + zcap[1].lower()
                cap_list.append(zcap2)

        # cap_list is now a list of captured pieces in the correct order
        # (black R, B, G, S, N, L, P followed by white R, B, G, S, N, L, P)

        # create pices in hand string (pih) from cap_list
        for c in cap_list:
            piece = c[1:2]
            num = c[0:1]
            if int(num) > 1:
                pih += str(num)
            pih += piece

        if pih == "":
            pih = "-"

        move_count = gv.gshogi.get_move_count()
        sfen = sfen + " " + pih + " " + str(move_count)
        return sfen

    def getcap(self, piece, cap):
        for p in cap:
            if p == "":
                continue
            if p[1] == piece and p[0] != "0":
                return p
        return ""

    def display_board(self, squares_to_hilite=None):
        self.squares_to_hilite = squares_to_hilite
        #
        # loop through the board squares and set the pieces
        # x, y = 0, 0 is the top left square of the board
        #
        for x in range(9):
            for y in range(9):
                gv.gui.get_event_box(x, y).queue_draw()

    def display_komadai(self, side):
        #
        # cap contains a list of captured pieces  e.g.
        # 0P 0L 0N 0S 0G 0B 0R 0P 0L 0N 0S 0B 0R 0K
        #
        self.cap2[side] = ["-", "-", "-", "-", "-", "-", "-"]
        for i in range(7):
            self.cap_label[side][i].set_text("   ")

        i = 0
        for c in self.cap[side]:
            if c == "":
                continue
            piece = c[1:2]
            num = c[0:1]
            if i < 7:
                z = " " + piece
                idx = i
                if side == BLACK:
                    z = z.lower()
                    idx = 6 - i
                self.cap2[side][idx] = piece
                # if more than 10 captured need to manipulate ordinal values
                # since num only occupies 1 character.
                # eg. if 10 captured num is set to ":" which is converted to
                # "1" + chr(48) = "10"
                if num > "9":
                    num = "1" + chr(ord(num) - 10)
                self.cap_label[side][idx].set_text(" " + num + " ")
            i = i + 1
        for i in range(7):
            gv.gui.get_komadai_event_box(side, i).queue_draw()
    #
    # test if user has clicked on a valid source square
    # i.e. one that contains a black piece if side to move is black
    #      otherwise white piece

    #
    def valid_source_square(self, x, y, stm):
        l = self.get_gs_loc(x, y)
        piece = self.board_position[l]

        pieces = [
            [
               " p", " l", " n", " s", " g", " b", " r", " k", "+p", "+l",
               "+n", "+s", "+b", "+r"
            ],
            [
                " P", " L", " N", " S", " G", " B", " R", " K", "+P", "+L",
                "+N", "+S", "+B", "+R"
            ]
        ]

        try:
            idx = pieces[stm].index(piece)
        except ValueError as ve:
            return False

        return True

#
# Check if promotion is mandatory (i.e on last rank of board for
# pawn/lance or last 2 ranks for knight) or optional
#
# return
# 0 - no promotion
# 1 - promotion optional
# 2 - promotion mandatory
#
    def promote(self, piece, src_x, src_y, dst_x, dst_y, stm):

        # check for mandatory
        if stm == BLACK:
            if (dst_y == 0):
                if (piece == " p" or piece == " l" or piece == " n"):
                    return 2
            elif (dst_y == 1):
                if (piece == " n"):
                    return 2
        else:
            if (dst_y == 8):
                if (piece == " P" or piece == " L" or piece == " N"):
                    return 2
            elif (dst_y == 7):
                if (piece == " N"):
                    return 2

        # check for optional
        #        BlackPawn,    BlackLance,   BlackKnight, BlackSilver,
        #        BlackBishop,  BlackRook,
        promotable_pieces = [
            [
                " p", " l", " n", " s", " b", " r"
            ],
            [
                " P", " L", " N", " S", " B", " R"
            ]
        ]

        try:
            idx = promotable_pieces[stm].index(piece)
        except ValueError as ve:
            return 0

        return 1

    def use_pieceset(self, pieceset):
        gv.pieces.set_pieceset(pieceset)
        self.refresh_screen()

    def getboard(self):
        return engine.getboard()

    def update(self, refresh_gui=True, squares_to_hilite=None):
        self.board_position = self.getboard()
        self.cap[BLACK] = engine.getcaptured(BLACK)
        self.cap[WHITE] = engine.getcaptured(WHITE)
        if refresh_gui:
            self.refresh_screen(squares_to_hilite=squares_to_hilite)

    def refresh_screen(self, squares_to_hilite=None):
        self.display_board(squares_to_hilite=squares_to_hilite)
        self.display_komadai(WHITE)
        self.display_komadai(BLACK)

    def get_cap_piece(self, y, stm):
        return self.cap2[stm][y]

    #
    # return a pixbuf of the piece at the given square
    # used by drag_and_drop.py to get the drag and drop icon
    #
    def get_piece_pixbuf(self, x, y):
        # convert the x, y square to the location value used by the engine
        l = self.get_gs_loc(x, y)
        piece = self.board_position[l]
        pb = gv.pieces.getpixbuf(piece)
        a = gv.gui.get_event_box(x, y).get_allocation()
        spb = pb.scale_simple(
            int(a.width*SCALE), int(a.height*SCALE), GdkPixbuf.InterpType.HYPER)
        return spb

    def get_piece_pixbuf_unscaled(self, x, y):
        # convert the x, y square to the location value used by the engine
        l = self.get_gs_loc(x, y)
        piece = self.board_position[l]
        pb = gv.pieces.getpixbuf(piece)
        return pb

    def get_cap_pixbuf(self, y, stm):
        piece = self.cap2[stm][y]
        piece = " " + piece
        if stm == BLACK:
            piece = piece.lower()
        pb = gv.pieces.getpixbuf(piece)
        a = gv.gui.get_komadai_event_box(stm, y).get_allocation()
        spb = pb.scale_simple(
            int(a.width*SCALE), int(a.height*SCALE), GdkPixbuf.InterpType.HYPER)
        return spb

    #
    # called from gshogi.py to clear the source square when a drag of
    # a piece has started
    #
    def set_square_as_unoccupied(self, x, y):
        piece = " -"    # empty square
        self.set_piece_at_square(x, y, piece)

    # called from this module to clear the source square when draggin and
    # dropping.
    # Also called from gui.py when editing the board position to set the piece
    # on a square.
    def set_piece_at_square(self, x, y, piece):
        l = self.get_gs_loc(x, y)
        self.board_position[l] = piece
        GLib.idle_add(gv.gui.get_event_box(x, y).queue_draw)

    # called when user does a "clear board" in board edit
    def clear_board(self):
        for x in range(9):
            for y in range(9):
                self.set_square_as_unoccupied(x, y)
        self.cap[BLACK] = ["0B", "0S", "0G", "0L", "0N", "0R", "0P"]
        self.cap[WHITE] = ["0B", "0S", "0G", "0L", "0N", "0R", "0P"]
        self.display_komadai(BLACK)
        self.display_komadai(WHITE)

    #
    # called from gshogi.py to clear the source komadai square or
    # reduce the count by 1 when a drag of a piece has started
    #
    def set_cap_as_unoccupied(self, y, piece, stm):
        i = 0
        for cp in self.cap[stm]:
            if cp.endswith(piece):
                ct = int(cp[0])
                ct -= 1
                if ct == 0:
                    newcap = ""
                else:
                    newcap = str(ct) + piece
                break
            i += 1
        self.cap[stm][i] = newcap

    # In edit mode show all pieces in the komadai with a zero next to those
    # not present. This allows for easy editing by clicking on each piece
    # to change the count
    def set_komadai_for_edit(self):
        for side in range(2):
            newcap = ["0B", "0S", "0G", "0L", "0N", "0R", "0P"]
            cap = self.cap[side]
            found = False
            i = 0
            for item in newcap:
                for cp in cap:
                    if cp.endswith(item[1]):
                        newcap[i] = cp
                        break
                i += 1
            self.cap[side] = newcap
            self.display_komadai(side)

    # called from board.py in edit board mode when the user left clicks
    # on a piece in the komadai to reduce the count of the piece by 1.
    def decrement_cap_piece(self, y, colour):
        cap = self.cap[colour]
        if colour == BLACK:
            y = 6 - y
        ct = int(cap[y][0])
        ct -= 1
        if ct < 0:
            ct = 0
        cap[y] = str(ct) + cap[y][1]
        self.display_komadai(colour)

    # called from board.py in edit board mode when the user right clicks
    # on a piece in the komadai to increase the count of the piece by 1.
    def increment_cap_piece(self, y, colour):
        cap = self.cap[colour]
        if colour == BLACK:
            y = 6 - y
        ct = int(cap[y][0])
        ct += 1
        if ct > 9:
            ct = 9
        cap[y] = str(ct) + cap[y][1]
        self.display_komadai(colour)

    def set_image_cairo_komadai(self, y, piece, side, wid=None, cr=None):
        if side == BLACK:
            piece = piece.lower()
        keb = gv.gui.get_komadai_event_box(side, y)
        a = keb.get_allocation()

        if cr is None:
            w = keb.get_window()
            cr = w.cairo_create()

        # clear square to bg colour
        gv.set_board_colours.set_komadai_square_colour(cr, a)

        # set offset so piece is centered in the square
        cr.translate(a.width*(1.0-SCALE)/2.0, a.height*(1.0-SCALE)/2.0)

        # scale piece so it is smaller than the square
        pb = gv.pieces.getpixbuf(piece)
        sfw = (a.width * 1.0 / pb.get_width()) * SCALE
        sfh = (a.height * 1.0 / pb.get_height()) * SCALE
        cr.scale(sfw, sfh)

        Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
        cr.paint()

    def set_image_cairo(self, x, y, cr=None, widget=None):

        piece = self.get_piece(x, y)

        if cr is None:
            w = gv.gui.get_event_box(x, y).get_window()
            cr = w.cairo_create()

        if widget is not None:
            a = widget.get_allocation()
        else:
            a = gv.gui.get_event_box(x, y).get_allocation()

        # if user has set hilite moves on then check if this square is
        # in last move and if so hilight it
        hilite = False
        if gv.gui.get_highlight_moves():
            movesquares = []            
            if self.squares_to_hilite is not None:
                for sq in self.squares_to_hilite:
                    if sq[1] != "*":
                        movesquares.append(self.get_gs_square_posn(sq)) 
            else:
                lastmove = gv.gshogi.get_lastmove()
                if lastmove != "":
                    movesquares = []
                    src = lastmove[0:2]
                    dst = lastmove[2:4]
                    if src[1] != "*":
                        movesquares.append(self.get_gs_square_posn(lastmove[0:2]))
                    movesquares.append(self.get_gs_square_posn(lastmove[2:4]))
            if (x, y) in movesquares:
                hilite = True

        # clear square to square colour
        gv.set_board_colours.set_square_colour(cr, a, LINEWIDTH, hilite)

        # set offset so piece is centered in the square
        cr.translate(a.width*(1.0-SCALE)/2.0, a.height*(1.0-SCALE)/2.0)

        # scale piece so it is smaller than the square
        pb = self.get_piece_pixbuf_unscaled(x, y)
        sfw = (a.width * 1.0 / pb.get_width()) * SCALE
        sfh = (a.height * 1.0 / pb.get_height()) * SCALE
        cr.scale(sfw, sfh)

        Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
        cr.paint()

    def get_captured(self, y, side):
        if side == WHITE:
            return self.cap[WHITE][y]
        else:
            return self.cap[BLACK][y]

    def get_capturedw(self):
        return self.cap[WHITE]

    def get_capturedb(self):
        return self.cap[BLACK]

    def get_piece(self, x, y):
        l = self.get_gs_loc(x, y)
        piece = self.board_position[l]
        return piece
