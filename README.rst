gshogi - John Cheetham - http://www.johncheetham.com/projects/gshogi

Description
-----------
gshogi is a program to play Shogi (Japanese Chess). It has a builtin
engine and can also use USI engines. It is written in python3/C and runs
on GTK3 (PyGI) desktops.

It's licensed under the GPL v3+ (see the file named LICENSE) and aimed mainly
at Linux users.

It uses GTK3 for the gui and C for the engine code.

See the project homepage for more information on gshogi and USI engines.


Installation
------------
Python 3 is required. If you are using a system that uses python 2 as default
(do python -V to check) then you need to use python3 for commands and package
names. For example the package name will be python3-cairo instead of
python-cairo and the build command will be python3 setup.py build.


You need to install these packages first:

    gcc python python-devel python-cairo python-gobject gtk3


Running gshogi from the Source Directory

    You can run gshogi from the source directory without
    doing the full install.

    To do this:

        Enter 'python setup.py build' to build it.

        Then 'python run.py' to run it.


Installing on the system

    Enter 'python setup.py build' to build it (as normal user).
    Then 'python setup.py install' to install it (as root user).

    Note:

        You must run 'python setup.py build' first since this creates
        the opening book (don't just run 'python setup.py install'
        on it's own)

        You can check the build step worked by looking for a file called
        engine.so under the build directory.

        gshogi should now be installed on your system. You can launch it from
        the gnome menu (under games) or type 'gshogi' in any terminal window.

        There is no uninstall (setuptools doesn't have one). If you need to
        uninstall you have to make a note of the file names and then delete
        them manually.

        If running the build/install multiple times it's best to delete the
        build folder each time.

Note that the binary opening book (data/opening.bbk) has a different format
on 32 bit and 64 bit systems. You cannot use the 32 bit book on a 64 bit
system and vice versa. For this reason the opening book is created during the
install when you do 'python setup.py build'.

Here is some help for installing on specific distros.

For Fedora 23:

    Install packages (as root user)

        dnf install gcc redhat-rpm-config python3 python3-devel python3-cairo python3-gobject

    build (as normal user)

        python3 setup.py build

    run from the source directory

        python3 run.py

    Install on the system (as root user)

        python3 setup.py install

    run the installed version

        gshogi
    

For Debian 8 Jessie:

    Install packages (as root user)

        apt-get install gcc python3-dev python3-gi-cairo

    build (as normal user)

        python3 setup.py build

    run from the source directory

        python3 run.py

    Install on the system (as root user)

        python3 setup.py install

    run the installed version

        gshogi

For Arch:

    Install packages (as root user)

        pacman -S python python-gobject python-cairo gcc

    build (as normal user)

        python setup.py build

    run from the source directory

        python run.py

    Install on the system (as root user)

        python setup.py install

    run the installed version

        gshogi


Usage
-----
You play black (the pieces at the bottom of the board). The computer plays
white (the pieces at the top of the board). Press the green go button to
start the clock. To move a piece click on it and then click on the square
you want to move it to (or drag it and drop it).

Also you can play one engine against another which is good for comparing
USI engines.

See http://en.wikipedia.org/wiki/Shogi for the rules of Shogi.

If you want to see the USI commands then start it from a terminal with:

    gshogi -vusi     (or ./run.py -vusi if not installed)

For full debugging output use the command:

        gshogi -v    (or ./run.py -v if not installed)


File Support
------------
You can load/save games in PSN format or in gshog format.
It is recommended to use PSN format.

gshogi can also read multi-game PSN files.

Use gshog format for exchanging games with GNU Shogi.


Edit Board Function
-------------------
When edting the board position you can increase the count of a piece in
the komadai by right-clicking on it. Left-click on it to decrease the
count.

To add a white piece to the main board right-click on the square you
want to add the piece to then select the piece from the pop-up menu.
To add a black piece left-click on the square.


Time control/Level support
--------------------------
Examples of time controls that can be used with gshogi.

These were tested with the gse 0.1.4 engine.
Note that not all USI engines will work with all time controls.
Most engines work OK with byoyomi so use that if you have problems.

Note that times on the go command are in milliseconds.

byoyomi

    e.g. 60 minutes game time plus 30 seconds byoyomi
    This means the player can make as many or as few moves as they like
    in the 30 minutes and after that they will have 30 seconds per move.

    go btime 3600000 wtime 3600000 byoyomi 30000

    If you want a fixed time of 10 seconds per move:
    go btime 0 wtime 0 byoyomi 10000

    see http://en.wikipedia.org/wiki/Byoyomi

classical

    e.g. 5 moves in 10 minutes

    go btime 300000 wtime 300000 movestogo 40

Incremental

    e.g. 30 minutes game time and 10 seconds bonus time per move
    This means the basic time for the game is 30 minutes and after
    each move a bonus of 10 seconds is added to the clock.

    go btime 1800000 wtime 1800000 binc 10000 winc 10000

Fixed Time Per Move

    e.g. 20 seconds per move
    go movetime 20000

Fixed Search Depth

    e.g. Terminate the search when a depth of 8 is reached.

    go depth 8

Infinite search

    The search will go on indefinitely and will only terminate if
    a stop command (move now) is sent from the gui.

    go infinite

Fixed No. of Nodes

    The search will terminate after a fixed no. of nodes has been searched.

    go nodes 10000000


Note that byoyomi is not part of the original USI specification
(See http://www.glaurungchess.com/shogi/usi.html) but it is
supported in most USI engines.


Custom Pieces
-------------
You can load custom pieces using the 'Load Custom Pieces' button on the
'set pieces' menu.

To set up your own custom pieces you must provide images with these filenames.
You can use either png or svg files. If you use png change the file extension
from svg to png.

    Black Pieces:

        =======================   ============
        Piece                     Filename
        =======================   ============
        King                      kingB.svg
        Rook                      rookB.svg
        Bishop                    bishopB.svg
        Gold General              goldB.svg
        Silver General            silverB.svg
        Knight                    knightB.svg
        Lance                     lanceB.svg
        Pawn                      pawnB.svg
        Promoted Rook             rookPB.svg
        Promoted Bishop           bishopPB.svg
        Promoted Silver General   silverPB.svg
        Promoted Knight           knightPB.svg
        Promoted Lance            lancePB.svg
        Promoted Pawn             pawnPB.svg
        =======================   ============

The black piece images are mandatory. You can optionally provide images
for the white pieces as well. If you provide white piece images gshogi
will use them. If you don't it will use the black piece images and
rotate them through 180 degress.

    White Pieces:

        =======================   ============
        Piece                     Filename
        =======================   ============
        King                      kingW.svg
        Rook                      rookW.svg
        Bishop                    bishopW.svg
        Gold General              goldW.svg
        Silver General            silverW.svg
        Knight                    knightW.svg
        Lance                     lanceW.svg
        Pawn                      pawnW.svg
        Promoted Rook             rookPW.svg
        Promoted Bishop           bishopPW.svg
        Promoted Silver General   silverPW.svg
        Promoted Knight           knightPW.svg
        Promoted Lance            lancePW.svg
        Promoted Pawn             pawnPW.svg
        =======================   ============

See the project homepage to download an example.


Acknowledgements
----------------
gshogi uses C engine code and includes some board pieces from
GNU Shogi (version 1.3.2).

