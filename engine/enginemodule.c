/*
    enginemodule.c - Interface between the gui (written in python/pygtk)
                     and the engine (written in C)

    This file is part of gshogi

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

#include <Python.h>

#include "version.h"
#include "gnushogi.h"

#include <signal.h>


/* Initialise the engine */
static PyObject *
engine_init(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "sh", &binbookfile, &verbose))
        return NULL;

    InitMain();

    Py_RETURN_NONE;
}

/* command */
static PyObject *
engine_command(PyObject *self, PyObject *args)
{

    char *command;

    if (!PyArg_ParseTuple(args, "s", &command))
        return NULL;

    InputCommand(command);
    if (verbose)
    {
        printf("-> gshogi builtin:%s\n", command);
    }

    Py_RETURN_NONE;

}


/* generate binary opening book file from text opening book file */
static PyObject *
engine_genbook(PyObject *self, PyObject *args)
{

    if (!PyArg_ParseTuple(args, "ssii", &bookfile, &binbookfile, &booksize, &bookmaxply))
        return NULL;

    GetOpenings();

    Py_RETURN_NONE;

}


/* check if mate */
static PyObject *
engine_getmate(PyObject *self, PyObject *args)
{

    return Py_BuildValue("h", flag.mate);

}

/* get winner of the game */
static PyObject *
engine_getwinner(PyObject *self, PyObject *args)
{

    return Py_BuildValue("h", winner);

}

/* print engine data */
static PyObject *
engine_info(PyObject *self, PyObject *args)
{
    printf("------------\n");
    printf("black=%d\n", black);
    printf("computer=%d\n", computer);
    printf("opponent=%d\n", opponent);
    printf("player=%d\n", player);

    Py_RETURN_NONE;

}

/* set player to black */
static PyObject *
engine_setplayer(PyObject *self, PyObject *args)
{

    int plyr;

    if (!PyArg_ParseTuple(args, "i", &plyr))
        return NULL;

    if (plyr == black)
    {
        player = black;
        opponent = black;
        computer = white;
    }
    else
    {
        player = white;
        opponent = white;
        computer = black;
    }

    Py_RETURN_NONE;

}

/* get white move */
static PyObject *
engine_getmove(PyObject *self, PyObject *args)
{

    return Py_BuildValue("s", mvstr[0]);

}

/* load game */
static PyObject *
engine_loadgame(PyObject *self, PyObject *args)
{
    short rc;
    char *filename;

    if (!PyArg_ParseTuple(args, "s", &filename))
        return NULL;

    rc = GetGame(filename);

    return Py_BuildValue("h", rc);
}

/* save game */
static PyObject *
engine_savegame(PyObject *self, PyObject *args)
{
    char *filename;
    char *sfen;

    if (!PyArg_ParseTuple(args, "ss", &filename, &sfen))
        return NULL;

    SaveGame(filename, sfen);

    Py_RETURN_NONE;
}

/* set search depth */
static PyObject *
engine_depth(PyObject *self, PyObject *args)
{

    if (!PyArg_ParseTuple(args, "h", &MaxSearchDepth))
        return NULL;

    if (verbose)
    {
        printf("-> gshogi builtin depth set to %i\n", MaxSearchDepth);
    }

    Py_RETURN_NONE;
}

/* set search nodes limit */
static PyObject *
engine_nodes(PyObject *self, PyObject *args)
{

    if (!PyArg_ParseTuple(args, "l", &NodeCntLimit))
        return NULL;

    if (verbose)
    {
        printf("-> gshogi builtin node limit set to %d\n", NodeCntLimit);
    }

    Py_RETURN_NONE;
}


/* human move */
static PyObject *
engine_hmove(PyObject *self, PyObject *args)
{

    char *hmove;
    short rc;

    if (!PyArg_ParseTuple(args, "s", &hmove))
        return NULL;

    winner = 0;
    oppptr = (oppptr + 1) % MINGAMEIN;

    rc = DoMove(hmove); /* in commondsp.c */

    return Py_BuildValue("h", rc);
}

/* computer move */
static PyObject *
engine_cmove(PyObject *self, PyObject *args)
{
    if (verbose)
    {
        printf("gshogi builtin engine settings\n");
        printf("  - computer player (side to move) is: %d", computer);
        if (computer == white)
        {
            printf(" (white)\n");
        }
        else
        {
            printf(" (black)\n");
        }
        printf("  - depth=%i\n",MaxSearchDepth);
        printf("  - nodes=%d",NodeCntLimit);
        if (NodeCntLimit > 0)
        {
            printf("\n");
        }
        else
        {
            printf(" (no limit)\n");
        }
        printf("  - tournament (classical) TC (true/false): %d\n", TCflag);
        printf("  - tournament TC minutes: %d\n", TCminutes);
        printf("  - tournament TC seconds: %d\n", TCseconds);
        printf("  - max response time if not using tournament TC (centiseconds): %d\n", MaxResponseTime);
    }
    winner = 0;
    compptr = (compptr + 1) % MINGAMEIN;

    if (!(flag.quit || flag.mate || flag.force))
    {
#ifdef INTERRUPT_TEST
        printf("starting search...\n");
#endif
        Py_BEGIN_ALLOW_THREADS
        SelectMove(computer, FOREGROUND_MODE);
        Py_END_ALLOW_THREADS

        if (computer == white)
        {
            if (flag.gamein)
            {
                TimeCalc();
            }
            else if (TimeControl.moves[computer] == 0)
            {
                if (XC)
                {
                    if (XCmore < XC)
                    {
                        TCmoves = XCmoves[XCmore];
                        TCminutes = XCminutes[XCmore];
                        TCseconds = XCseconds[XCmore];
                        XCmore++;
                    }
                }
                 SetTimeControl();
            }
        }
    }

    /*
    short side;
    for (side = black; side <= white; side++)
    {

        short piece, c;
        printf((side == black)?"black ":"white ");

        side = white;

        for (piece = pawn; piece <= king; piece++)
        {
            c = Captured[side][piece];
            printf("%i%c ", c, pxx[piece]);

        }

        printf("\n");


    }
    */

    return Py_BuildValue("s", mvstr[0]);
}

/* user has issued a movenow command */
static PyObject *
engine_movenow(PyObject *self, PyObject *args)
{
    flag.musttimeout = true;
    Py_RETURN_NONE;
}

/*

   values in engine

   board[l]
   0 - unoccupied
   1 - Pawn            (p)
   2 - Lance           (l)
   3 - Knight          (n)
   4 - Silver General  (s)
   5 - Gold General    (g)
   6 - Bishop          (b)
   7 - Rook            (r)
  14 - King            (k)


   colour
   0 - black
   1 - white
   2 - neutral

   promoted
   0 - not promoted
   1? - promoted

   -----------------------

   values in gui

   0 - unoccupied
   1 - Pawn            (p)
   2 - Lance           (l)
   3 - Knight          (n)
   4 - Silver General  (s)
   5 - Gold General    (g)
   6 - Bishop          (b)
   7 - Rook            (r)
   8 - King            (k)

   9 - promoted pawn            (+p)
  10 - promoted lance           (+l)
  11 - promoted Knight          (+n)
  12 - promoted Silver General  (+s)
  13 - promoted Bishop          (+b)
  14 - promoted Rook            (+r)



  Board used in gnushogi

                       ROW
    L N S G K G S N L   8     l = 72..80
    - R - - - - - B -   7     l = 63..71
    P P P P P P P P P   6     l = 54..62
    - - - - - - - - -   5     l = 45..53
    - - - - - - - - -   4     l = 36..44
    - - - - - - - - -   3     l = 27..35
    p p p p p p p p p   2     l = 18..26
    - b - - - - - r -   1     l =  9..17
    l n s g k g s n l   0     l =  0..8

COL 0 1 2 3 4 5 6 7 8

*/

/* get board */
static PyObject *
engine_getboard(PyObject *self, PyObject *args)
{

    PyObject *lst = PyList_New(81);

    char cpos[81][3] = { "aa", "bb", "cc", "dd"};

    int r,c,l;

    for (r = (NO_ROWS - 1); r >= 0; r--)
    {
        for (c = 0; c <= (NO_COLS - 1); c++)
        {
            char pc;

            l = locn((NO_ROWS - 1) - r, (NO_COLS - 1) - c);
            pc = (is_promoted[board[l]] ? '+' : ' ');

            if (color[l] == neutral)
            {
                cpos[l][0] = ' ';
                cpos[l][1] = '-';
                cpos[l][2] = '\0';
            }
            else if (color[l] == black)
            {
                cpos[l][0] = pc;
                cpos[l][1] = qxx[board[l]];
                cpos[l][2] = '\0';
            }
            else
            {
                cpos[l][0] = pc;
                cpos[l][1] = pxx[board[l]];
                cpos[l][2] = '\0';
            }
        }

    }


        lst = Py_BuildValue("[sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss]",   \
            cpos[0],cpos[1],cpos[2],cpos[3],cpos[4],cpos[5],cpos[6],cpos[7],cpos[8],cpos[9],cpos[10],cpos[11],cpos[12],cpos[13], \
            cpos[14],cpos[15],cpos[16],cpos[17],cpos[18],cpos[19],cpos[20],cpos[21],cpos[22],cpos[23],       \
            cpos[24],cpos[25],cpos[26],cpos[27],cpos[28],cpos[29],cpos[30],cpos[31],cpos[32],cpos[33],       \
            cpos[34],cpos[35],cpos[36],cpos[37],cpos[38],cpos[39],cpos[40],cpos[41],cpos[42],cpos[43],       \
            cpos[44],cpos[45],cpos[46],cpos[47],cpos[48],cpos[49],cpos[50],cpos[51],cpos[52],cpos[53], \
            cpos[54],cpos[55],cpos[56],cpos[57],cpos[58],cpos[59],cpos[60],cpos[61],cpos[62],cpos[63], \
            cpos[64],cpos[65],cpos[66],cpos[67],cpos[68],cpos[69],cpos[70],cpos[71],cpos[72],cpos[73], \
            cpos[74],cpos[75],cpos[76],cpos[77],cpos[78],cpos[79],cpos[80] \
    );


    return lst;

}

/* get captured pieces */
/* black 0P 0L 0N 0S 0G 0B 0R 0P 0L 0N 0S 0B 0R 0K */
/* white 0P 0L 0N 0S 0G 0B 0R 0P 0L 0N 0S 0B 0R 0K */

static PyObject *
engine_getcaptured_pieces(PyObject *self, PyObject *args)
{
    short side;
    char cp[NO_PIECES][3];
    PyObject *lst = PyList_New(NO_PIECES);
    short piece, c;

     if (!PyArg_ParseTuple(args, "h", &side))
        return NULL;

    for (piece = pawn; piece <= king; piece++)
    {
        short p = piece - 1;
        if ((c = Captured[side][piece]))
        {
            /* printf("%i%c ", c, pxx[piece]);   */
            cp[p][0] = c + '0';
            cp[p][1] = pxx[piece];
            cp[p][2] = '\0';
        }
        else
        {
            cp[p][0] = '\0';
        }
    }

    lst = Py_BuildValue("[ssssssssssssss]",   \
            cp[0],cp[1],cp[2],cp[3],cp[4],cp[5],cp[6],cp[7],cp[8],cp[9],cp[10],cp[11],cp[12],cp[13],cp[13] \
     );


    return lst;

}


/* set computer player to black or white*/
void set_player(short plyr)
{
    if (plyr == black)
    {
        player = black;
        opponent = black;
        computer = white;
    }
    else
    {
        player = white;
        opponent = white;
        computer = black;
    }
}


/* set computer player to black or white*/
void set_computer_player(short plyr)
{
    if (plyr == black)
    {
        player = white;
        opponent = white;
        computer = black;
    }
    else
    {
        player = black;
        opponent = black;
        computer = white;
    }
}


static PyObject *
engine_setfen(PyObject *self, PyObject *args)
{

    /*                                                                                       */
    /* USI SFEN string                                                                       */
    /*                                                                                       */
    /* uppercase letters for black pieces, lowercase letters for white pieces                */
    /*                                                                                       */
    /* examples:                                                                             */
    /*      lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1                  */
    /*      8l/1l+R2P3/p2pBG1pp/kps1p4/Nn1P2G2/P1P1P2PP/1PS6/1KSG3+r1/LN2+p3L w Sbgn3p 124   */

    /*

   values in engine

   board[l]
   0 - unoccupied
   1 - Pawn            (p)
   2 - Lance           (l)
   3 - Knight          (n)
   4 - Silver General  (s)
   5 - Gold General    (g)
   6 - Bishop          (b)
   7 - Rook            (r)
  14 - King            (k)


   colour
   0 - black
   1 - white
   2 - neutral

   promoted
   0 - not promoted
   1 - promoted

  Board used in gshogi

                       ROW
    L N S G K G S N L   8     l = 72..80
    - R - - - - - B -   7     l = 63..71
    P P P P P P P P P   6     l = 54..62
    - - - - - - - - -   5     l = 45..53
    - - - - - - - - -   4     l = 36..44
    - - - - - - - - -   3     l = 27..35
    p p p p p p p p p   2     l = 18..26
    - b - - - - - r -   1     l =  9..17
    l n s g k g s n l   0     l =  0..8

COL 0 1 2 3 4 5 6 7 8

*/

    char *fen;
    char *p;
    int c, i, j, z;
    short sq;
    short side, isp;
    char ch;
    char num[3];

    if (!PyArg_ParseTuple(args, "s", &fen))
        return NULL;

    p = fen;
    NewGame();
    flag.regularstart = false;
    Book = false;

    i = NO_ROWS - 1; /* i is row index */
    j = 0; /* j is column index */

    while (*p != ' ')
    {
        if (*p == '/')
        {
            j = 0;
            i--;
            p++;
        }

        if (*p == '+')
        {
            isp = 1;
            p++;
        }
        else
        {
            isp = 0;
        }

        sq = i * NO_COLS + j;

        if (isdigit(*p))
        {
            num[0] = *p;
            num[1] = '\0';
            for (z = 0; z < atoi(num); z++)
            {
                board[sq] = no_piece;
                color[sq] = neutral;
                j++;
                sq = i * NO_COLS + j;
            }
            j--;
        }
        else
        {
            for (c = 0; c < NO_PIECES; c++)
            {
                if (*p == qxx[c])
                {
                    if (isp)
                    {
                        board[sq] = promoted[c];
                    }
                    else
                    {
                        board[sq] = unpromoted[c];
                    }

                    color[sq] = white;
                }
            }

            for (c = 0; c < NO_PIECES; c++)
            {
                if (*p == pxx[c])
                {
                    if (isp)
                    {
                        board[sq] = promoted[c];
                    }
                    else
                    {
                        board[sq] = unpromoted[c];
                    }

                    color[sq] = black;
                }
            }
        }
        p++;
        j++;
    }

    /* side to move */
    p++;
    if (*p == 'w')
    {
        set_player(white);
    }
    else if (*p == 'b')
    {
        set_player(black);
    }
    else
    {
        fprintf(stderr, "error - side to move not valid in sfen: %c\n",*p);
        set_computer_player(black);
    }

    p++;
    if (*p != ' ')
    {
        fprintf(stderr, "error in sfen string. no space after side to move\n");
    }

    /* pieces in hand */
    ClearCaptured();
    p++;
    if (*p != '-')
    {
        while (*p != ' '  && *p != '\n' && *p != '\0')
        {
            strcpy(num, "1");
            if (isdigit(*p))
            {
                num[0] = *p;
                num[1] = '\0';
                p++;
                if (isdigit(*p))
                {
                    num[1] = *p;
                    num[2] = '\0';
                    p++;
                }

            }

            ch = *p;
            if (isupper(ch))
            {
                side = black;
                ch = tolower(ch);
            }
            else
            {
                side = white;
            }


            if (ch == 'p')
            {
                Captured[side][pawn]   = atoi(num);
            }
            else if (ch == 'l')
            {
                Captured[side][lance]  = atoi(num);
            }
            else if (ch == 'n')
            {
                Captured[side][knight] = atoi(num);
            }
            else if (ch == 's')
            {
                Captured[side][silver] = atoi(num);
            }
            else if (ch == 'g')
            {
                Captured[side][gold]   = atoi(num);
            }
            else if (ch == 'b')
            {
                Captured[side][bishop] = atoi(num);
            }
            else if (ch == 'r')
            {
                Captured[side][rook]   = atoi(num);
            }
            p++;
        }

    }

    Game50 = 1;
    ZeroRPT();
    InitializeStats();
    UpdateDisplay(0, 0, 1, 0);
    Sdepth = 0;
    hint = 0;

    Py_RETURN_NONE;
}


static PyObject *
engine_getlegalmoves(PyObject *self, PyObject *args)
{
    static short pnt;
    struct leaf  *node;
    PyObject *lst = PyList_New(GameCnt);
    int nummoves, len, maxlen;
#if defined(_WIN32)
    char legalmoves[10000];
#endif
    MoveList(opponent, 2, -1, true);
    generate_move_flags = false;
    pnt = TrPnt[2];

    nummoves = (TrPnt[3] - TrPnt[2]);
#if !defined(_WIN32)
    char legalmoves[nummoves * ((int)sizeof(mvstr[0]) + 1) * 4 + 1];
#endif
    legalmoves[0] = '\0';

    while (pnt < TrPnt[3])
    {
        node = &Tree[pnt++];
        algbr(node->f, node->t, (short) node->flags);
        /*printf("move: %s %s %s %s\n", mvstr[0], mvstr[1], mvstr[2], mvstr[3]);*/

        strcat(legalmoves, mvstr[0]);
        strcat(legalmoves, ",");

        strcat(legalmoves, mvstr[1]);
        strcat(legalmoves, ",");

        strcat(legalmoves, mvstr[2]);
        strcat(legalmoves, ",");

        strcat(legalmoves, mvstr[3]);
        strcat(legalmoves, ";");

    }

    len = (int)strlen(legalmoves);
    maxlen = (int)sizeof(legalmoves);
    if (len > maxlen)
    {
        printf("error in getlegalmoves, char length is too small\n");
        printf("len/maxlen of legalmoves is %i / % i \n", len, maxlen);
    }

    lst = Py_BuildValue("s",   \
            legalmoves \
    );

    return lst;

}


static PyObject *
engine_getmovelist(PyObject *self, PyObject *args)
{
    PyObject *lst = PyList_New(GameCnt);
#if !defined(_WIN32)
    char movelist[GameCnt * 11 + 10];
#else
    char movelist[10000];
#endif
    short i, f, t;
    int len, maxlen;
    char *p;
    char cap = ' ';
    char prm = ' ';

    movelist[0] = '\0';
    for (i = 1; i <= GameCnt; i++)
    {
        struct GameRec  *g = &GameList[i];

        f = g->gmove >> 8;
        t = (g->gmove & 0xFF);
        algbr(f, t, g->flags);

        /* set prm to + if piece is promoted */
        if (f > NO_SQUARES)
        {
            prm = ' ';
        }
        else if (is_promoted[g->fpiece])
        {
            prm = '+';
        }
        else
        {
            prm = ' ';
        }

        /* set cap to x if the move resulted in a capture */
        if (g->piece != no_piece)
        {
            cap = 'x';
        }
        else
        {
            cap = '-';
        }

        p = movelist + strlen(movelist);
        *p = cap;
        p++;
        *p = ';';
        p++;

        *p = prm;
        p++;
        *p = ';';
        p++;

        *p = pxx[g->fpiece];
        p++;
        p[0] = '\0';

        strcat(movelist, (f > NO_SQUARES) ? &mvstr[0][1] : mvstr[0]);
        strcat(movelist, ",");
        /*printf("%s %s %s %s %c\n", mvstr[0], mvstr[1], mvstr[2], mvstr[3], cap);*/
    }

    p = movelist + strlen(movelist);
    p--;
    if (*p == ',') *p = '\0';

    len = (int)strlen(movelist);
    maxlen = (int)sizeof(movelist);
    if (len > maxlen)
    {
        printf("error in getmovelist, char length is too small\n");
        printf("len/maxlen of movelist is %i / % i \n", len, maxlen);
    }

    lst = Py_BuildValue("s",   \
           movelist \
    );

    return lst;
}

static PyMethodDef EngineMethods[] = {
//    PyModuleDef_HEAD_INIT,
    {"init", engine_init, METH_VARARGS, "Initialise the engine."},
    {"hmove", engine_hmove, METH_VARARGS, "Human move."},
    {"cmove", engine_cmove, METH_VARARGS, "Computer move."},
    {"movenow", engine_movenow, METH_VARARGS, "Move Now."},
    {"getboard", engine_getboard, METH_VARARGS, "Get Board."},
    {"getcaptured", engine_getcaptured_pieces, METH_VARARGS, "Get Captured Pieces."},
    {"command", engine_command, METH_VARARGS, "Command."},
    {"getmate", engine_getmate, METH_VARARGS, "Check if Mate."},
    {"getwinner", engine_getwinner, METH_VARARGS, "Check if Mate."},
    {"getmove", engine_getmove, METH_VARARGS, "get Whites move."},
    {"genbook", engine_genbook, METH_VARARGS, "create binary opening book."},
    {"info", engine_info, METH_VARARGS, "print engine data."},
    {"setplayer", engine_setplayer, METH_VARARGS, "set player to black."},
    {"loadgame", engine_loadgame, METH_VARARGS, "load game."},
    {"savegame", engine_savegame, METH_VARARGS, "save game."},
    {"depth", engine_depth, METH_VARARGS, "set search depth."},
    {"nodes", engine_nodes, METH_VARARGS, "set search nodes limit."},
    {"setfen", engine_setfen, METH_VARARGS, "set start position from sfen."},
    {"getmovelist", engine_getmovelist, METH_VARARGS, "get the list of moves in the current game."},
    {"getlegalmoves", engine_getlegalmoves, METH_VARARGS, "get the list of legal moves for the player."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef enginedef = {
    PyModuleDef_HEAD_INIT,
    "enginemodule",      /* m_name */
    "This is the engine module",  /* m_doc */
    -1,                  /* m_size */
    EngineMethods,       /* m_methods */
    NULL,                /* m_reload */
    NULL,                /* m_traverse */
    NULL,                /* m_clear */
    NULL,                /* m_free */
};

PyMODINIT_FUNC PyInit_engine(void)
{
    return PyModule_Create(&enginedef);
}
