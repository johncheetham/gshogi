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
from gi.repository import GObject

import engine
from constants import WHITE, BLACK
import gv


class Board:

    def __init__(self):
        self.board_position = self.getboard()
        self.cap = [
            engine.getcaptured(BLACK),
            engine.getcaptured(WHITE)
        ]

    def build_board(self):
        self.myimage = [[Gtk.Image() for x in range(9)] for x in range(9)]
        self.cap_image = [
            [Gtk.Image() for x in range(9)],
            [Gtk.Image() for x in range(9)]
        ]
        self.cap_label = [
            [Gtk.Label() for x in range(9)],
            [Gtk.Label() for x in range(9)]
        ]
        self.init_board()

    def init_board(self):
        prefix = gv.gshogi.get_prefix()

        gv.pieces.load_pieces(prefix)

        # pieces captured by black (index 0) and white (index 1)
        self.cap2 = [
            ["0", "0", "0", "0", "0", "0", "0"],
            ["0", "0", "0", "0", "0", "0", "0"]
        ]

        # pieces contains the list of possible pieces in self.board_position
        pieces = [
            " -", " p", " l", " n", " s", " g", " b", " r", " k", "+p", "+l",
            "+n", "+s", "+b", "+r", " P", " L", " N", " S", " G", " B", " R",
            " K", "+P", "+L", "+N", "+S", "+B", "+R"
        ]

        #
        # loop through the board squares and set the pieces
        # x, y = 0, 0 is the top left square of the board
        #
        for x in range(9):
            for y in range(9):
                # convert the x, y square to the location value
                # used by the engine
                l = self.get_gs_loc(x, y)

                # get the piece at (x, y)
                piece = self.board_position[l]

                # set the image on the board square to the required piece
                pb = gv.pieces.getpixbuf(piece)
                self.myimage[x][y].set_from_pixbuf(pb)

                # call gui to show this square
                gv.gui.init_board_square(self.myimage[x][y], x, y)

        # initialise komadai (areas containing captured pieces)
        for y in range(7):
            for side in range(2):
                self.cap_image[side][y].set_from_pixbuf(
                    gv.pieces.getpixbuf(" -"))
                self.cap_label[side][y].set_text("   ")
                # call gui to show this square
                gv.gui.init_komadai_square(
                    self.cap_image[side][y], y,
                        self.cap_label[side][y], side)

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

    def display_board(self, w=None, h=None):

        sf = self.get_scale_factor(w, h)
        gv.pieces.set_scale_factor(sf)

        #
        # loop through the board squares and set the pieces
        # x, y = 0, 0 is the top left square of the board
        #
        for x in range(9):
            for y in range(9):
                # convert the x, y square to the location value
                # used by the engine
                l = self.get_gs_loc(x, y)
                piece = self.board_position[l]
                pb = gv.pieces.getpixbuf(piece)
                self.myimage[x][y].set_from_pixbuf(pb)

    def display_komadai(self, side):
        #
        # cap contains a list of captured pieces  e.g.
        # 0P 0L 0N 0S 0G 0B 0R 0P 0L 0N 0S 0B 0R 0K
        #
        self.cap2[side] = ["0", "0", "0", "0", "0", "0", "0"]
        for i in range(7):
            self.cap_image[side][i].set_from_pixbuf(gv.pieces.getpixbuf(" -"))
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
                self.cap_image[side][idx].set_from_pixbuf(gv.pieces.getpixbuf(z))
                self.cap2[side][idx] = piece
                self.cap_label[side][idx].set_text(" " + num + " ")
            i = i + 1

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

        # black_pieces = [" p", " l", " n", " s", " g", " b", " r", " k", "+p",
        # "+l", "+n", "+s", "+b", "+r"]
        try:
            idx = pieces[stm].index(piece)
        except ValueError, ve:
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
        except ValueError, ve:
            return 0

        return 1

    def use_pieceset(self, pieceset):
        gv.pieces.set_pieceset(pieceset)
        self.refresh_screen()

    def getboard(self):
        return engine.getboard()

    # work out a factor to scale the pieces by
    # this changes when the user resizes the board
    def get_scale_factor(self, w=None, h=None):
        square_size = gv.gui.get_square_size(w, h)
        width = square_size
        if width < 15:
            factor = 1.0
        else:
            factor = width / 64.0

        return factor

    def update(self, refresh_gui=True):
        self.board_position = self.getboard()
        self.cap[BLACK] = engine.getcaptured(BLACK)
        self.cap[WHITE] = engine.getcaptured(WHITE)
        if refresh_gui:
            self.refresh_screen()

    def refresh_screen(self, w=None, h=None):
        self.display_board(w, h)
        self.display_komadai(WHITE)
        self.display_komadai(BLACK)

    def get_cap_piece(self, y, stm):
        return self.cap2[stm][y]

    #
    # return a pixbuf of the piece at the given square
    # used by gshogi.py to get the drag and drop icon
    #
    def get_piece_pixbuf(self, x, y):
        # convert the x, y square to the location value used by the engine
        l = self.get_gs_loc(x, y)
        piece = self.board_position[l]
        return gv.pieces.getpixbuf(piece)

    def get_cap_pixbuf(self, y, stm):
        return self.cap_image[stm][y].get_pixbuf()

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
        pb = gv.pieces.getpixbuf(piece)
        self.myimage[x][y].set_from_pixbuf(pb)

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

    #
    # set the piece image on a board square to the supplied pixbuf
    # used in gshogi.py drag and drop
    #
    def set_image(self, x, y, pixbuf):
        self.myimage[x][y].set_from_pixbuf(pixbuf)

    def get_capturedw(self):
        return self.cap[WHITE]

    def get_capturedb(self):
        return self.cap[BLACK]

    def get_piece(self, x, y):
        l = self.get_gs_loc(x, y)
        piece = self.board_position[l]
        return piece
