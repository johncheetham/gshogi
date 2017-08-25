Windows downloads of gshogi are available on the website.

These instructions are for developers or those who wish to compile it
themselves.

You can run gshogi on windows by following these steps.
I tested this on windows 10.

 1. Install python 3.4

    Don't use later versions since pygobject for windows doesn't support it.

    Download from https://www.python.org/downloads/
    I used version 3.4.4 64 bit

    install for all users (which is the default)

    Accept the default install directory
        C:\Python34\


 2. Install pygobject for windows

    If you just want to build the engine module you can probably skip this 
    step.

    Download the latest version from
    http://sourceforge.net/projects/pygobjectwin32/files/latest/download

    I used pygi-aio-3.24.1_rev1.

    Enter 'No' to portable python installation.

    For choose python destination to install select version 3.4.
    This will install into C:\Python34\Lib\site-packages

    For choose available GNOME/Freedesktop libraries to install select these packages

       Base Packages
       Gdk-Pixbuf 2.36.6
       GTK+ 3.18.9
       Pango 1.40.6

    For choose available non gnome libraries to install
        none

    For choose development packages to install
        none


 3. Compile gshogi

    Install Visual Studio 2017 Community Edition

        Download from https://www.visualstudio.com/downloads/

        When installing select the Python development workload
        and the Native development tools option.

    compile gshogi

        Open x64 Native Tools Command prompt for VS 2017 from
        the start menu

        CD into the gshogi folder.

        # enter this command    
        set VS100COMNTOOLS=%VS140COMNTOOLS%

        # build it
        c:\Python34\python.exe setup.py build

    run it

        c:\Python34\python.exe run.py

