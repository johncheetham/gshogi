/*

    debug.h

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
 * FILE: debug.h
 *
 *       Various macros to help in debugging.
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

/* Some of this code requires gcc. */


#ifndef _DEBUG_H_
#define _DEBUG_H_

/*
 * Define simple macros PRINT_ENTER and PRINT_EXIT to print info when
 * a function is entered or left.  They only work if DEBUG is #defined.
 * This requires gcc.  You have to invoke them with a semicolon after them,
 * like this:
 *
 * PRINT_ENTER;
 * PRINT_EXIT;
 *
 * This is so as not to screw up automatic indentation in emacs.
 */

#if (defined __GNUC__)

#  define PRINT_ENTER printf("Entering function:  %s().\n", __FUNCTION__)
#  define PRINT_EXIT  printf("Exiting function:   %s().\n", __FUNCTION__)

#else

#  define PRINT_ENTER
#  define PRINT_EXIT

#endif  /* __GNUC__ */

/* Function inlining; not all C compilers support this. */
#if (!defined __GNUC__)
#  define inline
#endif

#endif  /* _DEBUG_H_ */
