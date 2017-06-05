#
#   psn.py
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
#Remark on games read from files: number of move in SFEN-String is ignored since it would be too complicated to
#correct all routines depending on number of records in movelist or length of movelist.
#Repetition is read in when loaded from file bw 5'17

from . import gv
if gv.installed:
    from gshogi import engine
else:
    import engine
from gi.repository import GLib   
from . import gamelist
from . import comments
from . import move_list
from .constants import WHITE, BLACK


class Psn:

    psn_ref = None

    def __init__(self):
        self.move_list = move_list.get_ref()
        self.gamelist = gamelist.get_ref()
        self.comments = comments.get_ref()
      

    def is_whitespace(self, ptr):
        if (self.gamestr[ptr] == "\n" or self.gamestr[ptr] == "\r" or
                self.gamestr[ptr] == "\t" or self.gamestr[ptr] == " "):
            return True
        return False

    def skip_whitespace(self, ptr):
        while 1:
            if ptr >= self.game_len:
                return None
            if self.is_whitespace(ptr):
                ptr += 1
                continue
            break
        return ptr

    def get_header(self, ptr):

        newptr = self.skip_whitespace(ptr)
        if newptr is None:
            return None, None
        ptr = newptr

        # Now pointing at none whitespace character
        # should be "[" if it is a header
        if self.gamestr[ptr] != "[":
            return None, None  # not a header

        ptr += 1  # step past "["

        hdr = ""
        while 1:
            if ptr >= self.game_len:
                return None, None
            if self.gamestr[ptr] == "]":
                ptr += 1   # step past "]"
                break
            hdr += self.gamestr[ptr]
            ptr += 1
        return hdr, ptr  # valid header found
    
    def get_header_from_string(self, f):
        # sente,gote,event, date
        myList = []
        for line in f.split('\n'):
                myList.append(line)
        ff = False
        eventfound = False
        for line in myList:
            if line != "":
                if line[0] == "[":
                        if line.find("Date") != -1:
                                gv.gamedate = line[6:-2]
                                #print("Date: ", gv.gamedate)
                                ff = True
                        if line.find("Event") !=-1:
                                gv.event = line[7:-2]
                                if gv.event=="" or gv.event=="##":
                                        gv.event="none"
                                #print(gv.event)
                                ff = True
                                eventfound = True
                               
                        if (line.find("Black")!=-1 or line.find("Sente")!=-1 ) and (line.find("SenteGrade")==-1) and (line.find("Black_grade")==-1):
                                        gv.sente =  line[8:-2] #"Sente:" +
                                        
                                        ff = True
                        if (line.find("White")!=-1 or line.find("Gote")!=-1) and (line.find("GoteGrade")==-1) and (line.find("White_grade")==-1):
                                gv.gote = line[7:-2]  #"Gote:" +
                                ff = True
       
        if ff == True:
                # Header from file: mask in event removed
                if gv.event.find("##")!=-1:
                        gv.event = "no event"
                if gv.show_header == True:
                    GLib.idle_add( gv.gui.header_lbldate.set_text, gv.gamedate[:50])
                    GLib.idle_add( gv.gui.header_lblgote.set_text,  gv.gote[:50])
                    GLib.idle_add( gv.gui.header_lblsente.set_text, gv.sente[:50])
                    GLib.idle_add( gv.gui.header_lblevent.set_text, gv.event[:50])
        else:
                gv.event = "##"  # marks file without header    

    # Note this can be called from 2 places
    # When and sfen header is read or when
    # "1...." is encountered for move 1.
    def process_sfen(self, sfen):
        move = 0
        sfen = sfen.strip('"')
        engine.setfen(sfen)
        startpos = sfen
        sfenlst = sfen.split()
        if sfenlst[1] == "b":
            stm = BLACK
        elif sfenlst[1] == "w":
            stm = WHITE
        else:
            stm = BLACK
        # only for malformed files:
        if len(sfenlst)!=3:
            if len(sfenlst) ==2:
                move = int(sfenlst[2])
        elif sfenlst[3]!="":
            move = int(sfenlst[3])
        engine.setplayer(stm)
        return startpos, stm, move

    # called from utils.py as well as this module
    def load_game_psn_from_str(self, gamestr):

        cnt = 0
        comment_active = False
        movelist = []
        redolist = []
        startpos = "startpos"
        engine.command("new")
        stm = BLACK
        moveread = 0
        movecnt = 0

        self.gamestr = gamestr
        self.game_len = len(self.gamestr)

        self.comments.clear_comments()

        # First header should be near the start of the file
        # Note the first chars in the file may be a BOM entry and
        # we need to skip these

        ptr = 0

        # Find "[" of first header
        while 1:
            if ptr >= self.game_len or ptr > 2000:
                gv.gui.info_box("Error (1) loading file. No headers found")
                gv.gshogi.new_game("NewGame")
                gv.gui.set_status_bar_msg("Error loading game")
                return 1
            if gamestr[ptr] == "[":
                break
            ptr += 1

        # First Header found (ptr pointing at "[")
        hdr, newptr = self.get_header(ptr)
        if hdr is None:
            gv.gui.info_box("Error (2) loading file. No headers found")
            gv.gshogi.new_game("NewGame")
            gv.gui.set_status_bar_msg("Error loading game")
            return 1

        # Read remaining headers
        while hdr is not None:
            ptr = newptr
            try:
                prop, value = hdr.split(None, 1)
            except ValueError:
                # Error - cannot split header into a property/value pair
                gv.gui.info_box("Error loading file. Invalid header:" + hdr)
                gv.gshogi.new_game("NewGame")
                gv.gui.set_status_bar_msg("Error loading game")
                return 1
            if prop == "SFEN":
                # set board position, side to move
                startpos, stm, moveread = self.process_sfen(value)  #moveread from position
            elif prop == "Handicap":

                handicap = value.strip('"')
                handicap = handicap.lower()

                sfen = ""
                if handicap == "lance":
                    sfen = "lnsgkgsn1/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "1B5R1/LNSGKGSNL w - 1"
                elif handicap == "bishop":
                    sfen = "lnsgkgsnl/1r7/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "1B5R1/LNSGKGSNL w - 1"
                elif handicap == "rook":
                    sfen = "lnsgkgsnl/7b1/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "1B5R1/LNSGKGSNL w - 1"
                elif handicap == "rook+lance":
                    sfen = "lnsgkgsn1/7b1/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "1B5R1/LNSGKGSNL w - 1"
                elif handicap == "rook+bishop":
                    sfen = "lnsgkgsnl/9/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "1B5R1/LNSGKGSNL w - 1"
                elif handicap == "four piece":
                    sfen = "1nsgkgsn1/9/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "1B5R1/LNSGKGSNL w - 1"
                elif handicap == "six piece":
                    sfen = "2sgkgs2/9/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "1B5R1/LNSGKGSNL w - 1"
                elif handicap == "eight piece":
                    sfen = "3gkg3/9/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "1B5R1/LNSGKGSNL w - 1"
                elif handicap == "ten piece":
                    sfen = "4k4/9/ppppppppp/9/9/9/PPPPPPPPP/" \
                           "B5R1/LNSGKGSNL w - 1"
                elif handicap == "three pawn":
                    sfen = "4k4/9/9/9/9/9/" \
                           "PPPPPPPPP/1B5R1/LNSGKGSNL w - 3p 1"

                if sfen != "":
                    startpos, stm, moveread= self.process_sfen(sfen)

            hdr, newptr = self.get_header(ptr)

        # Moves
        lastmove = ""
        while 1:

            if gv.verbose:
                print()
                print("Processing move number (ply):" + str(movecnt + 1))

            newptr = self.skip_whitespace(ptr)
            if newptr is None:
                break
            ptr = newptr

            # if we get a header here then it must be a multi-game file
            # We cannot process multi-game so treat it as eof and exit
            if gamestr[ptr] == "[":
                break

            # Check for stuff to ignore
            # ignore it and continue processing
            ignore_string, newptr = self.get_ignore_string(ptr)
            if ignore_string is not None:
                #  Can get "1...." to indicate white to move first
                # if ignore_string == "1...." and movecnt == 0:
                #    # Use sfen for initial position but set stm to white
                #    startpos, stm = self.process_sfen(
                #       "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/" \
                #       "1B5R1/LNSGKGSNL w - 1")
                ptr = newptr
                continue

            # comment
            if self.gamestr[ptr] == "{":
                comment = ""
                ptr += 1
                while 1:
                    if ptr >= self.game_len:
                        gv.gui.info_box("Error unterminated comment")
                        gv.gshogi.new_game("NewGame")
                        gv.gui.set_status_bar_msg("Error loading game")
                        return 1  # end of file before end of comment
                    if self.gamestr[ptr] == "}":
                        ptr += 1
                        break
                    comment += self.gamestr[ptr]
                    ptr += 1

                # add comment
                self.comments.set_comment(movecnt, comment)
                continue

            # move number
            # we do not use it
            moveno, newptr = self.get_moveno(ptr)
            if moveno is not None:
                ptr = newptr
                continue

            # move
            move, newptr = self.get_move(ptr, movelist, stm)
            if move is not None:
                ptr = newptr

                engine.setplayer(stm)
                stm = stm ^ 1
                if gv.verbose:
                    print("move=", move)
                validmove = engine.hmove(move)
                if (not validmove):
                    # Should never get this message since get_move has already
                    # validated the move aginst the legal move list
                    # Can get it for sennichite (repetition)
                    gv.gui.info_box(
                        "Error loading file, illegal move (possible "
                        "sennichite (repetition)):" + move + " move number:" +
                        str(movecnt + 1))
                    #gv.gshogi.new_game("NewGame")
                    #gv.gui.set_status_bar_msg("Error loading game")
                    #return 1
                movecnt += 1
                movelist.append(move)
                lastmove = move
                if gv.verbose:
                    engine.command("bd")

                continue

            # Invalid - Display Error
            # If we get here we have an invalid word
            # Errors here will stop the processing and prevent the file loading
            # If the invalid word should be skipped instead then add it to the
            # ignore processing above
            word, newptr = self.get_word(ptr)
            if word is not None:
                gv.gui.info_box(
                    "Error loading file, unable to process move number " +
                    str(movecnt + 1) + ". (illegal move or invalid format):" +
                    word)
                # Load failed part way through so reset the game
                gv.gshogi.new_game("NewGame")
                gv.gui.set_status_bar_msg("Error loading game")
                return 1

            ptr += 1

        gv.usib.set_newgame()
        gv.usiw.set_newgame()
        gv.gui.set_status_bar_msg("game loaded")
        self.gameover = False

        gv.gshogi.set_movelist(movelist)
        gv.gshogi.set_redolist(redolist)
        gv.gshogi.set_startpos(startpos)
        gv.gshogi.set_lastmove(lastmove)

        gv.board.update()
        

        # update move list in move list window
        self.move_list.update()
        stm = gv.gshogi.get_side_to_move()
        gv.gshogi.set_side_to_move(stm)
        gv.gui.set_side_to_move(stm)

        gv.tc.reset_clock()

        return 0

    def get_word(self, ptr):
        word = ""
        while 1:
            if ptr >= self.game_len:
                if word != "":
                    return word, ptr
                else:
                    return None, None

            if self.is_whitespace(ptr):
                break
            word += self.gamestr[ptr]
            ptr += 1
        return word, ptr

    # Ignore certain strings
    def get_ignore_string(self, ptr):

        # ignore things enclosed in brackets such variations and timecodes
        if self.gamestr[ptr] == "(":
            ignore_str = "("
            ptr += 1
            nestcnt = 0
            while 1:
                if ptr >= self.game_len:
                    return None, None
                if self.gamestr[ptr] == "(":
                    nestcnt += 1
                elif self.gamestr[ptr] == ")":
                    if nestcnt > 0:
                        # nested parentheses - just decrease count
                        nestcnt -= 1
                    else:
                        ignore_str += self.gamestr[ptr]  # )
                        ptr += 1
                        # return with sting to ignore and new ptr
                        return ignore_str, ptr
                ignore_str += self.gamestr[ptr]
                ptr += 1

        # get next word in file
        word, newptr = self.get_word(ptr)
        if word is None:
            return None, None

        # List of strings to ignore
        reject = ["Resigns", "Interrupt"]
        for rej in reject:
            if rej == word:
                return word, newptr

        return None, None  # nothing to ignore

    #
    # move
    # parse move into piece, source square, capture, destination square,
    # promote
    # e.g.   L1fx1c+ -> L, 1f, x, 1c, +
    #
    #
    # Example moves we can expect in a file created by gshogi
    #
    # These are of the format piece/source square/capture/destination
    # square/promote
    # where capture = "-" or "x"
    #       promote = "" or "+"
    #   +P2ax1a
    #   B9ex6h+
    #   S5d-5e
    #
    # For drops the format is:
    #   P*5f
    #
    # Other formats we can expect in files not created by gshogi
    #   P2f
    #   Px4d
    #   +Rx6a
    #   xS
    #   Sx
    #
    def get_move(self, ptr, movelist, stm):

        # get next word in file
        word, newptr = self.get_word(ptr)
        if word is None:
            return None, None

        move = word

        if gv.verbose:
            print()
            print("In get_move in psn.py")
            print("get_move has been passed this possible move:", move)

        # Parse move and return its component parts
        (promoted_piece, piece, source_square, dest_square,
         move_promotes, move_equals, move_type) = self.parse_move(move,
                                                                  movelist)
        if piece is None:
            if gv.verbose:
                print("Unable to parse move:", move)
            return None, None

        # Get list of legal moves
        engine.setplayer(stm)
        legal_move_list = self.get_legal_move_list(piece)
        if gv.verbose:
            print("legal_move_list=", legal_move_list)

        # Create move by concat of component parts
        if (self.validate_square(source_square) and
                self.validate_square(dest_square)):
            move = source_square + dest_square + move_promotes
        else:
            move = promoted_piece + piece + source_square + dest_square + \
                   move_promotes

        # Search for move in the legal move list
        move2 = self.search_legal_moves(move, legal_move_list)
        if move2 is not None:
            # Move Found
            # The move returned by the search is in the source+dest format
            # suitable for gshogi
            # e.g. S7b -> 7a7b
            if gv.verbose:
                print("Search succeeded and returned move:", move2)
            return move2, newptr  # found a valid move

        # Search failed
        if gv.verbose:
            print("Search did not find move")

        # try a drop
        if move_type == 1 and len(move) == 3:
            rmove = move[0] + "*" + move[1:]
            if gv.verbose:
                print("trying a drop. move changed from", move, "to", rmove)
            move2 = self.search_legal_moves(rmove, legal_move_list)
            if move2 is not None:
                # Move Found
                if gv.verbose:
                    print("Search succeeded and returned move:", move2)
            return move2, newptr  # found a valid move

        # No valid move found
        return None, None

    # get list of legal moves
    def get_legal_move_list(self, piece):
        if gv.verbose:
            print("in get legal movelist with piece:", piece)
        # Make sure board is up to date so that when we do a "get_piece"
        # it will return the correct value
        gv.board.update(refresh_gui=False)

        lm = engine.getlegalmoves()
        lm = lm.rstrip(";")
        lm = lm.split(";")
        legal_move_list = []

        for l in lm:
            fl = l.split(",")
            # e.g. fl = ["7h9f", "B9f", "Bh9f", "B79f"]

            # If the piece being moved is already promoted then add a "+"
            # in front of the piece when adding the move to the list.
            if piece != "":
                source_square = fl[0][0:2]  # e.g. "7h" or "G*" (if drop)
                if self.validate_square(source_square):
                    valid = True
                    # convert standard notation for square into gshogi
                    # co-ordinates (e.g.  7g -> (2, 6) )
                    x, y = gv.board.get_gs_square_posn(source_square)
                    piece2 = gv.board.get_piece(x, y)
                    if piece2.startswith("+"):
                        i = 0
                        for m in fl:
                            if m.startswith(piece):
                                fl[i] = fl[i].replace(piece, "+" + piece)
                            i += 1

            legal_move_list.append(fl)

        return legal_move_list

    # parse move into promoted_piece, piece, source_square, dest_square,
    # move_promotes, move_equals
    def parse_move(self, orig_move, movelist):

        promoted_piece = ""
        piece = ""
        source_square = ""
        dest_square = ""
        move_promotes = ""
        move_equals = False
        move_type = 0

        error_return = None, None, None, None, None, None, None

        if gv.verbose:
            print()
            print("In parse_move in psn.py")
            print("move passed in=", orig_move)

        # orig_move : move passed in
        # move0     : latest modified version of the move
        # move      : used as a temporary work field

        move0 = orig_move

        # check for drop e.g. P*2f
        move = move0
        if len(move) == 4 and (move[1] == "*" or move[1] == "'"):

            promoted_piece = ""
            piece = move[0]

            if not self.validate_piece(piece):
                if gv.verbose:
                    print("Move invalid (1). Drop Move has invalid " \
                          "piece. ", move0)
                return error_return

            source_square = "*"

            dest_square = move[2:4]
            if not self.validate_square(dest_square):
                if gv.verbose:
                    print("Move invalid (1). Drop Move has invalid dest " \
                          "square. ", move0)
                return error_return

            move_promotes = ""

            return (promoted_piece, piece, source_square, dest_square,
                    move_promotes, move_equals, move_type)

        # If move starts with "x" flip it so the piece is first
        # e.g. xS -> Sx, x+R -> +Rx, xS+ -> Sx+, xR= -> Rx=, xB7 -> B7x
        move = move0
        if move[0] == "x":
            move1 = move

            # get piece
            try:
                if move[1] == "+":
                    pce = move[1:3]
                else:
                    pce = move[1]
            except IndexError:
                return error_return

            # validate piece
            if not self.validate_piece(pce):
                if gv.verbose:
                    print("Move invalid (6). Move has invalid " \
                          "piece. ", orig_move, move0, pce)
                return error_return

            # check if move promotes
            prom = ""
            if move.endswith("+"):
                prom = "+"
            elif move.endswith("="):
                prom = "="

            # Remove "+" / "=" from end of move, then shift "x" from start to
            # end, then add "+" / "=" back if present
            move = move.rstrip("+")
            move = move.rstrip("=")
            move0 = move[1:] + "x" + prom
            if gv.verbose:
                print("move reformatted from", move1, "to", move0)

        # If move ends in x (i.e. no dest square specified) then get dest
        # square from the previous move
        # e.g. Sx ->  S4d
        move = move0
        if move.endswith("x") or move.endswith("x+") or move.endswith("x="):
            prevmove = movelist[-1]
            prevmove = prevmove.rstrip("+")
            move0 = move.replace("x", prevmove[-2:])
            if gv.verbose:
                print("move reformatted from", move, "to", move0)

        # set promoted_piece, move_promotes, capture
        # e.g. +Bx7f

        #
        # promoted_piece
        #
        move = move0
        if move.startswith("+"):
            promoted_piece = "+"
            move = move.lstrip("+")
        else:
            promoted_piece = ""

        # e.g. Nx7g+
        move_equals = False            # ends in "=" and move does not promote
        if move.endswith("+"):
            move_promotes = "+"
            move = move.rstrip("+")
        elif move.endswith("="):
            move_promotes = ""
            move = move.rstrip("=")
            move_equals = True
        else:
            move_promotes = ""

        capture = False
        if move.find("-") != -1:
            move = move.replace("-", "")
            capture = False
        elif move.find("x") != -1:
            move = move.replace("x", "")
            capture = True

        if move0 != move:
            if gv.verbose:
                print("move reformatted from", move0, "to", move)
            move0 = move

        # move0 now has leading/trailing "+" and "-" and "x" symbols removed
        # e.g. +Bx7f   ->  B7f
        #       Nx7g+  ->  N7g
        #       G5h-6g ->  G5h6g
        #       G5hx6g ->  G5h6g
        #      +B2hx1i ->  B2h1i

        # e.g. P7f
        move = move0
        if len(move) == 3:

            piece = move[0]

            if not self.validate_piece(piece):
                if gv.verbose:
                    print("Move invalid (2). Move has invalid piece. ", move0)
                return error_return

            source_square = ""

            dest_square = move[1:3]
            if not self.validate_square(dest_square):
                if gv.verbose:
                    print("Move invalid (2). Move has invalid dest " \
                          "square. ", move0)
                return error_return

            move_type = 1  # Move type is piece + dest square

            return (promoted_piece, piece, source_square, dest_square,
                    move_promotes, move_equals, move_type)

        # e.g. G5h6g
        move = move0
        if len(move) == 5:

            piece = move[0]
            if not self.validate_piece(piece):
                if gv.verbose:
                    print("Move invalid (3). Move has invalid piece. ", move0)
                return error_return

            # just search on e.g. 5h6g to get match in legal move list
            piece = ""

            source_square = move[1:3]
            if not self.validate_square(source_square):
                if gv.verbose:
                    print("Move invalid (3). Move has invalid source" \
                          " square. ", move0)
                return error_return

            dest_square = move[3:5]
            if not self.validate_square(dest_square):
                if gv.verbose:
                    print("Move invalid (3). Move has invalid dest square. ", \
                          move0)
                return error_return

            return (promoted_piece, piece, source_square, dest_square,
                    move_promotes, move_equals, move_type)

        # e.g. G45h or Sf3g
        move = move0
        if len(move) == 4:
            piece = move[0]
            if not self.validate_piece(piece):
                if gv.verbose:
                    print("Move invalid (4). Move has invalid piece. ", move0)
                return error_return

            # in this format the 2nd char is either a row (a to i) or
            # column (1-9)
            source_square = move[1]
            if "123456789abcdefghi".find(source_square) == -1:
                if gv.verbose:
                    print("Move invalid (4). Move has invalid source square", \
                          move0)
                return error_return

            dest_square = move[2:4]
            if not self.validate_square(dest_square):
                if gv.verbose:
                    print("Move invalid (4). Move has invalid dest square. ", \
                          move0)
                return error_return

            return (promoted_piece, piece, source_square, dest_square,
                    move_promotes, move_equals, move_type)

        # Fallen through without formatting a valid move
        if gv.verbose:
            print("Move invalid (5).", move0)

        return error_return

    def validate_piece(self, piece):
        validpieces = (
            "L", "N", "S", "G", "K", "B", "R",
            "P", "+L", "+N", "+S", "+B", "+R", "+P")
        try:
            idx = validpieces.index(piece)
        except ValueError:
            return False
        return True

    def validate_square(self, square):
        if len(square) != 2:
            return ""
        # square is e.g. "7h"
        numstr = square[0]
        try:
            num = int(numstr)
        except:
            return ""

        # num must be 1-9
        if num == 0:
            return ""

        let = square[1]
        if "abcdefghi".find(let) == -1:
            return ""

        # square is valid
        return square

    def search_legal_moves(self, move, legal_move_list):
        if gv.verbose:
            print("searching for move", move)

        check_for_dupes = True
        hit_cnt = 0
        hit_list = []

        if move.endswith("+"):
            prom = True
        else:
            prom = False

        for legal_moves in legal_move_list:
            for lmove in legal_moves:
                lmove = lmove.strip()

                if lmove == move:
                    if not check_for_dupes:
                        return legal_moves[0]   # found a valid move
                    else:
                        hit_cnt += 1
                        hit_list.append(legal_moves[0])
                        break

                # if move does not promote and legal move does then count as a
                # matchand return unpromoted version of the move
                if not move.endswith("+") and lmove.endswith("+"):
                    if move == lmove[:len(lmove) - 1]:
                        move = legal_moves[0].replace("+", "")
                        return move

                        if not check_for_dupes:
                            return move            # found a valid move
                        else:
                            hit_cnt += 1
                            hit_list.append(move)
                            break

        if not check_for_dupes:
            return None

        if hit_cnt == 0:
            return None
        elif hit_cnt == 1:
            return hit_list[0]
        else:
            print("Duplicate hits for move:", move, "-", hit_list)
            return None

    # move number is numeric digits followed by a fullstop
    # e.g. "12."
    def get_moveno(self, ptr):
        moveno = ""
        while 1:
            if ptr >= self.game_len:
                return None, None
            if self.gamestr[ptr] >= "0" and self.gamestr[ptr] <= "9":
                moveno += self.gamestr[ptr]
                ptr += 1
                continue
            if self.gamestr[ptr] == ".":
                ptr += 1
                break
            return None, None  # Not a move number
        return moveno, ptr

    def load_game_psn(self, fname):

        self.fname = fname

        # check if it's a multi-game file
        gamecnt = 0
        headers = []
        self.file_position = []

        f = open(fname)
        position = f.tell()
        line = f.readline()
        while 1:
            if not line:
                break
            if line.startswith("["):
                self.file_position.append(position)
                gamecnt += 1
                hdr = []
                while 1:
                    hdr.append(line)
                    line = f.readline()
                    if not line:
                        break
                    if not line.startswith("["):
                        break
                headers.append(hdr)
            position = f.tell()
            line = f.readline()
        f.close()

        # No games in file
        if gamecnt == 0:
            self.gamelist.set_game_list([])
            gv.gui.info_box("No games in file")
            return

        # single game file - Load the game
        if gamecnt == 1:
            self.gamelist.set_game_list([])
            # Read the file a line at a time
            gamestr = ""

            f = open(fname)
            while 1:
                line = f.readline()
                if not line:
                    break
                gamestr += line
            f.close()
            self.load_game_psn_from_str(gamestr)
            return

        # multi game file - Display the Game List so user can select a game
        self.gamelist.set_game_list(headers)
        self.gamelist.show_gamelist_window()

        # Code to test all games in a file to see if gshogi will load them
        """
        ok_cnt = 0
        error_cnt = 0
        # use range(1, ..  i.e. start at 1 not 0 for 1st game
        for i in range(1, gamecnt):
            rc = self.load_game_from_multigame_file(i)
            if rc == 0:
                ok_cnt += 1
            else:
                error_cnt += 1
                print "Error in game ",i
                break
        print "OK:", ok_cnt, "Errors",error_cnt
        """

    # called from gamelist.py to load the game selected from the gamelist
    # of a multigame file
    def load_game_from_multigame_file(self, gameno):

        f = open(self.fname)
        f.seek(self.file_position[gameno - 1])
        gamestr = ""
        line = f.readline()
        while line.startswith("["):
            if not line:
                break
            gamestr += line
            line = f.readline()

        while not line.startswith("["):
            if not line:
                break
            gamestr += line
            line = f.readline()

        f.close()
        hdr = self.get_header_from_string(gamestr)
        rc = self.load_game_psn_from_str(gamestr)
        
            
        

        

def get_ref():
    if Psn.psn_ref is None:
        Psn.psn_ref = Psn()
    return Psn.psn_ref
