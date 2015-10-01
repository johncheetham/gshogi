/*

    opts.h

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
 * FILE: opts.h
 *
 *     #defines to set various options.
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


/*
 * This file is for options that control the behavior of GNU shogi,
 * and also for debugging #defines.  They were previously placed on the
 * command line as -D<option> statements, but this cluttered things
 * up so much that I changed it.  For the evaluator options, I recommend
 * you don't change anything unless you *really* know what you're doing.
 * These options come in pairs of:
 *
 * #define <option>
 * #undef <option>
 *
 * For each pair, simply comment out the one you don't want.
 *
 */


#ifndef _OPTS_H_
#define _OPTS_H_

/*
 * ======================================================================
 *
 * 1) Evaluator options.
 *
 * ======================================================================
 */

/*
 * QUIETBACKGROUND:
 * Don't print post information in background (easy mode OFF)
 */

#define QUIETBACKGROUND
/* #undef  QUIETBACKGROUND */


/*
 * NODYNALPHA:
 * Don't dynamically adjust alpha.
 */

/* #define NODYNALPHA */
#undef  NODYNALPHA


/*
 * HISTORY:
 * Use history killer heuristic.
 */

#define HISTORY
/* #undef  HISTORY */


/*
 * CACHE:
 * Cache static evaluations.
 */

#define CACHE
/* #undef  CACHE */


/*
 * QUIETBOOKGEN:
 * Don't print errors while loading a book or generating a binbook.
 */

/* #define QUIETBOOKGEN */
#undef  QUIETBOOKGEN


/*
 * SEMIQUIETBOOKGEN:
 * Print less verbose errors while reading book or generating binbook.
 */

/* #define SEMIQUIETBOOKGEN */
#undef  SEMIQUIETBOOKGEN


/*
 * NULLMOVE:
 * Include null move heuristic.
 */

#define NULLMOVE
/* #undef  NULLMOVE */


/*
 * Options for genmove.c in order to support move ordering at a
 * cost in speed.
 */

/*
 * TESUJIBONUS:
 * Add bonus to a move that seems to be a tesuji.
 */

#define TESUJIBONUS
/* #undef  TESUJIBONUS */


/*
 * FIELDBONUS:
 * Add bonus to regular moves.
 */

#define FIELDBONUS
/* #undef  FIELDBONUS */


/*
 * DROPBONUS:
 * Add bonus to drops.
 */

#define DROPBONUS
/* #undef  DROPBONUS */


/*
 * CHECKBONUS:
 * Add bonus to checks.
 */

#define CHECKBONUS
/* #undef  CHECKBONUS */


/*
 * DEEPSEARCHCUT:
 * Check for moves not to consider at deep plys.
 */

#define DEEPSEARCHCUT
/* #undef  DEEPSEARCHCUT */



/*
 * ======================================================================
 *
 * 2) Debug options.  We don't put a #define/#undef pair here, since
 *    usually only one or a few of these will be defined.
 *
 * ======================================================================
 */


/* FIXME: write comments for these: */
#undef HASHKEYTEST
#undef HASHTEST
#undef CACHETEST

/* This is used in rawdsp.c and cursesdsp.c: */
#define VERYBUGGY

/* This affects the history table.  See gnushogi.h. */
#define EXACTHISTORY


/*
 * ======================================================================
 *
 * 3) Other options.
 *
 * ======================================================================
 */

/*
 * Define this if you want to automatically have the game saved on exit.
 * This tends to litter whatever directory you're in with game files you
 * may not want, so it's off by default.
 */

#undef LIST_ON_EXIT

#endif /* _OPTS_H_ */
