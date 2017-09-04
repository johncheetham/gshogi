/*

    eval.c

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
 * FILE: eval.c
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
#include "pattern.h"

extern void
ShowStage(void);

/* Hash table for preventing multiple scoring of the same position */

int EADD = 0;       /* number of writes to the cache table */
int EGET = 0;       /* number of hits to the cache table */
int PUTVAR = false; /* shall the current scoring be cached? */


/* Pieces and colors of initial board setup */

const small_short Stboard[NO_SQUARES] =
{
    lance, knight, silver,   gold,   king,   gold, silver, knight,  lance,
    0, bishop,      0,      0,      0,      0,      0,   rook,      0,
    pawn,   pawn,   pawn,   pawn,   pawn,   pawn,   pawn,   pawn,   pawn,
    0,      0,      0,      0,      0,      0,      0,      0,      0,
    0,      0,      0,      0,      0,      0,      0,      0,      0,
    0,      0,      0,      0,      0,      0,      0,      0,      0,
    pawn,   pawn,   pawn,   pawn,   pawn,   pawn,   pawn,   pawn,   pawn,
    0,   rook,      0,      0,      0,      0,      0, bishop,      0,
    lance, knight, silver,   gold,   king,   gold, silver, knight,  lance
};


const small_short Stcolor[NO_SQUARES] =
{
    black,   black,   black,   black,
    black,   black,   black,   black,   black,
    neutral, black, neutral, neutral,
    neutral, neutral, neutral,   black, neutral,
    black,   black,   black,   black,
    black,   black,   black,   black,   black,
    neutral, neutral, neutral, neutral,
    neutral, neutral, neutral, neutral, neutral,
    neutral, neutral, neutral, neutral,
    neutral, neutral, neutral, neutral, neutral,
    neutral, neutral, neutral, neutral,
    neutral, neutral, neutral, neutral, neutral,
    white,   white,   white,   white,
    white,   white,   white, white, white,
    neutral, white, neutral, neutral,
    neutral, neutral, neutral, white, neutral,
    white,   white,   white,   white,
    white,   white,   white, white, white
};


/* Actual pieces and colors */

small_short board[NO_SQUARES], color[NO_SQUARES];


/* relative piece values at the beginning of main stages */

#define MAIN_STAGES 4

static small_short ispvalue[NO_PIECES][MAIN_STAGES] =
{
    {   0,  35,  70,  99 }, /* main stage borders */
    /* ------------------------------------------ */
    {   7,   7,   8,  10 }, /* Pawn               */
    {  20,  35,  45,  60 }, /* Lance              */
    {  20,  35,  45,  60 }, /* Knight             */
    {  35,  40,  60,  80 }, /* Silver             */
    {  35,  50,  65,  80 }, /* Gold               */
    {  90,  90,  90,  90 }, /* Bishop             */
    {  95,  95,  95,  95 }, /* Rook               */
    {  15,  25,  40,  65 }, /* promoted Pawn      */
    {  25,  45,  55,  65 }, /* promoted Lance     */
    {  25,  45,  55,  65 }, /* promoted Knight    */
    {  35,  55,  75,  75 }, /* promoted Silver    */
    {  99,  99,  99,  99 }, /* promoted Bishop    */
    {  97,  97,  99,  99 }, /* promoted Rook      */
    { 100, 100, 100, 100 }, /* King               */
};

/* Features and Weights */

#define ATTACKED    0
#define HUNGP       1
#define HUNGX       2
#define CNTRL5TH    3
#define HOLES       4
#define PCASTLE     5
#define PATTACK     6
#define CTRLK       7
#define PROTECT     8
#define HCLSD       9
#define PINVAL     10
#define XRAY       11
#define OPENWRONG  12
#define SEED       13
#define LOOSE      14
#define MOBILITY   15
#define TARGET     16
#define KSFTY      17
#define HOPN       18
#define PROMD      19
#define KINGOD     20
#define PWNDROP    21
#define DFFDROP    22
#define FCLATTACK  23
#define KNGATTACK  24
#define KNGPROTECT 25
#define DNGLPC     26
#define LSATTACK   27
#define NIHATTACK  28
#define COHESION   29
#define OPPDROP    30


static small_short weight[NO_FEATURES + 1][MAIN_STAGES + 2] =
{
    {  80, 100, 100,  40,  10,  15 },    /* ATTACKED      */
    {  80, 100, 100,  50,  14,  10 },    /* HUNGP         */
    {  80, 100, 100,  50,  18,  12 },    /* HUNGX         */
    { 100,  50,   0,   0,   2,   1 },    /* CNTRL5TH      */
    { 100, 100,  60,  10,   4,   2 },    /* HOLES         */
    { 100,  50,   0,   0,  14,   7 },    /* PCASTLE       */
    { 100,  50,   0,   0,   6,  12 },    /* PATTACK       */
    {  10,  40,  70, 100,  10,  15 },    /* CTRLK         */
    { 100,  80,  50,  40,   2,   1 },    /* PROTECT       */
    {  40, 100,  40,   5,   4,   4 },    /* HCLSD         */
    {  80, 100,  80,  30,  10,  15 },    /* PINVAL        */
    {  80, 100,  60,  15,   6,  10 },    /* XRAY          */
    { 100,  50,   0,   0,  15,  15 },    /* OPENWRONG     */
    {   0,  40,  70, 100,   8,  12 },    /* SEED          */
    {  50, 100,  80,  20,   5,   3 },    /* LOOSE         */
    {  50, 100,  80,  50, 100, 100 },    /* MOBILITY (%)  */
    {  50, 100,  80,  50,   4,   8 },    /* TARGET        */
    {  50,  40, 100,  80,   8,   4 },    /* KSFTY         */
    {  80, 100,  60,  20,   5,   5 },    /* HOPN          */
    {  20,  40,  80, 100,   3,   6 },    /* PROMD         */
    {  20,  40,  80, 100,   4,   1 },    /* KINGOD        */
    {   5,  40, 100,  50,   0,   4 },    /* PWNDROP       */
    {   0,  20,  80, 100,   0,   4 },    /* DFFDROP       */
    {  20,  50, 100,  80,   0,   4 },    /* FCLATTACK     */
    {   0,  20,  80, 100,   0,   8 },    /* KNGATTACK     */
    {  40,  80, 100,  80,   6,   0 },    /* KNGPROTECT    */
    {  50, 100,  60,  10,   0,   8 },    /* DNGPC         */
    {  30, 100,  60,   5,   0,   6 },    /* LSATTACK      */
    {   0,  50,  80, 100,   0,   8 },    /* NIHATTACK     */
    {  50, 100,  80,  60,   8,   0 },    /* COHESION      */
    { 100, 100,  80,  60,   4,   4 },    /* OPPDROP       */
};


short ADVNCM[NO_PIECES];

/* distance to enemy king */
static const short EnemyKingDistanceBonus[10] =
{ 0, 6, 4, -1, -3, -4, -6, -8, -10, -12 };

/* distance to own king */
static const short OwnKingDistanceBonus[10] =
{ 0, 5, 2, 1, 0, -1, -2, -3, -4, -5 };

/* distance to promotion zone */
static const int PromotionZoneDistanceBonus[NO_ROWS] =
{ 0, 0, 0, 0, 2, 6, 6, 8, 8 };

#define MAX_BMBLTY 20
#define MAX_RMBLTY 20
#define MAX_LMBLTY 8

/* Bishop mobility bonus indexed by # reachable squares */
static const short BMBLTY[MAX_BMBLTY] =
{ 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14, 14, 16, 16, 16, 16 };

/* Rook mobility bonus indexed by # reachable squares */
static const short RMBLTY[MAX_RMBLTY] =
{ 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14, 14, 16, 16, 16, 16 };

/* Lance mobility bonus indexed by # reachable squares */
static const short LMBLTY[MAX_LMBLTY] =
{ 0, 0, 0, 0, 4, 6, 8, 10 };

static const short MBLTY[NO_PIECES] =
{ 0, 2, 1, 10, 5, 5, 1, 1, 5, 5, 5, 5, 1, 1, 4 };

static const short KTHRT[36] =
{   0,  -8, -20, -36, -52, -68, -80, -80, -80, -80, -80, -80,
    -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80,
    -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80 };

static small_short fvalue[2][NO_FEATURES];

int attack[2][NO_SQUARES];          /* threats to squares */
small_short sseed[NO_SQUARES];      /* square occupied by a seed piece? */

struct signature threats_signature[2] = /* statistics valid for position.. */
{ { -1, -1 }, { -1, -1 } };             /* attack and sseed available */

small_short starget[2][NO_SQUARES]; /* significance as a target for a
                                     * side of a square */
small_short sloose[NO_SQUARES];     /* square occupied by a loose piece? */
small_short shole[NO_SQUARES];      /* empty square a hole? */
small_short shung[NO_SQUARES];      /* hung piece? */

struct signature squares_signature =  /* statistics valid for position ... */
{ 0, 0 };                /* starget, sloose, shole, shung available */

short target[2], seed[2], loose[2], hole[2];

short captured[2];  /* number of captured pieces */
short dcaptured[2]; /* different types of captured pieces */

small_short Kdist[2][NO_SQUARES];    /* distance to king */

short MAXADIST, MAXCDIST; /* maximum half move distance to pattern */

char GameType[2] = { UNKNOWN, UNKNOWN }; /* chosen game type of each side */


static short attack_opening_sequence[2];    /* current castle patterns */
static short castle_opening_sequence[2];    /* current attack formations */

static small_short Mpawn  [2][NO_SQUARES];
static small_short Msilver[2][NO_SQUARES];
static small_short Mgold  [2][NO_SQUARES];
static small_short Mking  [2][NO_SQUARES];
static small_short Mlance [2][NO_SQUARES];
static small_short Mknight[2][NO_SQUARES];
static small_short Mbishop[2][NO_SQUARES];
static small_short Mrook  [2][NO_SQUARES];

static Mpiece_array Mpawn, Mlance, Mknight, Msilver, Mgold,
    Mbishop, Mrook, Mking;

Mpiece_array *Mpiece[NO_PIECES] =
{ NULL, &Mpawn, &Mlance, &Mknight, &Msilver, &Mgold, &Mbishop, &Mrook,
  &Mgold, &Mgold, &Mgold, &Mgold, &Mbishop, &Mrook, &Mking };


static short c1, c2;
static small_short *PC1, *PC2;
static small_short *fv1;
static int *atk1, *atk2;
static int  a1, a2;

#define csquare(side, sq) ((side == black) ? sq : (NO_SQUARES_1 - sq))
#define crow(side, sq)    row(csquare(side, sq))
#define ccolumn(side, sq) column(csquare(side, sq))


inline static short
on_csquare(short side, short piece, short square)
{
    short sq;
    /* FIXME: un-obfuscate this! */
    return ((board[sq = csquare(side, square)] == piece)
            && (color[sq] == side));
}


inline static short
on_column(short side, short piece, short c)
{
    short sq;

    for (sq = c; sq < NO_SQUARES; sq += 9)
    {
        if (on_csquare(side, piece, sq))
            return true;
    }

    return false;
}


#define empty_csquare(side, square) \
  (board[csquare(side, square)] == no_piece)

inline static short
on_left_side(short side, short piece)
{
    short c;

    for (c = 0; c < 4; c++)
    {
        if (on_column(side, piece, c))
            return true;
    }

    return false;
}


inline static short
on_right_side(short side, short piece)
{
    short c;

    for (c = 5; c < NO_COLS; c++)
    {
        if (on_column(side, piece, c))
            return true;
    }

    return false;
}


short pscore[2];  /* piece score for each side */




/*
 * Fill array attack[side][] with info about attacks to a square.  Bits
 * 16-31 are set if the piece (king .. pawn) attacks the square.  Bits 0-15
 * contain a count of total attacks to the square.  Fill array sseed[] with
 * info about occupation by a seed piece.
 */

void
threats(short side)
{
    short  u, sq;
    int    c;
    int   *a;
#ifdef SAVE_NEXTPOS
    short d;
#else
    unsigned char  *ppos, *pdir;
#endif
    short i, kd, piece, xside;
    small_short *PL;

    if (MatchSignature(threats_signature[side]))
    {
        /* data valid for current positional signature */
        return;
    }

    a = attack[side];
    xside = side ^ 1;

    array_zero(a, NO_SQUARES * sizeof(a[0]));

    PL = PieceList[side];

    for (i = PieceCnt[side]; i >= 0; i--)
    {
        short ptyp;

        sq = PL[i];
        piece = board[sq];
        ptyp = ptype[side][piece];
        c = control[piece];
#ifdef SAVE_NEXTPOS
        u = first_direction(ptyp, &d, sq);
#else
        ppos = (*nextpos[ptyp])[sq];
        pdir = (*nextdir[ptyp])[sq];
        u = ppos[sq];
#endif

        do
        {
            a[u] = ((a[u] + 1) | c);

            if ((kd = Kdist[xside][u]) < 2)
            {
                sseed[sq] += 2 - kd;
                seed[side]++;
            }

#ifdef SAVE_NEXTPOS
            u = ((color[u] == neutral)
                 ? next_position(ptyp, &d, sq, u)
                 : next_direction(ptyp, &d, sq));
#else
            u = ((color[u] == neutral) ? ppos[u] : pdir[u]);
#endif
        }
        while (u != sq);
    }

    /* data valid for current positional signature */
    CopySignature(threats_signature[side]);
}



/*
 * Compute the board square with nunmap offset "id".  If side == white,
 * offset is negated.  inunmap[sq] is the corresponding nunmap index isq.
 * nunmap[isq + id] computes the board square. If negative, it is outside
 * the board.
 */

static void
add_target(short sq, short side, short id)
{
    short isq, tsq, xside;
    isq = inunmap[sq];
    tsq = (side == black) ? nunmap[isq + id] : nunmap[isq - id];

    if (tsq >= 0)
    {
        target[xside = side^1]++;

        if (attack[side][tsq])
            starget[xside][tsq]++;  /* protected target square */
        else
            starget[xside][tsq] += 2; /* unprotected target square */
    }
}



/*
 * Target squares can be vertically ahead, diagonally ahead
 * or diagonally behind.
 */

static void
CheckTargetPiece(short sq, short side)
{
    switch (board[sq])
    {
    case pawn: /* vertically ahead if unprotected */
        if (!attack[side][sq])
            add_target(sq, side, 11);
        break;

    case king: /* diagonally and vertically ahead */
        add_target(sq, side, 10);
        add_target(sq, side, 11);
        add_target(sq, side, 12);
        break;

    case rook: /* diagonally ahead and behind */
        add_target(sq, side, 10);
        add_target(sq, side, 12);
        add_target(sq, side, -10);
        add_target(sq, side, -12);
        break;

    case bishop: /* vertically ahead */
        add_target(sq, side, 11);
        break;

    case knight: /* vertically ahead if advanced */
        /* FIXME: gotta love them magic numbers... */
        if ((sq != 1) && (sq != 7) && (sq != 73) && (sq != 79))
            add_target(sq, side, 11);
        break;
    }
}



static short
ScoreKingOpeningFeatures(void)
{
    short s = 0, sq = OwnKing, ds;

    if (GameType[c1] == STATIC_ROOK)
    {
        /* Penalty for king on right side or fifth file */
        short c;
        c = 4 - ccolumn(c1, sq);

        if ((c < 0) || ((c == 0) && (sq != kingP[c1])))
            s += (ds = -c - c - fv1[OPENWRONG]);
    }
    else if (GameType[c1] == RANGING_ROOK)
    {
        /* Penalty for king on left side or fifth file */
        short c;
        c = 4 - ccolumn(c1, sq);

        if ((c > 0) || ((c == 0) && (sq != kingP[c1])))
        {
            s += (ds = -c - c - fv1[OPENWRONG]);
        }

        /* Penalty for king moved before rook switch */
        if (sq != kingP[c1])
        {
            if (on_csquare(c1, rook, 16))
            {
                s += (ds = -4 * fv1[OPENWRONG]);
            }
        }
        else
        {
            /* Penalty for sitting king after rook switch */
            if (!on_csquare(c1, rook, 16))
            {
                s += (ds = -2 * fv1[OPENWRONG]);
            }
        }

        /* Penalty for defending general moved
         * before king switch to right side */
        if (ccolumn(c1, sq) < 6)
        {
            if (Mvboard[csquare(c1, 5)] || Mvboard[csquare(c1, 6)])
            {
                s += (ds = -2 * fv1[OPENWRONG]);
            }
        }
    }

    return s;
}




inline static void
ExamineSquares(void)
{
    short sq, side, piece, n;

    if (MatchSignature(squares_signature))
    {
        /* data valid for current positional signature */
        return;
    }

    array_zero(shole,   sizeof(shole));
    array_zero(sloose,  sizeof(sloose));
    array_zero(starget, sizeof(starget));

    hole[0] = hole[1] = loose[0] = loose[1]
        = target[0] = target[1] = 0;

    for (sq = 0; sq < NO_SQUARES; sq++)
    {
        if ((side = color[sq]) == neutral)
        {
            if (InWhiteCamp(sq))
            {
                if (!attack[white][sq])
                {
                    shole[sq] = 1;
                    hole[white]++;
                }
            }
            else if (InBlackCamp(sq))
            {
                if (!attack[black][sq])
                {
                    shole[sq] = 1;
                    hole[black]++;
                }
            }
        }
        else
        {
            /* occupied by "side" piece */
            if (!attack[side][sq])
            {
                sloose[sq] = 1;
                loose[side]++;
            }

            CheckTargetPiece(sq, side);
        }
    }

    for (side = black; side <= white; side++)
    {
        captured[side] = dcaptured[side] = 0;

        for (piece = pawn; piece <= rook; piece++)
        {
            if ((n = Captured[side][piece]) != 0)
            {
                if (piece != pawn)
                    captured[side] += n;

                dcaptured[side]++;
            }
        }
    }

    /* Data valid for current positional signature */
    CopySignature(squares_signature);
}



/* ............    POSITIONAL EVALUATION ROUTINES    ............ */

/*
 * Inputs are:
 * mtl[side]       - value of all material
 * hung[side]      - count of hung pieces
 * Tscore[ply]     - search tree score for ply ply
 * Pscore[ply]     - positional score for ply ply
 * INCscore        - bonus score or penalty for certain moves
 * Sdepth          - search goal depth
 * xwndw           - evaluation window about alpha/beta
 * EWNDW           - second evaluation window about alpha/beta
 * ChkFlag[ply]    - checking piece at level ply or 0 if no check
 * TesujiFlag[ply] - 1 if tesuji move at level ply or 0 if no tesuji
 * PC1[column]     - # of my pawns in this column
 * PC2[column]     - # of opponents pawns in column
 * PieceCnt[side]  - just what it says
 */




/*
 * Compute an estimate of the score by adding the positional score from the
 * previous ply to the material difference. If this score falls inside a
 * window which is 180 points wider than the alpha-beta window (or within a
 * 50 point window during quiescence search) call ScorePosition() to
 * determine a score, otherwise return the estimated score.  "side" is the
 * side which has to move.
 */

int
evaluate(short side,
         short ply,
         short alpha,
         short beta,
         short INCscore,
         short *InChk,     /* output Check flag     */
         short *blockable) /* king threat blockable */
{
    short xside;
    short s;

    xside = side ^ 1;
    s = -Pscore[ply - 1] + mtl[side] - mtl[xside] /* - INCscore */;
    hung[black] = hung[white] = 0;

    /* should we use the estimete or score the position */
    if ((ply == 1)
        || (ply == Sdepth)
        || (ply > Sdepth && s >= (alpha - 30) && s <= (beta + 30))
#ifdef CACHE
        || (use_etable && CheckEETable(side))
#endif
        )
    {
        short sq;

        /* score the position */
        array_zero(sseed, sizeof(sseed));

        seed[0] = seed[1] = 0;
        threats(side);

        if (Anyattack(side, sq = PieceList[xside][0]) && (board[sq] == king))
        {
            *InChk = (board[sq = PieceList[side][0]] == king)
                ? SqAttacked(sq, xside, blockable)
                : false;

            return ((SCORE_LIMIT + 1001) - ply);
        }

        threats(xside);
        *InChk = (board[sq = PieceList[side][0]] == king)
            ? Anyattack(xside, sq)
            : false;
        *blockable = true;
        EvalNodes++;

        if (ply > 4)
            PUTVAR = true;

        ExamineSquares();
        s = ScorePosition(side);
        PUTVAR = false;
    }
    else
    {
        /* use the estimate but look at check */
        short sq;

        *InChk = (board[sq = PieceList[side][0]] == king)
            ? SqAttacked(sq, xside, blockable)
            : false;

        if ((board[sq = PieceList[xside][0]] == king)
            && SqAttacked(sq, side, blockable))
        {
            return ((SCORE_LIMIT + 1001) - ply);
        }
    }

    Pscore[ply] = s - mtl[side] + mtl[xside];
    ChkFlag[ply - 1] = ((*InChk) ? Pindex[TOsquare] : 0);

    return s;
}



static short
value_of_weakest_attacker(int a2)
{
    short piece;
    short min_value, v;
    min_value = SCORE_LIMIT;

    for (piece = pawn; piece <= king; piece++)
    {
        if (control[piece] & a2)
        {
            if (min_value > (v = (*value)[stage][piece]))
                min_value = v;
        }
    }

    return min_value;
}




/*
 * Find (promoted) Bishop, (promoted) Rook, and Lance mobility, x-ray
 * attacks, and pins.  Let BRL be the bishop, rook, or lance.  Let P be the
 * first piece (not a king or a pawn) in a direction and let Q be the
 * second piece in the same direction.  If Q is an unprotected opponent's
 * piece with bigger relative value than BRL, there is a pin if P is an
 * opponent's piece and there is an x-ray attack if P belongs to this side.
 * Increment the hung[] array if a pin is found.
 */

inline int
BRLscan(short sq, short *mob)
{
#ifdef SAVE_NEXTPOS
    short d, dd;
#else
    unsigned char  *ppos, *pdir;
#endif

    short s, mobx;
    short u, xu, pin, ptyp, csq = column(sq);
    short piece, upiece, xupiece, rvalue, ds;
    small_short *Kd = Kdist[c2];

    mobx = s = 0;
    piece = board[sq];

    rvalue = (*value)[stage][piece];
    ptyp = ptype[c1][upiece = unpromoted[piece]];
    rvalue = (*value)[stage][upiece];

#ifdef SAVE_NEXTPOS
    u = first_direction(ptyp, &d, sq);
#else
    ppos = (*nextpos[ptyp])[sq];
    pdir = (*nextdir[ptyp])[sq];
    u = ppos[sq];
#endif

    pin = -1;           /* start new direction */

    do
    {
        if (Kd[u] < 2)
        {
            s += (ds = fv1[CTRLK] * (2 - Kd[u]));
        }

        if ((ds = starget[c1][u]) != 0)
        {
            /* threatening a target square */
            if ((pin < 0)               /* direct threat */
                || (color[pin] == c2))  /* pin threat    */
            {
                s += (ds *= fv1[TARGET]);
            }
        }

        if ((ds = shole[u]) != 0)
        {
            /* attacking or protecting a hole */
            s += (ds = fv1[HOLES]);
        }
        else if (InPromotionZone(c1, u))
        {
            /* attacking a square in promotion zone */
            s += (ds = fv1[HOLES] / 2);
        }

        if (color[u] == neutral)
        {
#ifdef SAVE_NEXTPOS
            dd = d;
            xu = next_position(ptyp, &d, sq, u);

            if (xu == next_direction(ptyp, &dd, sq))
                pin = -1;   /* oops new direction */
#else

            if ((xu = ppos[u]) == pdir[u])
                pin = -1;   /* oops new direction */
#endif
            u = xu;
            mobx++;
        }
        else
        {
            /* there is a piece in current direction */
            if (pin < 0)
            {
                /* it's the first piece in the current direction */
                if (color[u] == c1)
                {
                    /* own intercepting piece in x-ray attack */
                    if (upiece == lance)
                    {
                        /* lance x-ray */
                        if (board[u] == pawn)
                        {
                            s += (ds = 2*fv1[PROTECT]);
                        }
                        else if (in_opening_stage)
                        {
                            s += (ds = -2*fv1[PROTECT]);
                        }
                    }
                    else
                    {
                        /* bishop or rook x-ray */
                        if ((upiece == bishop) && (board[u] == pawn)
                            && (GameType[c1] == STATIC_ROOK))
                        {
                            s += (ds = -2*fv1[HCLSD]);
                        }
                        else if ((upiece == rook) && (board[u] == lance)
                                 && (GameType[c1] == STATIC_ROOK)
                                 && (column(u) == csq))
                        {
                            s += (ds = fv1[XRAY]);
                        }
                    }
                }
                else
                {
                    /* enemy's intercepting piece in pin attack */
                    if (upiece == lance)
                    {
                        /* lance pin attack */
                        if (board[u] == pawn)
                        {
                            s += (ds = -2*fv1[PROTECT]);
                        }
                        else if (in_opening_stage)
                        {
                            s += (ds = 2 * fv1[PROTECT]);
                        }
                    }
                    else
                    {
                        /* bishop or rook pin attack */
                        if (board[u] == pawn)
                        {
                            s += (ds = -fv1[HCLSD]);
                        }
                    }
                }

#ifdef SAVE_NEXTPOS
                dd = d;
                xu = next_position(ptyp, &d, sq, u);

                if (xu != next_direction(ptyp, &dd, sq))
                    pin = u;    /* not on the edge and on to find a pin */
#else
                if ((xu = ppos[u]) != pdir[u])
                    pin = u;    /* not on the edge and on to find a pin */
#endif
                u = xu;
            }
            else
            {
                /* it's the second piece in the current direction */

                if (color[u] == c1)
                {
                    /* second piece is an own piece */
                    if ((upiece == bishop) && (board[u] == pawn)
                        && (GameType[c1] == STATIC_ROOK))
                    {
                        s += (ds = -fv1[HCLSD]);
                    }
                }
                else
                {
                    /* second piece is an enemy piece */
                    if (upiece == bishop && board[u] == pawn)
                    {
                        s += (ds = -fv1[HCLSD]/2);
                    }

                    if (((*value)[stage][xupiece = unpromoted[board[u]]]
                         > rvalue)
                        || (atk2[u] == 0))
                    {
                        if (color[pin] == c2)
                        {
                            if ((xupiece == king) && (in_endgame_stage))
                            {
                                s += (ds = 2 * fv1[PINVAL]);
                            }
                            else
                            {
                                s += (ds = fv1[PINVAL]);
                            }

                            if ((atk2[pin] == 0)
                                || (atk1[pin] > control[board[pin]] + 1))
                            {
                                hung[c2]++;
                                shung[u]++;
                            }
                        }
                        else
                        {
                            if (upiece == lance)
                            {
                                s += (ds = fv1[XRAY] / 2);
                            }
                            else
                            {
                                s += (ds = fv1[XRAY]);
                            }
                        }
                    }
                }

                pin = -1;   /* new direction */

#ifdef SAVE_NEXTPOS
                u = next_direction(ptyp, &d, sq);
#else
                u = pdir[u];
#endif
            }
        }
    }
    while (u != sq);

    *mob = mobx;

    return s;
}


#define ctlSG (ctlS | ctlG | ctlPp | ctlLp | ctlNp | ctlSp)



/*
 * Assign penalties if king can be threatened by checks, if squares near
 * the king are controlled by the enemy (especially by promoted pieces), or
 * if there are no own generals near the king.
 *
 * The following must be true:
 * board[sq] == king, c1 == color[sq], c2 == otherside[c1]
 */

#define SCORETHREAT \
{ \
    if (color[u] != c2) \
    { \
        if ((atk1[u] == 0) || ((atk2[u] & CNT_MASK) > 1)) \
        { \
            ++cnt; \
        } \
        else \
        { \
            s += (ds = -fv1[CTRLK]); \
        } \
    } \
}




inline short
KingScan(short sq)
{
    short cnt;

#ifdef SAVE_NEXTPOS
    short d;
#else
    unsigned char  *ppos, *pdir;
#endif

    short s;
    short u, ptyp;
    short ok, ds;

    /* Penalties, if a king can be threatened by checks. */

    s = 0;
    cnt = 0;

    {
        short p;

        for (p = pawn; p < king; p++)
        {
            if (HasPiece[c2][p] || Captured[c2][p])
            {
                short ptyp;

                /* if a c1 piece can reach u from sq,
                 * then a c2 piece can reach sq from u.
                 * That means, each u is a square, from which a
                 * piece of type p and color c2 threats square sq.
                 */
                ptyp = ptype[c1][p];

#ifdef SAVE_NEXTPOS
                u = first_direction(ptyp, &d, sq);
#else
                ppos = (*nextpos[ptyp])[sq];
                pdir = (*nextdir[ptyp])[sq];
                u = ppos[sq];
#endif

                do
                {
                    /* If a p piece can reach (controls or can drop to)
                     * square u, then score threat.
                     */

                    if (atk2[u] & control[p])
                        SCORETHREAT
                    else if ((Captured[c2][p] && color[u]) == neutral)
                        SCORETHREAT

#ifdef SAVE_NEXTPOS
                    u = ((color[u] == neutral)
                         ? next_position(ptyp, &d, sq, u)
                         : next_direction(ptyp, &d, sq));
#else
                    u = ((color[u] == neutral) ? ppos[u] : pdir[u]);
#endif
                }
                while (u != sq);
            }
        }
    }

    s += (ds = fv1[KSFTY] * KTHRT[cnt] / 16);

    /* Penalties, if squares near king are controlled by enemy. */

    cnt = 0;
    ok = false;
    ptyp = ptype[c1][king];

#ifdef SAVE_NEXTPOS
    u = first_direction(ptyp, &d, sq);
#else
    pdir = (*nextpos[ptyp])[sq];
    u = pdir[sq];
#endif

    do
    {
        if (!ok && color[u] == c1)
        {
            short ptype_piece = ptype[black][board[u]];

            if ((ptype_piece == ptype_silver) || (ptype_piece == ptype_gold))
                ok = true;
        }

        if (atk2[u] > atk1[u])
        {
            ++cnt;

            if (atk2[u] & ctlSG)
            {
                s += (ds = -fv1[KSFTY] / 2);
            }
        }

#ifdef SAVE_NEXTPOS
        u = next_direction(ptyp, &d, sq);
#else
        u = pdir[u];
#endif
    }
    while (u != sq);

    if (!ok || (cnt > 1))
    {
        if (cnt > 1)
            s += (ds = -fv1[KSFTY]/2);
        else
            s += (ds = -fv1[KSFTY]);
    }

    return s;
}


static short checked_trapped;


/*
 * See if the attacked piece has unattacked squares to move to. The following
 * must be true: c1 == color[sq] c2 == otherside[c1]
 */

inline int
trapped(short sq)
{
    short u, ptyp;
#ifdef SAVE_NEXTPOS
    short d;
#else
    unsigned char *ppos, *pdir;
#endif
    short piece;
    short rvalue;

    piece  = board[sq];
    rvalue = (*value)[stage][piece];
    ptyp   = ptype[c1][piece];

#ifdef SAVE_NEXTPOS
    u = first_direction(ptyp, &d, sq);
#else
    ppos = (*nextpos[ptyp])[sq];
    pdir = (*nextdir[ptyp])[sq];
    u = ppos[sq];
#endif

    do
    {
        if (color[u] != c1)
        {
            if ((atk2[u] == 0) || ((*value)[stage][board[u]] >= rvalue))
                return false;
        }

#ifdef SAVE_NEXTPOS
        u = ((color[u] == neutral)
             ? next_position(ptyp, &d, sq, u)
             : next_direction(ptyp, &d, sq));
#else
        u = ((color[u] == neutral) ? ppos[u] : pdir[u]);
#endif
    }
    while (u != sq);

    checked_trapped = true;

    return true;
}



static int
AttackedPieceValue(short sq, short side)
{
    short s, ds;

    s = 0;

	ds = -fv1[HUNGP] * 2;
    hung[c1]++;
    shung[sq]++;

    if (trapped(sq))
    {
        hung[c1]  += 2;
        shung[sq] += 2;
    }

    return s;
}



static inline int
OpenFileValue(short sq, short hopn, short hopnx)
{
    short s = 0, fyle;

    if (PC1[fyle = column(sq)] == 0)
    {
        s += hopn;
    }

    if (PC2[fyle] == 0)
    {
        s += hopnx;
    }

    return s;
}




/* Distance bonus */

#define PromotionZoneDistanceValue(sq, dd) \
if ((ds = fv1[PROMD])) \
{ \
    s += (ds = ds * PromotionZoneDistanceBonus[crow(c1, sq)] * dd); \
}

#define OwnKingDistanceValue(sq, dd, maxd) \
if ((ds = fv1[KINGOD]) && ((ad = Kdist[c1][sq]) <= maxd)) \
{ \
    s += (ds = ds * OwnKingDistanceBonus[ad] * dd); \
}

#define EnemyKingDistanceValue(sq, dd, maxd) \
if ((ds = fv1[KINGOD]) && ((ad = Kdist[c2][sq]) <= maxd)) \
{ \
    s += (ds = ds * EnemyKingDistanceBonus[ad] * dd); \
}





/*
 * Calculate the positional value for a pawn on 'sq'.
 */

static inline int
PawnValue(short sq, short side)
{
    short s = 0;
    short ds;
    short ccol = ccolumn(c1, sq);

    PromotionZoneDistanceValue(sq, 3);

    /* pawn mobility */
    if (color[(c1 == black) ? (sq + 9) : (sq - 9)] == neutral)
    {
        s += (ds = MBLTY[pawn]);
    }

    if ((a1 & ((ctlR | ctlRp) | ctlL)))
    {
        s += (ds = fv1[ATTACKED]);
    }

    if (in_opening_stage)
    {
        if (crow(c1, sq) == 2) /* pawn on 3d rank */
        {
            if (board[(c1 == black) ? (sq + 27) : (sq - 27)] == pawn)
            {
                /* opposing pawn has been moved (even column == (sq & 1)) */

                short m;

                switch (ccol)
                {
                case 0:
                case 8:
                    m = (side == c1) ? 3 : 5;
                    break;

                case 4:
                    m = (side == c1) ? 2 : 3;
                    break;

                default:
                    m = (side == c1) ? 1 : 2;
                    break;
                }

                s += (ds = -m * MBLTY[pawn]);
            }
        }

        if ((GameType[c1] == STATIC_ROOK) && (sq == csquare(c1, 43)))
        {
            if ((atk2[csquare(c1, 52)] & CNT_MASK) < 2)
            {
                s += (ds = fv1[ATTACKED]);
            }
        }

        if ((GameType[c2] == STATIC_ROOK) && (ccol == 1))
        {
            if (sq == csquare(c1, 28))
            {
                s += (ds = -fv1[ATTACKED]);
            }

            if (((atk1[csquare(c1, 19)] & CNT_MASK) < 2)
                && ((atk1[csquare(c1, 28)] & CNT_MASK) < 2))
            {
                s += (ds = -2 * fv1[ATTACKED]);
            }
        }
    }

    return s;
}



/*
 * Calculate the positional value for a lance on 'sq'.
 */

static inline int
LanceValue(short sq, short side)
{
    short s = 0, ds, ad;

    OwnKingDistanceValue(sq, 1, 2);

    OpenFileValue(sq, -fv1[HOPN], fv1[HOPN]);

    if (!checked_trapped && (crow(c1, sq) > 2))
    {
        if (in_opening_stage || trapped(sq))
        {
            s += (ds = -3 * fv1[ATTACKED]);
        }
        else
        {
            s += (ds = -2 * fv1[ATTACKED]);
        }
    }

    return s;
}



/*
 * Calculate the positional value for a knight on 'sq'.
 */

static inline int
KnightValue(short sq, short side)
{
    short s = 0, ad;
    short ds, checked_trapped = false;
    short c = column(sq);

    PromotionZoneDistanceValue(sq, 1);
    OwnKingDistanceValue(sq, 1, 2);

    if (!checked_trapped && (crow(c1, sq) > 2))
    {
        if (trapped(sq))
        {
            s += (ds = -4 * fv1[ATTACKED]);
        }
        else
        {
            s += (ds = -3 * fv1[ATTACKED]);
        }
    }

    if ((c == 0) || (c == 8))
    {
        s += (ds = -fv1[ATTACKED]);
    }

    return s;
}



/*
 * Calculate the positional value for a silver on 'sq'.
 */

static inline int
SilverValue(short sq, short side)
{
    short s= 0, ds, ad;

    OwnKingDistanceValue(sq, 2, 3);

    if ((Kdist[c1][sq] < 3)
        && (atk1[sq] & (control[gold] | control[silver])))
    {
        s += (ds = fv1[COHESION]);
    }

    if (in_opening_stage)
    {
        if (GameType[c1] == STATIC_ROOK)
        {
            if (csquare(c1, sq) == 12)
            {
                short csq;

                if ((board[csq = csquare(c1, 20)] == bishop)
                    && (color[csq] == c1))
                {
                    s += (ds = -2 * fv1[OPENWRONG]);
                }
            }
        }
    }
    else
    {
        EnemyKingDistanceValue(sq, 2, 3);
    }

    return s;
}



/*
 * Calculate the positional value for a gold on 'sq'.
 */

static inline int
GoldValue(short sq, short side)
{
    short s = 0, ds, ad;

    OwnKingDistanceValue(sq, 2, 3);

    if ((Kdist[c1][sq] < 3)
        && (atk1[sq] & (control[gold] | control[silver])))
    {
        s += (ds = fv1[COHESION]);
    }

    if (in_opening_stage)
    {
        if ((GameType[c1] == STATIC_ROOK) && (GameType[c2] != STATIC_ROOK))
        {
            if (Mvboard[csquare(c1, 3)])
            {
                s += (ds = -2 * fv1[OPENWRONG]);
            }
        }
    }
    else
    {
        EnemyKingDistanceValue(sq, 2, 3);
    }

    return s;
}



/*
 * Calculate the positional value for a bishop on 'sq'.
 */

static inline int
BishopValue(short sq, short side)
{
    short s = 0, ds, ad;

    if (in_opening_stage)
    {
        if (GameType[c1] == RANGING_ROOK)
        {
            /* Bishops diagonal should not be open */
            if (!on_csquare(c1, pawn, 30))
            {
                s += (ds = -fv1[OPENWRONG]);
            }
        }
        else if (GameType[c2] == RANGING_ROOK)
        {
            /* Bishops diagonal should be open */
            if ((csquare(c1, sq) == 10)
                && (!empty_csquare(c1, 20) || !empty_csquare(c1, 30)))
            {
                s += (ds = -fv1[OPENWRONG]);
            }
            else if ((csquare(c1, sq) == 20) && !empty_csquare(c1, 30))
            {
                s += (ds = -fv1[OPENWRONG]);
            }
        }
    }
    else
    {
        EnemyKingDistanceValue(sq, 1, 3);
    }

    return s;
}



/*
 * Calculate the positional value for a rook on 'sq'.
 */

static inline int
RookValue(short sq, short side)
{
    short s = 0, ds, ad;

    OpenFileValue(sq, 2 * fv1[HOPN], 4*fv1[HOPN]);

    if (in_opening_stage)
    {
        short WRONG = fv1[OPENWRONG], OPOK = WRONG / 3;

        if (GameType[c1] == STATIC_ROOK)
        {
            short c = ccolumn(c1, sq);

            /* Bonus for rook on 8th file */
            if (c == 7)
            {
                 s += (ds = OPOK);
            }

            /*
             * Bonus for rook on right side,
             * penalty for rook on left side
             */

            c = 4 - c;
            ds = 0;

            if (c < 0)
            {
                s += (ds = c + c + OPOK);
            }
            else if (c >= 0)
            {
                s += (ds = -c - c - WRONG);
            }
        }
        else if (GameType[c1] == RANGING_ROOK)
        {
            /* Bonus for rook on left side and
             * bishops diagonal closed, penalty otherwise. */

            short c;
            c = 4 - ccolumn(c1, sq);
            ds = 0;

            if (c >= 0)
            {
                /* Bishops diagonal should not be open. */
                if (on_csquare(c1, pawn, 30))
                    s += (ds = OPOK);
                else
                    s += (ds = -c - c - WRONG);
            }
            else if (c < 0)
            {
                s += (ds = -c - c - WRONG);

                /* Penalty for king not on initial square. */
                if (!on_csquare(side, king, 4))
                {
                    s  += -4 * WRONG;
                    ds += -4 * WRONG;
                }
            }
        }
    }
    else
    {
        EnemyKingDistanceValue(sq, 1, 3);
    }

    return s;
}



/*
 * Calculate the positional value for a promoted pawn on 'sq'.
 */

static inline int
PPawnValue(short sq, short side)
{
    short s = 0, ds, ad;

    EnemyKingDistanceValue(sq, 3, 10);

    return s;
}



/*
 * Calculate the positional value for a promoted lance on 'sq'.
 */

static inline int
PLanceValue(short sq, short side)
{
    short s = 0, ds, ad;

    EnemyKingDistanceValue(sq, 3, 10);

    return s;
}



/*
 * Calculate the positional value for a promoted knight on 'sq'.
 */

static inline int
PKnightValue(short sq, short side)
{
    short s = 0, ds, ad;

    EnemyKingDistanceValue(sq, 3, 10);

    return s;
}



/*
 * Calculate the positional value for a promoted silver on 'sq'.
 */

static inline int
PSilverValue(short sq, short side)
{
    short s = 0, ds, ad;

    EnemyKingDistanceValue(sq, 3, 10);

    return s;
}



/*
 * Calculate the positional value for a promoted bishop on 'sq'.
 */

static inline int
PBishopValue(short sq, short side)
{
    short s = 0, ds, ad;

    EnemyKingDistanceValue(sq, 3, 4);

    return s;
}



/*
 * Calculate the positional value for a promoted rook on 'sq'.
 */

static inline int
PRookValue(short sq, short side)
{
    short s = 0, ds, ad;

    EnemyKingDistanceValue(sq, 3, 4);

    OpenFileValue(sq, 3 * fv1[HOPN], 2 * fv1[HOPN]);

    return s;
}



/*
 * Calculate the positional value for a king on 'sq'.
 */

static inline int
KingValue(short sq, short side)
{
    short s = 0, ds;

    if (fv1[KSFTY] != 0)
        s += KingScan(sq);

    if (in_opening_stage)
    {
        if ((GameType[c1] != UNKNOWN) && (ccolumn(c1, sq) == 4))
        {
            s += (ds = -fv1[OPENWRONG] / 3);
        }
        else if ((GameType[c1] == STATIC_ROOK) && on_right_side(c1, sq))
        {
            s += (ds = -fv1[OPENWRONG] / 2);
        }
        else if ((GameType[c1] == RANGING_ROOK) && on_left_side(c1, sq))
        {
            s += (ds = -fv1[OPENWRONG] / 2);
        }
    }

    /* CHECKME: is this correct? */
    if ((ds = fv1[HOPN]))
    {
        s += OpenFileValue(sq, -2 * ds, -4 * ds);
    }

    return s;
}



/*
 * Calculate the positional value for a piece on 'sq'.
 */

static inline int
PieceValue(short sq, short side)
{
    short s, piece, ds;
    short mob;

    piece = board[sq];

    if (piece == no_piece)
        return 0;

    s = (*Mpiece[piece])[c1][sq];

    checked_trapped = false;

    if (sweep[piece])
    {
        /* pin/x-ray attack and mobility for sweeping pieces */
        s += (ds = BRLscan(sq, &mob));

        if ((piece == bishop) || (piece == pbishop))
            s += (ds = BMBLTY[mob] * fv1[MOBILITY] / 100);
        else if ((piece == rook) || (piece == prook))
            s += (ds = RMBLTY[mob] * fv1[MOBILITY] / 100);
        else
            s += (ds = LMBLTY[mob] * fv1[MOBILITY] / 100);
    }
    else
    {
        /* mobility for non-sweeping pieces */
    }

    a2 = atk2[sq];
    a1 = atk1[sq];

    if (a2 > 0)
    {
        /* opponent attacks piece */
        if (a1 == 0)
        {
            /* undefended piece */
            s += AttackedPieceValue(sq, side);
        }
        else
        {
            /* defended piece */
            short attack_value = value_of_weakest_attacker(a2);
            short piece_value = (*value)[stage][piece];

            if (attack_value < piece_value)
            {
                /* attacked by a weaker piece */
                s += AttackedPieceValue(sq, side) / 2;
            }
            else if (abs(attack_value - piece_value) < 10)
            {
                /* opponent has the option to exchange equal pieces */
                s += (ds = -fv1[ATTACKED]);
            }
        }
    }

    if (piece != king)
    {

        if (a1 > 0)
        {
            /* piece is defended */
            s += (ds = (a1 & CNT_MASK) * fv1[PROTECT]);
        }

        if (sseed[sq])
        {
            s += (ds = fv1[SEED]);
        }

        if (sloose[sq])
        {
            s += (ds = -fv1[LOOSE]);
        }

        if (starget[c1][sq])
        {
            if (sweep[piece])
            {
                s -= (ds = -fv1[ATTACKED]/2);
            }
            else if (piece == pawn)
            {
                s += (ds = fv1[ATTACKED]);
            }
        }

        if (starget[c2][sq])
        {
            if (piece != pawn)
            {
                s -= (ds = -fv1[ATTACKED] / 3);
            }
            else
            {
                s += (ds = fv1[ATTACKED]);
            }
        }

        if (Kdist[c1][sq] == 1)
        {
            s += (ds = fv1[KSFTY]);
        }
    }

    switch (piece)
    {
    case pawn:
        s += PawnValue(sq, side);
        break;

    case lance:
        s += LanceValue(sq, side);
        break;

    case knight:
        s += KnightValue(sq, side);
        break;

    case silver:
        s += SilverValue(sq, side);
        break;

    case gold:
        s += GoldValue(sq, side);
        break;

    case bishop:
        s += BishopValue(sq, side);
        break;

    case rook:
        s += RookValue(sq, side);
        break;

    case king:
        s += KingValue(sq, side);
        break;

    case ppawn:
        s += PPawnValue(sq, side);
        break;

    case plance:
        s += PLanceValue(sq, side);
        break;

    case pknight:
        s += PKnightValue(sq, side);
        break;

    case psilver:
        s += PSilverValue(sq, side);
        break;

    case pbishop:
        s += PBishopValue(sq, side);
        break;

    case prook:
        s += PRookValue(sq, side);
        break;
    }

    return s;
}



/*
 * Score distance to pattern regarding the game type which side plays.
 */

short
ScorePatternDistance(short c1)
{
    short ds, s = 0;
    small_short *fv1 = fvalue[c1];
    short os = 0;

    if ((MAXCDIST > 0) && (fv1[PCASTLE] != 0)
        && ((os = castle_opening_sequence[c1]) >= 0))
    {
        ds = board_to_pattern_distance(c1, os, MAXCDIST, GameCnt);

        if (ds != 0)
        {
            s += (ds *= fv1[PCASTLE]);
        }
    }

    if ((MAXADIST > 0) && (fv1[PATTACK] != 0)
        && ((os = attack_opening_sequence[c1]) >= 0))
    {
        ds = board_to_pattern_distance(c1, os, MAXADIST, GameCnt);

        if (ds != 0)
        {
            s += (ds *= fv1[PATTACK]);
        }
    }

    return s;
}




/*
 * Determine castle and attack pattern which should be reached next.
 * Only patterns are considered, which have not been reached yet.
 */

static void
UpdatePatterns(short side, short GameCnt)
{
    char s[12];
    short xside = side ^ 1;
    short os;
    short j, k, n = 0;

    strcpy(s, "CASTLE_?_?");
    s[7] = GameType[side];
    s[9] = GameType[xside];
    castle_opening_sequence[side] = os
        = locate_opening_sequence(side, s, GameCnt);

    if (flag.post && (os != END_OF_SEQUENCES))
    {
        for (j = 0; j < MAX_SEQUENCE; j++)
        {
            for (k = OpeningSequence[os].first_pattern[j];
                 k != END_OF_PATTERNS;
                 k = Pattern[k].next_pattern)
            {
                if (Pattern[k].distance[side] >= 0)
                    n++;
            }
        }
    }

    if (os != END_OF_SEQUENCES)
        update_advance_bonus(side, os);

    strcpy(s, "ATTACK_?_?");
    s[7] = GameType[side];
    s[9] = GameType[xside];
    attack_opening_sequence[side] = os
        = locate_opening_sequence(side, s, GameCnt);

    if (flag.post && (os != END_OF_SEQUENCES))
    {
        for (j = 0; j < MAX_SEQUENCE; j++)
        {
            for (k = OpeningSequence[os].first_pattern[j];
                 k != END_OF_PATTERNS;
                 k = Pattern[k].next_pattern)
            {
                if (Pattern[k].distance[side] >= 0)
                    n++;
            }
        }
    }

    if (flag.post)
        ShowPatternCount(side, n);

    if (os != END_OF_SEQUENCES)
        update_advance_bonus(side, os);
}



static void
ScoreCaptures(void)
{
    short ds, col, n, m, piece;

    if ((n = Captured[c1][pawn]))
    {
        ds = m = 0;

        for (col = 0; col < NO_COLS; col++)
        {
            if (!PC1[col])
            {
                m++;
                ds += fv1[PWNDROP];
            }
        }

        /* FIXME! another great obfuscated line... */
        pscore[c1] += (ds *= ((n > 2) ? 3 : n));
    }

    if ((m = seed[c1]))
    {
        for (piece = lance, n = 0; piece <= rook; piece++)
        {
            if (Captured[c1][piece])
                n++;
        }

        pscore[c1] += (ds = m * fv1[DFFDROP]);
    }

    for (piece = pawn, n = 0; piece <= rook; piece++)
    {
        if (Captured[c1][piece])
        {
            switch (piece)
            {
            case bishop:
                ds = BMBLTY[MAX_BMBLTY - 1];
                break;

            case rook:
                ds = RMBLTY[MAX_RMBLTY - 1];
                break;

            case lance:
                ds = LMBLTY[MAX_LMBLTY - 1];
                break;

            default:
                ds = MBLTY[piece];
            }

            pscore[c1] += ds;

            if (!Captured[c2][piece])
                n += relative_value[piece];
        }
    }

    if (n)
    {
        pscore[c1] += (ds = -n * fv1[OPPDROP] / 2);
    }
}





/*
 * Perform normal static evaluation of board position. A score is generated
 * for each piece and these are summed to get a score for each side.
 */

short
ScorePosition(short side)
{
    short score;
    short sq, i, xside;
    short s;
    short ds;

    xside = side ^ 1;

    UpdateWeights(side);

    hung[black] = hung[white] = pscore[black] = pscore[white] = 0;

    array_zero(shung, sizeof(shung));

#ifdef CACHE
    if (!(use_etable && ProbeEETable(side, &s)))
    {
#endif
        for (c1 = black; c1 <= white; c1++)
        {
            c2 = c1 ^ 1;

            /* atk1 is array of attacks on squares by my side */
            atk1 = attack[c1];

            /* atk2 is array of attacks on squares by other side */
            atk2 = attack[c2];

            /* same for PC1 and PC2 */
            PC1 = PawnCnt[c1];
            PC2 = PawnCnt[c2];

            /* same for fv1 and fv2 */
            fv1 = fvalue[c1];

            for (i = PieceCnt[c1]; i >= 0; i--)
            {
                sq = PieceList[c1][i];

#if defined SAVE_SVALUE
                pscore[c1] += PieceValue(sq, side);
#else
                pscore[c1] += (svalue[sq] = PieceValue(sq, side));
#endif
            }

            ScoreCaptures();
        }

        for (c1 = black, c2 = white; c1 <= white; c1++, c2--)
        {
            short n;

            fv1 = fvalue[c1];

            /* Score fifth rank */
            for (sq = 36, n = 0; sq <= 44; sq++)
            {
                if ((color[sq] == c1) || (attack[c1][sq] != 0))
                    n++;
            }

            if (n != 0)
            {
                pscore[c1] += (ds = n * fv1[CNTRL5TH]);
            }

            /* Score holes */
            for (sq = ((c1 == black) ? 0 : 54), n = 0;
                 sq <= ((c1 == black) ? 26 : 80);
                 sq++)
            {
                if (board[sq] == no_piece && attack[c1][sq] == 0)
                    n++;
            }

            if (n != 0)
            {
                pscore[c1] += (ds = -n * fv1[HOLES]);
            }

            if (hung[c1] > 1)
            {
                pscore[c1] += (ds = -fv1[HUNGX]);
            }

            /* Score opening features and
             * castle/attack pattern distances */

            if (in_opening_stage)
            {
                pscore[c1] += (ds = ScoreKingOpeningFeatures());
                pscore[c1] += (ds = ScorePatternDistance(c1));
            }
        }

        score = mtl[side] - mtl[xside]
            + pscore[side] - pscore[xside] + 10;

#ifdef CACHE
        if (use_etable && PUTVAR)
            PutInEETable(side, score);
#endif

        return score;
#ifdef CACHE /* CHECKME: this looks bad */
    }

    return s;
#endif
}



/*
 * Try to determine the game type of "side".
 */

inline static void
GuessGameType(short side_to_move)
{
    short side, gt;
    short StaticRook[2]  = { 0, 0 };
    short RangingRook[2] = { 0, 0 };

    for (side = black; side <= white; side++)
    {
        /* computer should not change its mind */

        extern int bookflag; /* search.c */

        gt = GameType[side];

        if (!bookflag && (side == side_to_move))
        {
            if (gt == STATIC_ROOK)
                StaticRook[side] += 4;
            else if (gt == RANGING_ROOK)
                RangingRook[side] += 4;
        }

        /* static rook conditions */

        if (on_column(side, rook, 7))
            StaticRook[side] += 3;

        if (on_csquare(side, pawn, 34))
            StaticRook[side] += 6;
        else if (on_csquare(side, pawn, 43))
            StaticRook[side] += 4;
        else if (!on_column(side, pawn, 7))
            StaticRook[side] += 5;

        if (empty_csquare(side, 5) || empty_csquare(side, 6))
            StaticRook[side] += 2;

        if (on_left_side(side, king))
            StaticRook[side] += 2;

        /* ranging rook conditions */

        if (on_left_side(side, rook))
            RangingRook[side] += 5;
        else if (!on_column(side, rook, 7))
            RangingRook[side] += 3;

        if (on_csquare(side, pawn, 25))
            RangingRook[side] += 1;

        if (on_csquare(side, pawn, 30))
            RangingRook[side] += 1;
        else
            RangingRook[side] -= 2;

        if (!on_right_side(side, rook))
            RangingRook[side] += 4;

        if (on_right_side(side, king))
            RangingRook[side] += 4;

        if (on_csquare(side, bishop, 20))
        {
            if (on_csquare(side, silver, 11)
                || on_csquare(side, silver, 12)
                || on_csquare(side, silver, 21))
            {
                RangingRook[side] += 3;
            }
        }

        if ((StaticRook[side] > 5) || (RangingRook[side] > 5))
        {
            GameType[side] = (StaticRook[side] > RangingRook[side])
                ? STATIC_ROOK : RANGING_ROOK;
        }
        else
        {
            GameType[side] = UNKNOWN;
        }
    }

    if ((GameType[black] == UNKNOWN) || (GameType[white] == UNKNOWN))
    {
        for (side = black; side <= white; side++)
        {
            if ((side == computer) && (GameType[side] == UNKNOWN))
            {
                /*
                 * Game type is UNKNOWN.
                 * Make a decision what type of game to play.
                 * To make computer games more interesting, make a
                 * random decision.
                 */

                if (!on_csquare(side, pawn, 25))
                {
                    /* Play static rook if rook pawn has been pushed! */
                    GameType[side] = STATIC_ROOK;
                }
                else
                {
                    unsigned int random = urand() % 100;
                    short d = StaticRook[side] - RangingRook[side];

                    switch (GameType[side ^ 1])
                    {
                    case STATIC_ROOK:
                        if (random < 35 + d)
                            GameType[side] = STATIC_ROOK;
                        else if (random < 95)
                            GameType[side] = RANGING_ROOK;
                        break;

                    case RANGING_ROOK:
                        if (random < 75 + d)
                            GameType[side] = STATIC_ROOK;
                        else if (random < 95)
                            GameType[side] = RANGING_ROOK;
                        break;

                    default:
                        if (random < 33 + d)
                            GameType[side] = STATIC_ROOK;
                        else if (random < 66)
                            GameType[side] = RANGING_ROOK;
                    }
                }
            }
        }
    }
}




static void
DetermineGameType(short side_to_move)
{
    short side;

    GuessGameType(side_to_move);

    array_zero(Mpawn,   sizeof(Mpawn));
    array_zero(Mlance,  sizeof(Mlance));
    array_zero(Mknight, sizeof(Mknight));
    array_zero(Msilver, sizeof(Msilver));
    array_zero(Mgold,   sizeof(Mgold));
    array_zero(Mbishop, sizeof(Mbishop));
    array_zero(Mrook,   sizeof(Mrook));
    array_zero(Mking,   sizeof(Mking));

    if (in_opening_stage)
    {
        for (side = black; side <= white; side++)
            UpdatePatterns(side, GameCnt);
    }
    else
    {
        ShowPatternCount(black, -1);
        ShowPatternCount(white, -1);
    }
}



/*
 * This is done one time before the search is started. Set up arrays
 * Mwpawn, Mbpawn, Mknight, Mbishop, Mking which are used in the SqValue()
 * function to determine the positional value of each piece.
 */

void
ExaminePosition(short side)
{
    short c1, piece, sq, i, bsq, wsq;

    /* Build enemy king distance tables. */

    for (sq = 0, bsq = BlackKing, wsq = WhiteKing; sq < NO_SQUARES; sq++)
    {
        Kdist[black][sq] = distance(sq, bsq);
        Kdist[white][sq] = distance(sq, wsq);
    }

    threats(black);
    threats(white);

    ExamineSquares();

    DetermineGameType(side);
    DetermineStage(side);

    UpdateWeights(side);

    array_zero(HasPiece, sizeof(HasPiece));

    for (c1 = black; c1 <= white; c1++)
    {
        for (i = PieceCnt[c1]; i >= 0; i--)
        {
            ++HasPiece[c1][piece = board[sq = PieceList[c1][i]]];
        }
    }
}



void
DetermineStage(short side)
{
    short xside = side ^ 1, ds, db1, c1, c2, feature;

    /* Determine initial stage */

    balance[side] = balance[xside] = 50;

    if ((GameType[side] == STATIC_ROOK)
        && (GameType[xside] == STATIC_ROOK))
    {
        if (GameCnt < 40)
            stage = 0;
        else if (GameCnt < 60)
            stage = 15;
        else if (GameCnt < 80)
            stage = 25;
        else
            stage = 30;
    }
    else if ((GameType[side] == RANGING_ROOK)
             || (GameType[xside] == RANGING_ROOK))
    {
        if (GameCnt < 30)
            stage = 0;
        else if (GameCnt < 50)
            stage = 15;
        else if (GameCnt < 70)
            stage = 25;
        else
            stage = 30;
    }
    else
    {
        if (GameCnt < 35)
            stage = 0;
        else if (GameCnt < 55)
            stage = 15;
        else if (GameCnt < 75)
            stage = 25;
        else
            stage = 30;
    }

    /* Update stage depending on board features and attack balance value */

    if (abs(ds = (mtl[side] - mtl[xside]))
        > (db1 = (*value)[stage][lance]))
    {
        db1 = abs(4 * ds / db1);

        if (ds < 0)
            balance[side] += db1;
        else if (ds > 0)
            balance[xside] += db1;

        stage += (ds = db1);
    }

    for (c1 = black, c2 = white; c1 <= white; c1++, c2--)
    {
        if ((ds = seed[c1]) > 2)
        {
            balance[c1] += (db1 = ds * 2);
            balance[c2] -= db1;

            if (stage < 30)
                stage = 30;

            stage += ds;
        }

        if ((db1 = hung[c1]) > 2)
        {
            balance[c1] -= (db1 *= 2);
            balance[c2] += db1;
        }

        if ((db1 = loose[c1]) > 4)
        {
            balance[c1] -= (db1 /= 2);
            balance[c2] += db1;
            stage += (ds = 1);
        }

        if ((ds = hole[c1]))
        {
            balance[c1] -= (db1 = ds);
            balance[c2] += db1;
            stage += (ds /= 2);
        }

        if ((db1 = target[c1]) > 3)
        {
            balance[c1] += (db1 /= 3);
            balance[c2] -= db1;
            stage += (ds = db1 / 4);
        }

        stage += (ds = captured[c1] / 2);

        if ((db1 = captured[c1]) > 4)
        {
            balance[c1] += (db1 /= 2);
            stage += (ds = 3);
        }

        if ((db1 = dcaptured[c1]) > 3)
        {
            balance[c1] += db1;
            stage += (ds = 3);
        }

        if (balance[c1] > 99)
            balance[c1] = 99;
        else if (balance[c1] < 0)
            balance[c1] = 0;
    }

    if (stage > 99)
        stage = 99;
    else if (stage < 0)
        stage = 0;

    if (flag.post)
        ShowStage();

    /* Determine stage dependant weights */

    ADVNCM[pawn]   = 1; /* advanced pawn bonus increment   */
    ADVNCM[lance]  = 1;
    ADVNCM[knight] = 1;
    ADVNCM[silver] = 1; /* advanced silver bonus increment */
    ADVNCM[gold]   = 1; /* advanced gold bonus increment   */
    ADVNCM[bishop] = 1;
    ADVNCM[rook]   = 1;
    ADVNCM[king]   = 1; /* advanced king bonus increment   */

    MAXCDIST = (stage < 33) ? (33 - stage) / 4 : 0;
    MAXADIST = (stage < 30) ? (30 - stage) / 4 : 0;

    for (c1 = black; c1 <= white; c1++)
    {
        for (feature = 0; feature < NO_FEATURES; feature++)
        {
            fvalue[c1][feature] =
                ((((*fscore)[stage][feature][0] * (99 - balance[c1])) + 50)
                 / 100)
                + ((((*fscore)[stage][feature][1] * balance[c1]) + 50)
                   / 100);
        }
    }
}



void
UpdateWeights(short stage)
{
}



/*
 * Compute stage dependent relative material values assuming
 * linearity between the main stages:
 *
 *   minstage < stage < maxstage =>
 *          stage - minstage        value - minvalue
 *         -------------------  =  -------------------
 *         maxstage - minstage     maxvalue - minvalue
 */


static short
linear_piece_value(short piece, short stage, short i, short j)
{
    short minvalue, maxvalue, minstage, maxstage;

    minstage = ispvalue[0][i];
    maxstage = ispvalue[0][j];
    minvalue = ispvalue[piece][i];
    maxvalue = ispvalue[piece][j];

    /* FIXME: set a variable then return it, puh-leeze! */
    return ((stage - minstage) * (maxvalue - minvalue)
            / (maxstage - minstage)) + minvalue;
}



static short
linear_feature_value(short feature, short stage, short i, short j)
{
    short minvalue, maxvalue, minstage, maxstage;

    minstage = ispvalue[0][i];
    maxstage = ispvalue[0][j];
    minvalue = weight[feature][i];
    maxvalue = weight[feature][j];

    /* FIXME: set a variable then return it, puh-leeze! */
    return ((stage - minstage) * (maxvalue - minvalue)
            / (maxstage - minstage)) + minvalue;
}


/*
 * matweight = percentage_of_max_value * max_value(stage) / 100
 * max_value(0) = MAX_VALUE; max_value(100) = MIN_VALUE
 *  => max_value(stage) = a * stage + b; b = MAX_VALUE,
 *     a = (MIN_VALUE - MAX_VALUE)/100
 */

#define MIN_VALUE 300
#define MAX_VALUE 1000

#define max_value(stage) \
((int)(MIN_VALUE - MAX_VALUE) * stage + (int)100 * MAX_VALUE)
#define matweight(value, stage) \
((int)max_value(stage) * value / 10000)



void
Initialize_eval(void)
{
    short stage, piece, feature, i;

    for (stage = 0; stage < NO_STAGES; stage++)
    {
        for (i = 0; i < MAIN_STAGES; i++)
        {
            if (stage == ispvalue[0][i])
            {
                for (piece = 0; piece < NO_PIECES; piece++)
                {
                    (*value)[stage][piece] =
                        matweight(ispvalue[piece][i], stage);
                }

                for (feature = 0; feature < NO_FEATURES; feature++)
                {
                    (*fscore)[stage][feature][0] =
                        (weight[feature][i]
                         * weight[feature][MAIN_STAGES] + 50) / 100;

                    (*fscore)[stage][feature][1] =
                        (weight[feature][i]
                         * weight[feature][MAIN_STAGES + 1] + 50) / 100;
                }

                break;
            }

            if (i+1 < MAIN_STAGES && stage < ispvalue[0][i + 1])
            {
                for (piece = 0; piece < NO_PIECES; piece++)
                {
                    (*value)[stage][piece] =
                        matweight(
                            linear_piece_value(piece, stage, i, i + 1),
                            stage);
                }

                for (feature = 0; feature < NO_FEATURES; feature++)
                {
                    (*fscore)[stage][feature][0] =
                        (linear_feature_value(feature, stage, i, i + 1)
                         * weight[feature][MAIN_STAGES] + 50) / 100;

                    (*fscore)[stage][feature][1] =
                        (linear_feature_value(feature, stage, i, i + 1)
                         * weight[feature][MAIN_STAGES + 1] + 50) / 100;
                }

                break;
            }
        }
    }
}
