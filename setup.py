from distutils.core import setup, Extension
from glob import glob

import os, sys, string

if (sys.argv[1] == 'install'):
    if (not os.path.exists('data/opening.bbk')):
        print "warning - opening book not found"
        print "you must run 'python setup.py build' first to build the opening book" 
        sys.exit()

module1 = Extension('gshogi.engine',
     sources = ['engine/enginemodule.c', 
                'engine/init.c',  
                'engine/globals.c', 
                'engine/eval.c',  
                'engine/search.c', 
                'engine/pattern.c',                                   
                'engine/book.c', 
                'engine/util.c',
                'engine/commondsp.c',
                'engine/genmove.c',
                'engine/rawdsp.c',
                'engine/attacks.c',
                'engine/tcontrl.c', 
                'engine/sysdeps.c',                                   
                ],    
    define_macros=[('HASHFILE', '\"data/gnushogi.hsh\"'),
                   ('HAVE_BCOPY', '1'),
                   ('HAVE_ERRNO_H', '1'), 
                   ('HAVE_FCNTL_H', '1'),
                   ('HAVE_MEMCPY', '1'),
                   ('HAVE_MEMSET', '1'),
                   ('HAVE_SETLINEBUF', '1'),  
                   ('HAVE_UNISTD_H', '1'),                 
                ],
     )

setup (name = 'gshogi',
    version = '0.4.5',
    description = 'A Shogi Program (Japanese Chess)',
    ext_modules = [module1],
    author='John Cheetham',
    author_email='developer@johncheetham.com',  
    url='http://www.johncheetham.com/projects/gshogi/', 
    long_description='A Shogi program for Linux written in Python, PyGI (GTK3), C.',
    platforms = ['Linux'],

    license = "GPLv3+",

    packages=['gshogi'],    

    classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: X11 Applications :: GTK',
          'Intended Audience :: End Users/Desktop',                
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: POSIX :: Linux',          
          'Programming Language :: Python',
          'Programming Language :: C',
          'Topic :: Games/Entertainment :: Board Games',
          ],
    data_files = [("share/gshogi/images", glob('images/*.png')),
            ("share/gshogi/images/eastern", glob('images/eastern/*.png')),
            ("share/gshogi/images/western", glob('images/western/*.png')),
            ("share/gshogi/glade", glob('glade/*.glade')),
            ("share/gshogi/data", ['data/opening.bbk']),
            ("share/doc/gshogi-0.4.5", ["README", "LICENSE", "ChangeLog"]), 
            ('share/applications',['gshogi.desktop']),
            ('share/pixmaps', ['gshogi.png']),           
    ],    
    scripts = [
        'scripts/gshogi'
    ]
               
    )

if (sys.argv[1] != 'build'):
    sys.exit()
  
#
# build the opening book
#

(osname, host, release, version, machine) = os.uname()
osname = string.lower(osname)
osname = string.replace(osname, '/', '')
machine = string.replace(machine, ' ', '_')
machine = string.replace(machine, '/', '-')
plat_name = "%s-%s" % (osname, machine)
plat_specifier = ".%s-%s" % (plat_name, sys.version[0:3])
build_lib = "lib" + plat_specifier
pypath = os.path.join("build", build_lib)
pypath = os.path.join(pypath, "gshogi")
sys.path.append(pypath) 

import engine

text_opening_book = 'data/gnushogi.tbk'
bin_opening_book = 'data/opening.bbk'
booksize = 8000
bookmaxply = 40

# check input file exists
if (not os.path.exists(text_opening_book)):
    print "Input file", text_opening_book, "not found"
    sys.exit()

# delete the output file if it exists
try:
    os.remove(bin_opening_book)
except OSError, oe:
    pass

# initialise the engine
verbose = False
engine.init(bin_opening_book, verbose)

# call engine function to generate book file
engine.genbook(text_opening_book, bin_opening_book, booksize, bookmaxply)



