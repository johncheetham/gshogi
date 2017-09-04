/*

    util.c

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
 * FILE: util.c
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

unsigned int TTadd = 0;
short recycle;
short ISZERO = 1;


int
parse(FILE * fd, unsigned short *mv, short side, char *opening)
{
    int c, i, r1, r2, c1, c2;
    char s[128];
    char *p;

    while (((c = getc(fd)) == ' ') || (c == '\n'));

    i = 0;
    s[0] = (char) c;

    if (c == '!')
    {
        p = opening;
        do
        {
            *p++ = c;
            c = getc(fd);

            if ((c == '\n') || (c == EOF))
            {
                *p = '\0';
                return 0;
            }
        }
        while (true);
    }

    while ((c != '?') && (c != ' ')
           && (c != '\t') && (c != '\n') && (c != EOF))
    {
        s[++i] = (char) (c = getc(fd));
    }

    s[++i] = '\0';

    if (c == EOF)
        return (-1);

    if ((s[0] == '!') || (s[0] == ';') || (i < 3))
    {
        while ((c != '\n') && (c != EOF))
            c = getc(fd);

        return 0;
    }

    c1 = '9' - s[0];
    r1 = 'i' - s[1];
    c2 = '9' - s[2];
    r2 = 'i' - s[3];
    *mv = (locn(r1, c1) << 8) | locn(r2, c2);

    if (c == '?')
    {
        /* Bad move, not for the program to play */
        *mv |= 0x8000;      /* Flag it ! */
        c = getc(fd);
    }

    return 1;
}


/*
 * The field of a hashtable is computed as follows:
 *   if sq is on board (< NO_SQUARES) the field gets the value
 *     of the piece on the square sq;
 *   if sq is off board (>= NO_SQUARES) it is a catched figure,
 *     and the field gets the number of catched pieces for
 *     each side.
 */

inline unsigned char
CB(short sq)
{
    short i = sq;

    if (i < NO_SQUARES)
    {
        return ((color[i] == white) ? (0x80 | board[i]) : board[i]);
    }
    else
    {
        i -= NO_SQUARES;
        return ((Captured[black][i] << 4) | Captured[white][i]);
    }
}




#if ttblsz

/*
 * Look for the current board position in the transposition table.
 */

int
ProbeTTable (short side,
             short depth,
             short ply,
             short *alpha,
             short *beta,
             short *score)
{
    struct hashentry  *ptbl;
    /*unsigned*/ short i = 0;  /* to match new type of rehash --tpm */

    ptbl = &ttable[side][hashkey % ttblsize];

    while (true)
    {
        if ((ptbl->depth) == 0)
            return false;

        if (ptbl->hashbd == hashbd)
            break;

        if (++i > rehash)
            return false;

        ptbl++;
    }

    /* rehash max rehash times */

    if (((short)(ptbl->depth) >= (short) depth))
    {
#ifdef HASHTEST
        for (i = 0; i < PTBLBDSIZE; i++)
        {
            if (ptbl->bd[i] != CB(i))
            {
                HashCol++;

                if (!barebones)
                {
                    ShowMessage(CP[199]);    /* ttable collision detected */
                    ShowBD(ptbl->bd);
                    printf("hashkey = 0x%x, hashbd = 0x%x\n",
                           hashkey, hashbd);
                }

                break;
            }
        }
#endif /* HASHTEST */


        PV = SwagHt = ptbl->mv;

        HashCnt++;

        if (ptbl->flags & truescore)
        {
            *score = ptbl->score;
            /* adjust *score so moves to mate is from root */

            if (*score > SCORE_LIMIT)
                *score -= ply;
            else if (*score < -SCORE_LIMIT)
                *score += ply;

            *beta = -2 * (SCORE_LIMIT + 1000);
        }
        else if (ptbl->flags & lowerbound)
        {
            if (ptbl->score > *alpha)
                *alpha = ptbl->score - 1;
        }

        return true;
    }

    return false;
}



/*
 * Store the current board position in the transposition table.
 */

int
PutInTTable(short side,
            short score,
            short depth,
            short ply,
            short alpha,
            short beta,
            unsigned short mv)
{
    struct hashentry  *ptbl;
    /*unsigned*/ short i = 0;  /* to match new type of rehash --tpm */

    ptbl = &ttable[side][hashkey % ttblsize];

    while (true)
    {
        if ((ptbl->depth) == 0 || ptbl->hashbd == hashbd)
            break;

        if (++i > rehash)
        {
            THashCol++;
            ptbl += recycle;

            break;
        }

        ptbl++;
    }

    TTadd++;
    HashAdd++;

    /* adjust score so moves to mate is from this ply */

    if (score > SCORE_LIMIT)
        score += ply;
    else if (score < -SCORE_LIMIT)
        score -= ply;

    ptbl->hashbd = hashbd;
    ptbl->depth = (unsigned char) depth;
    ptbl->score = score;
    ptbl->mv = mv;

    if (score > beta)
    {
        ptbl->flags = lowerbound;
        ptbl->score = beta + 1;
    }
    else
    {
        ptbl->flags = truescore;
    }

#if defined HASHTEST
    for (i = 0; i < PTBLBDSIZE; i++)
        ptbl->bd[i] = CB(i);
#endif /* HASHTEST */

    return true;
}



void
ZeroTTable(void)
{
    array_zero(ttable[black], (ttblsize + rehash));
    array_zero(ttable[white], (ttblsize + rehash));

#ifdef CACHE
    array_zero(etab[0], sizeof(struct etable)*(size_t)ETABLE);
    array_zero(etab[1], sizeof(struct etable)*(size_t)ETABLE);
#endif

    TTadd = 0;
}




#ifdef HASHFILE
int
Fbdcmp(unsigned char *a, unsigned char *b)
{
    int i;

    for (i = 0; i < PTBLBDSIZE; i++)
    {
        if (a[i] != b[i])
            return false;
    }

    return true;
}



/*
 * Look for the current board position in the persistent transposition table.
 */

int
ProbeFTable(short side,
            short depth,
            short ply,
            short *alpha,
            short *beta,
            short *score)
{
    short i;
    unsigned int hashix;
    struct fileentry new, t;
    int rc;

    hashix = ((side == black) ? (hashkey & 0xFFFFFFFE)
              : (hashkey | 1)) % filesz;

    for (i = 0; i < PTBLBDSIZE; i++)
        new.bd[i] = CB(i);

    new.flags = 0;

    for (i = 0; i < frehash; i++)
    {
        fseek(hashfile,
              sizeof(struct fileentry) * ((hashix + 2 * i) % (filesz)),
              SEEK_SET);
        rc = fread(&t, sizeof(struct fileentry), 1, hashfile);

        if (!t.depth)
            break;

        if (!Fbdcmp(t.bd, new.bd))
            continue;

        if (((short) t.depth >= depth)
            && (new.flags == (unsigned short)(t.flags
                                              & (kingcastle | queencastle))))
        {
            FHashCnt++;

            PV = (t.f << 8) | t.t;
            *score = (t.sh << 8) | t.sl;

            /* adjust *score so moves to mate is from root */
            if (*score > SCORE_LIMIT)
                *score -= ply;
            else if (*score < -SCORE_LIMIT)
                *score += ply;

            if (t.flags & truescore)
            {
                *beta = -((SCORE_LIMIT + 1000)*2);
            }
            else if (t.flags & lowerbound)
            {
                if (*score > *alpha)
                    *alpha = *score - 1;
            }
            else if (t.flags & upperbound)
            {
                if (*score < *beta)
                    *beta = *score + 1;
            }

            return (true);
        }
    }

    return (false);
}



/*
 * Store the current board position in the persistent transposition table.
 */

void
PutInFTable(short side,
            short score,
            short depth,
            short ply,
            short alpha,
            short beta,
            unsigned short f,
            unsigned short t)
{
    unsigned short i;
    unsigned int hashix;
    struct fileentry new, tmp;
    int rc;

    hashix = ((side == black) ? (hashkey & 0xFFFFFFFE)
              : (hashkey | 1)) % filesz;

    for (i = 0; i < PTBLBDSIZE; i++)
        new.bd[i] = CB(i);

    new.f = (unsigned char) f;
    new.t = (unsigned char) t;

    if (score < alpha)
        new.flags = upperbound;
    else
        new.flags = ((score > beta) ? lowerbound : truescore);

    new.depth = (unsigned char) depth;

    /* adjust *score so moves to mate is from root */
    if (score > SCORE_LIMIT)
        score += ply;
    else if (score < -SCORE_LIMIT)
        score -= ply;


    new.sh = (unsigned char) (score >> 8);
    new.sl = (unsigned char) (score & 0xFF);

    for (i = 0; i < frehash; i++)
    {
        fseek(hashfile,
              sizeof(struct fileentry) * ((hashix + 2 * i) % (filesz)),
              SEEK_SET);

        if (!fread(&tmp, sizeof(struct fileentry), 1, hashfile) )
        {
            perror("hashfile");
            exit(1);
        }

        if (tmp.depth && !Fbdcmp(tmp.bd, new.bd))
            continue;

        if (tmp.depth == depth)
            break;

        if (!tmp.depth || ((short) tmp.depth < depth))
        {
            fseek(hashfile,
                  sizeof(struct fileentry) * ((hashix + 2 * i) % (filesz)),
                  SEEK_SET);

            rc = fwrite(&new, sizeof(struct fileentry), 1, hashfile);
            FHashAdd++;

            break;
        }
    }
}

#endif /* HASHFILE */
#endif /* ttblsz */



void
ZeroRPT(void)
{
    if (ISZERO )
    {
        array_zero(rpthash, sizeof(rpthash));
        ISZERO = 0;
    }
}



#if defined CACHE

/*
 * Store the current eval position in the transposition table.
 */

void
PutInEETable(short side, int score)
{
    struct etable  *ptbl;

    ptbl = &(*etab[side])[hashkey % (ETABLE)];
    ptbl->ehashbd = hashbd;
    ptbl->escore[black] = pscore[black];
    ptbl->escore[white] = pscore[white];
    ptbl->hung[black] = hung[black];
    ptbl->hung[white] = hung[white];
    ptbl->score = score;

#if !defined SAVE_SSCORE
    array_copy(svalue, &(ptbl->sscore), sizeof(svalue));
#endif

    EADD++;

    return;
}



/* Get an evaluation from the transposition table */

int
CheckEETable(short side)
{
    struct etable  *ptbl;

    ptbl = &(*etab[side])[hashkey % (ETABLE)];

    if (hashbd == ptbl->ehashbd)
        return true;

    return false;
}



/* Get an evaluation from the transposition table */

int
ProbeEETable(short side, short *score)
{
    struct etable  *ptbl;

    ptbl = &(*etab[side])[hashkey % (ETABLE)];

    if (hashbd == ptbl->ehashbd)
    {
        pscore[black] = ptbl->escore[black];
        pscore[white] = ptbl->escore[white];

#if defined SAVE_SSCORE
        array_zero(svalue, sizeof(svalue));
#else
        array_copy(&(ptbl->sscore), svalue, sizeof(svalue));
#endif

        *score = ptbl->score;
        hung[black] = ptbl->hung[black];
        hung[white] = ptbl->hung[white];

        EGET++;

        return true;
    }

    return false;
}

#endif /* CACHE */
