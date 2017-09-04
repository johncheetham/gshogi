/*

    rawdsp.c

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
 * FILE: rawdsp.c
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

#include <ctype.h>
#include <signal.h>

#if !defined(_WIN32)
#include <sys/param.h>
#include <sys/file.h>
#endif

#include <sys/types.h>

#include "gnushogi.h"
#include "rawdsp.h"

unsigned short MV[MAXDEPTH];
int MSCORE;
short winner;

int mycnt1, mycnt2;
char *DRAW;
extern char *InPtr;
extern short pscore[];


/****************************************
 * Trivial output functions.
 ****************************************/

void
ClearScreen(void)
{
    if (!barebones)
        printf("\n");
}


/* FIXME: change to ShowPrompt? */
void
PromptForMove(void)
{
    if (!barebones)
    {
        /* printf("\nYour move is? "); */
        printf("%s", CP[124]);
    }
}


void
ShowCurrentMove(short pnt, short f, short t)
{
}


void
ShowDepth(char ch)
{
    if (!barebones)
    {
        printf(CP[53], Sdepth, ch);   /* Depth = %d%c */
        printf("\n");
    }
}


void
ShowLine(unsigned short *bstline)
{
    int i;

    for (i = 1; bstline[i] > 0; i++)
    {
        if ((i > 1) && (i % 8 == 1))
            printf("\n                          ");

        algbr((short)(bstline[i] >> 8), (short)(bstline[i] & 0xFF), false);
        printf("%5s ", mvstr[0]);
    }

    printf("\n");
}


void
ShowMessage(char *s)
{
    if (verbose)
        printf("%s\n", s);
}


void
ShowPatternCount(short side, short n)
{
    if (flag.post)
        printf("%s matches %d pattern(s)\n", ColorStr[side], n);
}


void
ShowResponseTime(void)
{
}


void
ShowResults(short score, unsigned short *bstline, char ch)
{
    if (flag.post)
    {
        ElapsedTime(2);
        printf("%2d%c %6d %4d %8d  ",
               Sdepth, ch, score, et / 100, NodeCnt);
        ShowLine(bstline);
    }
}


void
ShowSidetoMove(void)
{
}


void
ShowStage(void)
{
    printf("stage = %d\n", stage);
    printf("balance[black] = %d balance[white] = %d\n",
           balance[black], balance[white]);
}

/****************************************
 * End of trivial output routines.
 ****************************************/


void
Initialize(void)
{
    mycnt1 = mycnt2 = 0;

    if (hard_time_limit)
    {
        if (!TCflag && (MaxResponseTime == 0))
            MaxResponseTime = 15L * 100L;
    }
}



void
ExitShogi(void)
{
    /* CHECKME: what purpose does this next statement serve? */
    signal(SIGTERM, SIG_IGN);

    if (!nolist)
        ListGame();
}


void
TerminateSearch(int sig)
{
#ifdef INTERRUPT_TEST
    ElapsedTime(INIT_INTERRUPT_MODE);
#endif

    if (!flag.timeout)
        flag.back = true; /* previous: flag.timeout = true; */

    flag.bothsides = false;
}



void
help(void)
{
    ClearScreen();
    /* printf("SHOGI command summary\n"); */
    printf("%s", CP[40]);
    printf("----------------------------------"
           "------------------------------\n");
    /* printf("7g7f      move from 7g to 7f      quit
     * Exit Shogi\n"); */
    printf("%s", CP[158]);
    /* printf("S6h       move silver to 6h       beep
     * turn %s\n", (flag.beep) ? "off" : "on"); */
    printf(CP[86], (flag.beep) ? CP[92] : CP[93]);
    /* printf("2d2c+     move from 2d to 2c and promote\n"); */
    printf(CP[128], (flag.material) ? CP[92] : CP[93]);
    /* printf("P*5e      drop pawn to 5e         easy
     * turn %s\n", (flag.easy) ? "off" : "on"); */
    printf(CP[173], (flag.easy) ? CP[92] : CP[93]);
    /* printf("                                  hash
     * turn %s\n", (flag.hash) ? "off" : "on"); */
    printf(CP[174], (flag.hash) ? CP[92] : CP[93]);
    /* printf("bd        redraw board            reverse
     * board display\n"); */
    printf("%s", CP[130]);
    /* printf("list      game to shogi.lst       book
     * turn %s used %d of %d\n", (Book) ? "off" : "on", bookcount); */
    printf(CP[170], (Book) ? CP[92] : CP[93], bookcount, booksize);
    /* printf("undo      undo last ply           remove
     * take back a move\n"); */
    printf("%s", CP[200]);
    /* printf("edit      edit board              force
     * enter game moves\n"); */
    printf("%s", CP[153]);
    /* printf("switch    sides with computer     both
     * computer match\n"); */
    printf("%s", CP[194]);
    /* printf("black     computer plays black    white
     * computer plays white\n"); */
    printf("%s", CP[202]);
    /* printf("depth     set search depth        clock
     * set time control\n"); */
    printf("%s", CP[149]);
    /* printf("post      principle variation     hint
     * suggest a move\n"); */
    printf("%s", CP[177]);
    /* printf("save      game to file            get
     * game from file\n"); */
    printf("%s", CP[188]);
    printf("xsave     pos. to xshogi file     xget"
           "      pos. from xshogi file\n");
    /* printf("random    randomize play          new
     * start new game\n"); */
    printf("%s", CP[181]);
    printf("--------------------------------"
           "--------------------------------\n");
    /* printf("Computer: %-12s Opponent:            %s\n", */
    printf(CP[46],
           ColorStr[computer], ColorStr[opponent]);
    /* printf("Depth:    %-12d Response time:       %d sec\n", */
    printf(CP[51],
           MaxSearchDepth, MaxResponseTime/100);
    /* printf("Random:   %-12s Easy mode:           %s\n", */
    printf(CP[99],
           (dither) ? CP[93] : CP[92], (flag.easy) ? CP[93] : CP[92]);
    /* printf("Beep:     %-12s Transposition file: %s\n", */
    printf(CP[36],
           (flag.beep) ? CP[93] : CP[92], (flag.hash) ? CP[93] : CP[92]);
    /* printf("Tsume:    %-12s Force:               %s\n")*/
    printf(CP[232],
           (flag.tsume) ? CP[93] : CP[92], (flag.force) ? CP[93] : CP[92]);
    /* printf("Time Control %s %d moves %d seconds %d opr %d
     * depth\n", (TCflag) ? "ON" : "OFF", */
    printf(CP[110],
           (TCflag) ? CP[93] : CP[92],
           TimeControl.moves[black], TimeControl.clock[black] / 100,
           TCadd/100, MaxSearchDepth);

    signal(SIGINT, TerminateSearch);
}


void
SearchStartStuff(short side)
{
    signal(SIGINT, TerminateSearch);

    if (flag.post)
    {
        printf(CP[123],
               GameCnt/2 + 1,
               ResponseTime, TimeControl.clock[side]);
    }
}



void
OutputMove(void)
{
    if (flag.illegal)
    {
        printf("%s\n", CP[225]);
        return;
    }

    if (mvstr[0][0] == '\0')
        goto nomove;

    if (verbose)
    {
        printf("%d. ... %s\n", ++mycnt1, mvstr[0]);
    }

 nomove:
    if ((root->flags & draw) || (root->score == -(SCORE_LIMIT + 999))
        || (root->score == (SCORE_LIMIT + 998)))
        goto summary;

    if (flag.post)
    {
        short h, l, t;

        h = TREE;
        l = 0;
        t = TREE >> 1;

        while (l != t)
        {
            if (Tree[t].f || Tree[t].t)
                l = t;
            else
                h = t;

            t = (l + h) >> 1;
        }

        /* printf("Nodes %ld Tree %d Eval %ld
         * Rate %ld RS high %ld low %ld\n", */
        printf(CP[89], GenCnt, NodeCnt, t, EvalNodes,
               (et > 100) ? (NodeCnt / (et / 100)) : 0,
               EADD, EGET, reminus, replus);

        /* printf("Hin/Hout/Coll/Fin/Fout =
         * %ld/%ld/%ld/%ld/%ld\n", */
        printf(CP[71],
               HashAdd, HashCnt, THashCol, HashCol, FHashCnt, FHashAdd);
    }

    UpdateDisplay(root->f, root->t, 0, root->flags);

    /* printf("My move is: %s\n", mvstr[0]); */
    if (verbose)
    {
        printf(CP[83], mvstr[0]);
    }

    /*
    if (flag.beep)
        printf("%c", 7);*/


 summary:
    if (root->flags & draw)
    {
        /*  printf("Drawn game!\n"); */
        printf("%s", CP[57]);
        winner = neutral + 1;
    }
    else if (root->score == -(SCORE_LIMIT + 999))
    {
        printf("%s mates!\n", ColorStr[opponent]);
        winner = opponent + 1;
    }
    else if (root->score == (SCORE_LIMIT + 998))
    {
        printf("%s mates!\n", ColorStr[computer]);
        winner = computer + 1;
    }
#ifdef VERYBUGGY
    else if (!barebones && (root->score < -SCORE_LIMIT))
    {
        printf("%s has a forced mate in %d moves!\n",
               ColorStr[opponent], SCORE_LIMIT + 999 + root->score - 1);
    }
    else if (!barebones && (root->score > SCORE_LIMIT))
    {
        printf("%s has a forced mate in %d moves!\n",
               ColorStr[computer], SCORE_LIMIT + 998 - root->score - 1);
    }
#endif /* VERYBUGGY */
}


void
UpdateDisplay(short f, short t, short redraw, short isspec)
{

    short r, c, l, m;

    if (redraw && verbose)
    {
        printf("\n");
        r = (short)(TimeControl.clock[black] / 6000);
        c = (short)((TimeControl.clock[black] % 6000) / 100);
        l = (short)(TimeControl.clock[white] / 6000);
        m = (short)((TimeControl.clock[white] % 6000) / 100);
        /* printf("Black %d:%02d  White %d:%02d\n", r, c, l, m); */
        printf(CP[116], r, c, l, m);
        printf("\n");

        for (r = (NO_ROWS - 1); r >= 0; r--)
        {
            for (c = 0; c <= (NO_COLS - 1); c++)
            {
                char pc;
                l = ((flag.reverse)
                     ? locn((NO_ROWS - 1) - r, (NO_COLS - 1) - c)
                     : locn(r, c));
                pc = (is_promoted[board[l]] ? '+' : ' ');

                if (color[l] == neutral)
                    printf(" -");
                else if (color[l] == black)
                    printf("%c%c", pc, qxx[board[l]]);
                else
                    printf("%c%c", pc, pxx[board[l]]);
            }

            printf("\n");
        }

        printf("\n");
        {
            short side;

            for (side = black; side <= white; side++)
            {
                short piece, c;
                printf((side == black)?"black ":"white ");

                for (piece = pawn; piece <= king; piece++)
                {
                    if ((c = Captured[side][piece]))
                        printf("%i%c ", c, pxx[piece]);
                }

                printf("\n");
            }
        }
    }
}



void
ChangeAlphaWindow(void)
{
    int rc;

    printf("WAwindow: ");
    rc = scanf("%hd", &WAwindow);
    printf("BAwindow: ");
    rc = scanf("%hd", &BAwindow);
}



void
ChangeBetaWindow(void)
{
    int rc;

    printf("WBwindow: ");
    rc = scanf("%hd", &WBwindow);
    printf("BBwindow: ");
    rc = scanf("%hd", &BBwindow);
}



void
GiveHint(void)
{
    if (hint)
    {
        algbr((short) (hint >> 8), (short) (hint & 0xFF), false);
        printf(CP[72], mvstr[0]);   /*hint*/
    }
    else
        printf("%s", CP[223]);
}



void
SelectLevel(char *sx)
{

    char T[NO_SQUARES + 1], *p, *q;
    char *rcc;

    if ((p = strstr(sx, CP[169])) != NULL)
        p += strlen(CP[169]);
    else if ((p = strstr(sx, CP[217])) != NULL)
        p += strlen(CP[217]);

    strcat(sx, "XX");
    q = T;
    *q = '\0';

    for (; *p != 'X'; *q++ = *p++);

    *q = '\0';

    /* line empty ask for input */
    if (!T[0])
    {
        printf("%s", CP[61]);
        rcc = fgets(T, NO_SQUARES + 1, stdin);
        strcat(T, "XX");
    }

    /* skip blackspace */
    for (p = T; *p == ' '; p++) ;

    /* could be moves or a fischer clock */
    if (*p == 'f')
    {
        /* its a fischer clock game */
        p++;
        TCminutes = (short)strtol(p, &q, 10);
        TCadd = (short)strtol(q, NULL, 10) *100;
        TCseconds = 0;
        TCmoves = 50;
    }
    else
    {
        /* regular game */
        TCadd = 0;
        TCmoves = (short)strtol(p, &q, 10);
        TCminutes = (short)strtol(q, &q, 10);

        if (*q == ':')
            TCseconds = (short)strtol(q + 1, (char **) NULL, 10);
        else
            TCseconds = 0;

#ifdef OPERATORTIME
        printf(CP[94]);
        rc = scanf("%hd", &OperatorTime);
#endif

        if (TCmoves == 0)
        {
            TCflag = false;
            MaxResponseTime = TCminutes*60L * 100L + TCseconds * 100L;
            TCminutes = TCseconds = 0;
        }
        else
        {
            TCflag = true;
            MaxResponseTime = 0;
        }
    }

    TimeControl.clock[black] = TimeControl.clock[white] = 0;
    SetTimeControl();

}




void
ChangeSearchDepth(void)
{
    int rc;

    printf("depth = ");
    rc = scanf("%hd", &MaxSearchDepth);
    TCflag = !(MaxSearchDepth > 0);
}




void
ChangeHashDepth(void)
{
    int rc;

    printf("hashdepth = ");
    rc = scanf("%hd", &HashDepth);
    printf("MoveLimit = ");
    rc = scanf("%hd", &HashMoveLimit);
}



void
SetContempt(void)
{
    int rc;

    printf("contempt = ");
    rc = scanf("%hd", &contempt);
}



void
ChangeXwindow(void)
{
    int rc;

    printf("xwndw = ");
    rc = scanf("%hd", &xwndw);
}


/*
 * ShowPostnValue(short sq)
 * must have called ExaminePosition() first
 */

void
ShowPostnValue(short sq)
{
    short score;
    score = ScorePosition(color[sq]);

    if (color[sq] != neutral)
    {
#if defined SAVE_SVALUE
        printf("???%c ", (color[sq] == white)?'b':'w');
#else
        printf("%3d%c ", svalue[sq], (color[sq] == white)?'b':'w');
#endif
    }
    else
    {
        printf(" *   ");
    }
}



void
DoDebug(void)
{
    short c, p, sq, tp, tc, tsq, score, j, k;
    char s[40];
    int rc;

    ExaminePosition(opponent);
    ShowMessage(CP[65]);
    rc = scanf("%s", s);
    c = neutral;

    if ((s[0] == CP[9][0]) || (s[0] == CP[9][1]))    /* w W */
        c = black;

    if ((s[0] == CP[9][2]) || (s[0] == CP[9][3]))    /* b B */
        c = white;

    for (p = king; p > no_piece; p--)
    {
        if ((s[1] == pxx[p]) || (s[1] == qxx[p]))
            break;
    }

    if (p > no_piece)
    {
        for (j = (NO_ROWS - 1); j >= 0; j--)
        {
            for (k = 0; k < (NO_COLS); k++)
            {
                sq = j*(NO_COLS) + k;
                tp = board[sq];
                tc = color[sq];
                board[sq] = p;
                color[sq] = c;
                tsq = PieceList[c][1];
                PieceList[c][1] = sq;
                ShowPostnValue(sq);
                PieceList[c][1] = tsq;
                board[sq] = tp;
                color[sq] = tc;
            }

            printf("\n");
        }
    }

    score = ScorePosition(opponent);

    for (j = (NO_ROWS - 1); j >= 0; j--)
    {
        for (k = 0; k < (NO_COLS); k++)
        {
            sq = j*(NO_COLS) + k;

            if (color[sq] != neutral)
            {
#if defined SAVE_SVALUE
                printf("%?????%c ", (color[sq] == white)?'b':'w');
#else
                printf("%5d%c ", svalue[sq], (color[sq] == white)?'b':'w');
#endif
            }
            else
            {
                printf("    *  ");
            }
        }

        printf("\n");
    }

    printf("stage = %d\n", stage);
    printf(CP[103], score,
           mtl[computer], pscore[computer], GameType[computer],
           mtl[opponent], pscore[opponent], GameType[opponent]);
}



void
ShowPostnValues(void)
{
    short sq, score, j, k;
    ExaminePosition(opponent);

    for (j = (NO_ROWS - 1); j >= 0; j--)
    {
        for (k = 0; k < NO_COLS; k++)
        {
            sq = j * NO_COLS + k;
            ShowPostnValue(sq);
        }

        printf("\n");
    }

    score = ScorePosition(opponent);
    printf(CP[103], score,
           mtl[computer], pscore[computer], GameType[computer],
           mtl[opponent], pscore[opponent], GameType[opponent]);
    printf("\nhung black %d hung white %d\n", hung[black], hung[white]);
}
