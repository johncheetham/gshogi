/*

    rawdsp.h

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
 * FILE: rawdsp.h
 *
 *     Raw text interface for GNU Shogi.
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

#ifndef _RAWDSP_H_
#define _RAWDSP_H_

/* The following are common to rawdsp.h and cursesdsp.h */

void ChangeAlphaWindow(void);
void ChangeBetaWindow(void);
void ChangeHashDepth(void);
void ChangeSearchDepth(void);
void ChangeXwindow(void);
void ClearScreen(void);
void DoDebug(void);
void ExitShogi(void);
void GiveHint(void);
void Initialize(void);
void OutputMove(void);
void SearchStartStuff(short side);
void SelectLevel(char *sx);
void SetContempt(void);
void ShowCurrentMove(short pnt, short f, short t);
void ShowDepth(char ch);
void ShowLine(unsigned short *bstline);
void ShowMessage(char *s);
void ShowPatternCount(short side, short n);
void ShowPostnValue(short sq);
void ShowPostnValues(void);
void ShowResponseTime(void);
void ShowResults(short score, unsigned short *bstline, char ch);
void ShowSidetoMove(void);
void ShowStage(void);
void TerminateSearch(int sig);
void UpdateDisplay(short f, short t, short redraw, short isspec);
void help(void);


/* The following are only found in rawdsp.h: */

void PromptForMove(void);

#endif /* _RAWDSP_H_ */
