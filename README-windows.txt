Windows downloads of gshogi are available on the website.

These instructions are for developers or those who wish to compile it
themselves.

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

    If you just want to build the engine module you can probably skip this 
    step.

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


 3. Compile gshogi

    I have used visual studio 2017 and mingw32/mingw-w64.

    For creating the windows installers I used mingw since Visual studio requires
    that users install the Microsoft Visual C++ Redistributable for vs 2017.

    Using MinGW-W64 for 64 bit build

        Install MinGW-W64 

            Download from https://sourceforge.net/projects/mingw-w64/files/
            Get and run MinGW-W64-install.exe
 
        Compile gshogi

            From the windows menu select MinGW-W64 project/Run terminal
            change directory into gshogi folder

            compile it
            "c:\Program Files\Common Files\Python\3.4\python.exe" setup.py build --compiler=mingw32


    Using MinGW32 for 32 bit build

        Install Mingw32 from mingw.org (filename: mingw-get-setup)
        This installs into C:\MinGW

        Launch MSYS terminal by clicking on C:\MinGW\msys\1.0\msys.bat

        change directory into gshogi folder

        compile it
        /c/Program\ Files/Common\ Files/Python/3.4/python.exe setup.py build --compiler=mingw32


    Using Visual Studio 2017

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



