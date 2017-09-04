/*

    book.c

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
 * FILE: book.c
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

#define O_BINARY 0

#if defined(_WIN32)
#include <io.h>
#endif

#if HAVE_UNISTD_H
/* Declarations of read(), write(), close(), and lseek(). */
#include <unistd.h>
#endif

#if HAVE_FCNTL_H
#include <fcntl.h>
#endif

#include "book.h"

unsigned booksize = BOOKSIZE;
unsigned short bookmaxply = BOOKMAXPLY;
unsigned bookcount = 0;

#ifdef BOOK
char *bookfile = BOOK;
#else
char *bookfile = NULL;
#endif

char *binbookfile = NULL;

static char bmvstr[3][7];

static UINT bhashbd;
static UINT bhashkey;


/*
 * Balgbr(f, t, flag)
 *
 * Generate move strings in different formats.
 */

void
Balgbr(short f, short t, short flag)
{
    short promoted = false;

    if ((f & 0x80) != 0)
    {
        f &= 0x7f;
        promoted = true;
    }

    if (f > NO_SQUARES)
    {
        short piece;
        piece = f - NO_SQUARES;

        if (f > (NO_SQUARES + NO_PIECES))
            piece -= NO_PIECES;

        flag = (dropmask | piece);
    }

    if ((t & 0x80) != 0)
    {
        flag |= promote;
        t &= 0x7f;
    }

    if ((f == t) && ((f != 0) || (t != 0)))
    {
        /*
         * error in algbr: FROM=TO=t
         */

        bmvstr[0][0] = bmvstr[1][0] = bmvstr[2][0] = '\0';
    }
    else
    {
        if ((flag & dropmask) != 0)
        {
            /* bmvstr[0]: P*3c bmvstr[1]: P'3c */
            short piece = flag & pmask;
            bmvstr[0][0] = pxx[piece];
            bmvstr[0][1] = '*';
            bmvstr[0][2] = cxx[column(t)];
            bmvstr[0][3] = rxx[row(t)];
            bmvstr[0][4] = bmvstr[2][0] = '\0';
            strcpy(bmvstr[1], bmvstr[0]);
            bmvstr[1][1] = '\'';
        }
        else
        {
            if ((f != 0) || (t != 0))
            {
                /* algebraic notation */
                /* bmvstr[0]: 7g7f bmvstr[1]:
                 * (+)P7g7f(+) bmvstr[2]: (+)P7f(+) */
                bmvstr[0][0] = cxx[column(f)];
                bmvstr[0][1] = rxx[row(f)];
                bmvstr[0][2] = cxx[column(t)];
                bmvstr[0][3] = rxx[row(t)];
                bmvstr[0][4] = '\0';

                if (promoted)
                {
                    bmvstr[1][0] = bmvstr[2][0] = '+';
                    bmvstr[1][1] = bmvstr[2][1] = pxx[board[f]];
                    strcpy(&bmvstr[1][2], &bmvstr[0][0]);
                    strcpy(&bmvstr[2][2], &bmvstr[0][2]);
                }
                else
                {
                    bmvstr[1][0] = bmvstr[2][0] = pxx[board[f]];
                    strcpy(&bmvstr[1][1], &bmvstr[0][0]);
                    strcpy(&bmvstr[2][1], &bmvstr[0][2]);
                }

                if (flag & promote)
                {
                    strcat(bmvstr[0], "+");
                    strcat(bmvstr[1], "+");
                    strcat(bmvstr[2], "+");
                }
            }
            else
            {
                bmvstr[0][0] = bmvstr[1][0] = bmvstr[2][0] = '\0';
            }
        }
    }
}




#ifndef QUIETBOOKGEN
void
bkdisplay(char *s, int cnt, int moveno)
{
    static short pnt;
    struct leaf  *node;
    int r, c, l;

    pnt = TrPnt[2];
    printf("matches = %d\n", cnt);
    printf("inout move is :%s: move number %d side %s\n",
            s, moveno / 2 + 1, (moveno & 1) ? "white" : "black");

#ifndef SEMIQUIETBOOKGEN
    printf("legal moves are \n");

    while (pnt < TrPnt[3])
    {
        node = &Tree[pnt++];

        if (is_promoted[board[node->f]] )
            Balgbr(node->f | 0x80, node->t, (short) node->flags);
        else
            Balgbr(node->f, node->t, (short) node->flags);

        printf("%s %s %s\n",
               bmvstr[0], bmvstr[1], bmvstr[2]);
    }

    printf("\n current board is\n");

    for (r = (NO_ROWS - 1); r >= 0; r--)
    {
        for (c = 0; c <= (NO_COLS - 1); c++)
        {
            char pc;

            l = locn(r, c);
            pc = (is_promoted[board[l]] ? '+' : ' ');

            if (color[l] == neutral)
                printf(" -");
            else if (color[l] == black)
                printf("%c%c", pc, qxx[board[l]]);
            else
                printf("%c%c", pc, pxx[board[l]]);
        }

        printf("\n");
    }

    printf("\n");
    {
        short color;

        for (color = black; color <= white; color++)
        {
            short piece, c;

            printf((color == black) ? "black " : "white ");

            for (piece = pawn; piece <= king; piece++)
            {
                if ((c = Captured[color][piece]))
                    printf("%i%c ", c, pxx[piece]);
            }

            printf("\n");
        };
    }
#endif /* SEMIQUIETBOOKGEN */
}

#endif /* QUIETBOOKGEN */



/*
 * BVerifyMove(s, mv, moveno)
 *
 * Compare the string 's' to the list of legal moves available for the
 * opponent. If a match is found, make the move on the board.
 */

int
BVerifyMove(char *s, unsigned short *mv, int moveno)
{
    static short pnt, tempb, tempc, tempsf, tempst, cnt;
    static struct leaf xnode;
    struct leaf  *node;

    *mv = 0;
    cnt = 0;
    MoveList(opponent, 2, -2, true);
    pnt = TrPnt[2];

    while (pnt < TrPnt[3])
    {
        node = &Tree[pnt++];

        if (is_promoted[board[node->f]] )
            Balgbr(node->f | 0x80, node->t, (short) node->flags);
        else
            Balgbr(node->f, node->t, (short) node->flags);

        if (strcmp(s, bmvstr[0]) == 0 || strcmp(s, bmvstr[1]) == 0 ||
            strcmp(s, bmvstr[2]) == 0)
        {
            cnt++;
            xnode = *node;
        }
    }

    if (cnt == 1)
    {
        short blockable;

        MakeMove(opponent, &xnode, &tempb,
                 &tempc, &tempsf, &tempst, &INCscore);

        if (SqAttacked(PieceList[opponent][0], computer, &blockable))
        {
            UnmakeMove(opponent, &xnode, &tempb, &tempc, &tempsf, &tempst);
            /* Illegal move in check */
#if !defined QUIETBOOKGEN
            /* 077: "Illegal move (in check) %s" */
            printf(CP[77], s);
            printf("\n");
            bkdisplay(s, cnt, moveno);
#endif
            return false;
        }
        else
        {
            *mv = (xnode.f << 8) | xnode.t;

            if (is_promoted[board[xnode.t]] )
                Balgbr(xnode.f | 0x80, xnode.t, false);
            else
                Balgbr(xnode.f, xnode.t, false);

            return true;
        }
    }

    /* Illegal move */
#if !defined QUIETBOOKGEN
    /* 075: "Illegal move (no match)%s\n" */
    printf(CP[75], s);
    bkdisplay(s, cnt, moveno);
#endif
    return false;
}




/*
 * RESET()
 *
 * Reset the board and other variables to start a new game.
 *
 */

void
RESET(void)
{
    short l;

    flag.illegal = flag.mate = flag.post = flag.quit
        = flag.reverse = flag.bothsides = flag.onemove = flag.force
        = false;

    flag.material = flag.coords = flag.hash = flag.easy
        = flag.beep = flag.rcptr
        = true;

    flag.stars = flag.shade = flag.back = flag.musttimeout = false;
    flag.gamein = false;
    GenCnt   = 0;
    GameCnt  = 0;
    CptrFlag[0] = TesujiFlag[0] = false;
    opponent = black;
    computer = white;

    for (l = 0; l < NO_SQUARES; l++)
    {
        board[l]   = Stboard[l];
        color[l]   = Stcolor[l];
        Mvboard[l] = 0;
    }

    ClearCaptured();
    InitializeStats();
    hashbd = hashkey = 0;
}



static
int
Vparse (FILE * fd, USHORT *mv, USHORT *flags, USHORT side, int moveno)
{
    int c, i;
    char s[255];

    *flags = 0;

    while (true)
    {
        while (((c = getc(fd)) == ' ')
               || (c == '!') || (c == '/') || (c == '\n'));

        if (c == '(')
        {
            /* amount of time spent for the last move */
            while (((c = getc(fd)) != ')') && (c != EOF));

            if (c == ')')
            {
                while (((c = getc(fd)) == ' ') || (c == '\n'));
            }
        }

        if (c == '[')
        {
            /* comment for the actual game */
            while (((c = getc(fd))) != ']' && (c != EOF));

            if (c == ']')
            {
                while (((c = getc(fd))) == ' ' || (c == '\n'));
            }
        }

        if (c == '\r')
            continue;

        if (c == '#')
        {
            /* comment */
            do
            {
                c = getc(fd);

                if (c == '\r')
                    continue;
                /* goes to end of line */

                if (c == '\n')
                    return 0;

                if (c == EOF)
                    return -1;
            }
            while (true);
        }

        s[i = 0] = (char) c;

        while ((c >= '0') && (c <= '9'))
        {
            c = getc(fd);
            s[++i] = (char) c;
        }

        if (c == '.')
        {
            while (((c = getc(fd)) == ' ') || (c == '.') || (c == '\n'));
            s[i = 0] = (char) c;
        }

        while (((c = getc(fd)) != '?') && (c != '!') && (c != ' ')
               && (c != '(') && (c != '\n') && (c != '\t') && (c != EOF))
        {
            if (c == '\r')
                continue;

            if ((c != 'x') && (c != '-') && (c != ',')
                && (c != ';') && (c != '='))
            {
                s[++i] = (char) c;
            }
        }

        s[++i] = '\0';

        if (c == '(')
        {
            while (((c = getc(fd)) != ')') && (c != EOF));

            if (c == ')')
                c = getc(fd);
        }

        if (c == EOF)
            return -1;

        if (s[0] == '#')
        {
            while ((c != '\n') && (c != EOF))
                c = getc(fd);

            if (c == EOF)
                return -1;
            else
                return 0;
        }

        if (strcmp(s, "draw") == 0)
            continue;
        else if (strcmp(s, "1-0") == 0)
            continue;
        else if (strcmp(s, "0-1") == 0)
            continue;
        else if (strcmp(s, "Resigns") == 0)
            continue;
        else if (strcmp(s, "Resigns.") == 0)
            continue;
        else if (strcmp(s, "Sennichite") == 0)
            continue;
        else if (strcmp(s, "Sennichite.") == 0)
            continue;
        else if (strcmp(s, "Jishogi") == 0)
            continue;
        else if (strcmp(s, "Jishogi.") == 0)
            continue;

        bhashkey = hashkey;
        bhashbd  = hashbd;

        i = BVerifyMove(s, mv, moveno);

        if (c == '?')
        {
            /* Bad move, not for the program to play */
            *flags |= BADMOVE;  /* Flag it ! */
            while (((c = getc(fd)) == '?') || (c == '!') || (c == '/'));
        }
#ifdef EASY_OPENINGS
        else if (c == '~')
        {
            /* Do not use by computer */
            *flags |= BADMOVE;  /* Flag it ! */

            while (((c = getc(fd)) == '?') || (c == '!') || (c == '/'));
        }
#endif
        else if (c == '!')
        {
            /* Good move */
            *flags |= GOODMOVE; /* Flag it ! */

            while (((c = getc(fd)) == '?') || (c == '!') || (c == '/'));
        }
        else if (c == '\r')
        {
            c = getc(fd);
        }

        if (c == '(' )
            while (((c = getc(fd)) != ')') && (c != EOF));

        if (!i)
        {
            /* flush to start of next */
            while (((c = getc(fd)) != '#') && (c != EOF));

            if (c == EOF)
            {
                return -1;
            }
            else
            {
                ungetc(c, fd);
                return i;
            }
        }

        return i;
    }
}


static struct gdxadmin ADMIN;
struct gdxadmin B;
static struct gdxdata DATA;

/* #define HashValue(l) lts(l) */
#define HashValue(l) (USHORT)(l & 0xffff)


static int gfd;
static UINT currentoffset;


#define MAXOFFSET(B) ((B.booksize - 1) * sizeof_gdxdata + sizeof_gdxadmin)

#define HashOffset(hashkey, B) \
{ \
  currentoffset = (hashkey % B.booksize) \
    * sizeof_gdxdata + sizeof_gdxadmin; \
}


#define NextOffset(B) \
{ \
  currentoffset += sizeof_gdxdata; \
  if (currentoffset > B.maxoffset) \
    currentoffset = sizeof_gdxadmin; \
}


#define WriteAdmin() \
{ \
  lseek(gfd, 0, 0); \
  rc = write(gfd, (char *)&ADMIN, sizeof_gdxadmin); \
}

#define WriteData() \
{ \
  if (mustwrite ) \
  { \
    lseek(gfd, currentoffset, 0); \
    rc = write(gfd, (char *)&DATA, sizeof_gdxdata); \
    mustwrite = false; \
  } \
}

static int ReadAdmin(void)
{
    lseek(gfd, 0, 0);
    return (sizeof_gdxadmin == read(gfd, (char *)&ADMIN, sizeof_gdxadmin));
}

static int ReadData(struct gdxdata *DATA)
{
    lseek(gfd, currentoffset, 0);
    return (sizeof_gdxdata == read(gfd, (char *)DATA, sizeof_gdxdata));
}


/*
 * GetOpenings()
 *
 * CHECKME: is this still valid esp. wrt gnushogi.book?
 *
 * Read in the Opening Book file and parse the algebraic notation for a move
 * into an unsigned integer format indicating the from and to square. Create
 * a linked list of opening lines of play, with entry->next pointing to the
 * next line and entry->move pointing to a chunk of memory containing the
 * moves. More Opening lines of up to 100 half moves may be added to
 * gnushogi.book. But now it's a hashed table by position which yields a move
 * or moves for each position. It no longer knows about openings per se only
 * positions and recommended moves in those positions.
 *
 */

void
GetOpenings(void)
{
    short i;
    int mustwrite = false, first;
    unsigned short xside, side;
    short c;
    USHORT mv, flags;
    unsigned int x;
    unsigned int games = 0;
    int  collisions = 0;
    char msg[80];
    int rc;
#if !defined( __MINGW32__)
    FILE *fd;

    fd = NULL;

    if ((bookfile == NULL) || (fd = fopen(bookfile, "r")) == NULL)
        fd = fopen("gnushogi.tbk", "r");

    if (fd != NULL)
    {
 
        /* yes add to book */
        /* open book as writer */
        gfd = open(binbookfile, O_RDONLY | O_BINARY);

        if (gfd >= 0)
        {
            if (ReadAdmin())
            {
                B.bookcount = ADMIN.bookcount;
                B.booksize = ADMIN.booksize;
                B.maxoffset = ADMIN.maxoffset;

                if (B.booksize && !(B.maxoffset == MAXOFFSET(B)))
                {
                    printf("bad format %s\n", binbookfile);
                    exit(1);
                }
            }
            else
            {
                printf("bad format %s\n", binbookfile);
                exit(1);
            }
            close(gfd);
            gfd = open(binbookfile, O_RDWR | O_BINARY);

        }
        else
        {
            gfd = open(binbookfile, O_RDWR | O_CREAT | O_BINARY, 0644);

            ADMIN.bookcount = B.bookcount = 0;
            ADMIN.booksize = B.booksize = booksize;
            B.maxoffset = ADMIN.maxoffset = MAXOFFSET(B);
            DATA.hashbd = 0;
            DATA.hashkey = 0;
            DATA.bmove = 0;
            DATA.flags = 0;
            DATA.hint = 0;
            DATA.count = 0;
            rc = write(gfd, (char *)&ADMIN, sizeof_gdxadmin);
            printf("creating bookfile %s %d %d\n",
                    binbookfile, B.maxoffset, B.booksize);

            for (x = 0; x < B.booksize; x++)
            {
                rc = write(gfd, (char *)&DATA, sizeof_gdxdata);
            }
        }

        if (gfd >= 0)
        {
            /* setvbuf(fd, buffr, _IOFBF, 2048); */
            side = black;
            xside = white;
            hashbd = hashkey = 0;
            i = 0;

            while ((c = Vparse(fd, &mv, &flags, side, i)) >= 0)
            {
                if (c == 1)
                {
                    /*
                     * If this is not the first move of an opening and
                     * if it's the first time we have seen it then
                     * save the next move as a hint.
                     */
                    i++;

                    if (i < bookmaxply + 2)
                    {
                        if (i > 1 && !(flags & BADMOVE))
                            DATA.hint = mv;

                        if (i < bookmaxply + 1)
                        {
                            /*
                             * See if this position and move already
                             * exist from some other opening.
                             */

                            WriteData();
                            HashOffset(bhashkey, B);
                            first = true;

                            while (true)
                            {
                                if (!ReadData(&DATA))
                                    break; /* corrupted binbook file */

                                if (DATA.bmove == 0)
                                    break;  /* free entry */

                                if (DATA.hashkey == HashValue(bhashkey)
                                    && DATA.hashbd == bhashbd)
                                {
                                    if (DATA.bmove == mv)
                                    {
                                        /*
                                         * Yes, so just bump count - count
                                         * is used to choose the opening
                                         * move in proportion to its
                                         * presence in the book.
                                         */

                                        DATA.count++;
                                        DATA.flags |= flags;
                                        mustwrite = true;
                                        break;
                                    }
                                    else
                                    {
                                        if (first)
                                            collisions++;

                                        if (DATA.flags & LASTMOVE)
                                        {
                                            DATA.flags &= (~LASTMOVE);
                                            mustwrite = true;
                                            WriteData();
                                        }
                                    }
                                }

                                NextOffset(B);
                                first = false;
                            }

                            /*
                             * Doesn't exist so add it to the book.
                             */

                            if (!mustwrite)
                            {
                                B.bookcount++;

                                if ((B.bookcount % 1000) == 0)
                                {
                                    /* CHECKME: may want to get rid of this,
                                     * especially for xshogi. */
                                    printf("%d rec %d openings "
                                           "processed\n",
                                           B.bookcount, games);
                                }

                                /* initialize a record */
                                DATA.hashbd = bhashbd;
                                DATA.hashkey = HashValue(bhashkey);
                                DATA.bmove = mv;
                                DATA.flags = flags | LASTMOVE;
                                DATA.count = 1;
                                DATA.hint = 0;
                                mustwrite = true;
                            }
                        }
                    }

                    computer = opponent;
                    opponent = computer ^ 1;

                    xside = side;
                    side = side ^ 1;
                }
                else if (i > 0)
                {
                    /* reset for next opening */
                    games++;
                    WriteData();
                    RESET();
                    i = 0;
                    side = black;
                    xside = white;

                }
            }

            WriteData();
            fclose(fd);
            /* write admin rec with counts */
            ADMIN.bookcount = B.bookcount;
            WriteAdmin();

            close(gfd);
        }
    }

    if (binbookfile != NULL)
    {

        /* open book as reader */
        gfd = open(binbookfile, O_RDONLY | O_BINARY);

        if (gfd >= 0)
        {
            if (ReadAdmin() && (!ADMIN.booksize
                                || (ADMIN.maxoffset == MAXOFFSET(ADMIN))))
            {
                B.bookcount = ADMIN.bookcount;
                B.booksize  = ADMIN.booksize;
                B.maxoffset = ADMIN.maxoffset;
            }
            else
            {
                printf("bad format %s\n", binbookfile);
                exit(1);
            }

        }
        else
        {
            B.bookcount = 0;
            B.booksize = booksize;

        }

        /* 213: "Book used %d(%d)." */
        sprintf(msg, CP[213], B.bookcount, B.booksize);
        ShowMessage(msg);
    }
#endif /* !defined(MINGW32) && !defined(MINGW64) */

    /* Set everything back to start the game. */
    Book = BOOKFAIL;
    RESET();

    /* Now get ready to play .*/
    if (!B.bookcount)
    {
        /* 212: "Can't find book." */
        ShowMessage(CP[212]);
        Book = 0;
    }
}



/*
 * OpeningBook(hint, side)
 *
 * Go through each of the opening lines of play and check for a match with
 * the current game listing. If a match occurs, generate a random
 * number. If this number is the largest generated so far then the next
 * move in this line becomes the current "candidate".  After all lines are
 * checked, the candidate move is put at the top of the Tree[] array and
 * will be played by the program.  Note that the program does not handle
 * book transpositions.
 */

int
OpeningBook(unsigned short *hint, short side)
{
    unsigned short r, m;
    int possibles = TrPnt[2] - TrPnt[1];

    gsrand((unsigned int) time((time_t *) 0));

    m = 0;

    /*
     * Find all the moves for this position  - count them and get their
     * total count.
     */

    {
        USHORT i, x;
        USHORT rec = 0;
        USHORT summ = 0;
        USHORT h = 0, b = 0;
        struct gdxdata OBB[128];

        if (B.bookcount == 0)
        {
            Book--;
            return false;
        }

        x = 0;
        HashOffset(hashkey, B);
#ifdef BOOKTEST
        printf("looking for book move, bhashbd = 0x%x bhashkey = 0x%x\n",
               hashbd, HashValue(hashkey));
#endif
        while (true)
        {
            if (!ReadData(&OBB[x]))
                break;

            if (OBB[x].bmove == 0)
                break;

#ifdef BOOKTEST
            printf("compare with bhashbd = 0x%x bhashkey = 0x%x\n",
                   OBB[x].hashbd, OBB[x].hashkey);
#endif
            if ((OBB[x].hashkey == HashValue(hashkey))
                && (OBB[x].hashbd == hashbd))
            {
                x++;

                if (OBB[x-1].flags & LASTMOVE)
                    break;
            }

            NextOffset(B);
        }

#ifdef BOOKTEST
        printf("%d book move(s) found.\n", x);
#endif

        if (x == 0)
        {
            Book--;
            return false;
        }

        for (i = 0; i < x; i++)
        {
            if (OBB[i].flags & BADMOVE)
            {
                m = OBB[i].bmove;

                /* Is the move in the MoveList? */
                for (b = TrPnt[1]; b < (unsigned) TrPnt[2]; b++)
                {
                    if (((Tree[b].f << 8) | Tree[b].t) == m)
                    {
                        if (--possibles)
                            Tree[b].score = DONTUSE;
                        break;
                    }
                }
            }
            else
            {
#if defined BOOKTEST
                char s[20];
                movealgbr(m = OBB[i].bmove, s);
                printf("finding book move: %s\n", s);
#endif
                summ += OBB[i].count;
            }
        }

        if (summ == 0)
        {
            Book--;
            return false;
        }

        r = (urand() % summ);

        for (i = 0; i < x; i++)
        {
            if (!(OBB[i].flags & BADMOVE))
            {
                if (r < OBB[i].count)
                {
                    rec = i;
                    break;
                }
                else
                {
                    r -= OBB[i].count;
                }
            }
        }

        h = OBB[rec].hint;
        m = OBB[rec].bmove;

        /* Make sure the move is in the MoveList. */
        for (b = TrPnt[1]; b < (unsigned) TrPnt[2]; b++)
        {
            if (((Tree[b].f << 8) | Tree[b].t) == m)
            {
                Tree[b].flags |= book;
                Tree[b].score = 0;
                break;
            }
        }

        /* Make sure it's the best. */

        pick(TrPnt[1], TrPnt[2] - 1);

        if (Tree[TrPnt[1]].score)
        {
            /* no! */
            Book--;
            return false;
        }

        /* Ok, pick up the hint and go. */
        *hint = h;
        return true;
    }

    Book--;
    return false;
}
