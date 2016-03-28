Note these instructions are out of date. They refer to python 2.7 and
the requirement is now for python 3.

You can run gshogi on windows by following these steps.

Install Prerequisites
---------------------

 1. Install python2.7

    Download from https://www.python.org/downloads/
    Select to install for all users, and select the default
    installation location, c:\Python27

    Optionally Add to path
        C:\Python27;C:\Python27\Scripts
       (means you don't have to type full path to python, pip etc)

    I tested with python 2.7.10.
    Note gshogi doesn't work with python 3.


 2. Install pygobject for windows

    Download the latest version from
    http://sourceforge.net/projects/pygobjectwin32/files/latest/download

    I used pygi-aio-3.14.0_rev22.setup.exe

    Install into c:\python27\lib\site-packages

    It will ask which packages you want to install.

    Choose these base packages:

       Gdk-Pixbuf 2.31.6
       GTK+ 3.14.15
       Pango 1.36.7

    choose non gnome libraries to install
        none

    choose development packages to install
        none


Install gshogi
--------------
There are some prebuilt versions at this link:
https://www.dropbox.com/sh/0z8pxbvaa927sd2/AAAsy2qpD_wglMXHdvapZOhga?dl=0

Double click the version for your system (32 or 64 bit) and install it.

Finally you may want to create a shortcut on the desktop.
To do this find c:\Python27\Scripts\gshogi.exe in explorer,
right click it and select send to desktop (create shortcut).


Compile it yourself
-------------------
To compile it go to http://aka.ms/vcpython27 and install
Microsoft Visual C++ Compiler for Python 2.7.

Then type c:\Python27\python.exe setup.py build.
Then c:\Python27\python.exe run.py to run it.

You can also compile using MinGW compiler.
To use MinGW use this command:
    c:\Python27\python.exe setup.py build --compiler=mingw32

If you get libpython27.a: error adding symbols: File format not recognized
with MinGW compiler then you need to create a new libpython27.a file
using pexports/dlltool.
