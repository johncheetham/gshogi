/*

    pattern.h

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
 * FILE: pattern.h
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


#ifndef _PATTERN_H_
#define _PATTERN_H_

#define MAX_NAME     16  /* maximum length of opening name */
#define MAX_SEQUENCE  4  /* maximum number of sequences
                          * for an opening type */

#define CANNOT_REACH (-1)
#define NOT_TO_REACH (-2)
#define IS_REACHED   (-3)
#define IS_SUCCESSOR (-4)

#define END_OF_SEQUENCES (-1)
#define END_OF_PATTERNS  (-2)
#define END_OF_LINKS     (-3)
#define END_OF_FIELDS    (-4)

struct PatternField
{
    short side;
    short piece;
    short square;
};


struct Pattern_rec
{
    small_short visited;
    small_short distance[2];
    short reachedGameCnt[2];
    short first_link;
    short first_field;
    short next_pattern;
};


struct OpeningSequence_rec
{
    short opening_type;
    short first_pattern[MAX_SEQUENCE];
};


extern struct Pattern_rec Pattern[];
extern struct OpeningSequence_rec OpeningSequence[];

extern short
piece_to_pattern_distance(short side, short piece,
                          short pside, short pattern);

extern short
pattern_distance(short pside, short pattern);

extern short
board_to_pattern_distance(short pside, short osequence,
                          short pmplty, short GameCnt);

extern short
locate_opening_sequence(short pside, char *s, short GameCnt);

extern void
DisplayPattern(FILE *fd, short first_field);

extern void
update_advance_bonus(short pside, short os);

extern void
GetOpeningPatterns(short *max_opening_sequence);

extern void
ShowOpeningPatterns(short max_opening_sequence);


extern short
ValueOfOpeningName(char *name);

extern void
NameOfOpeningValue(short i, char *name);

extern small_short pattern_data[];


#endif /* _PATTERN_H_ */
