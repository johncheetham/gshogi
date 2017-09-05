import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, Extension

import os
import sys
import shutil

import gshogi.constants

assert sys.version_info >= (3,0)

VERSION = gshogi.constants.VERSION

macros = [
        ("HAVE_BCOPY", "1"),
        ("HAVE_ERRNO_H", "1"),
        ("HAVE_FCNTL_H", "1"),
        ("HAVE_MEMCPY", "1"),
        ("HAVE_MEMSET", "1"),
        ("HAVE_SETLINEBUF", "1"),
        ]

if os.name == "nt":
    # windows
    macros.append(("HASHFILE", "1"))
    data_files=[]
else:
    # linux
    macros.append(("HAVE_UNISTD_H", "1"))
    macros.append(("HASHFILE", "\"data/gnushogi.hsh\""))
    data_files=[
      (sys.prefix+'/share/applications',['gshogi.desktop']),
      (sys.prefix+'/share/pixmaps', ['gshogi.png'])]

package_data_list = ["data/opening.bbk"]

# translations
if shutil.which("msgfmt") is None:
    print("msgfmt not found. Translations will not be built")
else:
    localedir = "locale"
    dirlist = os.listdir(localedir)
    for d in dirlist:
        pth = os.path.join(localedir, d)
        if not os.path.isdir(pth):
            continue
        filein = os.path.join(pth, "LC_MESSAGES", "gshogi.po")
        pthout = os.path.join("gshogi", pth, "LC_MESSAGES")
        if not os.path.exists(pthout):
            try:
                os.makedirs(pthout)
            except OSError as exc:
                print("Unable to create locale folder", pthout)
                sys.exit()
        fileout = os.path.join(pthout, "gshogi.mo")
        os.popen("msgfmt %s -o %s" % (filein, fileout))
        package_data_list.append(os.path.join(pth, "LC_MESSAGES", "gshogi.mo"))

module1 = Extension("gshogi.engine", sources=[
    "engine/enginemodule.c",
    "engine/init.c",
    "engine/globals.c",
    "engine/eval.c",
    "engine/search.c",
    "engine/pattern.c",
    "engine/book.c",
    "engine/util.c",
    "engine/commondsp.c",
    "engine/genmove.c",
    "engine/rawdsp.c",
    "engine/attacks.c",
    "engine/tcontrl.c",
    "engine/sysdeps.c",
    ],
    define_macros=macros,
)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name="gshogi",
      version=VERSION,
      description="A Shogi Program (Japanese Chess)",
      ext_modules=[module1],
      include_package_data=True,
      author="John Cheetham",
      author_email="developer@johncheetham.com",
      url="http://www.johncheetham.com/projects/gshogi/",
      long_description=read("README.rst"),
      platforms=["Linux"],
      license="GPLv3+",
      zip_safe=False,

      packages=["gshogi"],
      package_data={
          "gshogi": package_data_list,
      },
      data_files=data_files,
      entry_points={
          "gui_scripts": [
              "gshogi = gshogi.gshogi:run",
          ]
      },

      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: X11 Applications :: GTK",
          "Intended Audience :: End Users/Desktop",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python",
          "Programming Language :: C",
          "Topic :: Games/Entertainment :: Board Games",
          ],

      )
