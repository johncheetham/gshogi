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

#if HAVE_UNISTD_H
#include <unistd.h>
#endif

#if HAVE_SYS_FILIO_H
/* Definition of FIONREAD */
#include <sys/filio.h>
#endif

#if HAVE_ERRNO_H
/* Definition of errno(). */
#include <errno.h>
#endif

/* Forward declarations. */

void ElapsedTime_NOFIONREAD(ElapsedTime_mode iop);
void ElapsedTime_FIONREAD(ElapsedTime_mode iop);


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
    switch (display_type)
    {
    case DISPLAY_RAW:
        ElapsedTime_NOFIONREAD(iop);
        break;

    default:
        ElapsedTime_FIONREAD(iop);
        break;
    }
}



#ifdef HAVE_GETTIMEOFDAY
void
ElapsedTime_FIONREAD(ElapsedTime_mode iop)
{
    long current_time;
    int  i;
    int  nchar;

    struct timeval tv;

    if ((i = ioctl((int) 0, FIONREAD, &nchar)))
    {
        perror("FIONREAD");
        fprintf(stderr,
                "You probably have a non-ANSI <ioctl.h>; "
                "see README. %d %d %x\n",
                i, errno, FIONREAD);
        exit(1);
    }

    if (nchar)
    {
        if (!flag.timeout)
            flag.back = true;

        flag.bothsides = false;
    }

    gettimeofday(&tv, NULL);
    current_time = tv.tv_sec*100 + (tv.tv_usec/10000);

#  ifdef INTERRUPT_TEST
    if (iop == INIT_INTERRUPT_MODE)
    {
        itime0 = current_time;
    }
    else if (iop == COMPUTE_INTERRUPT_MODE)
    {
        it = current_time - itime0;
    }
    else
#  endif
    {
        et = current_time - time0;
        ETnodes = NodeCnt + znodes;

        if (et < 0)
        {
#  ifdef INTERRUPT_TEST
            printf("elapsed time %ld not positive\n", et);
#  endif
            et = 0;
        }

        if (iop == COMPUTE_AND_INIT_MODE)
        {
            if ((et > ResponseTime + ExtraTime) && (Sdepth > MINDEPTH))
                flag.timeout = true;

            time0 = current_time;
        }

    }
}


void
ElapsedTime_NOFIONREAD(ElapsedTime_mode iop)
{
    struct timeval tv;
    long current_time;

    gettimeofday(&tv, NULL);
    current_time = tv.tv_sec*100 + (tv.tv_usec/10000);

#  ifdef INTERRUPT_TEST
    if (iop == INIT_INTERRUPT_MODE)
    {
        itime0 = current_time;
    }
    else if (iop == COMPUTE_INTERRUPT_MODE)
    {
        it = current_time - itime0;
    }
    else
#  endif
    {
        et = current_time - time0;
        ETnodes = NodeCnt + znodes;

        if (et < 0)
        {
#  ifdef INTERRUPT_TEST
            printf("elapsed time %ld not positive\n", et);
#  endif
            et = 0;
        }

        if (iop == COMPUTE_AND_INIT_MODE)
        {
            if ((et > ResponseTime + ExtraTime) && (Sdepth > MINDEPTH))
                flag.timeout = true;

            time0 = current_time;
        }

    }
}


#else /* !HAVE_GETTIMEOFDAY */


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
ElapsedTime_FIONREAD(ElapsedTime_mode iop)
{
    long current_time;
    int  nchar;
    int  i;

    if ((i = ioctl((int) 0, FIONREAD, &nchar)))
    {
        perror("FIONREAD");
        fprintf(stderr,
                "You probably have a non-ANSI <ioctl.h>; "
                "see README. %d %d %x\n",
                i, errno, FIONREAD);
        exit(1);
    }

    if (nchar)
    {
        if (!flag.timeout)
            flag.back = true;
        flag.bothsides = false;
    }

    et = ((current_time = time((long *) 0)) - time0) * 100;

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



void
ElapsedTime_NOFIONREAD(ElapsedTime_mode iop)
{
    long current_time;

    et = ((current_time = time((long *) 0)) - time0) * 100;

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


#endif /* HAVE_GETTIMEOFDAY */
