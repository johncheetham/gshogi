/*

    commondsp.c

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
 * FILE: commondsp.c
 *
 *     Common display routines for GNU Shogi.
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

#if defined HAVE_GETTIMEOFDAY
#include <sys/time.h>
#endif

#include <ctype.h>
#include <signal.h>

#if !defined(_WIN32)
#include <sys/param.h>
#include <sys/file.h>
#endif

#include <sys/types.h>

#include "gnushogi.h"

char mvstr[4][6];
char *InPtr;
int InBackground = false;


#if defined(BOOKTEST)

void
movealgbr(short m, char *s)
{
    unsigned int f, t;
    short piece = 0, flag = 0;

    if (m == 0)
    {
        strcpy(s, "none");
        return;
    }

    f = (m >> 8) & 0x7f;
    t = m & 0xff;

    if (f > NO_SQUARES)
    {
        piece = f - NO_SQUARES;

        if (piece > NO_PIECES)
            piece -= NO_PIECES;

        flag = (dropmask | piece);
    }

    if (t & 0x80)
    {
        flag |= promote;
        t &= 0x7f;
    }

    if (flag & dropmask)
    {
        *s = pxx[piece];
        s++;
        *s = '*';
        s++;
        *s = cxx[column(t)];
        s++;
        *s = rxx[row(t)];
        s++;
    }
    else
    {
        *s = cxx[column(f)];
        s++;
        *s = rxx[row(f)];
        s++;
        *s = cxx[column(t)];
        s++;
        *s = rxx[row(t)];
        s++;

        if (flag & promote)
        {
            *s = '+';
            s++;
        }
    }

    if (m & 0x8000)
    {
        *s = '?';
        s++;
    }

    *s = '\0';
}

#endif /* BOOKTEST */




/*
 * Generate move strings in different formats.
 */

void
algbr(short f, short t, short flag)
{
    if (f > NO_SQUARES)
    {
        short piece;

        piece = f - NO_SQUARES;

        if (f > (NO_SQUARES + NO_PIECES))
            piece -= NO_PIECES;

        flag = (dropmask | piece);
    }

    if ((t & 0x80) != 0)
    {
        flag |= promote;
        t &= 0x7f;
    }

    if ((f == t) && ((f != 0) || (t != 0)))
    {
        if (!barebones)
        {
            printf("error in algbr: FROM=TO=%d, flag=0x%4x\n", t, flag);
        }

        mvstr[0][0] = mvstr[1][0] = mvstr[2][0] = mvstr[3][0] = '\0';
    }
    else if ((flag & dropmask) != 0)
    {
        short piece = flag & pmask;

        mvstr[0][0] = pxx[piece];
        mvstr[0][1] = '*';
        mvstr[0][2] = cxx[column(t)];
        mvstr[0][3] = rxx[row(t)];
        mvstr[0][4] = '\0';
        strcpy(mvstr[1], mvstr[0]);
        strcpy(mvstr[2], mvstr[0]);
        strcpy(mvstr[3], mvstr[0]);
    }
    else if ((f != 0) || (t != 0))
    {
        /* algebraic notation */
        mvstr[0][0] = cxx[column(f)];
        mvstr[0][1] = rxx[row(f)];
        mvstr[0][2] = cxx[column(t)];
        mvstr[0][3] = rxx[row(t)];
        mvstr[0][4] = mvstr[3][0] = '\0';
        mvstr[1][0] = pxx[board[f]];

        mvstr[2][0] = mvstr[1][0];
        mvstr[2][1] = mvstr[0][1];

        mvstr[2][2] = mvstr[1][1] = mvstr[0][2];    /* to column */
        mvstr[2][3] = mvstr[1][2] = mvstr[0][3];    /* to row */
        mvstr[2][4] = mvstr[1][3] = '\0';
        strcpy(mvstr[3], mvstr[2]);
        mvstr[3][1] = mvstr[0][0];

        if (flag & promote)
        {
            strcat(mvstr[0], "+");
            strcat(mvstr[1], "+");
            strcat(mvstr[2], "+");
            strcat(mvstr[3], "+");
        }
    }
    else
    {
        mvstr[0][0] = mvstr[1][0] = mvstr[2][0] = mvstr[3][0] = '\0';
    }
}



/*
 * Compare the string 's' to the list of legal moves available for the
 * opponent. If a match is found, make the move on the board.
 */

int
VerifyMove(char *s, VerifyMove_mode iop, unsigned short *mv)
{
    static short pnt, tempb, tempc, tempsf, tempst, cnt;
    static struct leaf xnode;
    struct leaf  *node;
    short i, l, local_flags;
    char buffer[60];

    /* check and remove quality flags */
    for (i = local_flags = 0, l = strlen(s); i < l; i++)
    {
        switch(s[i])
        {
        case '?':
            local_flags |= badmove;
            s[i] = '\0';
            break;

        case '!':
            local_flags |= goodmove;
            s[i] = '\0';
            break;

#ifdef EASY_OPENINGS
        case '~':
            local_flags |= difficult;
            s[i] = '\0';
            break;
#endif
        }
    }

    *mv = 0;

    if (iop == UNMAKE_MODE)
    {
        UnmakeMove(opponent, &xnode, &tempb, &tempc, &tempsf, &tempst);
        return false;
    }

    cnt = 0;

    if (iop == VERIFY_AND_MAKE_MODE)
        generate_move_flags = true;

    MoveList(opponent, 2, -1, true);
    generate_move_flags = false;
    pnt = TrPnt[2];

    while (pnt < TrPnt[3])
    {
        node = &Tree[pnt++];
        algbr(node->f, node->t, (short) node->flags);

        if ((strcmp(s, mvstr[0]) == 0)
            || (strcmp(s, mvstr[1]) == 0)
            || (strcmp(s, mvstr[2]) == 0)
            || (strcmp(s, mvstr[3]) == 0))
        {
            cnt++;
            xnode = *node;
        }
    }

    if ((cnt == 1) && (xnode.score > DONTUSE))
    {
        short blocked;

        MakeMove(opponent, &xnode, &tempb, &tempc,
                 &tempsf, &tempst, &INCscore);

        if (SqAttacked(PieceList[opponent][0], computer, &blocked))
        {
            UnmakeMove(opponent, &xnode, &tempb, &tempc, &tempsf, &tempst);

            /* Illegal move in check */
            printf(CP[77], mvstr[0]);
            printf("\n");

            return false;
        }
        else
        {
            if (iop == VERIFY_AND_TRY_MODE)
                return true;

            UpdateDisplay(xnode.f, xnode.t, 0, (short) xnode.flags);
            GameList[GameCnt].depth = GameList[GameCnt].score = 0;
            GameList[GameCnt].nodes = 0;
            ElapsedTime(COMPUTE_AND_INIT_MODE);
            GameList[GameCnt].time = (short) (et + 50)/100;
            GameList[GameCnt].flags |= local_flags;

            if (TCflag)
            {
                TimeControl.clock[opponent] -= et;
                timeopp[oppptr] = et;
                --TimeControl.moves[opponent];
            }

            *mv = (xnode.f << 8) | xnode.t;
            algbr(xnode.f, xnode.t, false);

            /* in force mode, check for mate conditions */
            /*if (flag.force)
            {*/
                if (IsCheckmate(opponent ^ 1, -1, -1))
                {
                    char buf[20];
                    winner = opponent + 1;
                    sprintf(buf, "%s mates!\n", ColorStr[opponent]);
                    ShowMessage(buf);
                    flag.mate = true;
                }
            /*}*/

            return true;
        }
    }

    /* Illegal move */
    printf (CP[75], s);

    if (!barebones && (cnt > 1))
    {
        sprintf(buffer, CP[32], s);
        ShowMessage(buffer);
    }

    return false;
}



static int
parser(char *f, int side, short *fpiece)
{
    int c1, r1, c2, r2;
    short i, p = false;

    if (*f == '+')
        f++, p = true;

    for (i = 1, *fpiece = no_piece; i < NO_PIECES; i++)
    {
        if (f[0] == pxx[i] || f[0] == qxx[i])
        {
            *fpiece = (p ? promoted[i] : unpromoted[i]);
            break;
        }
    }

    if (f[1] == '*' || f[1] == '\'')
    {
        c2 = '9' - f[2];
        r2 = 'i' - f[3];

        return ((NO_SQUARES + *fpiece) << 8) | locn(r2, c2);
    }
    else
    {
        c1 = '9' - f[1];
        r1 = 'i' - f[2];
        c2 = '9' - f[3];
        r2 = 'i' - f[4];
        p = (f[5] == '+') ? 0x80 : 0;

        return (locn(r1, c1) << 8) | locn(r2, c2) | p;
    }
}


void
skip()
{
    while (*InPtr != ' ')
        InPtr++;

    while (*InPtr == ' ')
        InPtr++;
}



void
skipb()
{
    while (*InPtr == ' ')
        InPtr++;
}



short
GetGame(char *filename)
{
    FILE *fd;
    char fname[256], *p;
    int c, i, j;
    short sq;
    short side, isp;

    /*filename += 4;*/
    strcpy(fname, filename);

    /* shogi.000 */
    if (fname[0] == '\0')
        strcpy(fname, CP[137]);

    if ((fd = fopen(fname, "r")) != NULL)
    {
        NewGame();
        if (fgets(fname, 256, fd) == NULL) return 1;
        computer = opponent = black;
        InPtr = fname;
        skip();

        if (*InPtr == 'c')
            computer = white;
        else
            opponent = white;

        /* FIXME: write a skipn() function so that we can get
         * 3 skips by doing skipn(3) */
        skip();
        skip();
        skip();
        Game50 = atoi(InPtr);
        skip();
        flag.force = (*InPtr == 'f');
        if (fgets(fname, 256, fd) == NULL) return 1; /* empty */
        if (fgets(fname, 256, fd) == NULL) return 1;
        InPtr = &fname[11];
        skipb();
        TCflag = atoi(InPtr);
        skip();
        InPtr += 14;
        skipb();
        OperatorTime = atoi(InPtr);
        if (fgets(fname, 256, fd) == NULL) return 1;
        InPtr = &fname[11];
        skipb();
        TimeControl.clock[black] = atol(InPtr);
        skip();
        skip();
        TimeControl.moves[black] = atoi(InPtr);
        if (fgets(fname, 256, fd) == NULL) return 1;
        InPtr = &fname[11];
        skipb();
        TimeControl.clock[white] = atol(InPtr);
        skip();
        skip();
        TimeControl.moves[white] = atoi(InPtr);
        if (fgets(fname, 256, fd) == NULL) return 1; /* empty */

        for (i = NO_ROWS - 1; i > -1; i--)
        {
            if (fgets(fname, 256, fd) == NULL) return 1;
            p = &fname[2];
            InPtr = &fname[23];

            for (j = 0; j < NO_COLS; j++)
            {
                sq = i * NO_COLS + j;
                isp = (*p == '+');
                p++;

                if (*p == '-')
                {
                    board[sq] = no_piece;
                    color[sq] = neutral;
                }
                else
                {
                    for (c = 0; c < NO_PIECES; c++)
                    {
                        if (*p == pxx[c])
                        {
                            if (isp)
                                board[sq] = promoted[c];
                            else
                                board[sq] = unpromoted[c];

                            color[sq] = white;
                        }
                    }

                    for (c = 0; c < NO_PIECES; c++)
                    {
                        if (*p == qxx[c])
                        {
                            if (isp)
                                board[sq] = promoted[c];
                            else
                                board[sq] = unpromoted[c];

                            color[sq] = black;
                        }
                    }
                }

                p++;
                Mvboard[sq] = atoi(InPtr);
                skip();
            }
        }

        if (fgets(fname, 256, fd) == NULL) return 1;  /* empty */
        if (fgets(fname, 256, fd) == NULL) return 1;  /* 9 8 7 ... */
        if (fgets(fname, 256, fd) == NULL) return 1;  /* empty */
        if (fgets(fname, 256, fd) == NULL) return 1;  /* p l n ... */
        ClearCaptured();

        for (side = 0; side <= 1; side++)
        {
            if (fgets(fname, 256, fd) == NULL) return 1;
            InPtr = fname;
            skip();
            skipb();
            Captured[side][pawn] = atoi(InPtr);
            skip();
            Captured[side][lance] = atoi(InPtr);
            skip();
            Captured[side][knight] = atoi(InPtr);
            skip();
            Captured[side][silver] = atoi(InPtr);
            skip();
            Captured[side][gold] = atoi(InPtr);
            skip();
            Captured[side][bishop] = atoi(InPtr);
            skip();
            Captured[side][rook] = atoi(InPtr);
            skip();
            Captured[side][king] = atoi(InPtr);
        }

        GameCnt = 0;
        flag.regularstart = true;
        Book = BOOKFAIL;
        if (fgets(fname, 256, fd) == NULL) return 1; /* empty */
        if (fgets(fname, 256, fd) == NULL) return 1;   /*  move score ... */

        while (fgets(fname, 256, fd))
        {
            struct GameRec  *g;
            int side = computer;

            side = side ^ 1;
            ++GameCnt;
            InPtr = fname;
            skipb();
            g = &GameList[GameCnt];
            g->gmove = parser(InPtr, side, &g->fpiece);
            skip();
            g->score = atoi(InPtr);
            skip();
            g->depth = atoi(InPtr);
            skip();
            g->nodes = atol(InPtr);
            skip();
            g->time = atol(InPtr);
            skip();
            g->flags = c = atoi(InPtr);
            skip();
            g->hashkey = strtol(InPtr, (char **) NULL, 16);
            skip();
            g->hashbd = strtol(InPtr, (char **) NULL, 16);

            if (c & capture)
            {
                short i, piece;

                skip();

                for (piece = no_piece, i = 0; i < NO_PIECES; i++)
                {
                    if (pxx[i] == *InPtr)
                    {
                        piece = i;
                        break;
                    }
                }

                skip();
                g->color = ((*InPtr == CP[119][0]) ? white : black);
                skip();
                g->piece = (*InPtr == '+'
                            ? promoted[piece]
                            : unpromoted[piece]);
            }
            else
            {
                g->color = neutral;
                g->piece = no_piece;
            }
        }

        if (TimeControl.clock[black] > 0)
            TCflag = true;

        fclose(fd);
    }

    ZeroRPT();
    InitializeStats();
    UpdateDisplay(0, 0, 1, 0);
    Sdepth = 0;
    hint = 0;
    return 0;
}



void
SaveGame(char *filename, char *sfen)
{
    FILE *fd;
    char fname[256];
    short sq, i, c, f, t;
    char p;
    short side, piece;
    char empty[2] = "\n";

    /* filename +=5;*/
    strcpy(fname, filename);

    if (fname[0] == '\0')        /* shogi.000 */
        strcpy(fname, CP[137]);

    if ((fd = fopen(fname, "w")) != NULL)
    {
        char *b, *w;
        b = w = CP[74];

        if (computer == white)
            w = CP[141];

        if (computer == black)
            b = CP[141];

        fprintf(fd, CP[37], w, b, Game50,
                flag.force ? "force" : "");
        /*fprintf(fd, "%s", empty);*/
        fprintf(fd, "%s", sfen);
        fprintf(fd, CP[111], TCflag, OperatorTime);
        fprintf(fd, CP[117],
                TimeControl.clock[black], TimeControl.moves[black],
                TimeControl.clock[white], TimeControl.moves[white]);
        fprintf(fd, "%s", empty);

        for (i = NO_ROWS - 1; i > -1; i--)
        {
            fprintf(fd, "%c ", 'i' - i);

            for (c = 0; c < NO_COLS; c++)
            {
                sq = i * NO_COLS + c;
                piece = board[sq];
                p = is_promoted[piece] ? '+' : ' ';
                fprintf(fd, "%c", p);

                switch(color[sq])
                {
                case white:
                    p = pxx[piece];
                    break;

                case black:
                    p = qxx[piece];
                    break;

                default:
                    p = '-';
                }

                fprintf(fd, "%c", p);
            }

            fprintf(fd, "  ");

            for (f = i * NO_COLS; f < i * NO_COLS + NO_ROWS; f++)
                fprintf(fd, " %d", Mvboard[f]);

            fprintf(fd, "\n");
        }

        fprintf(fd, "%s", empty);
        fprintf(fd, "   9 8 7 6 5 4 3 2 1\n");
        fprintf(fd, "%s", empty);
        fprintf(fd, "   p  l  n  s  g  b  r  k\n");

        for (side = 0; side <= 1; side++)
        {
            fprintf(fd, "%c", (side == black) ? 'B' : 'W');
            fprintf(fd, " %2d", Captured[side][pawn]);
            fprintf(fd, " %2d", Captured[side][lance]);
            fprintf(fd, " %2d", Captured[side][knight]);
            fprintf(fd, " %2d", Captured[side][silver]);
            fprintf(fd, " %2d", Captured[side][gold]);
            fprintf(fd, " %2d", Captured[side][bishop]);
            fprintf(fd, " %2d", Captured[side][rook]);
            fprintf(fd, " %2d", Captured[side][king]);
            fprintf(fd, "\n");
        }

        fprintf(fd, "%s", empty);
        fprintf(fd, "%s", CP[126]);

        for (i = 1; i <= GameCnt; i++)
        {
            struct GameRec  *g = &GameList[i];

            f = g->gmove >> 8;
            t = (g->gmove & 0xFF);
            algbr(f, t, g->flags);

            fprintf(fd, "%c%c%-5s %6d %5d %7d %6d %5d  0x%08x 0x%08x",
                    ((f > NO_SQUARES)
                     ? ' '
                     : (is_promoted[g->fpiece] ? '+' : ' ')),
                    pxx[g->fpiece],
                    ((f > NO_SQUARES) ? &mvstr[0][1] : mvstr[0]),
                    g->score, g->depth,
                    g->nodes, g->time, g->flags,
                    g->hashkey, g->hashbd);

            if (g->piece != no_piece)
            {
                fprintf(fd, "  %c %s %c\n",
                        pxx[g->piece], ColorStr[g->color],
                        (is_promoted[g->piece] ? '+' : ' '));
            }
            else
            {
                fprintf(fd, "\n");
            }
        }

        fclose(fd);

        /* Game saved */
        ShowMessage(CP[70]);
    }
    else
    {
        /* ShowMessage("Could not open file"); */
        ShowMessage(CP[48]);
    }
}


void
ListGame(void)
{
    FILE *fd;
    short i, f, t;
    time_t when;
    char fname[256], dbuf[256];

    if (listfile[0])
    {
        strcpy(fname, listfile);
    }
    else
    {
        time(&when);
        strncpy(dbuf, ctime(&when), 20);
        dbuf[7]  = '\0';
        dbuf[10] = '\0';
        dbuf[13] = '\0';
        dbuf[16] = '\0';
        dbuf[19] = '\0';

        /* use format "CLp16.Jan01-020304B" when patchlevel is 16,
           date is Jan 1
           time is 02:03:04
           program played white */

        sprintf(fname, "CLp%s.%s%s-%s%s%s%c",
                patchlevel, dbuf + 4, dbuf + 8, dbuf + 11, dbuf + 14,
                dbuf + 17, ColorStr[computer][0]);

        /* replace space padding with 0 */
        for (i = 0; fname[i] != '\0'; i++)
        {
            if (fname[i] == ' ')
                fname[i] = '0';
        }
    }

    fd = fopen(fname, "w");

    if (!fd)
    {
        printf(CP[219], fname);
        exit(1);
    }

    /* fprintf(fd, "gnushogi game %d\n", u); */
    fprintf(fd, CP[161], version, patchlevel);
    fprintf(fd, "%s", CP[10]);
    fprintf(fd, "%s", CP[11]);

    for (i = 1; i <= GameCnt; i++)
    {
        f = GameList[i].gmove >> 8;
        t = (GameList[i].gmove & 0xFF);
        algbr(f, t, GameList[i].flags);

        if (GameList[i].flags & book)
        {
            fprintf(fd, "%c%c%-5s  %5d    Book%7d %5d",
                    ((f > NO_SQUARES)
                     ? ' '
                     : (is_promoted[GameList[i].fpiece] ? '+' : ' ')),
                    pxx[GameList[i].fpiece],
                    ((f > NO_SQUARES)
                     ? &mvstr[0][1] : mvstr[0]),
                    GameList[i].score,
                    GameList[i].nodes,
                    GameList[i].time);
        }
        else
        {
            fprintf(fd, "%c%c%-5s  %5d     %2d %7d %5d",
                    (f > NO_SQUARES
                     ? ' '
                     : (is_promoted[GameList[i].fpiece] ? '+' : ' ')),
                    pxx[GameList[i].fpiece],
                    (f > NO_SQUARES ? &mvstr[0][1] : mvstr[0]),
                    GameList[i].score, GameList[i].depth,
                    GameList[i].nodes, GameList[i].time);
        }

        if ((i % 2) == 0)
        {
            fprintf(fd, "\n");
        }
        else
        {
            fprintf(fd, "         ");
        }
    }

    fprintf(fd, "\n\n");

    if (GameList[GameCnt].flags & draw)
    {
        fprintf(fd, CP[54], DRAW);

        if (DRAW == CP[101])
        {
            short j;

            fprintf(fd, "repetition by positions ");

            for (j = GameCnt - 1; j >= Game50; j -= 2)
            {
                if (GameList[j].hashkey == hashkey &&
                    GameList[j].hashbd == hashbd)
                    fprintf(fd, "%d ", j);
            }

            fprintf(fd, "\n");
        }
    }
    else if (GameList[GameCnt].score == -(SCORE_LIMIT + 999))
    {
        fprintf(fd, "%s\n", ColorStr[player ]);
    }
    else if (GameList[GameCnt].score == (SCORE_LIMIT + 998))
    {
        fprintf(fd, "%s\n", ColorStr[player ^ 1]);
    }

    fclose(fd);
}



void
FlagMove(char c)
{
    switch(c)
    {
    case '?' :
        GameList[GameCnt].flags |= badmove;
        break;

    case '!' :
        GameList[GameCnt].flags |= goodmove;
        break;

#ifdef EASY_OPENINGS
    case '~' :
        GameList[GameCnt].flags |= difficult;
        break;
#endif
    }
}




/*
 * Undo the most recent half-move.
 */

void
Undo(void)
{
    short f, t;

    f = GameList[GameCnt].gmove >> 8;
    t = GameList[GameCnt].gmove & 0x7F;

    if (f > NO_SQUARES)
    {
        /* the move was a drop */
        Captured[color[t]][board[t]]++;
        board[t] = no_piece;
        color[t] = neutral;
        Mvboard[t]--;
    }
    else
    {
        if (GameList[GameCnt].flags & promote)
            board[f] = unpromoted[board[t]];
        else
            board[f] = board[t];

        color[f] = color[t];
        board[t] = GameList[GameCnt].piece;
        color[t] = GameList[GameCnt].color;

        if (board[t] != no_piece)
            Captured[color[f]][unpromoted[board[t]]]--;

        if (color[t] != neutral)
            Mvboard[t]--;

        Mvboard[f]--;
    }

    InitializeStats();

    if (TCflag && (TCmoves > 1))
        ++TimeControl.moves[color[f]];

    hashkey = GameList[GameCnt].hashkey;
    hashbd = GameList[GameCnt].hashbd;
    GameCnt--;
    computer = computer ^ 1;
    opponent = opponent ^ 1;
    flag.mate = false;
    Sdepth = 0;
    player = player ^ 1;
    ShowSidetoMove();
    UpdateDisplay(0, 0, 1, 0);

    if (flag.regularstart)
        Book = false;
}



void
FlagString(unsigned short flags, char *s)
{
    short l, piece;
    *s = '\0';

    if (flags & promote)
        strcat(s, " promote");

    if (flags & dropmask)
        strcat(s, " drop:");

    if ((piece = (flags & pmask)))
    {
        l = strlen(s);

        if (is_promoted[piece])
            s[l++] = '+';

        s[l++] = pxx[piece];
        s[l] = '\0';
    }

    if (flags & capture)
        strcat(s, " capture");

    if (flags & exact)
        strcat(s, " exact");

    if (flags & tesuji)
        strcat(s, " tesuji");

    if (flags & check)
        strcat(s, " check");

    if (flags & draw)
        strcat(s, " draw");

    if (flags & stupid)
        strcat(s, " stupid");

    if (flags & questionable)
        strcat(s, " questionable");

    if (flags & kingattack)
        strcat(s, " kingattack");

    if (flags & book)
        strcat(s, " book");
}



void
TestSpeed(void(*f)(short side, short ply,
                   short in_check, short blockable),
          unsigned j)
{
#ifdef test
    unsigned jj;
#endif

    unsigned i;
    int cnt, rate, t1, t2;

#ifdef HAVE_GETTIMEOFDAY
    struct timeval tv;
#endif

#ifdef HAVE_GETTIMEOFDAY
    gettimeofday(&tv, NULL);
    t1 = (tv.tv_sec*100 + (tv.tv_usec/10000));
#else
    t1 = time(0);
#endif

    for (i = 0; i < j; i++)
    {
        f(opponent, 2, -1, true);

#ifdef test
        for (jj = TrPnt[2]; i < TrPnt[3]; jj++)
        {
            if (!pick(jj, TrPnt[3] - 1))
                break;
        }
#endif
    }

#ifdef HAVE_GETTIMEOFDAY
    gettimeofday(&tv, NULL);
    t2 = (tv.tv_sec * 100 + (tv.tv_usec / 10000));
#else
    t2 = time(0);
#endif

    cnt = j * (TrPnt[3] - TrPnt[2]);

    if (t2 - t1)
        et = (t2 - t1);
    else
        et = 1;

    rate = (((et) ? ((cnt * 100) / et) : 0));

#ifdef DYNAMIC_ZNODES
    if (rate > 0)
        znodes = rate;
#endif

    printf(CP[91], cnt, rate);

}



void
TestPSpeed(short(*f) (short side), unsigned j)
{
    short i;
    int cnt, rate, t1, t2;
#ifdef HAVE_GETTIMEOFDAY
    struct timeval tv;
#endif

#ifdef HAVE_GETTIMEOFDAY
    gettimeofday(&tv, NULL);
    t1 = (tv.tv_sec * 100 + (tv.tv_usec / 10000));
#else
    t1 = time(0);
#endif

    for (i = 0; i < j; i++)
        (void) f(opponent);

#ifdef HAVE_GETTIMEOFDAY
    gettimeofday(&tv, NULL);
    t2 = (tv.tv_sec * 100 + (tv.tv_usec / 10000));
#else
    t2 = time(0);
#endif

    cnt = j;

    if (t2 - t1)
        et = (t2 - t1);
    else
        et = 1;

    rate = (et) ? ((cnt * 100) / et) : 0;

    /* printf("Nodes= %ld Nodes/sec= %ld\n", cnt, rate); */

    printf(CP[91], cnt, rate);

}



void
SetOppTime(char *s)
{
    char *time;
    int m, t, sec;

    sec = 0;
    time = &s[strlen(CP[228])];
    t = (int)strtol(time, &time, 10);

    if (*time == ':')
    {
        time++;
        sec = (int)strtol(time, &time, 10);
    }

    m = (int)strtol(time, &time, 10);

    if (t)
        TimeControl.clock[opponent] = t;

    if (m)
        TimeControl.moves[opponent] = m;

    ElapsedTime(COMPUTE_AND_INIT_MODE);

}



void
SetMachineTime(char *s)
{
    char *time;
    int m, t, sec;

    time = &s[strlen(CP[197])];
    sec = 0;
    t = (int)strtol(time, &time, 10);

    if (*time == ':')
    {
        time++;
        sec = (int)strtol(time, &time, 10);
    }

    m = (int)strtol(time, &time, 10);

    if (t)
        TimeControl.clock[computer] = t;

    if (m)
        TimeControl.moves[computer] = m;

    ElapsedTime(COMPUTE_AND_INIT_MODE);

}


short
DoMove(char *command)
{
    short ok, is_move = false;
    unsigned short mv;
    char s[80], sx[80];

    s[0] = sx[0] = '\0';

    sx[0] = command[0];
    sx[1] = command[1];
    sx[2] = command[2];
    sx[3] = command[3];
    sx[4] = command[4];
    sx[5] = '\0';

    sscanf(sx, "%s", s);

    if ((ok = VerifyMove(s, VERIFY_AND_MAKE_MODE, &mv)))
    {
        /* check for repetition */
        short rpt = repetition();

        if (rpt >= 3)
        {
            DRAW = CP[101];
            ShowMessage(DRAW);
            GameList[GameCnt].flags |= draw;

            flag.mate = true;
        }
        else
        {
            is_move = true;
        }
    }

    /*ElapsedTime(COMPUTE_AND_INIT_MODE);*/

    return is_move;

}


/* FIXME!  This is truly the function from hell! */

/*
 * Process the user's command. If easy mode is OFF (the computer is thinking
 * on opponents time) and the program is out of book, then make the 'hint'
 * move on the board and call SelectMove() to find a response. The user
 * terminates the search by entering ^C (quit siqnal) before entering a
 * command. If the opponent does not make the hint move, then set Sdepth to
 * zero.
 */

void
InputCommand(char *command)
{
    int eof = 0;
    short have_shown_prompt = false;
    short ok, done, is_move = false;
    unsigned short mv;
    char s[80], sx[80];

    ok = flag.quit = done = false;
    player = opponent;

#if ttblsz
    if (TTadd > ttbllimit)
        ZeroTTable();
#endif

    if ((hint > 0) && !flag.easy && !flag.force)
    {
        /*
         * A hint move for the player is available.  Compute a move for the
         * opponent in background mode assuming that the hint move will be
         * selected by the player.
         */

        ft = time0; /* Save reference time for the player. */
        fflush(stdout);
        algbr((short) hint >> 8, (short) hint & 0xff, false);
        strcpy(s, mvstr[0]);

#if !defined NOPOST
        if (flag.post)
            GiveHint();
#endif

        /* do the hint move */
        if (VerifyMove(s, VERIFY_AND_TRY_MODE, &mv))
        {
            Sdepth = 0;

#ifdef QUIETBACKGROUND
            PromptForMove();

            have_shown_prompt = true;
#endif /* QUIETBACKGROUND */

            /* Start computing a move until the search is interrupted. */

#ifdef INTERRUPT_TEST
            itime0 = 0;
#endif

            /* would love to put null move in here */
            /* after we make the hint move make a 2 ply search
             * with both plys our moves */
            /* think on opponents time */
            SelectMove(computer, BACKGROUND_MODE);

#ifdef INTERRUPT_TEST
            ElapsedTime(COMPUTE_INTERRUPT_MODE);

            if (itime0 == 0)
            {
                printf("searching not terminated by interrupt!\n");
            }
            else
            {
                printf("elapsed time from interrupt to "
                       "terminating search: %ld\n", it);
            }
#endif

            /* undo the hint and carry on */
            VerifyMove(s, UNMAKE_MODE, &mv);
            Sdepth = 0;
        }

        time0 = ft; /* Restore reference time for the player. */
    }

    while(!(ok || flag.quit || done))
    {
        player = opponent;

#ifdef QUIETBACKGROUND
        if (!have_shown_prompt)
        {
#endif /* QUIETBACKGROUND */

            PromptForMove();

#ifdef QUIETBACKGROUND
        }

        have_shown_prompt = false;
#endif /* QUIETBACKGROUND */

        if (command == NULL)
        {

            s[0] = sx[0] = '\0';

            sx[0] = command[0];
            sx[1] = command[1];
            sx[2] = command[2];
            sx[3] = command[3];
            sx[4] = '\0';

        }
        else
        {
            strcpy(sx, command);
            done = true;
        }

        sscanf(sx, "%s", s);

        if (eof)
            ExitShogi();

        if (s[0] == '\0')
            continue;

        if (strcmp(s, CP[131]) == 0)   /* bd -- display board */
        {
            ClearScreen();
            UpdateDisplay(0, 0, 1, 0);
        }
        else if (strcmp(s, "post") == 0)
        {
            flag.post = !flag.post;
        }
        else if (strcmp(s, CP[129]) == 0)
        {
            /* noop */ ; /* alg */
        }
        else if ((strcmp(s, CP[180]) == 0)
                 || (strcmp(s, CP[216]) == 0))  /* quit exit */
        {
            flag.quit = true;
        }
#if !defined NOPOST
        else if (strcmp(s, CP[178]) == 0)  /* post */
        {
            flag.post = !flag.post;
        }
#endif
        else if (strcmp(s, CP[156]) == 0)  /* first */
        {
            ok = true;
        }
        else if (strcmp(s, CP[162]) == 0)  /* go */
        {
            ok = true;
            flag.force = false;

            if (computer == black)
            {
                computer = white;
                opponent = black;
            }
            else
            {
                computer = black;
                opponent = white;
            }
        }
        else if (strcmp(s, CP[166]) == 0)  /* help */
        {
            help();
        }
        else if (strcmp(s, CP[221]) == 0)  /* material */
        {
            flag.material = !flag.material;
        }
        else if (strcmp(s, CP[157]) == 0)  /* force */
        {
            flag.force = !flag.force;
            flag.bothsides = false;
        }
        else if (strcmp(s, CP[134]) == 0)  /* book */
        {
            Book = Book ? 0 : BOOKFAIL;
        }
        else if (strcmp(s, CP[172]) == 0)  /* new */
        {
            NewGame();
            UpdateDisplay(0, 0, 1, 0);
        }
        else if (strcmp(s, CP[171]) == 0)  /* list */
        {
            ListGame();
        }
        else if ((strcmp(s, CP[169]) == 0)
                 || (strcmp(s, CP[217]) == 0))  /* level clock */
        {
            SelectLevel(sx);
        }
        else if (strcmp(s, CP[165]) == 0)  /* hash */
        {
            flag.hash = !flag.hash;
        }
        else if (strcmp(s, CP[227]) == 0)  /* gamein */
        {
            flag.gamein = !flag.gamein;
        }
        else if (strcmp(s, CP[226]) == 0)  /* beep */
        {
            flag.beep = !flag.beep;
        }
        else if (strcmp(s, CP[197]) == 0)  /* time */
        {
            SetMachineTime(sx);
        }
        else if (strcmp(s, CP[228]) == 0)  /* otime */
        {
            SetOppTime(sx);
        }
        else if (strcmp(s, CP[33]) == 0)   /* Awindow */
        {
            ChangeAlphaWindow();
        }
        else if (strcmp(s, CP[39]) == 0)   /* Bwindow */
        {
            ChangeBetaWindow();
        }
        else if (strcmp(s, CP[183]) == 0)  /* rcptr */
        {
            flag.rcptr = !flag.rcptr;
        }
        else if (strcmp(s, CP[168]) == 0)  /* hint */
        {
            GiveHint();
        }
        else if (strcmp(s, CP[135]) == 0)  /* both */
        {
            flag.bothsides = !flag.bothsides;
            flag.force = false;
            Sdepth = 0;
            ElapsedTime(COMPUTE_AND_INIT_MODE);
            SelectMove(opponent, FOREGROUND_MODE);
            ok = true;
        }
        else if (strcmp(s, CP[185]) == 0)  /* reverse */
        {
            flag.reverse = !flag.reverse;
            ClearScreen();
            UpdateDisplay(0, 0, 1, 0);
        }
        else if (strcmp(s, CP[195]) == 0)  /* switch */
        {
            computer = computer ^ 1;
            opponent = opponent ^ 1;
            xwndw = (computer == black) ? WXWNDW : BXWNDW;
            flag.force = false;
            Sdepth = 0;
            ok = true;
        }
        else if (strcmp(s, CP[203]) == 0)  /* black */
        {
            computer = white;
            opponent = black;
            xwndw = WXWNDW;
            flag.force = false;
            Sdepth = 0;

            /*
             * ok = true; don't automatically start with black command
             */
        }
        else if (strcmp(s, CP[133]) == 0)  /* white */
        {
            computer = black;
            opponent = white;
            xwndw = BXWNDW;
            flag.force = false;
            Sdepth = 0;

            /*
             * ok = true; don't automatically start with white command
             */
        }
        else if (strcmp(s, CP[201]) == 0 && GameCnt > 0)   /* undo */
        {
            Undo();
        }
        else if (strcmp(s, CP[184]) == 0 && GameCnt > 1)   /* remove */
        {
            Undo();
            Undo();
        }
#ifdef EASY_OPENINGS
        else if ((strcmp(s, "?") == 0)
                 || (strcmp(s, "!") == 0)
                 || (strcmp(s, "~") == 0))
#else
        else if ((strcmp(s, "?") == 0)
                 || (strcmp(s, "!") == 0))
#endif
        {
            FlagMove(*s);
        }
        else if (strcmp(s, CP[160]) == 0)    /* get */
        {
            GetGame(command);
        }
        /*
        else if (strcmp(s, CP[189]) == 0) */   /* save */
      /*{
            SaveGame(command);
        }*/
        else if (strcmp(s, CP[151]) == 0)    /* depth */
        {
            ChangeSearchDepth();
        }
        else if (strcmp(s, CP[164]) == 0)    /* hashdepth */
        {
            ChangeHashDepth();
        }
        else if (strcmp(s, CP[182]) == 0)    /* random */
        {
            dither = DITHER;
        }
        else if (strcmp(s, CP[229]) == 0)    /* hard */
        {
            flag.easy = false;
        }
        else if (strcmp(s, CP[152]) == 0)    /* easy */
        {
            flag.easy = !flag.easy;
        }
        else if (strcmp(s, CP[230]) == 0)    /* tsume */
        {
            flag.tsume = !flag.tsume;
        }
        else if (strcmp(s, CP[143]) == 0)    /* contempt */
        {
            SetContempt();
        }
        else if (strcmp(s, CP[209]) == 0)    /* xwndw */
        {
            ChangeXwindow();
        }
        else if (strcmp(s, CP[186]) == 0)    /* rv */
        {
            flag.rv = !flag.rv;
            UpdateDisplay(0, 0, 1, 0);
        }
        else if (strcmp(s, CP[145]) == 0)    /* coords */
        {
            flag.coords = !flag.coords;
            UpdateDisplay(0, 0, 1, 0);
        }
        else if (strcmp(s, CP[193]) == 0)    /* stars */
        {
            flag.stars = !flag.stars;
            UpdateDisplay(0, 0, 1, 0);
        }
        else if (strcmp(s, CP[5]) == 0)          /* moves */
        {
            short temp;

#if MAXDEPTH > 3
            if (GameCnt > 0)
            {
                extern unsigned short PrVar[MAXDEPTH];

                SwagHt = (GameList[GameCnt].gmove == PrVar[1])
                    ? PrVar[2] : 0;
            }
            else
#endif
                SwagHt = 0;

            ShowMessage(CP[108]);  /* test movelist */
            temp = generate_move_flags;
            generate_move_flags = true;
            TestSpeed(MoveList, 1);
            generate_move_flags = temp;
            ShowMessage(CP[107]);  /* test capturelist */
            TestSpeed(CaptureList, 1);
            ShowMessage(CP[85]);   /* test score position */
            ExaminePosition(opponent);
            TestPSpeed(ScorePosition, 1);
        }
        else if (strcmp(s, CP[196]) == 0)    /* test */
        {
#ifdef SLOW_CPU
            ShowMessage(CP[108]); /* test movelist */
            TestSpeed(MoveList, 2000);
            ShowMessage(CP[107]); /* test capturelist */
            TestSpeed(CaptureList, 3000);
            ShowMessage(CP[85]); /* test score position */
            ExaminePosition(opponent);
            TestPSpeed(ScorePosition, 1500);
#else
            ShowMessage(CP[108]); /* test movelist */
            TestSpeed(MoveList, 20000);
            ShowMessage(CP[107]); /* test capturelist */
            TestSpeed(CaptureList, 30000);
            ShowMessage(CP[85]); /* test score position */
            ExaminePosition(opponent);
            TestPSpeed(ScorePosition, 15000);
#endif
        }
        else if (strcmp(s, CP[179]) == 0) /* p */
        {
            ShowPostnValues();
        }
        else if (strcmp(s, CP[148]) == 0)    /* debug */
        {
            DoDebug();
        }
        else
        {
            if (flag.mate)
            {
                ok = true;
            }
            else if ((ok = VerifyMove(s, VERIFY_AND_MAKE_MODE, &mv)))
            {
                /* check for repetition */
                short rpt = repetition();

                if (rpt >= 3)
                {
                    DRAW = CP[101];
                    ShowMessage(DRAW);
                    GameList[GameCnt].flags |= draw;

                        flag.mate = true;
                }
                else
                {
                    is_move = true;
                }
            }

            Sdepth = 0;
        }
    }

    ElapsedTime(COMPUTE_AND_INIT_MODE);

    if (flag.force)
    {
        computer = opponent;
        opponent = computer ^ 1;
    }

    signal(SIGINT, TerminateSearch);
}




void
SetTimeControl(void)
{
    if (TCflag)
    {
        TimeControl.moves[black] = TimeControl.moves[white] = TCmoves;
        TimeControl.clock[black] += 6000L * TCminutes + TCseconds * 100;
        TimeControl.clock[white] += 6000L * TCminutes + TCseconds * 100;
    }
    else
    {
        TimeControl.moves[black] = TimeControl.moves[white] = 0;
        TimeControl.clock[black] = TimeControl.clock[white] = 0;
    }

    flag.onemove = (TCmoves == 1);
    et = 0;
    ElapsedTime(COMPUTE_AND_INIT_MODE);
}
