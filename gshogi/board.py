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
        self.wcap = engine.getcaptured(WHITE)
        self.bcap = engine.getcaptured(BLACK)

    def build_board(self):
        self.myimage = [[Gtk.Image() for x in range(9)] for x in range(9)]

        self.wcap_image = [Gtk.Image() for x in range(9)]
        self.wcap_label = [Gtk.Label() for x in range(9)]
        self.bcap_image = [Gtk.Image() for x in range(9)]
        self.bcap_label = [Gtk.Label() for x in range(9)]

        self.piece_pixbuf = []

        self.init_board()

    def init_board(self):
        prefix = gv.gshogi.get_prefix()

        gv.pieces.load_pieces(prefix)

        # pieces captured by black (index 0) and white (index 1)
        self.bcap2 = [
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
        for x in range(0, 9):
            for y in range(0, 9):
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

        # initialise white komadai (area containing pieces captured by white)
        for y in range(0, 7):
            self.wcap_image[y].set_from_pixbuf(gv.pieces.getpixbuf(" -"))
            self.wcap_label[y].set_text("   ")
            # call gui to show this square
            gv.gui.init_wcap_square(self.wcap_image[y], y, self.wcap_label[y])

        # initialise black komadai (area containing pieces captured by black)
        for y in range(0, 7):
            self.bcap_image[y].set_from_pixbuf(gv.pieces.getpixbuf(" -"))
            self.bcap_label[y].set_text("   ")
            # call gui to show this square
            gv.gui.init_bcap_square(self.bcap_image[y], y, self.bcap_label[y])

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
        for y in range(0, 9):
            for x in range(0, 9):
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
            zcap = self.getcap(p, self.bcap)
            if zcap != "":
                cap_list.append(zcap)

        # get list captured pieces for white in the correct order
        # (rook, bishop, gold, silver, knight, lance, pawn)
        for p in ("R", "B", "G", "S", "N", "L", "P"):
            zcap = self.getcap(p, self.wcap)
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
        for x in range(0, 9):
            for y in range(0, 9):
                # convert the x, y square to the location value
                # used by the engine
                l = self.get_gs_loc(x, y)
                piece = self.board_position[l]
                pb = gv.pieces.getpixbuf(piece)
                # the get_pixbuf line prevents error messages of the type
                # Warning: g_object_unref: assertion `object->ref_count > 0'
                # failed on the set_from_pixbuf line
                cpb = self.myimage[x][y].get_pixbuf()
                self.myimage[x][y].set_from_pixbuf(pb)

    def display_capturedw(self, wcap):

        #
        # wcap contains a list of captured pieces  e.g.
        # 0P 0L 0N 0S 0G 0B 0R 0P 0L 0N 0S 0B 0R 0K
        #

        self.bcap2[WHITE] = ["0", "0", "0", "0", "0", "0", "0"]

        for i in range(0, 7):
            # the get_pixbuf line prevents error messages of the type
            # Warning: g_object_unref: assertion `object->ref_count > 0' failed
            # on the set_from_pixbuf line
            cpb = self.wcap_image[i].get_pixbuf()
            self.wcap_image[i].set_from_pixbuf(gv.pieces.getpixbuf(" -"))
            self.wcap_label[i].set_text("   ")

        i = 0
        for c in wcap:
            if c == "":
                continue
            piece = c[1:2]
            num = c[0:1]

            if i < 7:
                z = " " + piece
                # the get_pixbuf line prevents error messages of the type
                # Warning: g_object_unref: assertion `object->ref_count > 0'
                # failed on the set_from_pixbuf line
                cpb = self.wcap_image[i].get_pixbuf()
                self.wcap_image[i].set_from_pixbuf(gv.pieces.getpixbuf(z))
                self.bcap2[WHITE][i] = piece
                self.wcap_label[i].set_text(" " + num + " ")

            i = i + 1

    def display_capturedb(self, bcap):

        self.bcap2[BLACK] = ["0", "0", "0", "0", "0", "0", "0", "0", "0"]

        for i in range(0, 7):
            # the get_pixbuf line prevents error messages of the type
            # Warning: g_object_unref: assertion `object->ref_count > 0'
            # failed on the set_from_pixbuf line
            cpb = self.bcap_image[i].get_pixbuf()
            self.bcap_image[i].set_from_pixbuf(gv.pieces.getpixbuf(" -"))
            self.bcap_label[i].set_text("   ")

        i = 6
        for c in bcap:
            if c == "":
                continue
            piece = c[1:2]
            num = c[0:1]

            if i > -1:
                z = " " + piece
                z = z.lower()
                # the get_pixbuf line prevents error messages of the type
                # Warning: g_object_unref: assertion `object->ref_count > 0'
                # failed on the set_from_pixbuf line
                cpb = self.bcap_image[i].get_pixbuf()
                self.bcap_image[i].set_from_pixbuf(gv.pieces.getpixbuf(z))
                self.bcap2[BLACK][i] = piece
                self.bcap_label[i].set_text(" " + num + " ")
            i = i - 1

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
        self.wcap = engine.getcaptured(WHITE)
        self.bcap = engine.getcaptured(BLACK)
        if refresh_gui:
            self.refresh_screen()

    def refresh_screen(self, w=None, h=None):
        self.display_board(w, h)
        self.display_capturedw(self.wcap)
        self.display_capturedb(self.bcap)

    def get_cap_piece(self, y, stm):
        return self.bcap2[stm][y]

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
        if stm == BLACK:
            return self.bcap_image[y].get_pixbuf()
        else:
            return self.wcap_image[y].get_pixbuf()

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
        for x in range(0, 9):
            for y in range(0, 9):
                self.set_square_as_unoccupied(x, y)
        self.bcap = ["0B", "0S", "0G", "0L", "0N", "0R", "0P"]
        self.wcap = ["0B", "0S", "0G", "0L", "0N", "0R", "0P"]
        self.display_capturedb(self.bcap)
        self.display_capturedw(self.wcap)

    #
    # called from gshogi.py to clear the source komadai square or
    # reduce the count by 1 when a drag of a piece has started
    #
    def set_cap_as_unoccupied(self, y, piece, stm):
        if stm == BLACK:
            cap = self.bcap
        else:
            cap = self.wcap
        i = 0
        for cp in cap:
            if cp.endswith(piece):
                ct = int(cp[0])
                ct -= 1
                if ct == 0:
                    newcap = ""
                else:
                    newcap = str(ct) + piece
                break
            i += 1
        if stm == BLACK:
            self.bcap[i] = newcap
        else:
            self.wcap[i] = newcap

    # In edit mode show all pieces in the komadai with a zero next to those
    # not present. This allows for easy editing by clicking on each piece
    # to change the count
    def set_komadai_for_edit(self):

        # black
        newcap = ["0B", "0S", "0G", "0L", "0N", "0R", "0P"]
        cap = self.bcap
        found = False
        i = 0
        for item in newcap:
            for cp in cap:
                if cp.endswith(item[1]):
                    newcap[i] = cp
                    break
            i += 1
        self.bcap = newcap
        self.display_capturedb(self.bcap)

        # white
        newcap = ["0B", "0S", "0G", "0L", "0N", "0R", "0P"]
        cap = self.wcap
        found = False
        i = 0
        for item in newcap:
            for cp in cap:
                if cp.endswith(item[1]):
                    newcap[i] = cp
                    break
            i += 1
        self.wcap = newcap
        self.display_capturedw(self.wcap)

    # called from board.py in edit board mode when the user left clicks
    # on a piece in the komadai to reduce the count of the piece by 1.
    def decrement_cap_piece(self, y, colour):
        if colour == BLACK:
            cap = self.bcap
            y = 6 - y
        else:
            cap = self.wcap

        ct = int(cap[y][0])
        ct -= 1
        if ct < 0:
            ct = 0
        cap[y] = str(ct) + cap[y][1]
        if colour == BLACK:
            self.display_capturedb(self.bcap)
        else:
            self.display_capturedw(self.wcap)

    # called from board.py in edit board mode when the user right clicks
    # on a piece in the komadai to increase the count of the piece by 1.
    def increment_cap_piece(self, y, colour):
        if colour == BLACK:
            cap = self.bcap
            y = 6 - y
        else:
            cap = self.wcap

        ct = int(cap[y][0])
        ct += 1
        if ct > 9:
            ct = 9
        cap[y] = str(ct) + cap[y][1]
        if colour == BLACK:
            self.display_capturedb(self.bcap)
        else:
            self.display_capturedw(self.wcap)

    #
    # set the piece image on a board square to the supplied pixbuf
    # used in gshogi.py drag and drop
    #
    def set_image(self, x, y, pixbuf):
        self.myimage[x][y].set_from_pixbuf(pixbuf)

    def get_capturedw(self):
        return self.wcap

    def get_capturedb(self):
        return self.bcap

    def get_piece(self, x, y):
        l = self.get_gs_loc(x, y)
        piece = self.board_position[l]
        return piece

    """"
    # Board position history
    # self.board_pos contains a list of board positions
    # 1 board position for each move
    # This routine saves the board position after a move
    def save_board(self, idx):

        if (idx != len(self.board_hist)):
            print "Error saving board in board.py - index incorrrect"
            print "idx=",idx
            print "len boardpos=",len(self.board_hist)

        board_position = self.getboard()
        wcap = engine.getcaptured(WHITE)
        bcap = engine.getcaptured(BLACK)

        self.board_hist.append( (board_position, wcap, bcap) )

    # This reduces the number of saved boards if the user has restarted the
    #  game from an earlier position
    def reduce_board_history(self, movelist):
        num_moves = len(movelist)
        # no. of board positions saved should be 1 more than the number of
        # moves
        # Need to add 1 for the initial board position after zero moves
        num_boards = num_moves + 1
        while num_boards  < len(self.board_hist):
            self.board_hist.pop()
            print "popped"
    """
