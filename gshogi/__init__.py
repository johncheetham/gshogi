import os
import gettext
import locale

from . import gv

# translate strings in python files
localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
gettext.install(gv.domain, localedir)

# translate strings in glade files
locale.bindtextdomain(gv.domain, localedir)

