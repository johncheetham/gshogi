/*

    genmove.c

    This file is part of gshogi
    It came from GNU SHOGI and may have been modified for use in gshogi.

    gshogi is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    gshogi is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with gshogi.  If not, see <http://www.gnu.org/licenses/>.

*/


/*
 * FILE: genmove.c
 *
 * ----------------------------------------------------------------------
 * Copyright (c) 1993, 1994, 1995 Matthias Mutz
 * Copyright (c) 1999 Michael Vanier and the Free Software Foundation
 *
 * GNU SHOGI is based on GNU CHESS
 *
 * Copyright (c) 1988, 1989, 1990 John Stanback
 * Copyright (c) 1992 Free Software Foundation
 *
 * This file is part of GNU SHOGI.
 *
 * GNU Shogi is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 1, or (at your option) any
 * later version.
 *
 * GNU Shogi is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 * for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with GNU Shogi; see the file COPYING.  If not, write to the Free
 * Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
 * ----------------------------------------------------------------------
 *
 */

#include "gnushogi.h"

/* #define DONTUSE_HEURISTIC */

short *TrP;

static struct leaf  *node;
static short sqking, sqxking;
static short InCheck = false, GenerateAllMoves = false;
static short check_determined = false;

short deepsearchcut = true;
short tas = false, taxs = false, ssa = false;

short generate_move_flags = false;


/*
 * Ply limits for deep search cut.  No moves or drops flagged with "stupid"
 * are considered beyond ply BEYOND_STUPID.  Only moves or drops flagged
 * with "kingattack" are considered beyond ply BEYOND_KINGATTACK.  No moves
 * or drops flagged with "questionable" are considered beyond ply
 * BEYOND_QUESTIONABLE.  Only moves or drops flagged with "tesuji" are
 * considered beyond ply BEYOND_TESUJI.  No drops are considered beyond ply
 * BEYOND_DROP.  Exceptions: moves or drops that prevent check or give
 * check are always considered.
 */

#define BEYOND_STUPID        0
#define BEYOND_TIMEOUT       2
#define BEYOND_KINGATTACK    6
#define BEYOND_QUESTIONABLE  8
#define BEYOND_TESUJI        8
#define BEYOND_DROP         10

#ifdef DONTUSE_HEURISTIC
static short MaxNum[MAXDEPTH] =
{
    -1, 40, 80, 20, 40, 10, 5, 5, 5, 5,
     5,  5,  5,  5,  5,  5, 5, 5, 5, 5,
     5,  5,  5,  5,  5,  5, 5, 5, 5, 5,
     5,  5,  5,  5,  5,  5, 5, 5, 5, 5,
};
#endif

#ifdef HASHKEYTEST
extern int CheckHashKey();
extern char mvstr[4][6];
#endif


/*
 * Update Arrays board[] and color[] to reflect the new board
 * position obtained after making the move pointed to by node.
 */

inline static void
GenMakeMove(short side,
            short f,
            short t,
            short *tempb,  /* piece at to square */
            short *tempc,  /* color of to square */
            short promote_piece)
{
    short piece, upiece, n;

    t = t & 0x7f;

    if (f > NO_SQUARES)
    {
        piece = f - NO_SQUARES;

        if (piece > NO_PIECES)
            piece -= NO_PIECES;

        board[t] = piece;
        color[t] = side;
        n = (Captured[side][piece])--;
        UpdateDropHashbd(side, piece, n);
        UpdateHashbd(side, piece, -1, t);
        UpdatePieceList(side, t, ADD_PIECE);
    }
    else
    {
        *tempb = board[t];
        *tempc = color[t];

        if (*tempb != no_piece)
        {
            n = ++Captured[side][upiece = unpromoted[*tempb]];
            UpdateDropHashbd(side, upiece, n);
            UpdateHashbd(*tempc, *tempb, -1, t);
            UpdatePieceList(*tempc, t, REMOVE_PIECE);
        }

        piece = board[f];
        Pindex[t] = Pindex[f];
        PieceList[side][Pindex[t]] = t;
        color[f] = neutral;
        board[f] = no_piece;
        color[t] = side;

        if (promote_piece)
        {
            UpdateHashbd(side, piece, f, -1);
            board[t] = promoted[piece];
            UpdateHashbd(side, board[t], -1, t);
        }
        else
        {
            board[t] = piece;
            UpdateHashbd(side, piece, f, t);
        }
    }

#ifdef HASHKEYTEST
    if (CheckHashKey())
    {
        algbr(f, t, 0);
        printf("error in GenMakeMove: %s\n", mvstr[0]);
        exit(1);
    }
#endif
}



/*
 * Take back a move.
 */

static void
GenUnmakeMove(short side,
              short f,
              short t,
              short tempb,
              short tempc,
              short promote_piece)
{
    short piece, upiece, n;

    t = t & 0x7f;

    if (f > NO_SQUARES)
    {
        piece = f - NO_SQUARES;

        if (piece > NO_PIECES)
            piece -= NO_PIECES;

        board[t] = no_piece;
        color[t] = neutral;
        n = ++Captured[side][piece];
        UpdateDropHashbd(side, piece, n);
        UpdateHashbd(side, piece, -1, t);
        UpdatePieceList(side, t, REMOVE_PIECE);
    }
    else
    {
        piece = board[t];
        color[t] = tempc;
        board[t] = tempb;
        Pindex[f] = Pindex[t];
        PieceList[side][Pindex[f]] = f;

        if (tempb != no_piece)
        {
            /* FIXME: make this next line a bit more reasonable... */
            n = (Captured[side][upiece = unpromoted[tempb]])--;
            UpdateDropHashbd(side, upiece, n);
            UpdateHashbd(tempc, tempb, -1, t);
            UpdatePieceList(tempc, t, ADD_PIECE);
        }

        color[f] = side;

        if (promote_piece)
        {
            UpdateHashbd(side, piece, -1, t);
            board[f] = unpromoted[piece];
            UpdateHashbd(side, board[f], f, -1);
        }
        else
        {
            board[f] = piece;
            UpdateHashbd(side, piece, f, t);
        }
    }

#ifdef HASHKEYTEST
    if (CheckHashKey())
    {
        algbr(f, t, 0);
        printf("error in GenUnmakeMove: %s\n", mvstr[0]);
        exit(1);
    }
#endif
}



static void
gives_check_flag(unsigned short *flags, short side, short f, short t)
{
    short tempb, tempc, blockable, promote_piece;
    promote_piece = (*flags & promote) != 0;
    GenMakeMove(side, f, t, &tempb, &tempc, promote_piece);

    if (SqAttacked(sqxking, side, &blockable))
        *flags |= check;

    GenUnmakeMove(side, f, t, tempb, tempc, promote_piece);
}


inline static void
Link(short side, short piece,
     short from, short to, unsigned short local_flag, short s)
{
    if (*TrP == TREE)
    {
        ShowMessage("TREE overflow\n");
    }
    else
    {
        node->f = from;
        node->t = (local_flag & promote) ? (to | 0x80) : to;
        node->reply = 0;
        node->flags = local_flag;
        node->score = s;
        node->INCscore = INCscore;

        if (GenerateAllMoves)
        {
            /* FIXME: gimme a break! */
            (*TrP)++, node++;
        }
        else if (InCheck)
        {
            /* only moves out of check */
            short tempb, tempc, sq, threat, blockable, promote_piece;
            promote_piece = (node->flags & promote) != 0;
            GenMakeMove(side, node->f, node->t,
                        &tempb, &tempc, promote_piece);
            sq = (from == sqking) ? to : sqking;
            threat = SqAttacked(sq, side ^ 1, &blockable);
            GenUnmakeMove(side, node->f, node->t,
                          tempb, tempc, promote_piece);

            if (!threat)
            {
                /* FIXME! Gimme a break! */
                (*TrP)++, node++;
            }
        }
        else if (flag.tsume)
        {
            /* only moves that give check */
            if (!(node->flags & check) && !check_determined)
            {
                /* determine check flag */
                gives_check_flag(&node->flags, side, node->f, node->t);
            }

            if (node->flags & check)
            {
                /* FIXME! Gimme a break! */
                (*TrP)++, node++;
            }
        }
        else
        {
            /* FIXME! Gimme a break! */
            (*TrP)++, node++;
        }
    }
}


inline int
PromotionPossible(short color, short f, short t, short p)
{
    if (color == black)
    {
        if ((f < 54) && (t < 54))
            return false;
    }
    else
    {
        if ((f > 26) && (t > 26))
            return false;
    }

    /* FIXME: this can be simplified... */
    switch (p)
    {
    case pawn:
    case lance:
    case knight:
    case silver:
    case bishop:
    case rook:
        return true;
    };

    return false;
}


inline int
NonPromotionPossible(short color, short f,
                     short t, short p)
{
    switch (p)
    {
    case pawn :
        if (color == black)
        {
            return ((t < 72)
                    ? true
                    : (generate_move_flags ? ILLEGAL_TRAPPED : false));
        }
        else
        {
            return ((t > 8)
                    ? true
                    : (generate_move_flags ? ILLEGAL_TRAPPED : false));
        }

    case lance:
        if (color == black)
        {
            return ((t < 72)
                    ? true
                    : (generate_move_flags ? ILLEGAL_TRAPPED : false));
        }
        else
        {
            return ((t > 8)
                    ? true
                    : (generate_move_flags ? ILLEGAL_TRAPPED : false));
        }

    case knight:
        if (color == black)
        {
            return ((t < 63)
                    ? true
                    : (generate_move_flags ? ILLEGAL_TRAPPED : false));
        }
        else
        {
            return ((t > 17)
                    ? true
                    : (generate_move_flags ? ILLEGAL_TRAPPED : false));
        }
    }

    return true;
}


#if defined FIELDBONUS || defined DROPBONUS

/* bonus for possible next moves */

inline static short
field_bonus(short ply, short side, short piece,
            short f, short t, unsigned short *local_flag)
{
    short s, u, ptyp;
    unsigned char *ppos, *pdir;
    short c1, c2;

#ifdef SAVE_NEXTPOS
    short d;
#endif

    c1 = side;
    c2 = side ^ 1;
    s = 0;
    check_determined = true;

    ptyp = ptype[side][piece];

#ifdef SAVE_NEXTPOS
    u = first_direction(ptyp, &d, t);
#else
    ppos = (*nextpos[ptyp])[t];
    pdir = (*nextdir[ptyp])[t];
    u = ppos[t];
#endif

    do
    {
        short coloru = color[u];

        if (piece != king && GameCnt > 40)
        {
            if (distance(u, EnemyKing) <= 1)
            {
                /* can reach square near own king */
                s += 2;
                *local_flag |= kingattack;
            }
            else if (distance(u, OwnKing) <= 1)
            {
                /* can reach square near enemy king */
                s++;
                *local_flag |= kingattack;
            }
        }

        if (coloru == side)
        {
            /* impossible next move */
#ifdef SAVE_NEXTPOS
            u = next_direction(ptyp, &d, t);
#else
            u = pdir[u];
#endif
        }
        else
        {
            /* possible next move */
            if (PromotionPossible(side, t, u, piece))
            {
                /* possible promotion in next move */
                if (piece == pawn)
                {
                    s += 2;
#ifdef TESUJIBONUS
                    if (!InPromotionZone(side, t))
                    {
                        *local_flag |= tesuji; /* The dangling pawn */
                        s++;
                    }
#endif
                }
                else
                {
                    s++;
                }
            }

            if (coloru == neutral)
            {
                /* next move to an empty square */
                if (u == FROMsquare)
                {
                    /* opponent has just left this square */
                    s++;
                }

#ifdef SAVE_NEXTPOS
                u = next_position(ptyp, &d, t, u);
#else
                u = ppos[u];
#endif
            }
            else
            {
                /* attack opponents piece */
#ifdef TESUJIBONUS
                short boardu, upiece, rvupiece, rvuboard;
#endif
                s++;

                if (u == TOsquare) /* opponent has moved to TOsquare */
                    s++;

                if ((boardu = board[u]) == king)
                {
                    s += 20; INCscore -= 18;
                    *local_flag |= check; /* move threatens
                                           * opponents king */
                }

#ifdef TESUJIBONUS
                upiece = unpromoted[piece];
                rvupiece = relative_value[upiece];
                rvuboard = relative_value[unpromoted[boardu]];

                if ((upiece == pawn) && (Captured[side][pawn] > 1))
                {
                    *local_flag |= tesuji; /* The joining pawn attack */
                    s++;
                }

                if (rvupiece <= rvuboard)
                {
                    *local_flag |= tesuji; /* The striking pawn
                                            * (piece) attack */

                    if (f > NO_SQUARES)
                        s += 2;
                    else
                        s++;

                    if (upiece == pawn)
                        s++;

                    /* CHECKME: is this right? */
                    if (((rvupiece == rvuboard) && (upiece == pawn))
                        || (upiece == bishop) || (upiece == knight))
                    {
                        s++; /* The opposing pawn (piece) */

                        if (upiece == pawn)
                            s++;
                    }
                }
#endif

#ifdef SAVE_NEXTPOS
                u = next_direction(ptyp, &d, t);
#else
                u = pdir[u];
#endif
            }
        }
    }
    while (u != t);

    INCscore += s;

    return s;
}

#endif




/*
 * Add a move to the tree.  Assign a bonus to order the moves as follows:
 * 1. Principle variation 2. Capture of last moved piece 3. Other captures
 * (major pieces first) 4. Killer moves 5. Tesuji drops 6. Other Moves
 * 7. Other drops. 8. Non-promoting moves
 * If the flag.tsume is set, assign a high bonus for checks.
 */

/* inline */ void
LinkMove(short ply, short f,
         short t,
         unsigned short local_flag,
         short xside,
         short score_if_impossible)
{
    short s = 0;
    short side, piece, mv;
    short flag_tsume, try_link = true;
    short c1, c2, ds, is_drop = f > NO_SQUARES;
    unsigned int as = 0;

    flag_tsume = flag.tsume;

    c1 = side = xside ^ 1;
    c2 = xside;

    /*
     * Is it determined whether the move gives check ?
     */

    check_determined = ((local_flag & check) != 0);

    mv = (f << 8) | ((local_flag & promote) ? (t | 0x80) : t);

    if (f > NO_SQUARES)
    {
        piece = f - NO_SQUARES;

        if (piece > NO_PIECES)
            piece -= NO_PIECES;
    }
    else
    {
        piece = board[f];
    }

    if (score_if_impossible < 0)
    {
        /* The move is flagged as illegal. */
        Link(side, piece,
             f, t, local_flag, score_if_impossible);

        return;
    }

    INCscore = 0;

#ifdef HISTORY
    s += history[hindex(side, mv)];
#endif

    /* If we're running short of tree nodes, go into tsume mode. */

    if (!(local_flag & capture))
    {
        if (*TrP > (TREE - 300))
        {
            /* too close to tree table limit */
            flag.tsume = true;
        }
    }

    /* Guess strength of move and set flags. */

    if ((piece != king) && (!in_opening_stage))
    {
        if (distance(t, EnemyKing) <= 1)
        {
            /* bonus for square near enemy king */
            s += 15;
            INCscore += 2;
            local_flag |= kingattack;
        }
        else if (distance(t, OwnKing) <= 1)
        {
            /* bonus for square near own king */
            s += 10;
            INCscore++;
            local_flag |= kingattack;
        }
    }

    if (tas)  /* own attack array available */
    {
        /* square t defended by own piece (don't count piece to move) ? */
        if (is_drop
            ? (as = attack[side][t])
            : (as = ((attack[side][t] & CNT_MASK) > 1)))
            s += (ds = in_endgame_stage ? 100 : 10);
    }

    if (taxs)  /* opponents attack array available */
    {
        /* square t not threatened by opponent or
         * defended and only threatened by opponents king ?
         */
        unsigned int axs;

        if (!(axs = attack[xside][t])
            || (tas && as && (axs & control[king]) && (axs & CNT_MASK) == 1))
        {
            /* FIXME: this is a mess; clean up. */
            s += (ds = in_endgame_stage
                  ? 200
                  : (is_drop
                     ? (InPromotionZone(side, t)
                        ? 40 + relative_value[piece]
                        : 10)
                     : 20));
        }
    }

    /* target square near area of action */

    if (TOsquare >= 0)
        s += (9 - distance(TOsquare, t));

    if (FROMsquare >= 0)
        s += (9 - distance(FROMsquare, t)) / 2;

    /* target square near own or enemy king */

    if (!in_opening_stage && piece != king)
    {
        if (balance[c1] < 50)
            s += (9 - distance(EnemyKing, t)) * (50 - balance[c1]) / 20;
        else
            s += (9 - distance(OwnKing, t)) * (balance[c1] - 50) / 20;
    }

    if (f > NO_SQUARES)
    {
        /* bonus for drops, in order to place
         * drops before questionable moves */
        s += in_endgame_stage ? 25 : 10;

        if (t == FROMsquare)
        {
            /* drop to the square the opponent has just left */
            s += 5;
        };

        if (piece == gold)
            s -= 32 / Captured[side][gold];
        else if (piece == silver)
            s -= 16 / Captured[side][silver];

#if defined DROPBONUS
        s += field_bonus(ply, side, piece, f, t, &local_flag);

        if (s == 10 && piece != pawn)
            local_flag |= questionable;
#endif
    }
    else
    {
        /* bonus for moves (non-drops) */
        int consider_last = false;

        if (in_endgame_stage && Captured[side][gold])
            s += 10;

        s += 20;

        if (t == FROMsquare)
        {
            /* move to the square the opponent has just left */
            s += in_endgame_stage ? 10 : 1;
        }

        if (color[t] != neutral)
        {
            /* Captures */
            if (in_endgame_stage)
            {
                s += relative_value[board[t]] - relative_value[piece];
            }
            else
            {
                s += (*value)[stage][board[t]] - relative_value[piece];
            }

            if (t == TOsquare) /* Capture of last moved piece */
                s += in_endgame_stage ? 5 : 50;
        }

        if (local_flag & promote)
        {
            /* bonus for promotions */
            s++;
            INCscore += value[stage][promoted[piece]] - value[stage][piece];
        }
        else
        {
            /* bonus for non-promotions */
            if (PromotionPossible(side, f, t, piece))
            {
#ifdef TESUJIBONUS
                /* Look at non-promoting silver or knight */
                if (piece == silver || piece == knight)
                {
                    local_flag |= tesuji; /* Non-promotion */
                    s++;
                }
                else
#endif
                {
                    consider_last = true;

                    if (piece == pawn || piece == bishop || piece == rook)
                    {
                        local_flag |= stupid;
                        INCscore -= 20;
                    }
                    else
                    {
                        local_flag |= questionable;
                        INCscore -= 10;
                    }
                }
            }
        }

        if (consider_last)
        {
            if (local_flag & stupid)
                s = 0;
            else
                s = s % 20;
        }
        else
        {
#if defined FIELDBONUS
            s += field_bonus(ply, side, piece, f, t, &local_flag);
#endif
        }
    }

#if defined CHECKBONUS
    /* determine check flag */
    if (!(local_flag & check) && !check_determined)
    {
        gives_check_flag(&local_flag, side, f, t);

        if (local_flag & check)
            s += 20;
    }
#endif

    /* check conditions for deep search cut (flag.tsume = true) */

#ifdef DEEPSEARCHCUT
    if (!flag.tsume && deepsearchcut)
    {
        if ((ply > BEYOND_STUPID) && (local_flag & stupid))
        {
            try_link = flag.force || ((ply == 1) && (side != computer));
        }
        else if (hard_time_limit && (ply > BEYOND_TIMEOUT) && flag.timeout)
        {
            flag.tsume = true;
        }
        else if ((ply > BEYOND_KINGATTACK) && !(local_flag & kingattack))
        {
            flag.tsume = true;
        }
        else if ((ply > BEYOND_QUESTIONABLE) && (local_flag & questionable))
        {
            flag.tsume = true;
#ifdef TESUJIBONUS
        }
        else if ((ply > BEYOND_TESUJI) && !(local_flag & tesuji))
        {
            flag.tsume = true;
#endif
        }
        else if ((ply > BEYOND_DROP) && (f > NO_SQUARES))
        {
            flag.tsume = true;
        }
    }
#endif

    if (try_link || GenerateAllMoves)
    {
        Link(side, piece, f, t, local_flag,
             s - ((SCORE_LIMIT + 1000) * 2));
    }

    flag.tsume = flag_tsume;
}



short
DropPossible(short piece, short side, short sq)
{
    short r = row(sq), possible = true;

    if (board[sq] != no_piece)
    {
        possible = false;
    }
    else if (piece == pawn)
    {
        if ((side == black) && (r == 8))
        {
            possible = (generate_move_flags ? ILLEGAL_TRAPPED : false);
        }
        else if ((side == white) && (r == 0))
        {
            possible = (generate_move_flags ? ILLEGAL_TRAPPED : false);
        }
        else if (PawnCnt[side][column(sq)])
        {
            possible = (generate_move_flags ? ILLEGAL_DOUBLED : false);
        }

        /* Pawn drops are invalid if they mate the opponent. */
        if (possible)
        {
            short f, tempb, tempc;
            f = pawn + NO_SQUARES;

            if (side == white)
                f += NO_PIECES;

            GenMakeMove(side, f, sq, &tempb, &tempc, false);

            if (IsCheckmate(side^1, -1, -1))
                possible = (generate_move_flags ? ILLEGAL_MATE : false);

            GenUnmakeMove(side, f, sq, tempb, tempc, false);
        }
    }
    else if (piece == lance)
    {
        if ((side == black) && (r == 8))
            possible = (generate_move_flags ? ILLEGAL_TRAPPED : false);
        else if ((side == white) && (r == 0))
            possible = (generate_move_flags ? ILLEGAL_TRAPPED : false);
    }
    else if (piece == knight)
    {
        if ((side == black) && (r >= 7))
            possible = (generate_move_flags ? ILLEGAL_TRAPPED : false);
        else if ((side == white) && (r <= 1))
            possible = (generate_move_flags ? ILLEGAL_TRAPPED : false);
    }

    return possible;
}


#if defined DONTUSE_HEURISTIC
static void
SortMoves(short ply)
{
    short p;

    for (p = TrPnt[ply]; p < TrPnt[ply+1]; p++)
        pick(p, TrPnt[ply+1] - 1);
}
#endif /* DONTUSE_HEURISTIC */


#ifdef DONTUSE_HEURISTIC

static void
DontUseMoves(short ply, short n)
{
    struct leaf  *p;
    short i, k;

   /* k = number of check moves + number of captures */
    for (i = TrPnt[ply], k = 0; i < TrPnt[ply+1]; i++)
    {
        p = &Tree[i];

        if ((p->flags & check) || (p->flags & capture))
        {
            if (++k >= n)
                return;
        }
    }

    /* use n moves */
    for (i = TrPnt[ply]; i < TrPnt[ply+1]; i++)
    {
        p = &Tree[i];

        if (!((p->flags & check) || (p->flags & capture)))
        {
            if (k < n)
                k++;
            else
            {
                p->score = DONTUSE;
            }
        }
    }
}

#endif



/*
 * Generate moves for a piece. The moves are taken from the precalculated
 * array nextpos/nextdir.  If the board is free, next move is chosen from
 * nextpos else from nextdir.
 */

inline void
GenMoves(short ply, short sq, short side,
         short xside)
{
    short u, piece;
    short ptyp, possible;
#ifdef SAVE_NEXTPOS
    short d;
#else
    unsigned char *ppos, *pdir;
#endif

    piece = board[sq];
    ptyp = ptype[side][piece];

#ifdef SAVE_NEXTPOS
    u = first_direction(ptyp, &d, sq);
#else
    ppos = (*nextpos[ptyp])[sq];
    pdir = (*nextdir[ptyp])[sq];
    u = ppos[sq];
#endif

    do
    {
        unsigned short local_flag;
        short  c;

        if ((c = color[u]) == xside)
            local_flag = capture;
        else
            local_flag = 0;

        if (c != side && board[u] != king)
        {
            if (PromotionPossible(color[sq], sq, u, piece))
            {
                LinkMove(ply, sq, u, local_flag | promote, xside, true);

                if ((possible
                     = NonPromotionPossible(color[sq], sq, u, piece)))
                {
                    LinkMove(ply, sq, u, local_flag, xside, possible);
                }
            }
            else
            {
                LinkMove(ply, sq, u, local_flag, xside, true);
            }
        }

        if (c == neutral)
#ifdef SAVE_NEXTPOS
        {
            u = next_position(ptyp, &d, sq, u);
        }
        else
        {
            u = next_direction(ptyp, &d, sq);
        }
#else
        {
            u = ppos[u];
        }
        else
        {
            u = pdir[u];
        }
#endif
    }
    while (u != sq);
}




/*
 * Drop each piece in hand of "side" to square "u" (if allowed).
 */

static void
DropToSquare(short side, short xside, short ply, short u)
{
    short i, possible;

    for (i = pawn; i < king; i++)
    {
        if (Captured[side][i])
        {
            if ((possible = DropPossible(i, side, u)))
            {
                short f;
                f = NO_SQUARES + i;

                if (side == white)
                    f += NO_PIECES;

                LinkMove(ply, f, u, (dropmask | i), xside, possible);
            }
        }
    }
}



/*
 * Add drops of side that prevent own king from being in check
 * from xside's sweeping pieces.
 */

static void
LinkPreventCheckDrops(short side, short xside, short ply)
{
#ifdef SAVE_NEXTPOS
    short d, dd;
#else
    unsigned char *ppos, *pdir;
#endif
    short piece, u, xu, square, ptyp;
    short n, drop_square[9];

    if (board[square = PieceList[side][0]] != king)
        return;

    for (piece = lance; piece <= rook; piece++)
    {
        if (piece == lance || piece == bishop || piece == rook)
        {
            /* check for threat of xside piece */
            ptyp = ptype[side][piece];
            n = 0;
#ifdef SAVE_NEXTPOS
            u = first_direction(ptyp, &d, square);
#else
            ppos = (*nextpos[ptyp])[square];
            pdir = (*nextdir[ptyp])[square];
            u = ppos[square];
#endif

            do
            {
                if (color[u] == neutral)
                {
#ifdef SAVE_NEXTPOS
                    dd = d;
                    xu = next_position(ptyp, &d, square, u);

                    if (xu == next_direction(ptyp, &dd, square))
                    {
                        n = 0;  /* oops new direction */
                    }
                    else
                    {
                        drop_square[n++] = u;
                    }
#else

                    if ((xu = ppos[u]) == pdir[u])
                    {
                        n = 0;  /* oops new direction */
                    }
                    else
                    {
                        drop_square[n++] = u;
                    }
#endif
                    u = xu;
                }
                else
                {
                    if (color[u] == xside && (unpromoted[board[u]] == piece))
                    {
                        /* king is threatened by opponents piece */
                        while (n > 0)
                        {
                            DropToSquare(side, xside, ply, drop_square[--n]);
                        }
                    }
                    else
                    {
                        n = 0;
                    }
#ifdef SAVE_NEXTPOS
                    u = next_direction(ptyp, &d, square);
#else
                    u = pdir[u];
#endif
                }
            }
            while (u != square);
        }
    }
}



/*
 * Add drops that check enemy king.
 */

static void
LinkCheckDrops(short side, short xside, short ply)
{
#ifdef SAVE_NEXTPOS
    short d;
#else
    unsigned char *ppos, *pdir;
#endif
    short u, ptyp;
    short square, piece;

    if (board[square = PieceList[xside][0]] != king)
        return;

    for (piece = pawn; piece < king; piece++)
    {
        if (Captured[side][piece])
        {
            /*
             * "side" has "piece" in hand. Try to make a piece move from
             * opponents king square and drop this piece to each reachable
             * empty square. This definitely gives check!  For a pawn drop
             * it must not double pawns and it must not be checkmate!
             */

            ptyp = ptype[xside][piece];
#ifdef SAVE_NEXTPOS
            u = first_direction(ptyp, &d, square);
#else
            ppos = (*nextpos[ptyp])[square];
            pdir = (*nextdir[ptyp])[square];
            u = ppos[square];
#endif
            do
            {
                if (color[u] == neutral)
                {
                    if (piece != pawn || DropPossible(pawn, side, u))
                    {
                        short f;
                        f = NO_SQUARES + piece;

                        if (side == white)
                            f += NO_PIECES;

                        LinkMove(ply, f, u,
                                 (dropmask | piece | check), xside, true);
                    }

#ifdef SAVE_NEXTPOS
                    u = next_position(ptyp, &d, square, u);
#else
                    u = ppos[u];
#endif
                }
                else
                {
#ifdef SAVE_NEXTPOS
                    u = next_direction(ptyp, &d, square);
#else
                    u = pdir[u];
#endif
                }
            }
            while (u != square);
        }
    }
}



/*
 * Fill the array Tree[] with all available moves for side to play. Array
 * TrPnt[ply] contains the index into Tree[] of the first move at a ply.
 * in_check = 0 side is not in check
 * in_check > 1 side is in check
 * in_check < 0 don't know
 * in_check -2 indicates move generation for book moves
 */

void
MoveList(short side, short ply,
         short in_check, short blockable)
{
    short i, xside, u;
    struct leaf  *firstnode;
    short flag_tsume, num;

#ifdef HISTORY
    unsigned short hiHt = 0, hi0 = 0, hi1 = 0, hi2 = 0, hi3 = 0, hi4 = 0;
#endif

    flag_tsume = flag.tsume;

    xside = side ^ 1;

    sqking  = PieceList[side][0];
    sqxking = PieceList[xside][0];

    if (in_check >= 0)
    {
        InCheck = in_check;
    }
    else
    {
        InCheck = (board[sqking] == king)
            ? SqAttacked(sqking, xside, &blockable)
            : false;
    }

    GenerateAllMoves = (in_check == -2) || generate_move_flags;

    if (InCheck /* && (ply > 1 || side == computer) */)
    {
        /* Own king in check */
        flag.tsume = true;
    }

    TrP = &TrPnt[ply + 1];
    *TrP = TrPnt[ply];

    firstnode = node = &Tree[*TrP];

    if (!PV)
        Swag0 = killr0[ply];
    else
        Swag0 = PV;

    Swag1 = killr1[ply];
    Swag2 = killr2[ply];
    Swag3 = killr3[ply];

    if (ply > 2)
        Swag4 = killr1[ply - 2];
    else
        Swag4 = 0;

#ifdef HISTORY
    if (use_history)
    {
        history[hiHt = hindex(side, SwagHt)] += 5000;
        history[hi0  = hindex(side, Swag0)]  += 2000;
        history[hi1  = hindex(side, Swag1)]  += 60;
        history[hi2  = hindex(side, Swag2)]  += 50;
        history[hi3  = hindex(side, Swag3)]  += 40;
        history[hi4  = hindex(side, Swag4)]  += 30;
    }
#endif

    for (i = PieceCnt[side]; i >= 0; i--)
        GenMoves(ply, PieceList[side][i], side, xside);

    if (!InCheck || blockable)
    {
        if (flag.tsume)
        {
            /* special drop routine for tsume problems */
            if (InCheck)
                LinkPreventCheckDrops(side, xside, ply);
            else
                LinkCheckDrops(side, xside, ply);
        }
        else
        {
            for (u = 0; u < NO_SQUARES; u++)
                DropToSquare(side, xside, ply, u);
        }
    }

#ifdef HISTORY
    if (use_history)
    {
        history[hiHt] -= 5000;
        history[hi0]  -= 2000;
        history[hi1]  -= 60;
        history[hi2]  -= 50;
        history[hi3]  -= 40;
        history[hi4]  -= 30;
    }
#endif

    SwagHt = 0;           /* SwagHt is only used once */

    if (flag.tsume && node == firstnode)
        (*TrP)++;

    GenCnt += (num = (TrPnt[ply+1] - TrPnt[ply]));

#ifdef DONTUSE_HEURISTIC
    /* remove some nodes in case of wide spread in depth */
    if (!flag.tsume && (i = MaxNum[ply]) > 0 && num > i)
    {
        SortMoves(ply);
        DontUseMoves(ply, i);
    }
#endif

    flag.tsume = flag_tsume;
}



/*
 * Fill the array Tree[] with all available captures for side to play.  If
 * there is a non-promote option, discard the non-promoting move.  Array
 * TrPnt[ply] contains the index into Tree[] of the first move at a ply.
 * If flag.tsume is set, only add captures (but also the non-promoting)
 * that threaten the opponents king.
 *
 * in_check = 0: side is not in check
 * in_check > 1: side is in check
 * in_check < 0: we don't know
 */

void
CaptureList(short side, short ply,
            short in_check, short blockable)
{
    short u, sq, xside;
#ifdef SAVE_NEXTPOS
    short d;
#else
    unsigned char *ppos, *pdir;
#endif
    short i, piece, flag_tsume;
    small_short *PL;

    xside = side ^ 1;

    TrP = &TrPnt[ply + 1];
    *TrP = TrPnt[ply];
    node = &Tree[*TrP];

    flag_tsume = flag.tsume;

    sqking = PieceList[side][0];
    sqxking = PieceList[xside][0];

    if (in_check >= 0)
    {
        InCheck = in_check;
    }
    else
    {
        InCheck = (board[sqking] == king)
            ? SqAttacked(sqking, xside, &blockable)
            : false;
    }

    GenerateAllMoves = (in_check == -2);

    if (InCheck && (ply > 1 || side == computer))
    {
        /* Own king is in check */
        flag.tsume = true;
    }

    check_determined = false;

    PL = PieceList[side];

    for (i = 0; i <= PieceCnt[side]; i++)
    {
        short ptyp;
        sq = PL[i];
        piece = board[sq];
        ptyp = ptype[side][piece];
#ifdef SAVE_NEXTPOS
        u = first_direction(ptyp, &d, sq);
#else
        ppos = (*nextpos[ptyp])[sq];
        pdir = (*nextdir[ptyp])[sq];
        u = ppos[sq];
#endif
        do
        {
            if (color[u] == neutral)
            {
#ifdef SAVE_NEXTPOS
                u = next_position(ptyp, &d, sq, u);
#else
                u = ppos[u];
#endif
            }
            else
            {
                if (color[u] == xside && board[u] != king)
                {
                    short PP;

                    if ((PP = PromotionPossible(color[sq], sq, u, piece)))
                    {
                        Link(side, piece,
                             sq, u, capture | promote,
                             (*value)[stage][board[u]]
#if !defined SAVE_SVALUE
                             + svalue[board[u]]
#endif
                             - relative_value[piece]);
                    }

                    if (!PP || flag.tsume)
                    {
                        Link(side, piece,
                             sq, u, capture,
                             (*value)[stage][board[u]]
#if !defined SAVE_SVALUE
                             + svalue[board[u]]
#endif
                             - relative_value[piece]);
                    }
                }

#ifdef SAVE_NEXTPOS
                u = next_direction(ptyp, &d, sq);
#else
                u = pdir[u];
#endif
            }
        }
        while (u != sq);
    }

    flag.tsume = flag_tsume;

    SwagHt = 0;           /* SwagHt is only used once */
}




/*
 * If the king is in check, try to find a move that prevents check.
 * If such a move is found, return false, otherwise return true.
 * in_check = 0: side is not in check
 * in_check > 1: side is in check
 * in_check < 0: don't know
 * blockable > 0 && check: check can possibly be prevented by a drop
 * blockable = 0 && check: check can definitely not be prevented by a drop
 * blockable < 0 && check: nothing known about type of check
 */

short
IsCheckmate(short side, short in_check, short blockable)
{
    short u, sq, xside;
#ifdef SAVE_NEXTPOS
    short d;
#else
    unsigned char *ppos, *pdir;
#endif
    short i, piece;
    small_short *PL;
    short tempb, tempc, ksq, threat, dummy, sqking;
    short InCheck;

    xside = side ^ 1;

    sqking = PieceList[side][0];

    /*
     * Checkmate is possible only if king is in check.
     */

    if (in_check >= 0)
        InCheck = in_check;
    else if (board[sqking] == king)
        InCheck = SqAttacked(sqking, xside, &blockable);
    else
        InCheck = false;

    if (!InCheck)
        return false;

    /*
     * Try to find a move that prevents check.
     */

    PL = PieceList[side];

    for (i = 0; i <= PieceCnt[side]; i++)
    {
        short ptyp;
        sq = PL[i];
        piece = board[sq];
        ptyp = ptype[side][piece];
#ifdef SAVE_NEXTPOS
        u = first_direction(ptyp, &d, sq);
#else
        ppos = (*nextpos[ptyp])[sq];
        pdir = (*nextdir[ptyp])[sq];
        u = ppos[sq];
#endif
        do
        {
            if (color[u] == neutral || color[u] == xside)
            {
                GenMakeMove(side, sq, u, &tempb, &tempc, false);
                ksq = (sq == sqking) ? u : sqking;
                threat = SqAttacked(ksq, xside, &dummy);
                GenUnmakeMove(side, sq, u, tempb, tempc, false);

                if (!threat)
                    return false;
            }

#ifdef SAVE_NEXTPOS
            u = (color[u] == neutral)
                ? next_position(ptyp, &d, sq, u)
                : next_direction(ptyp, &d, sq);
#else
            u = (color[u] == neutral) ? ppos[u] : pdir[u];
#endif
        }
        while (u != sq);
    }

    /*
     * Couldn't find a move that prevents check.
     * Try to find a drop that prevents check.
     */

    if (blockable != 0)
    {
        for (piece = king - 1; piece >= pawn; piece--)
        {
            if (Captured[side][piece])
            {
                for (u = 0; u < NO_SQUARES; u++)
                {
                    if (DropPossible(piece, side, u))
                    {
                        short f;
                        f = NO_SQUARES + piece;

                        if (side == white)
                            f += NO_PIECES;

                        GenMakeMove(side, f, u, &tempb, &tempc, false);
                        threat = SqAttacked(sqking, xside, &dummy);
                        GenUnmakeMove(side, f, u, tempb, tempc, false);

                        if (!threat)
                            return false;
                    }
                }

                /*
                 * If the piece could be dropped at any square, it is
                 * impossible for any other piece drop to prevent check.
                 * Drops are restricted for pawns, lances, and knights.
                 */

                if (piece > knight)
                    break;
            }
        }
    }

    return true;

}
