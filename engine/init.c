/*

    init.c

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
 * FILE: init.c
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

#if defined HAVE_GETTIMEOFDAY
#include <sys/time.h>
#endif

#include <signal.h>

#include "pattern.h"

/****************************************
 *     A variety of global flags.
 ****************************************/

/*
 * If hard_time_limit is nonzero, exceeding the time limit means
 * losing the game.
 */

short verbose         = 0;
short hard_time_limit = 1;
short barebones       = 0;  /* Suppress printing of statistics
                             * (mainly for xshogi). */
#ifdef LIST_ON_EXIT
short nolist          = 0;  /* List the game after exit. */
#else
short nolist          = 1;  /* Don't list the game after exit. */
#endif

unsigned int ttbllimit;

/* .... MOVE GENERATION VARIABLES AND INITIALIZATIONS .... */


#define max(a, b) (((a) < (b))?(b):(a))
#define odd(a) ((a) & 1)


const small_short piece_of_ptype[NO_PTYPE_PIECES] =
{
    pawn, lance, knight, silver, gold, bishop, rook, pbishop, prook, king,
    pawn, lance, knight, silver, gold
};


const small_short side_of_ptype[NO_PTYPE_PIECES] =
{
    black, black, black, black, black, black, black, black, black, black,
    white, white, white, white, white
};

#ifdef SAVE_NEXTPOS
const small_short psweep[NO_PTYPE_PIECES] =
{
    false, true, false, false, false, true, true, true, true, false,
    false, true, false, false, false
};
#endif

const small_short sweep[NO_PIECES] =
{
    false, false, true, false, false, false, true, true,
    false, false, false, false, true, true, false
};


#if !defined EXTLANGFILE

char *CP[CPSIZE] =

{
/* 000: eng: */ "",
#ifdef LANGFILE
#include LANGFILE
#else
#include "gnushogi.lng"
#endif
};

#else

char *CP[CPSIZE];

#endif


/*
 * Determine the minimum number of moves for a piece from
 * square "f" to square "t". If the piece cannot reach "t",
 * the count is set to CANNOT_REACH.
 */

#define csquare(sq) ((side == black) ? sq : (NO_SQUARES - 1 - sq))
#define crow(sq) row(csquare(sq))
#define ccol(sq) column(csquare(sq))

short
ptype_distance(short ptyp, short f, short t)
{
    short side, piece;
    short colf, colt, rowf, rowt, dcol, drow;

    if (f == t)
        return 0;

    piece = piece_of_ptype[ptyp];
    side  = side_of_ptype[ptyp];

    dcol = (colt = ccol(t)) - (colf = ccol(f));
    drow = (rowt = crow(t)) - (rowf = crow(f));

    switch (piece)
    {
    case pawn:
        if ((dcol != 0) || (drow < 1))
            return CANNOT_REACH;
        else
            return drow;

    case lance:
        if ((dcol != 0) || (drow < 1))
            return CANNOT_REACH;
        else
            return 1;

    case knight:
        if (odd(drow) || (odd(drow / 2) != odd(dcol)))
            return CANNOT_REACH;
        else if ((drow == 0) || ((drow / 2) < abs(dcol)))
            return CANNOT_REACH;
        else
            return (drow / 2);

    case silver:
        if (drow > 0)
        {
            if (odd(drow) == odd(dcol))
            {
                return max(abs(drow), abs(dcol));
            }
            else
            {
                if (abs(dcol) <= drow)
                    return drow;
                else
                    return (max(abs(drow), abs(dcol)) + 1);
            }
        }
        else
        {
            if (odd(drow) == odd(dcol))
                return (max(abs(drow), abs(dcol)));
            else
                return (max(abs(drow) + 1, abs(dcol)) + 1);
        };

    case gold:
    case ppawn:
    case pknight:
    case plance:
    case psilver:
        if (abs(dcol) == 0)
            return (abs(drow));
        else if (drow >= 0)
            return max(drow, abs(dcol));
        else
            return (abs(dcol) - drow);

    case bishop:
        if (odd(dcol) != odd(drow))
            return CANNOT_REACH;
        else
            return ((abs(dcol) == abs(drow)) ? 1 : 2);

    case pbishop:
        if (odd(dcol) != odd(drow))
        {
            if ((abs(dcol) <= 1) && (abs(drow) <= 1))
                return 1;
            else if (abs(abs(dcol) - abs(drow)) == 1)
                return 2;
            else
                return 3;
        }
        else
        {
            return ((abs(dcol) == abs(drow)) ? 1 : 2);
        }

    case rook:
        if ((dcol == 0) || (drow == 0))
            return 1;
        else
            return 2;

    case prook:
        if ((dcol == 0) || (drow == 0))
            return 1;
        else if ((abs(dcol) == 1) && (abs(drow) == 1))
            return 1;
        else
            return 2;

    case king:
        return max(abs(drow), abs(dcol));

    default:
        /* should never occur */
        return (CANNOT_REACH);
    }
}


#ifdef SAVE_DISTDATA
short
distance(short a, short b)
{
    return (short)computed_distance(a, b);
}
#else
short
distance(short a, short b)
{
    return (use_distdata
            ? (short)(*distdata)[(int)a][(int)b]
            : (short)computed_distance(a, b));
}
#endif


#ifdef SAVE_PTYPE_DISTDATA
short
piece_distance(short side, short piece, short f, short t)
{
    return ((f > NO_SQUARES)
            ? (short)1
            : (short)ptype_distance(ptype[side][piece], f, t));
}
#else
short
piece_distance(short side, short piece, short f, short t)
{
    return ((f > NO_SQUARES)
            ? (short)1
            : (use_ptype_distdata
               ? (short)(*ptype_distdata[ptype[side][piece]])[f][t]
               : (short)ptype_distance(ptype[side][piece], f, t)));
}
#endif


void
Initialize_dist(void)
{
    short a, b, d, di, ptyp;
#ifndef SAVE_DISTDATA
    for (a = 0; a < NO_SQUARES; a++)
    {
        for (b = 0; b < NO_SQUARES; b++)
        {
            d = abs(column(a) - column(b));
            di = abs(row(a) - row(b));
            (*distdata)[a][b] = (small_short)((d > di) ? d : di);
        }
    }
#endif
#ifndef SAVE_PTYPE_DISTDATA
    for (ptyp = 0; ptyp < NO_PTYPE_PIECES; ptyp++)
    {
        for (a = 0; a < NO_SQUARES; a++)
            for (b = 0; b < NO_SQUARES; b++)
                (*ptype_distdata[ptyp])[a][b] = ptype_distance(ptyp, a, b);
    }
#endif
}


/*
 * nextpos[piece][from-square], nextdir[piece][from-square] gives vector
 * of positions reachable from from-square in ppos with piece such that the
 * sequence
 *
 *     ppos = nextpos[piece][from-square];
 *     pdir = nextdir[piece][from-square];
 *     u = ppos[sq];
 *
 *     do
 *     {
 *         u = ppos[u];
 *
 *         if(color[u] != neutral)
 *             u = pdir[u];
 *     }
 *     while (sq != u);
 *
 * will generate the sequence of all squares reachable from sq.
 *
 * If the path is blocked u = pdir[sq] will generate the continuation of the
 * sequence in other directions.
 */


/*
 * ptype is used to separate black and white pawns, like this; ptyp =
 * ptype[side][piece] piece can be used directly in nextpos/nextdir when
 * generating moves for pieces that are not white pawns.
 */

const small_short ptype[2][NO_PIECES] =
{
    {
        ptype_no_piece, ptype_pawn,  ptype_lance,  ptype_knight,
        ptype_silver,   ptype_gold,  ptype_bishop, ptype_rook,
        ptype_gold,     ptype_gold,  ptype_gold,   ptype_gold,
        ptype_pbishop,  ptype_prook, ptype_king
    },
    {
        ptype_no_piece, ptype_wpawn, ptype_wlance, ptype_wknight,
        ptype_wsilver,  ptype_wgold, ptype_bishop, ptype_rook,
        ptype_wgold,    ptype_wgold, ptype_wgold,  ptype_wgold,
        ptype_pbishop,  ptype_prook, ptype_king
    },
};

const small_short promoted[NO_PIECES] =
{
    no_piece, ppawn, plance, pknight, psilver, gold, pbishop, prook,
    ppawn, plance, pknight, psilver, pbishop, prook, king
};

const small_short unpromoted[NO_PIECES] =
{
    no_piece, pawn, lance, knight, silver, gold, bishop, rook,
    pawn, lance, knight, silver, bishop, rook, king
};

const small_short is_promoted[NO_PIECES] =
{
    false, false, false, false, false, false, false, false,
    true, true, true, true, true, true, false
};

/* data used to generate nextpos/nextdir */
#if !defined SAVE_NEXTPOS
static
#endif
const small_short direc[NO_PTYPE_PIECES][8] =
{
    {  11,   0,   0,   0,   0,   0,   0,   0 },   /*  0 ptype_pawn    */
    {  11,   0,   0,   0,   0,   0,   0,   0 },   /*  1 ptype_lance   */
    {  21,  23,   0,   0,   0,   0,   0,   0 },   /*  2 ptype_knight  */
    {  10,  11,  12, -12, -10,   0,   0,   0 },   /*  3 ptype_silver  */
    {  10,  11,  12,  -1,   1, -11,   0,   0 },   /*  4 ptype_gold    */
    {  10,  12, -12, -10,   0,   0,   0,   0 },   /*  5 ptype_bishop  */
    {  11,  -1,   1, -11,   0,   0,   0,   0 },   /*  6 ptype_rook    */
    {  10,  12, -12, -10,  11,  -1,   1, -11 },   /*  7 ptype_pbishop */
    {  11,  -1,   1, -11,  10,  12, -12, -10 },   /*  8 ptype_prook   */
    {  10,  11,  12,  -1,   1, -12, -11, -10 },   /*  9 ptype_king    */
    { -11,   0,   0,   0,   0,   0,   0,   0 },   /* 10 ptype_wpawn   */
    { -11,   0,   0,   0,   0,   0,   0,   0 },   /* 11 ptype_wlance  */
    { -21, -23,   0,   0,   0,   0,   0,   0 },   /* 12 ptype_wknight */
    { -10, -11, -12,  12,  10,   0,   0,   0 },   /* 13 ptype_wsilver */
    { -10, -11, -12,   1,  -1,  11,   0,   0 }
};  /* 14 ptype_wgold */


small_short diagonal(short d)
{
    return (abs(d) == 10 || abs(d) == 12);
}


static const small_short max_steps[NO_PTYPE_PIECES] =
{
    1, 8, 1, 1, 1, 8, 8, 8, 8, 1, 1, 8, 1, 1, 1
};


const small_short nunmap[(NO_COLS + 2)*(NO_ROWS + 4)] =
{
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1,  0,  1,  2,  3,  4,  5,  6,  7,  8, -1,
    -1,  9, 10, 11, 12, 13, 14, 15, 16, 17, -1,
    -1, 18, 19, 20, 21, 22, 23, 24, 25, 26, -1,
    -1, 27, 28, 29, 30, 31, 32, 33, 34, 35, -1,
    -1, 36, 37, 38, 39, 40, 41, 42, 43, 44, -1,
    -1, 45, 46, 47, 48, 49, 50, 51, 52, 53, -1,
    -1, 54, 55, 56, 57, 58, 59, 60, 61, 62, -1,
    -1, 63, 64, 65, 66, 67, 68, 69, 70, 71, -1,
    -1, 72, 73, 74, 75, 76, 77, 78, 79, 80, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
};


const small_short inunmap[NO_SQUARES] =
{
     23,  24,  25,  26,  27,  28,  29,  30,  31,
     34,  35,  36,  37,  38,  39,  40,  41,  42,
     45,  46,  47,  48,  49,  50,  51,  52,  53,
     56,  57,  58,  59,  60,  61,  62,  63,  64,
     67,  68,  69,  70,  71,  72,  73,  74,  75,
     78,  79,  80,  81,  82,  83,  84,  85,  86,
     89,  90,  91,  92,  93,  94,  95,  96,  97,
    100, 101, 102, 103, 104, 105, 106, 107, 108,
    111, 112, 113, 114, 115, 116, 117, 118, 119
};


int InitFlag = false;


#if defined SAVE_NEXTPOS

short
next_direction(short ptyp, short *d, short sq)
{
    short delta, to, sfrom = inunmap[sq];

    do
    {
        (*d)++;
        if (*d >= 8)
            return sq;

        delta = direc[ptyp][*d];
        if (delta == 0)
            return sq;

        to = nunmap[sfrom + delta];
    }
    while (to < 0);

    return to;
}


short
next_position(short ptyp, short *d, short sq, short u)
{
    if (*d < 4 && psweep[ptyp])
    {
        short to = nunmap[inunmap[u] + direc[ptyp][*d]];

        if (to < 0)
            return next_direction(ptyp, d, sq);
        else
            return to;
    }
    else
    {
        return next_direction(ptyp, d, sq);
    }
}


short
first_direction(short ptyp, short *d, short sq)
{
    *d = -1;
    return next_direction(ptyp, d, sq);
}

#else

/*
 * This procedure pre-calculates all moves for every piece from every
 * square.  This data is stored in nextpos/nextdir and used later in the
 * move generation routines.
 */

void
Initialize_moves(void)
{
    short ptyp, po, p0, d, di, s, delta;
    unsigned char *ppos, *pdir;
    short dest[8][9];
    short sorted[9];
    short steps[8];
    short fpo = 23, tpo = 120;

    for (ptyp = 0; ptyp < NO_PTYPE_PIECES; ptyp++)
    {
        for (po = 0; po < NO_SQUARES; po++)
        {
            for (p0 = 0; p0 < NO_SQUARES; p0++)
            {
                (*nextpos[ptyp])[po][p0] = (unsigned char)po;
                (*nextdir[ptyp])[po][p0] = (unsigned char)po;
            }
        }
    }

    for (ptyp = 0; ptyp < NO_PTYPE_PIECES; ptyp++)
    {
        for (po = fpo; po < tpo; po++)
        {
            if (nunmap[po] >= (small_short)0)
            {
                ppos = (*nextpos[ptyp])[nunmap[po]];
                pdir = (*nextdir[ptyp])[nunmap[po]];

                /* dest is a function of direction and steps */
                for (d = 0; d < 8; d++)
                {
                    dest[d][0] = nunmap[po];
                    delta = direc[ptyp][d];

                    if (delta != 0)
                    {
                        p0 = po;

                        for (s = 0; s < max_steps[ptyp]; s++)
                        {
                            p0 = p0 + delta;

                            /*
                             * break if (off board) or (promoted rooks
                             * wishes to move two steps diagonal) or
                             * (promoted bishops wishes to move two steps
                             * non-diagonal)
                             */
                            if ((nunmap[p0] < (small_short)0)
                                || ((ptyp == ptype_prook)
                                    && (s > 0)
                                    && diagonal(delta))
                                || ((ptyp == ptype_pbishop)
                                    && (s > 0)
                                    && !diagonal(delta)))
                                break;
                            else
                                dest[d][s] = nunmap[p0];
                        }
                    }
                    else
                    {
                        s = 0;
                    }

                    /*
                     * Sort dest in number of steps order; currently no sort
                     * is done due to compatibility with the move generation
                     * order in old gnuchess.
                     */

                    steps[d] = s;

                    for (di = d; s > 0 && di > 0; di--)
                    {
                        if (steps[sorted[di - 1]] == 0) /* should be: < s */
                            sorted[di] = sorted[di - 1];
                        else
                            break;
                    }

                    sorted[di] = d;
                }

                /*
                 * update nextpos/nextdir
                 */

                p0 = nunmap[po];
                pdir[p0] = (unsigned char)dest[sorted[0]][0];

                for (d = 0; d < 8; d++)
                {
                    for (s = 0; s < steps[sorted[d]]; s++)
                    {
                        ppos[p0] = (unsigned char)dest[sorted[d]][s];
                        p0 = dest[sorted[d]][s];

                        if (d < 7)
                            pdir[p0] = (unsigned char)dest[sorted[d + 1]][0];

                        /*
                         * else is already initialized
                         */
                    }
                }
            }
        }
    }
}

#endif



/*
 * Reset the board and other variables to start a new game.
 */

void
NewGame(void)
{
    short l, c, p, max_opening_sequence;
#ifdef HAVE_GETTIMEOFDAY
    struct timeval tv;
#endif
    compptr = oppptr = 0;
    stage = 0;
    stage2 = -1;    /* the game is not yet started */
    flag.illegal = flag.mate = flag.post = flag.quit
        = flag.reverse = flag.bothsides = flag.onemove = flag.force
        = false;
    flag.material = flag.coords = flag.hash = flag.easy
        = flag.beep = flag.rcptr
        = true;
    flag.stars  = flag.shade = flag.back = flag.musttimeout = false;
    flag.gamein = false;
    flag.rv     = true;

    mycnt1 = mycnt2 = 0;
    GenCnt = NodeCnt = et0 = dither =  XCmore = 0;
    znodes = ZNODES;
    WAwindow = WAWNDW;
    WBwindow = WBWNDW;
    BAwindow = BAWNDW;
    BBwindow = BBWNDW;
    xwndw = BXWNDW;

    if (!MaxSearchDepth)
        MaxSearchDepth = MAXDEPTH - 1;

    contempt = 0;
    GameCnt = 0;
    Game50 = 1;
    CptrFlag[0] = TesujiFlag[0] = false;
    hint = OPENING_HINT;
    ZeroRPT();
    GameType[0] = GameType[1] = UNKNOWN;
    Pscore[0] = Tscore[0] = (SCORE_LIMIT + 3000);
    opponent = player = black;
    computer = white;

    for (l = 0; l < TREE; l++)
        Tree[l].f = Tree[l].t = 0;

    gsrand((unsigned int) 1);

    if (!InitFlag)
    {
        for (c = black; c <= white; c++)
        {
            for (p = pawn; p <= king; p++)
            {
                for (l = 0; l < NO_SQUARES; l++)
                {
                    (*hashcode)[c][p][l].key
                         = ((urand()));
                    (*hashcode)[c][p][l].key
                        += ((urand()) << 16);
                    (*hashcode)[c][p][l].bd
                         = ((urand()));
                    (*hashcode)[c][p][l].bd
                        += ((urand()) << 16);
                }
            }
        }

        for (c = black; c <= white; c++)
        {
            for (p = pawn; p <= king; p++)
            {
                for (l = 0; l < MAX_CAPTURED; l++)
                {
                    (*drop_hashcode)[c][p][l].key
                         = ((urand()));
                    (*drop_hashcode)[c][p][l].key
                        += ((urand()) << 16);
                    (*drop_hashcode)[c][p][l].bd
                         = ((urand()));
                    (*drop_hashcode)[c][p][l].bd
                        += ((urand()) << 16);
                }
            }
        }
    }

    for (l = 0; l < NO_SQUARES; l++)
    {
        board[l] = Stboard[l];
        color[l] = Stcolor[l];
        Mvboard[l] = 0;
    }

    ClearCaptured();
    ClearScreen();
    InitializeStats();

#ifdef HAVE_GETTIMEOFDAY
    gettimeofday(&tv, NULL);
    time0 = tv.tv_sec*100 + tv.tv_usec/10000;
#else
    time0 = time((time_t *) 0);
#endif

    /* resetting reference time */
    ElapsedTime(COMPUTE_AND_INIT_MODE);
    flag.regularstart = true;
    Book = BOOKFAIL;

    if (!InitFlag)
    {
        char sx[256];
        strcpy(sx, CP[169]);

        if (TCflag)
            SetTimeControl();
        else if (MaxResponseTime == 0)
            SelectLevel(sx);

        UpdateDisplay(0, 0, 1, 0);
        GetOpenings();
        GetOpeningPatterns(&max_opening_sequence);

        InitFlag = true;
    }

#if ttblsz
    if (TTadd)
    {
        ZeroTTable();
        TTadd = 0;
    }
#endif /* ttblsz */

    hashbd = hashkey = 0;
    return;
}



int
Initialize_data(void)
{
    size_t n;
    int i;
    char buffer[60];
    int doit = true;

    {
        small_short x = -1;

        if (x >= 0)
        {
            ShowMessage("datatype 'small_short' is unsigned; "
                        "check gnushogi.h\n");
            return 1;
        }
    }

    n = sizeof(struct leaf) * (size_t)TREE;
    Tree = malloc(n);

    if (!Tree)
    {
        sprintf(buffer, "Cannot allocate %d bytes for search tree",
                (int)n);
        ShowMessage(buffer);
        return 1;
    }

    n = sizeof(hashcode_array);
    hashcode = malloc(n);

    if (!hashcode)
    {
        sprintf(buffer, "Cannot allocate %d bytes for hashcode", (int)n);
        ShowMessage(buffer);
        return 1;
    }

    n = sizeof(drop_hashcode_array);
    drop_hashcode = malloc(n);

    if (!drop_hashcode)
    {
        sprintf(buffer,
                "Cannot allocate %d bytes for drop_hashcode",
                (int)n);
        ShowMessage(buffer);
        return 1;
    }

    n = sizeof(struct GameRec) * (size_t)(MAXMOVES + MAXDEPTH);
    GameList = malloc(n);

    if (!GameList)
    {
        sprintf(buffer,
                "Cannot allocate %d bytes for game record",
                (int)n);
        ShowMessage(buffer);
        return 1;
    }

#if !defined SAVE_NEXTPOS
    n = sizeof(next_array);

    for (i = 0; i < NO_PTYPE_PIECES; i++)
    {
        nextdir[i] = use_nextpos ? malloc(n) : NULL;

        if (!nextdir[i])
        {
            if (use_nextpos)
            {
                sprintf(buffer, "cannot allocate %d space for nextdir %d",
                        (int)(n), i);
                ShowMessage(buffer);
            }

            nextdir[i] = NULL;
            use_nextpos = false;
        }

        nextpos[i] = use_nextpos ? malloc(n) : NULL;

        if (!nextpos[i])
        {
            if (use_nextpos)
            {
                sprintf(buffer, "cannot allocate %d space for nextpos %d",
                        (int)(n), i);
                ShowMessage(buffer);
            }

            use_nextpos = false;
        }
    }

    if (!use_nextpos)
    {
        return 1;
    }
#endif

    n = sizeof(value_array);
    value = malloc(n);

    if (!value)
    {
        ShowMessage("cannot allocate value space");
        return 1;
    }

    n = sizeof(fscore_array);
    fscore = malloc(n);

    if (!fscore)
    {
        ShowMessage("cannot allocate fscore space");
        return 1;
    }

#if defined HISTORY
    n = sizeof_history;
    history = malloc(n);

    if (!history)
    {
        sprintf(buffer, "Cannot allocate %d bytes for history table",
                (int)sizeof_history);
        ShowMessage(buffer);
        use_history = false;
    }
#endif

#if defined CACHE
    n = sizeof(struct etable) * (size_t)ETABLE;

    for (i = 0; i < 2; i++)
    {
        etab[i] = use_etable ? malloc(n) : 0;

        if (!etab[i])
        {
            sprintf(buffer, "Cannot allocate %d bytes for cache table %d",
                    (int)n, (int)i);
            ShowMessage(buffer);
            use_etable = false;
        }
    }
#endif

#if ttblsz

    if (rehash < 0)
        rehash = MAXrehash;

    n = sizeof(struct hashentry)*(ttblsize + rehash);

    while (doit && ttblsize > MINTTABLE)
    {
        ttable[0] = malloc(n);  /* FIXME: cast to the correct type. */
        ttable[1] = ttable[0] ? malloc(n) : NULL;

        if (!ttable[0] || !ttable[1])
        {
            if (!ttable[0])
                free(ttable[0]);

            if (!ttable[1])
                free(ttable[1]);

            ttblsize = ttblsize >> 1;
            n = sizeof(struct hashentry) * (ttblsize + rehash);
        }
        else
        {
            doit = false;
        }
    }

    if (ttblsize <= MINTTABLE)
    {
        use_ttable = false;
    }

    if (use_ttable)
    {
        /* CHECKME: is the precedence here correct? */
        /* ttbllimit = ttblsize << 1 - ttblsize >> 2; */
        ttbllimit = (ttblsize << 1) - (ttblsize >> 2);
    }
    else
    {
        sprintf(buffer, "Cannot allocate %d bytes for transposition table",
                (int)(2 * n));
        ShowMessage(buffer);
        ttable[0] = ttable[1] = NULL;
    }
#endif /* ttblsz */

#if !defined SAVE_DISTDATA
    n = sizeof(distdata_array);
    distdata = malloc(n);

    if (!distdata)
    {
        ShowMessage("cannot allocate distdata space...");
        use_distdata = false;
    }
#endif

#if !defined SAVE_PTYPE_DISTDATA
    n = sizeof(distdata_array);

    for (i = 0; i < NO_PTYPE_PIECES; i++)
    {
        ptype_distdata[i] = use_ptype_distdata ? malloc(n) : 0;

        if (!ptype_distdata[i])
        {
            sprintf(buffer,
                    "cannot allocate %d bytes for ptype_distdata %d...",
                    (int)n, i);
            use_ptype_distdata = false;
        }
    }
#endif

    return 0;
}


#if defined EXTLANGFILE

#ifdef OLDLANGFILE

void
InitConst(char *lang)
{
    FILE *constfile;
    char s[256];
    char sl[5];
    char buffer[120];
    int len, entry;
    char *p, *q;
    constfile = fopen(LANGFILE, "r");

    if (!constfile)
    {
        ShowMessage("NO LANGFILE");
        exit(1);
    }

    while (fgets(s, sizeof(s), constfile))
    {
        if (s[0] == '!')
            continue;

        len = strlen(s);

        for (q = &s[len]; q > &s[8]; q--)
            if (*q == '}')
                break;

        if (q == &s[8])
        {
            ShowMessage("{ error in cinstfile");
            exit(1);
        }

        *q = '\0';

        if ((s[3] != ':') || (s[7] != ':') || (s[8] != '{'))
        {
            sprintf(buffer, "Langfile format error %s", s);
            ShowMessage(buffer);
            exit(1);
        }

        s[3] = s[7] = '\0';

        if (lang == NULL)
        {
            lang = sl;
            strcpy(sl, &s[4]);
        }

        if (strcmp(&s[4], lang))
            continue;

        entry = atoi(s);

        if ((entry < 0) || (entry >= CPSIZE))
        {
            ShowMessage("Langfile number error");
            exit(1);
        }

        for (q = p = &s[9]; *p; p++)
        {
            if (*p != '\\')
            {
                *q++ = *p;
            }
            else if (*(p + 1) == 'n')
            {
                *q++ = '\n';
                p++;
            }
        }

        *q = '\0';

        if ((entry < 0) || (entry > 255))
        {
            sprintf(buffer, "Langfile error %d\n", entry);
            ShowMessage(buffer);
            exit(0);
        }

        CP[entry] = (char *)GLOBAL_ALLOC((unsigned) strlen(&s[9]) + 1);

        if (CP[entry] == NULL)
        {
            char buffer[80];
            sprintf(buffer, "CP MALLOC, entry %d", entry);
            perror(buffer);
            exit(0);
        }

        strcpy(CP[entry], &s[9]);
    }

    fclose(constfile);
}

#else

void
InitConst(char *lang)
{
    FILE *constfile;
    char s[256];
    char sl[5];
    char buffer[120];
    int len, entry;
    char *p, *q;
    constfile = fopen(LANGFILE, "r");

    if (!constfile)
    {
        ShowMessage("NO LANGFILE");
        exit(1);
    }

    while (fgets(s, sizeof(s), constfile))
    {
        if (s[0] == '!')
            continue;

        len = strlen(s);

        if ((len > 3) && (s[3] == ':') || (len > 7) && (s[7] == ':'))
        {
            ShowMessage("old Langfile error");
            exit(1);
        }

        if (len <= 15)
        {
            ShowMessage("length error in Langfile");
            exit(1);
        }

        for (q = &s[len]; q > &s[15]; q--)
        {
            if (*q == '"')
                break;
        }

        if (q == &s[15])
        {
            ShowMessage("\" error in Langfile");
            exit(1);
        }

        *q = '\0';

        if ((s[6] != ':') || (s[10] != ':') || (s[15] != '"'))
        {
            sprintf(buffer, "Langfile format error %s", s);
            ShowMessage(buffer);
            exit(1);
        }

        s[6] = s[10] = '\0';

        if (lang == NULL)
        {
            lang = sl;
            strcpy(sl, &s[7]);
        }

        if (strcmp(&s[7], lang))
            continue;

        entry = atoi(&s[3]);

        if ((entry < 0) || (entry >= CPSIZE))
        {
            ShowMessage("Langfile number error");
            exit(1);
        }

        for (q = p = &s[16]; *p; p++)
        {
            if (*p != '\\')
            {
                *q++ = *p;
            }
            else if (*(p + 1) == 'n')
            {
                *q++ = '\n';
                p++;
            }
        }

        *q = '\0';

        if ((entry < 0) || (entry > 255))
        {
            sprintf(buffer, "Langfile error %d\n", entry);
            ShowMessage(buffer);
            exit(0);
        }

        CP[entry] = (char *)GLOBAL_ALLOC((unsigned)strlen(&s[16]) + 1);

        if (CP[entry] == NULL)
        {
            char buffer[80];
            sprintf(buffer, "CP MALLOC, entry %d", entry);
            perror(buffer);
            exit(0);
        }

        strcpy(CP[entry], &s[16]);
    }

    fclose(constfile);
}

#endif

#endif


int
InitMain(void)
{
    gsrand(starttime = ((unsigned int)time((time_t *)0)));    /* init urand */

    NodeCntLimit = 0;

#if ttblsz
    ttblsize = ttblsz;
    rehash = -1;
#endif /* ttblsz */

    if (Initialize_data() != 0)
        return 1;

#if defined EXTLANGFILE
    InitConst(Lang);
#endif

    strcpy(ColorStr[0], CP[118]);
    strcpy(ColorStr[1], CP[119]);

    XC = 0;
    MaxResponseTime = 0;

    TCflag       = false;
    OperatorTime = 0;
    barebones    = 1; /* set for gshogi to suppress msgs */

    Initialize();
    Initialize_dist();
    Initialize_eval();
#if !defined SAVE_NEXTPOS
    Initialize_moves();
#endif

    NewGame();

    flag.easy = ahead;
    flag.hash = hash;

    if (xwin)
        xwndw = atoi(xwin);

#ifdef HASHFILE
    hashfile = NULL;
#endif

#if ttblsz
#ifdef HASHFILE
#if defined(_WIN32)
    hashfile = NULL;
#else
    hashfile = fopen(HASHFILE, RWA_ACC);
#endif
    if (hashfile)
    {
        fseek(hashfile, 0L, SEEK_END);
        filesz = ftell(hashfile) / sizeof(struct fileentry) - 1 - MAXrehash;
        hashmask = filesz >> 1;
        hashbase = hashmask + 1;
    }
#endif /* HASHFILE */
#endif /* ttblsz */

    savefile[0] = '\0';
    listfile[0] = '\0';

    return 0;
}


void
ExitMain(void)
{
#if ttblsz
#ifdef HASHFILE
    if (hashfile)
        fclose(hashfile);
#endif /* HASHFILE */
#endif /* ttblsz */

    ExitShogi();
}
