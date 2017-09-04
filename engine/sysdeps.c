/*

    sysdeps.c

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
 * FILE: sysdeps.c
 *
 *     System-dependent functions for GNU Shogi.
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

/* Forward declarations. */

void ElapsedTime_NOFIONREAD(ElapsedTime_mode iop);

/*
 * Determine the time that has passed since the search was started. If the
 * elapsed time exceeds the target(ResponseTime + ExtraTime) then set timeout
 * to true which will terminate the search.
 * iop = COMPUTE_MODE calculate et, bump ETnodes
 * iop = COMPUTE_AND_INIT_MODE calculate et, set timeout if time exceeded,
 *     set reference time
 */

/*
 * ElapsedTime() is actually a wrapper function around the different
 * versions of ElapsedTime_XXX().  This allows us to compile all the
 * different ways of measuring time in one executable.
 */

void
ElapsedTime(ElapsedTime_mode iop)
{
    ElapsedTime_NOFIONREAD(iop);
}

/*
 * Determine the time that has passed since the search was started.  If the
 * elapsed time exceeds the target (ResponseTime + ExtraTime) then set
 * timeout to true which will terminate the search.
 *
 * iop = 0   calculate et, bump ETnodes
 * iop = 1   calculate et, set timeout if time exceeded, calculate et
 *
 */

void
ElapsedTime_NOFIONREAD(ElapsedTime_mode iop)
{
    int current_time;

    et = ((current_time = time((time_t *) 0)) - time0) * 100;

#ifdef INTERRUPT_TEST
    if (iop == INIT_INTERRUPT_MODE)
    {
        itime0 = current_time;
    }
    else if (iop == COMPUTE_INTERRUPT_MODE)
    {
        it = current_time - itime0;
    }
    else
#endif
    {
        ETnodes = NodeCnt + znodes;

        if (et < 0)
        {
#ifdef INTERRUPT_TEST
            printf("elapsed time %ld not positive\n", et);
#endif
            et = 0;
        }

        if (iop == COMPUTE_AND_INIT_MODE)
        {
            if ((et > (ResponseTime + ExtraTime)) && (Sdepth > MINDEPTH))
                flag.timeout = true;

            time0 = current_time;
        }

    }
}
