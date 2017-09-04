/*

    search.c

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
 * FILE: search.c
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

#if !defined OLDTIME && defined HAVE_GETTIMEOFDAY
double pow(double x, double y);
#endif

short background = 0;
static short DepthBeyond;
unsigned short PrVar[MAXDEPTH];
extern short recycle, ISZERO;
extern void FlagString(unsigned short flags, char *s);

#ifdef NULLMOVE
short null;         /* Null-move already made or not */
short PVari;        /* Is this the PV */
#endif

short zwndw;



/* ............    MOVE GENERATION & SEARCH ROUTINES    .............. */



/*
 *  Check for draw by fourfold repetition
 *  (same side, same captures, same board).
 *  WARNING: this is not save (sp? safe?) yet due to possible hash collisions.
 */

short
repetition()
{
    short i, cnt = 0;

#ifndef NOREPETITION
    struct GameRec  *g;

    if (GameCnt > Game50 + 6)
    {
        for (i = GameCnt - 1; i >= Game50; i -= 2)
        {
            g = &GameList[i];

            if (g->hashkey == hashkey && g->hashbd == hashbd)
                cnt++;
        }
    }
#endif

    return cnt;
}



int plyscore, globalscore;


/*
 * Find the best move in the tree between indexes p1 and p2. Swap the best
 * move into the p1 element.
 */

int
pick(short p1, short p2)
{
    struct leaf  *p, *q, *r, *k;
    short s0;
    struct leaf temp;

    k = p = &Tree[p1];
    q = &Tree[p2];
    s0 = p->score;

    for (r = p + 1; r <= q; r++)
    {
        if ((r->score) > s0)
        {
            s0 = r->score;
            p = r;
        }
    }

    if (p != k)
    {
        temp = *p;
        *p = *k;
        *k = temp;
        return true;
    }

    return false;
}

int bookflag = false;
int Jscore = 0;

int TCcount;
int TCleft = 0;




/*
 * Select a move by calling function search() at progressively deeper ply
 * until time is up or a mate or draw is reached. An alpha-beta window of
 * -Awindow to +Bwindow points is set around the score returned from the
 * previous iteration. If Sdepth != 0 then the program has correctly
 * predicted the opponents move and the search will start at a depth of
 * Sdepth + 1 rather than a depth of 1.
 */

void
SelectMove(short side, SelectMove_mode iop)
{
    static short i, tempb, tempc, tempsf, tempst, xside, rpt;
    static short alpha, beta, score;
    static struct GameRec  *g;
    short sqking, in_check, blockable;

#ifdef BOOKTEST
    printf("hashbd = 0x%x (hashkey >> 16)|side = %d\n",
           hashbd, (hashkey >> 16)|side);
#endif

    flag.timeout = false;
    flag.back = false;
    flag.musttimeout = false;

    xside = side ^ 1;

#if ttblsz
    recycle = (GameCnt % rehash) - rehash;
#endif

    ExaminePosition(side);

    /* if background mode set to infinite */
    if (iop == BACKGROUND_MODE)
    {
        background = true;
        /* if background mode set response time to infinite */
        ResponseTime = 9999999;
    }
    else
    {
        player = side;
        SetResponseTime(side);
    }

#ifdef QUIETBACKGROUND
    if (!background)
#endif /* QUIETBACKGROUND */
        ShowResponseTime();

    ExtraTime = 0;

    score = ScorePosition(side);

#ifdef QUIETBACKGROUND
    if (!background)
#endif /* QUIETBACKGROUND */
        ShowSidetoMove();

#ifdef QUIETBACKGROUND
    if (!background)
#endif /* QUIETBACKGROUND */
        SearchStartStuff(side);

#ifdef HISTORY
    array_zero(history, sizeof_history);
#endif

    FROMsquare = TOsquare = -1;
    PV = 0;

    if (iop == FOREGROUND_MODE)
        hint = 0;

    /*
     * If the last move was the hint, select the computed answer to the
     * hint as first move to examine.
     */

#if MAXDEPTH > 3
    if (GameCnt > 0)
    {
        SwagHt = (GameList[GameCnt].gmove == PrVar[2]) ? PrVar[3] : 0;
    }
    else
#endif
        SwagHt = 0;


    for (i = 0; i < MAXDEPTH; i++)
        PrVar[i] = killr0[i] = killr1[i] = killr2[i] = killr3[i] = 0;

    /* set initial window for search */

    if (flag.tsume)
    {
        alpha =  -(SCORE_LIMIT + 999);
        beta = SCORE_LIMIT + 999;
    }
    else
    {
        alpha = score - ((computer == white) ? BAwindow : WAwindow);
        beta  = score + ((computer == white) ? BBwindow : WBwindow);
    }

    rpt = 0;
    TrPnt[1] = 0;
    root = &Tree[0];

    sqking = PieceList[side][0];
    in_check = (board[sqking] == king)
        ? SqAttacked(sqking, side^1, &blockable)
        : false;

    MoveList(side, 1, in_check, blockable);

    for (i = TrPnt[1]; i < TrPnt[2]; i++)
    {
        if (!pick(i, TrPnt[2] - 1))
            break;
    }

    /* Can I get a book move? */

    if (flag.regularstart && Book)
    {
        flag.timeout = bookflag = OpeningBook(&hint, side);

        if (TCflag)
            ResponseTime += ResponseTime;
    }

    /* Zero stats for hash table. */

    reminus = replus = 0;
    GenCnt = NodeCnt = ETnodes = EvalNodes = HashCnt
        = FHashAdd = HashAdd = FHashCnt = THashCol = HashCol = 0;

    globalscore = plyscore = score;
    Jscore = 0;
    zwndw = 20;


    /********************* main loop ********************************/

    Sdepth = (MaxSearchDepth < (MINDEPTH - 1))
        ? MaxSearchDepth
        : (MINDEPTH - 1);

    while (!flag.timeout)
    {
        /* go down a level at a time */
        Sdepth++;

#ifdef NULLMOVE
        null = 0;
        PVari = 1;
#endif

        /* terminate search at DepthBeyond ply past goal depth */
        if (flag.tsume)
            DepthBeyond = Sdepth;
        else
#if defined SLOW_CPU
            DepthBeyond = Sdepth + ((Sdepth == 1) ? 3 : 5);
#else
        DepthBeyond = Sdepth + ((Sdepth == 1) ? 7 : 11);
#endif

# ifdef QUIETBACKGROUND
        if (!background)
#endif /* QUIETBACKGROUND */
            ShowDepth(' ');

        /* search at this level returns score of PV */
        score = search(side, 1, Sdepth, alpha, beta, PrVar, &rpt);

        /* save PV as killer */
        for (i = 1; i <= Sdepth; i++)
            killr0[i] = PrVar[i];

        /* low search failure re-search with (-inf, score) limits  */
        if (score < alpha)
        {
            reminus++;
#ifdef QUIETBACKGROUND
            if (!background)
#endif /* QUIETBACKGROUND */
                ShowDepth('-');

            if (TCflag && TCcount < MAXTCCOUNTR)
            {
                if (hard_time_limit)
                    ExtraTime += (MAXTCCOUNTR - TCcount) * TCleft;
                else
                    ExtraTime += (8 * TCleft);

                TCcount = MAXTCCOUNTR - 1;
            }

            score = search(side, 1, Sdepth, -(SCORE_LIMIT + 999),
                           (SCORE_LIMIT + 999), PrVar, &rpt);
        }
        /* high search failure re-search with (score, +inf) limits */
        else if (score > beta && !(root->flags & exact))
        {
            replus++;
#ifdef QUIETBACKGROUND
            if (!background)
#endif /* QUIETBACKGROUND */
                ShowDepth('+');

            score = search(side, 1, Sdepth, -(SCORE_LIMIT + 999),
                           (SCORE_LIMIT + 999), PrVar, &rpt);
        }

        /**************** out of search ***********************************/
        CheckForTimeout(score, globalscore, Jscore, zwndw);

        /************************ time control ****************************/

        /* save PV as killer */
        for (i = 1; i <= Sdepth + 1; i++)
            killr0[i] = PrVar[i];

        if (!flag.timeout)
            Tscore[0] = score;

        /* if (!flag.timeout) */
        /*
          for (i = TrPnt[1] + 1; i < TrPnt[2]; i++)
          if (!pick (i, TrPnt[2] - 1))
          break;
        */

        /* if done or nothing good to look at quit */
        if ((root->flags & exact) || (score < -SCORE_LIMIT))
            flag.timeout = true;

        /* find the next best move put below root */

        if (!flag.timeout)
        {
#if !defined NODYNALPHA
            Jscore = (plyscore + score) >> 1;
#endif
            zwndw = 20 + abs(Jscore / 12);
            plyscore = score;

            /* recompute search window */
            beta = score + ((computer == white) ? BBwindow : WBwindow);
#if !defined NODYNALPHA
            alpha = ((Jscore < score) ? Jscore : score)
                - ((computer == white) ? BAwindow : WAwindow)
                - zwndw;
#else
            alpha = score - ((computer == white) ? BAwindow : WAwindow);
#endif
        }

#ifdef QUIETBACKGROUND
        if (!background)
#endif /* QUIETBACKGROUND */
            ShowResults(score, PrVar, '.');
    }

    /********************** end of main loop ***************************/

    /* background mode */
    if (iop == BACKGROUND_MODE)
        return;

    if (rpt >= 3)
    {
        root->flags |= draw;
        DRAW = CP[101];     /* Repetition */
    }
    else
    {
        /*
         * If there are no moves and we're not in check (stalemate) then
         * it's mate in shogi (whereas it's a draw in chess).
         */

        if (GameCnt == MAXMOVES)
        {
            root->flags |= draw;
            DRAW = CP[80];      /* Max Moves */
        }
    }

    /* not in book so set hint to guessed move for other side */
    if (!bookflag)
        hint = ((PrVar[1]) ? PrVar[2] : 0);

    /* if not mate or draw make move and output it */
    if (((score > -(SCORE_LIMIT + 999))
         && (rpt <= 3)) || (root->flags & draw))
    {
        MakeMove(side, &Tree[0], &tempb, &tempc,
                 &tempsf, &tempst, &INCscore);
        algbr(root->f, root->t, (short) root->flags);
    }
    else
    {
        algbr(0, 0, 0);       /* Zero move string when mate. */
        root->score = score;  /* When mate, ignore distinctions!
                               * --SMC */
    }

    g = &GameList[GameCnt];

    if ((g->flags & capture) && (g->piece == king))
        flag.mate = flag.illegal = true;

    /* If Time Control get the elapsed time */
    if (TCflag)
        ElapsedTime(COMPUTE_AND_INIT_MODE);

    /* update time control info */
    OutputMove();

    /* if mate set flag */
    if ((score == -(SCORE_LIMIT + 999) || score == (SCORE_LIMIT + 998)))
        flag.mate = true;

    /* add move to game list */
    g->score = score;
    g->nodes = NodeCnt;
    g->time = (et +50)/100;
    /* g->time = TCcount; */
    g->depth = Sdepth;

    /* update time control info */
    if (TCflag)
    {
        TimeControl.clock[side] -= (et + OperatorTime);
        timecomp[compptr] = (et + OperatorTime);

        /* finished our required moves - setup the next set */
        --TimeControl.moves[side];
    }

    /* check for end conditions */
    if ((root->flags & draw) /* && flag.bothsides */)
    {
        flag.mate = true;
    }
    else if (GameCnt == MAXMOVES)
    {
        flag.mate = true;
    }
    /* out of move store, you lose */
    else
    {
        /* switch to other side */
        player = xside;
    }

    /* if mate clear hint */
    if (flag.mate)
        hint = 0;

    Sdepth = 0;
}



/*
 * Perform an alpha-beta search to determine the score for the current
 * board position.  If depth <= 0 only capturing moves and responses to
 * check are generated and searched, otherwise all moves are processed. The
 * search depth is modified for check evasions, certain re-captures and
 * threats.  Extensions may continue for up to 11 ply beyond the nominal
 * search depth.
 */

int
search(short side,
       short ply,
       short depth,
       short alpha,
       short beta,
       unsigned short *bstline,
       short *rpt)
{
    short j, pnt;
    short tempb, tempc, tempsf, tempst;
    short xside, pbst, score, rcnt, in_check, blockable;
    unsigned short mv, nxtline[MAXDEPTH];
    struct leaf  *node, tmp;
    short best = -(SCORE_LIMIT + 3000);
    short bestwidth = 0;
    short mustcut;

#ifdef NULLMOVE
    short PVsave;
    short PVarisave;
#endif

    NodeCnt++;
    if (NodeCnt % 1000000 == 0 && verbose)
    {
        printf("nodes searched:%d\n",NodeCnt);
    }

    /* look every ZNODE nodes for a timeout */
#ifdef NULLMOVE
    if (!null)
    {
#endif
        if (NodeCnt > NodeCntLimit && NodeCntLimit > 0)
        {
            if (verbose)
            {
                printf("end search due to node count limit reached\n");
            }
            flag.back = false;
            flag.timeout = true;
            flag.musttimeout = false;
        }
        else if (NodeCnt > ETnodes)
        {
            ElapsedTime(COMPUTE_MODE);

            if (flag.back)
            {
                flag.back = false;
                flag.timeout = true;
                flag.musttimeout = false;
            }
            else if (TCflag || MaxResponseTime)
            {
                if ((et >= (ResponseTime + ExtraTime))
                    && (Sdepth > MINDEPTH))
                {
                    /* try to extend to finish ply */
                    if (flag.back || (TCflag && TCcount < MAXTCCOUNTX))
                    {
                        flag.back = false;
                        flag.musttimeout = true;
                        TCcount++;
                        ExtraTime += TCleft;
                    }
                    else
                    {
                        flag.back = false;
                        flag.timeout = true;
                        flag.musttimeout = false;
                    }
                }
            }
            else if (flag.back)
            {
                flag.back = false;
                flag.timeout = true;
                flag.musttimeout = false;
            }

#ifdef QUIETBACKGROUND
            if (!background)
#endif
                ShowResponseTime();
        }
        else if (!TCflag && flag.musttimeout && Sdepth > MINDEPTH)
        {
            flag.timeout = true;
            flag.musttimeout = false;
        }
#ifdef NULLMOVE
    }
#endif

    xside = side ^ 1;
    score = evaluate(side, ply, alpha, beta,
                     INCscore, &in_check, &blockable);

    /*
     * check for possible repitition if so call repitition - rpt is
     * repeat count
     */

    if ((ply <= Sdepth + 3) && rpthash[side][hashkey & 0xFF] > 0)
    {
        *rpt = repetition();

        /*
         * repeat position >3 don't need to return score it's taken
         * care of above
         */

        if (*rpt == 1)
        {
            score /= 3;
            score *= 2;
        }
        else if (*rpt == 2)
            score /= 2;
    }
    else
    {
        *rpt = 0;
    }

    /* score > SCORE_LIMIT its a draw or mate */
    if (score > SCORE_LIMIT)
    {
        bstline[ply] = 0;
        return score;
    }

    /* Do we need to add depth because of special conditions */
    /* if in check or in capture sequence search deeper */

    /***************** depth extensions *****************/

    if (depth > 0)
    {
        /* Allow opponent a chance to check again */
        if (in_check)
        {
            if (depth < 2)
                depth = 2;
        }
        else if (flag.rcptr
                 && (score > alpha) && (score < beta)
                 && (ply > 2)
                 && CptrFlag[ply - 1] && CptrFlag[ply - 2])
        {
            if (hard_time_limit)
            {
                if (!flag.timeout)
                    ++depth;
            }
            else
            {
                ++depth;
            }

        }
    }
    else
    {
        short timeout = 0;

        if (hard_time_limit)
            timeout = flag.timeout;

        if ((score >= alpha)
            && (in_check
                || ((!timeout && (hung[side] > 1))
                    && (ply == Sdepth + 1))))
        {
            depth = 1;
        }
        else if ((score <= beta)
                 && (((ply < Sdepth + 4) && (ply > 4))
                     && ChkFlag[ply - 2]
                     && ChkFlag[ply - 4]
                     && (ChkFlag[ply - 2] != ChkFlag[ply - 4])))
        {
            depth = 1;
        }
    }

    /***************************************************/
    /* try the local transition table if it's there */

#if ttblsz
    if (/* depth > 0 && */ flag.hash && ply > 1)
    {
        if (use_ttable
            && ProbeTTable(side, depth, ply, &alpha, &beta, &score) == true)
        {
            bstline[ply] = PV;
            bstline[ply + 1] = 0;

            if (beta == -((SCORE_LIMIT + 1000) * 2))
                return score;

            if (alpha > beta)
                return alpha;
        }

#ifdef HASHFILE
        /* ok try the transition file if its there */
        else if (hashfile
                 && (depth > HashDepth)
                 && (GameCnt < HashMoveLimit)
                 && (ProbeFTable(side, depth, ply, &alpha, &beta, &score)
                     == true))
        {
            PutInTTable(side, score, depth, ply, alpha, beta, PV);
            bstline[ply] = PV;
            bstline[ply + 1] = 0;

            if (beta == -((SCORE_LIMIT + 1000) * 2))
                return score;

            if (alpha > beta)
            {
                return alpha;
            }
        }
#endif /* HASHFILE */
    }
#endif /* ttblsz */

    if (TrPnt[ply] > (TREE - 300))
        mustcut = true;
    else
        mustcut = false;

    /*
     * If more then DepthBeyond ply past goal depth or at goal depth and
     * score > beta quit - means we are out of the window.
     */

    if (mustcut || (ply > DepthBeyond) || ((depth < 1) && (score > beta)))
        return score;

    /*
     * If below first ply and not at goal depth generate all moves else
     * only capture moves.
     */

    if (ply > 1)
    {
        if ((depth > 0) || (ply < (SDEPTHLIM))
            || (background && (ply < Sdepth + 2)))
            MoveList(side, ply, in_check, blockable);
        else
            CaptureList(side, ply, in_check, blockable);
    }

    /* no moves return what we have */

    /*
     * normally a search will continue til past goal and no more capture
     * moves exist
     */

    /* unless it hits DepthBeyond */
    if (TrPnt[ply] == TrPnt[ply + 1])
        return score;

    /* if not at goal set best = -inf else current score */
    best = (depth > 0) ? -(SCORE_LIMIT + 3000) : score;

#ifdef NULLMOVE

    PVarisave = PVari;

    /* CHECKME: is the & really an && here? */
    if (!null  &&                        /* no previous null-move */
        !PVari &&                        /* no null-move during the PV */
        (ply > 2) &                      /* not at ply 1 */
        (ply <= Sdepth) &&
        (depth > 3) &&
        !in_check)                       /* no check */
        /* enough material such that zugzwang is unlikely
         * but who knows which value is suitable? */
    {
        /*
           OK, we make a null move, i.e.  this means we have nothing to do
           but we have to keep the some arrays up to date otherwise gnushogi
           gets confused.  Maybe somebody knows exactly which information is
           important and which isn't.

           Another idea is that we try the null-move first and generate the
           moves later.  This may save time but we have to take care that
           PV and other variables contain the right value so that the move
           ordering works right.
        */

        struct GameRec  *g;

        nxtline[ply + 1] = 0;
        CptrFlag[ply] = 0;
        TesujiFlag[ply] = 0;
        Tscore[ply] = score;
        PVsave = PV;
        PV = 0;
        null = 1;
        g = &GameList[++GameCnt];
        g->hashkey = hashkey;
        g->hashbd = hashbd;
        FROMsquare = TOsquare = -1;
        g->Game50 = Game50;
        g->gmove = -1;
        g->flags = 0;
        g->piece = 0;
        g->color = neutral;

        best = -search(xside, ply + 1, depth - 2,
                       -beta - 1, -beta, nxtline, &rcnt);
        null = 0;
        PV = PVsave;
        GameCnt--;

        if (best < alpha)
        {
            best = -(SCORE_LIMIT + 3000);
        }
        else if (best > beta)
        {
            return best;
        }
        else
        {
            best = -(SCORE_LIMIT + 3000);
        }
    }
#endif

    /* if best so far is better than alpha set alpha to best */
    if (best > alpha)
        alpha = best;

    /********************** main loop ****************************/

    /* look at each move until no more or beta cutoff */
    for (pnt = pbst = TrPnt[ply];
         (pnt < TrPnt[ply + 1]) && (best <= beta);
         pnt++)
    {
        /* find the most interesting looking of the remaining moves */
        if (ply > 1)
            pick(pnt, TrPnt[ply + 1] - 1);

#ifdef NULLMOVE
        PVari = PVarisave && (pnt == TrPnt[ply]);  /* Is this the PV? */
#endif

        node = &Tree[pnt];

        /* is this a forbidden move */
        if (/* ply == 1 && */ node->score <= DONTUSE)
            continue;

        nxtline[ply + 1] = 0;

        /* if at top level */
#if !defined NOPOST
        if (ply == 1)
        {
/* at the top update search status */
            if (flag.post)
            {
#ifdef QUIETBACKGROUND
                if (!background)
#endif /* QUIETBACKGROUND */
                    ShowCurrentMove(pnt, node->f, node->t);
            }
        }
#endif

        if (!(node->flags & exact))
        {
            /* make the move and go deeper */

            MakeMove(side, node, &tempb, &tempc, &tempsf,
                     &tempst, &INCscore);

            /*
            printf("capture=%d\n",capture);
            printf("node->flags=%d\n",node->flags);
            */


            /* fix to set CptrFlag[ply] correctly
               CptrFlag[ply] is small_short (i.e signed char) and
               not big enough for (node->flags & capture)
               since capture is 0x0200 and node->flags is unsigned short*/
            /* CptrFlag[ply] = (node->flags & capture); */
            if (node->flags & capture)
            {
                CptrFlag[ply] = true;
            }
            else
            {
                CptrFlag[ply] = false;
            }


            /*printf("CptrFlag[ply]=%d\n",CptrFlag[ply]);*/

            TesujiFlag[ply] = (node->flags & tesuji)
                && (node->flags & dropmask);
            Tscore[ply] = node->score;
            PV = node->reply;

            node->score = -search(xside, ply + 1,
                                  (depth > 0) ? (depth - 1) : 0,
                                  -beta, -alpha,
                                  nxtline, &rcnt);

            /*
             * if(!flag.timeout)
             *     node->score = score;
             */

            node->width = ((ply % 2) == 1)
                ? (TrPnt[ply + 2] - TrPnt[ply + 1])
                : 0;

            if ((node->score > SCORE_LIMIT) || (node->score < -SCORE_LIMIT) )
                node->flags |= exact;
            else if (rcnt == 1)
                node->score /= 2;

            if (((rcnt >= 3)
                 || ((node->score == (SCORE_LIMIT + 999) - ply)
                     && !ChkFlag[ply])))
            {
                node->flags |= (draw | exact);
                DRAW = CP[58];  /* Draw */
                node->score = ((side == computer) ? contempt : -contempt);
            }

            node->reply = nxtline[ply + 1];

            /* reset to try next move */
            UnmakeMove(side, node, &tempb, &tempc, &tempsf, &tempst);
        }

        /* if best move so far */
        /* CHECKME: flag.timeout isn't valid if no hard time limit */
        if (!flag.timeout
            && ((node->score > best)
                || ((node->score == best) && (node->width > bestwidth))))
        {
            /*
             * All things being equal pick the denser part of the
             * tree.
             */
            bestwidth = node->width;

            /*
             * If not at goal depth and better than alpha and not
             * an exact score increment by depth.
             */

            if ((depth > 0) && (node->score > alpha)
                && !(node->flags & exact))
            {
                node->score += depth;
            }

            best = node->score;
            pbst = pnt;

            if (best > alpha)
                alpha = best;

            /* update best line */
            for (j = ply + 1; nxtline[j] > 0; j++)
                bstline[j] = nxtline[j];

            bstline[j] = 0;
            bstline[ply] = (node->f << 8) | node->t;

            /* if at the top */
            if (ply == 1)
            {
                /*
                 * If it's better than the root score make it the root.
                 */
                if ((best > root->score)
                    || ((best == root->score)
                        && (bestwidth > root->width)))
                {
                    tmp = Tree[pnt];

                    for (j = pnt - 1; j >= 0; j--)
                        Tree[j + 1] = Tree[j];

                    Tree[0] = tmp;
                    pbst = 0;
                }

#ifdef QUIETBACKGROUND
                if (!background)
                {
#endif /* QUIETBACKGROUND */
                    if (Sdepth > 2)
                    {
                        if (best > beta)
                        {
                            ShowResults(best, bstline, '+');
                        }
                        else if (best < alpha)
                        {
                            ShowResults(best, bstline, '-');
                        }
                        else
                        {
                            ShowResults (best, bstline, '&');
                        }
                    }
#ifdef QUIETBACKGROUND
                }
#endif
            }
        }

        if (flag.timeout)
            return Tscore[ply - 1];
    }

    /******************************************************/

    node = &Tree[pbst];
    mv = (node->f << 8) | node->t;

#ifdef NULLMOVE
    PVari = PVarisave;
#endif

    /*
     * We have a move so put it in local table - if it's already there
     * done else if not there or needs to be updated also put it in
     * hashfile
     */

#if ttblsz
    if (flag.hash && ply <= Sdepth && *rpt == 0 && best == alpha)
    {
#  ifdef HASHFILE /* MCV: warning: this confuses the formatter. */
        if (use_ttable
            && PutInTTable(side, best, depth, ply, alpha, beta, mv)
            && hashfile
            && (depth > HashDepth)
            && (GameCnt < HashMoveLimit))
#  else
        if (use_ttable
            && PutInTTable(side, best, depth, ply, alpha, beta, mv))
#  endif
        {
            PutInFTable(side, best, depth, ply,
                        alpha, beta, node->f, node->t);
        }
    }
#endif /* ttblsz */

    if (depth > 0)
    {
#if defined HISTORY
        unsigned short h, x;
        h = mv;

        if (history[x = hindex(side, h)] < HISTORYLIM)
            history[x] += (unsigned short) 1 << depth;
#endif

        if (node->t != (short)(GameList[GameCnt].gmove & 0xFF))
        {
            if (best <= beta)
            {
                killr3[ply] = mv;
            }
            else if (mv != killr1[ply])
            {
                killr2[ply] = killr1[ply];
                killr1[ply] = mv;
            }
        }

        killr0[ply] = ((best > SCORE_LIMIT) ? mv : 0);
    }

    return best;
}



/*
 * Update the PieceList and Pindex arrays when a piece is captured or when a
 * capture is unmade.
 */

void
UpdatePieceList(short side, short sq, UpdatePieceList_mode iop)
{
    short i;

    if (iop == REMOVE_PIECE)
    {
        PieceCnt[side]--;

        for (i = Pindex[sq]; i <= PieceCnt[side]; i++)
        {
            PieceList[side][i] = PieceList[side][i + 1];
            Pindex[PieceList[side][i]] = i;
        }
    }
    else if (board[sq] == king)
    {
        /* king must have index 0 */
        for (i = PieceCnt[side]; i >= 0; i--)
        {
            PieceList[side][i + 1] = PieceList[side][i];
            Pindex[PieceList[side][i + 1]] = i + 1;
        }

        PieceCnt[side]++;
        PieceList[side][0] = sq;
        Pindex[sq] = 0;
    }
    else
    {
        PieceCnt[side]++;
        PieceList[side][PieceCnt[side]] = sq;
        Pindex[sq] = PieceCnt[side];
    }
}



/* Make or Unmake drop move. */

void
drop(short side, short piece, short f, short t, short iop)
{
    if (iop == 1)
    {
        short n;
        board[t] = piece;
        color[t] = side;

#if !defined SAVE_SVALUE
        svalue[t] = 0;
#endif

        n = Captured[side][piece]--;

        UpdateDropHashbd(side, piece, n);
        UpdateHashbd(side, piece, -1, t);
        UpdatePieceList(side, t, ADD_PIECE);

        if (piece == pawn)
        {
            ++PawnCnt[side][column(t)];
        }

        Mvboard[t]++;
        HasPiece[side][piece]++;
    }
    else
    {
        short n;
        board[t] = no_piece;
        color[t] = neutral;
        n = ++Captured[side][piece];

        UpdateDropHashbd(side, piece, n);
        UpdateHashbd(side, piece, -1, t);
        UpdatePieceList(side, t, REMOVE_PIECE);

        if (piece == pawn)
            --PawnCnt[side][column(t)];

        Mvboard[t]--;
        HasPiece[side][piece]--;
    }
}


#ifdef HASHKEYTEST
int
CheckHashKey()
{
    unsigned int chashkey, chashbd;
    short side, sq;
    chashbd = chashkey = 0;

    for (sq = 0; sq < NO_SQUARES; sq++)
    {
        if (color[sq] != neutral)
        {
            chashbd ^= (*hashcode)[color[sq]][board[sq]][sq].bd;
            chashkey ^= (*hashcode)[color[sq]][board[sq]][sq].key;
        }

        /* hashcodes for initial board are 0 ! */
        if (Stcolor[sq] != neutral)
        {
            chashbd ^= (*hashcode)[Stcolor[sq]][Stboard[sq]][sq].bd;
            chashkey ^= (*hashcode)[Stcolor[sq]][Stboard[sq]][sq].key;
        }
    }

    for (side = 0; side <= 1; side++)
    {
        short piece;

        for (piece = 0; piece < NO_PIECES; piece++)
        {
            short n = Captured[side][piece];

            if (n > 0)
            {
                short i;

                for (i = 1; i <= n; i++)
                {
                    chashbd ^= (*drop_hashcode)[side][piece][i].bd;
                    chashkey ^= (*drop_hashcode)[side][piece][i].key;
                }
            }
        }
    }

    if (chashbd != hashbd)
        printf("chashbd %lu != hashbd %lu\n", chashbd, hashbd);

    if (chashkey != hashkey)
        printf("chashkey %lu != hashkey %lu\n", chashkey, hashkey);

    if (chashbd != hashbd || chashkey != hashkey)
        return 1;

    return 0;
}
#endif




/*
 * Update Arrays board[], color[], and Pindex[] to reflect the new board
 * position obtained after making the move pointed to by node. Also update
 * miscellaneous stuff that changes when a move is made.
 */

void
MakeMove(short side,
         struct leaf  *node,
         short *tempb,  /* piece at to square */
         short *tempc,  /* color of to square */
         short *tempsf, /* static value of piece on from */
         short *tempst, /* static value of piece on to */
         short *INCscore)   /* score increment */
{
    short f, t, xside;
    struct GameRec  *g;
    short fromb, fromc;

    xside = side ^ 1;
    g = &GameList[++GameCnt];
    g->hashkey = hashkey;
    g->hashbd = hashbd;
    FROMsquare = f = node->f;
    TOsquare = t = (node->t & 0x7f);
    *INCscore = (short)node->INCscore;
    g->Game50 = Game50;
    g->gmove = (f << 8) | node->t;
    g->flags = node->flags;

#ifdef HASHKEYTEST
    if (CheckHashKey())
    {
        short i;
        algbr(f, t, node->flags);
        printf("error before MakeMove: %s\n", mvstr[0]);
        UpdateDisplay(0, 0, 1, 0);

        for (i = 1; i <= GameCnt; i++)
        {
            movealgbr(GameList[i].gmove, mvstr[0]);
            printf("%d: %s\n", i, mvstr[0]);
        }

        exit(1);
    }
#endif

    rpthash[side][hashkey & 0xFF]++, ISZERO++;

    if (f > NO_SQUARES)
    {
        g->fpiece = (node->flags & pmask);
        g->piece = *tempb = no_piece;
        g->color = *tempc = neutral;

#if !defined SAVE_SVALUE
        *tempsf = 0;
        *tempst = svalue[t];
#endif

        (void)drop(side, g->fpiece, f, t, 1);
    }
    else
    {
#if !defined SAVE_SVALUE
        *tempsf = svalue[f];
        *tempst = svalue[t];
#endif

        g->fpiece = board[f];
        g->piece = *tempb = board[t];
        g->color = *tempc = color[t];
        fromb = board[f];
        fromc = color[f];

        if (*tempc != neutral)
        {
            /* Capture a piece */
            UpdatePieceList(*tempc, t, REMOVE_PIECE);

            /* if capture decrement pawn count */
            if (*tempb == pawn)
                --PawnCnt[*tempc][column(t)];

            mtl[xside] -= (*value)[stage][*tempb];
            HasPiece[xside][*tempb]--;

            {
                short n, upiece = unpromoted[*tempb];

                /* add "upiece" captured by "side" */
                n = ++Captured[side][upiece];

                UpdateDropHashbd(side, upiece, n);
                mtl[side] += (*value)[stage][upiece];
            }

            /* remove "*tempb" of "xside" from board[t] */
            UpdateHashbd(xside, *tempb, -1, t);

#if !defined SAVE_SVALUE
            *INCscore += *tempst; /* add value of catched piece
                                   * to own score */
#endif

            Mvboard[t]++;
        }

        color[t] = fromc;

#if !defined SAVE_SVALUE
        svalue[t] = svalue[f];
        svalue[f] = 0;
#endif

        Pindex[t] = Pindex[f];
        PieceList[side][Pindex[t]] = t;
        color[f] = neutral;
        board[f] = no_piece;

        if (node->flags & promote)
        {
            short tob;

            board[t] = tob = promoted[fromb];

            /* remove unpromoted piece from board[f] */
            UpdateHashbd(side, fromb, f, -1);

            /* add promoted piece to board[t] */
            UpdateHashbd(side, tob, -1, t);
            mtl[side] += value[stage][tob] - value[stage][fromb];

            if (fromb == pawn)
                --PawnCnt[side][column(f)];

            HasPiece[side][fromb]--;
            HasPiece[side][tob]++;

#if !defined SAVE_SVALUE
            *INCscore -= *tempsf;
#endif
        }
        else
        {
            board[t] = fromb;
            /* remove piece from board[f] and add it to board[t] */
            UpdateHashbd(side, fromb, f, t);
        }

        Mvboard[f]++;
    }

#ifdef HASHKEYTEST
    algbr(f, t, node->flags);

    if (CheckHashKey())
    {
        printf("error in MakeMove: %s\n", mvstr[0]);
        exit(1);
    }
#endif
}




/*
 * Take back a move.
 */

void
UnmakeMove(short side,
           struct leaf  *node,
           short *tempb,
           short *tempc,
           short *tempsf,
           short *tempst)
{
    short f, t, xside;

    xside = side ^ 1;
    f = node->f;
    t = node->t & 0x7f;
    Game50 = GameList[GameCnt].Game50;

    if (node->flags & dropmask)
    {
        (void)drop(side, (node->flags & pmask), f, t, 2);

#if !defined SAVE_SVALUE
        svalue[t] = *tempst;
#endif
    }
    else
    {
        short tob, fromb;

        color[f] = color[t];
        board[f] = tob = fromb = board[t];

#if !defined SAVE_SVALUE
        svalue[f] = *tempsf;
#endif

        Pindex[f] = Pindex[t];
        PieceList[side][Pindex[f]] = f;
        color[t] = *tempc;
        board[t] = *tempb;

#if !defined SAVE_SVALUE
        svalue[t] = *tempst;
#endif

        /* Undo move */
        if (node->flags & promote)
        {
            board[f] = fromb = unpromoted[tob];
            mtl[side] += value[stage][fromb] - value[stage][tob];

            if (fromb == pawn)
                ++PawnCnt[side][column(f)];

            HasPiece[side][fromb]++;
            HasPiece[side][tob]--;

            /* add unpromoted piece to board[f] */
            UpdateHashbd(side, fromb, f, -1);

            /* remove promoted piece from board[t] */
            UpdateHashbd(side, tob, -1, t);
        }
        else
        {
            if (fromb == pawn)
            {
                --PawnCnt[side][column(t)];
                ++PawnCnt[side][column(f)];
            };

            /* remove piece from board[t] and add it to board[f] */
            UpdateHashbd(side, fromb, f, t);
        }

        /* Undo capture */
        if (*tempc != neutral)
        {
            short n, upiece = unpromoted[*tempb];

            UpdatePieceList(*tempc, t, ADD_PIECE);

            if (*tempb == pawn)
                ++PawnCnt[*tempc][column(t)];

            mtl[xside] += (*value)[stage][*tempb];
            HasPiece[xside][*tempb]++;
            mtl[side] -= (*value)[stage][upiece];

            /* remove "upiece" captured by "side" */
            n = Captured[side][upiece]--;

            UpdateDropHashbd(side, upiece, n);

            /* replace captured piece on board[t] */
            UpdateHashbd(xside, *tempb, -1, t);
            Mvboard[t]--;
        }

        Mvboard[f]--;
    }

    GameCnt--;
    rpthash[side][hashkey & 0xFF]--, ISZERO--;

#ifdef HASHKEYTEST
    algbr(f, t, node->flags);

    if (CheckHashKey())
    {
        printf("error in UnmakeMove: %s\n", mvstr[0]);
        exit(1);
    }
#endif
}



/*
 * Scan thru the board seeing what's on each square. If a piece is found,
 * update the variables PieceCnt, PawnCnt, Pindex and PieceList. Also
 * determine the material for each side and set the hashkey and hashbd
 * variables to represent the current board position. Array
 * PieceList[side][indx] contains the location of all the pieces of either
 * side. Array Pindex[sq] contains the indx into PieceList for a given
 * square.
 */

void
InitializeStats(void)
{
    short i, sq;

    for (i = 0; i < NO_COLS; i++)
        PawnCnt[black][i] = PawnCnt[white][i] = 0;

    mtl[black] = mtl[white] = 0;
    PieceCnt[black] = PieceCnt[white] = 0;
    hashbd = hashkey = 0;

    for (sq = 0; sq < NO_SQUARES; sq++)
    {
        if (color[sq] != neutral)
        {
            mtl[color[sq]] += (*value)[stage][board[sq]];

            if (board[sq] == pawn)
                ++PawnCnt[color[sq]][column(sq)];

            Pindex[sq] = ((board[sq] == king) ? 0 : ++PieceCnt[color[sq]]);
            PieceList[color[sq]][Pindex[sq]] = sq;
            UpdateHashbd(color[sq], board[sq], sq, -1);
        }

        /* hashcodes for initial board are 0 ! */
        if (Stcolor[sq] != neutral)
            UpdateHashbd(Stcolor[sq], Stboard[sq], sq, -1);
    }

    {
        short side;

        for (side = 0; side <= 1; side++)
        {
            short piece;

            for (piece = 0; piece < NO_PIECES; piece++)
            {
                short n = Captured[side][piece];

                if (n > 0)
                {
                    Captured[side][piece] = 0;

                    for (i = 1; i <= n; i++)
                    {
                        ++Captured[side][piece];
                        UpdateDropHashbd(side, piece, i);
                        mtl[side] += (*value)[stage][piece];
                    }
                }
            }
        }
    }

#ifdef HASHKEYTEST
    if (CheckHashKey())
    {
        printf("error in InitializeStats\n");
        exit(1);
    }
#endif
}
