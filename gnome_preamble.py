# used when creating windows installer
os.environ['PATH'] += os.pathsep + os.path.join(pkgdir, 'gnome')
import gshogi.gv
gshogi.gv.installed = False
