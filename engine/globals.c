/*

    globals.c

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
 * FILE: globals.c
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


short ahead = true, hash = true;
char  *xwin = 0;
char  *Lang = NULL;


short FROMsquare, TOsquare;

small_short ChkFlag[MAXDEPTH], CptrFlag[MAXDEPTH], TesujiFlag[MAXDEPTH];
short Pscore[MAXDEPTH], Tscore[MAXDEPTH];
small_short Pindex[NO_SQUARES];

short mtl[2], hung[2];
small_short PieceCnt[2];

char ColorStr[2][10];

int znodes;

extern char *binbookfile;

extern char *bookfile;

unsigned int hashkey, hashbd;

char savefile[128];
char listfile[128];

short rpthash[2][256];
short TrPnt[MAXDEPTH];
small_short PieceList[2][NO_SQUARES];
small_short PawnCnt[2][NO_COLS];
small_short Captured[2][NO_PIECES];
small_short Mvboard[NO_SQUARES];

#if !defined SAVE_SVALUE
short svalue[NO_SQUARES];
#endif

struct flags flag;

short opponent, computer, WAwindow, WBwindow, BAwindow, BBwindow, dither,
    INCscore = 0;
int ResponseTime = 0, ExtraTime = 0, MaxResponseTime = 0,
    et = 0, et0 = 0, time0 = 0, ft = 0;

#ifdef INTERRUPT_TEST
int it, itime0;
#endif

int   GenCnt, NodeCnt, ETnodes, EvalNodes, HashCnt, HashAdd,
    FHashCnt, FHashAdd, HashCol, THashCol, filesz, hashmask, hashbase, NodeCntLimit;
int   replus, reminus;
short HashDepth = HASHDEPTH, HashMoveLimit = HASHMOVELIMIT;
short player, xwndw;
short rehash = -1;
short Sdepth, Game50, MaxSearchDepth;
short GameCnt = 0;
short contempt;
int   Book;
struct TimeControlRec TimeControl;
int   TCadd = 0;
short TCflag, TCmoves, TCminutes, TCseconds, OperatorTime;
short XCmoves[3]   = { 0, 0, 0 };
short XCminutes[3] = { 0, 0, 0 };
short XCseconds[3] = { 0, 0, 0 };
short XC = 0, XCmore = 0;
const short otherside[3] = { white, black, neutral };
unsigned short hint;
short TOflag;       /* force search re-init if we backup search */

unsigned short killr0[MAXDEPTH], killr1[MAXDEPTH];
unsigned short killr2[MAXDEPTH], killr3[MAXDEPTH];
unsigned short PV, SwagHt, Swag0, Swag1, Swag2, Swag3, Swag4, sidebit;

small_short HasPiece[2][NO_PIECES];

const short kingP[3] =
{ 4, 76, 0 };

const small_short relative_value[NO_PIECES] =
{ 0,  1,  3,  4,  7,  9,  10,  12,
  2,  5,  6,  8, 11, 13,  14 };

const int control[NO_PIECES] =
{ 0,  ctlP,  ctlL,  ctlN,  ctlS,  ctlG, ctlB, ctlR,
     ctlPp, ctlLp, ctlNp, ctlSp, ctlBp, ctlRp, ctlK };

short stage, stage2;
short balance[2];

#ifdef HASHFILE
FILE *hashfile;
#endif

unsigned int starttime;

int timeopp[MINGAMEIN], timecomp[MINGAMEIN];
int compptr, oppptr;


struct leaf  *Tree = NULL;

hashcode_array       *hashcode      = NULL;
drop_hashcode_array  *drop_hashcode = NULL;

struct leaf  *root = NULL;

struct GameRec  *GameList = NULL;

value_array   *value  = NULL;
fscore_array  *fscore = NULL;

#ifndef SAVE_DISTDATA
short use_distdata = true;
distdata_array  *distdata = NULL;
#endif

#ifndef SAVE_PTYPE_DISTDATA
short use_ptype_distdata = true;
distdata_array  *ptype_distdata[NO_PTYPE_PIECES];
#endif

#if !defined SAVE_NEXTPOS
next_array  *nextdir[NO_PTYPE_PIECES];
next_array  *nextpos[NO_PTYPE_PIECES];
short use_nextpos = true;
#endif

#if defined HISTORY
short use_history = true;
unsigned short  *history = NULL;
#endif

#ifdef CACHE
short use_etable = true;
etable_field  *etab[2] = { NULL, NULL };
#endif

#if ttblsz
short use_ttable = true;
unsigned int ttblsize = ttblsz;
struct hashentry  *ttable[2] = { NULL, NULL };
#endif
