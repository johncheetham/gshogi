/*

    attacks.c

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
 * FILE: attacks.c
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


#define CHECK_DISTANCE

/*
 * See if any piece with color 'side' attacks sq.
 * *blockable == attack could be blocked by drop
 */

int
SqAttacked(short square, short side, short *blockable)
{
#ifdef SAVE_NEXTPOS
    short d;
#else
    unsigned char *ppos, *pdir;
#endif

    short u, ptyp;

    if (MatchSignature(threats_signature[side]))
    {
        *blockable = true; /* don't know */
        return Anyattack(side, square);
    }

    /*
     * First check neighbouring squares,
     * then check Knights.
     * then check Bishops,
     * then (last) check Rooks,
     */

    *blockable = false;

    /* try a capture from direct neighboured squares */

    ptyp = ptype[black][king];

#ifdef SAVE_NEXTPOS
    u = first_direction(ptyp, &d, square);
#else
    pdir = (*nextdir[ptyp])[square];
    u = pdir[square];
#endif

    do
    {
        if (color[u] == side) /* can piece reach square in one step ? */
#ifdef CHECK_DISTANCE
        {
            if (piece_distance(side, board[u], u, square) == 1)
                return true;
        }
#else
        {
            short v;
            short ptypv = ptype[side][board[u]];
#ifdef SAVE_NEXTPOS
            short dv;
            v = first_direction(ptypv, &dv, u);
#else
            unsigned char *qdir;
            qdir = (*nextdir[ptypv])[u];
            v = qdir[u];
#endif
            do
            {
                if (v == square)
                    return true;
#ifdef SAVE_NEXTPOS
                v = next_direction(ptypv, &dv, u);
#else
                v = qdir[v];
#endif
            }
            while (v != u);
        }
#endif

#ifdef SAVE_NEXTPOS
        u = next_direction(ptyp, &d, square);
#else
        u = pdir[u];
#endif
    }
    while (u != square);

    /* try a knight capture (using xside's knight moves) */

    ptyp = ptype[side ^ 1][knight];

#ifdef SAVE_NEXTPOS
    u = first_direction(ptyp, &d, square);
#else
    pdir = (*nextdir[ptyp])[square];
    u = pdir[square];
#endif

    do
    {
        if (color[u] == side && board[u] == knight)
            return true;

#ifdef SAVE_NEXTPOS
        u = next_direction(ptyp, &d, square);
#else
        u = pdir[u];
#endif
    }
    while (u != square);

    *blockable = true;

    /* try a (promoted) bishop capture */

    ptyp = ptype[black][bishop];

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
#ifdef SAVE_NEXTPOS
            u = next_position(ptyp, &d, square, u);
#else
        u = ppos[u];
#endif
        else
        {
            if (color[u] == side && (unpromoted[board[u]] == bishop))
                return true;

#ifdef SAVE_NEXTPOS
            u = next_direction(ptyp, &d, square);
#else
            u = pdir[u];
#endif
        }
    }
    while (u != square);

    /* try a (promoted) rook capture */

    ptyp = ptype[black][rook];

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
#ifdef SAVE_NEXTPOS
        {
            u = next_position(ptyp, &d, square, u);
        }
#else
        {
            u = ppos[u];
        }
#endif
        else
        {
            if (color[u] == side && (unpromoted[board[u]] == rook))
                return true;

#ifdef SAVE_NEXTPOS
            u = next_direction(ptyp, &d, square);
#else
            u = pdir[u];
#endif
        }
    }
    while (u != square);

    /* try a lance capture (using xside's lance moves) */

    ptyp = ptype[side ^ 1][lance];

#ifdef SAVE_NEXTPOS
    u = first_direction(ptyp, &d, square);
#else
    ppos = (*nextpos[ptyp])[square];
    u = ppos[square];
#endif

    do
    {
        if (color[u] == neutral)
#ifdef SAVE_NEXTPOS
        {
            u = next_position(ptyp, &d, square, u);
        }
#else
        {
            u = ppos[u];
        }
#endif
        else
        {
            if ((color[u] == side) && (board[u] == lance))
                return true;

            u = square;
        }
    }
    while (u != square);

    return false;
}
