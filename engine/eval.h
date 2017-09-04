/*

    eval.h

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
 * FILE: eval.h
 *
 *     Interface to the board evaluator.
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


#ifndef _EVAL_H_
#define _EVAL_H_

#define NO_STAGES 100
#define NO_FEATURES 31


struct signature
{
    unsigned int hashbd;
    unsigned int hashkey;
};

#define MatchSignature(s) ((s.hashbd == hashbd) && (s.hashkey == hashkey))
#define CopySignature(s)  { s.hashbd = hashbd; s.hashkey = hashkey; }

typedef short        value_array[NO_STAGES][NO_PIECES];
typedef small_short fscore_array[NO_STAGES][NO_FEATURES][2];

extern value_array  *value;
extern fscore_array *fscore;

extern void threats (short side);

extern int attack[2][NO_SQUARES];
extern small_short sseed[NO_SQUARES];

extern struct signature threats_signature[2];

extern small_short starget[2][NO_SQUARES];
extern small_short sloose[NO_SQUARES];
extern small_short shole[NO_SQUARES];
extern small_short shung[NO_SQUARES];

extern struct signature squares_signature;

#endif /* _EVAL_H_ */
