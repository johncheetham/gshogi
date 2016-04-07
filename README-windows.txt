
You can run gshogi on windows by following these steps.
I tested this on windows 10.

 1. Install python 3.4

    Don't use Python 3.5 since pygobject for windows doesn't support it.    

    Download from https://www.python.org/downloads/
    I used version 3.4.4 64 bit

    install for all users (which is the default)

    Accept the default install directory
        C:\Python34\

    in customisations select
        Add python.exe to path


 2. Install pygobject for windows

    Download the latest version from
    http://sourceforge.net/projects/pygobjectwin32/files/latest/download

    I used pygi-aio-3.18.2_rev5-setup.exe

    Install into default location

    It will ask which packages you want to install.

    Choose these base packages:

       Gdk-Pixbuf 2.32.3
       GTK+ 3.18.8
       Pango 1.36.7

    choose non gnome libraries to install
        none

    choose development packages to install
        none


 3. Install Visual Studio 2015 Community Edition

    Download from https://www.visualstudio.com/en-us/downloads/visual-studio-2015-downloads-vs.aspx


 4. Install gshogi

    Open a command prompt and CD into the gshogi folder.

    # enter this command    
    set VS100COMNTOOLS=%VS140COMNTOOLS%

    # build it
    c:\Python34\python.exe setup.py build

    # run it
    c:\Python34\python.exe run.py

