#
#   usi.py
#
#   This file is part of gshogi
#
#   gshogi is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   gshogi is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with gshogi.  If not, see <http://www.gnu.org/licenses/>.
#
# timeout in line 152 set to 60 bw 8.2.17
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GLib
import os
import subprocess
import _thread
import time

from . import engine_debug
from . import engine_output
from . import gv


class Usi:

    def __init__(self, side):
#from gi.repository import GLib
        self.engine = "gshogi"
        self.path = ""
        self.engine_running = False
        self.newgame = False
        self.running_engine = ""
        self.stop_pending = False
        self.ponder_move = None
        self.side = side
        self.engine_debug = engine_debug.get_ref()
        self.engine_output = engine_output.get_ref()

    def start_engine(self, path):

        if path is None:
            path = self.path
            # if using builtin engine return (not USI)
            if self.engine == "gshogi":
                return

        # path is the path to the USI engine executable
        if not os.path.isfile(path):
            print("invalid usipath:", path)
            return False

        #
        # get engine working directory
        #from gi.repository import GLib
        orig_cwd = os.getcwd()
        if gv.verbose:
            print("current working directory is", orig_cwd)

        engine_wdir = os.path.dirname(path)
        if gv.verbose:
            print("engine working directory is", engine_wdir)

        # Attempt to start the engine as a subprocess
        if gv.verbose:
            print("starting engine with path:", path)
        path = path.strip()
        #print("engine:" + path)
        
        # when gshogi is started on windows with pythonw
        # a console window appears each time the engine starts
        # Use STARTUPINFO to suppress this
        if os.name == 'nt':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(
                path,bufsize = 1,   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=engine_wdir,
                universal_newlines=True,startupinfo=si)
        else:
            p = subprocess.Popen(
                path,bufsize = 1,   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=engine_wdir,
                universal_newlines=True)
        self.p = p
       
        #check process is running
        i = 0
        while (p.poll() is not None):
            i += 1
            if i > 40:
                print("unable to start engine process")
                return False
            time.sleep(0.25)

        if gv.verbose:
            print("pid=", p.pid)
        # start thread to read stdout
        self.op = []
        self.soutt = _thread.start_new_thread(self.read_stdout, ()) # commenting this line doesn't help

        # Tell engine to use the USI (universal shogi interface).
        self.command("usi\n")

        # wait for reply
        self.uservalues=gv.engine_manager.get_uservalues(self.engine)
        self.usi_option = []
        usi_ok = False
        i = 0
        while True:
            for l in self.op:
                l = l.strip()
                # print l
                if l.startswith("option"):
                    self.usi_option.append(self.option_parse(l))
                if l == "usiok":
                    usi_ok = True
            self.op = []
            if usi_ok:
                break
            i += 1
            if i > 40:
                print("error - usiok not returned from engine")
                return False
            time.sleep(0.25)

        # set pondering
        # self.command("setoption name USI_Ponder value false\n")
        if gv.engine_manager.get_ponder():
            ponder_str = "true"
        else:
            ponder_str = "false"
        self.command("setoption name USI_Ponder value " + ponder_str + "\n")

        # set hash value
        # self.command("setoption name USI_Hash value 256\n")
        self.command(
            "setoption name USI_Hash value " +
            str(gv.engine_manager.get_hash_value()) + "\n")
        
        # send setoption where we have a uservalue that differs from default
        uservalues = gv.engine_manager.get_uservalues(self.engine)
        for name, value in uservalues.items():
            self.command("setoption name " + name + " value " + value + "\n")
            
        # Ask if ready
        self.command("isready\n")

        # wait for reply
        ready_ok = False
        i = 0
        while True:
            for l in self.op:
                l = l.strip()
                # print l
                if l == "readyok":
                    ready_ok = True
            self.op = []
            if ready_ok:
                break
            i += 1
            if i > 200:
                print("error - readyok not returned from engine")
                return False
            time.sleep(0.25)

        # Tell engine we are starting new game
        self.command("usinewgame\n")
        self.engine_running = True
        self.running_engine = self.engine

        return True

    def option_parse(self, option_line):
        name = ""
        otype = ""
        default = ""
        minimum = ""
        maximum = ""
        userval = ""
        try:
            words = option_line.split()
            w = words.pop(0)
            if w != "option":
                if gv.verbose:
                    print("invalid option line ignored:", option_line)
                return

            # get option name
            w = words.pop(0)
            if w != "name":
                if gv.verbose:
                    print("invalid option line ignored:", option_line)
                return
            # name can contain spaces
            name = ''
            w = words.pop(0)
            while w != "type" and len(words) != 0:
                name += ' ' + w
                w = words.pop(0)
            name=name.strip()

            # get option type
            if w != "type":
                if gv.verbose:
                    print("invalid option line ignored:", option_line)
                return
            otype = words.pop(0)

            uvars = []
            while True:
                w = words.pop(0)
                w2 = words.pop(0)
                if w == "default":
                    default = w2
                elif w == "min":
                    minimum = w2
                elif w == "max":
                    maximum = w2
                elif w == "var":
                    uvars.append(w2)
                elif w == "userval":
                    userval = w2
                else:
                    if gv.verbose:
                        print("error parsing option:", option_line)
        except IndexError:
            pass
        userval = self.uservalues.get(name, default)
        return([name, otype, default, minimum, maximum, uvars, userval])
                       
    def command(self, cmd):
        e = self.side + "(" + self.get_running_engine().strip() + "):"
        if gv.verbose or gv.verbose_usi:
            print("->" + e + cmd.strip())
        GObject.idle_add(self.engine_debug.add_to_log, "->" + e + cmd.strip())
        try:
            # write as string (not bytes) since universal_newlines=True
            self.p.stdin.write(cmd)
        except AttributeError:
            GObject.idle_add(
                self.engine_debug.add_to_log,
                "# engine process is not running")
        except IOError:
            GObject.idle_add(
                self.engine_debug.add_to_log,
                "# engine process is not running")

    def stop_engine(self):
        if not self.engine_running:
            return

        self.stop_pending = True
        engine_stopped = False

        try:
            if gv.verbose:
                print("stopping engine")

            self.command("quit\n")

            # allow 2 seconds for engine process to end
            i = 0
            while True:
                if self.p.poll() is not None:
                    engine_stopped = True
                    break
                i += 1
                if i > 8:
                    if gv.verbose:
                        print("engine has not terminated after quit command")
                    break
                time.sleep(0.25)

            if not engine_stopped:
                if gv.verbose:
                    print("terminating engine subprocess pid ", self.p.pid)
                # SIGTERM
                self.p.terminate()
                i = 0
                while True:
                    if self.p.poll() is not None:
                        engine_stopped = True
                        break
                    i += 1
                    if i > 8:
                        if gv.verbose:
                            print("engine has not responded to terminate " \
                                  "command")
                        break
                    time.sleep(0.25)

            if not engine_stopped:
                if gv.verbose:
                    print("killing engine subprocess pid ", self.p.pid)
                # SIGKILL
                self.p.kill()
                i = 0
                while True:
                    if self.p.poll() is not None:
                        engine_stopped = True
                        break
                    i += 1
                    if i > 16:
                        if gv.verbose:
                            print("engine has not responded to kill command")
                        print("unable to stop engine pid", self.p.pid)
                        break
                    time.sleep(0.25)
        except:
            pass

        if gv.verbose:
            print()
        if engine_stopped:
            if gv.verbose:
                print("engine stopped ok")
        self.engine_running = False
        self.stop_pending = False
        self.running_engine = ""

    def read_stdout(self): 
        while True:
            try:
                e = ("<-" + self.side + "(" +
                     self.get_running_engine().strip() + "):")
                line= ""
                # python2 line = unicode(self.p.stdout.readline(), errors ='ignore')
                    # or: 'your iso 8859-15 text'.decode('iso8859-15')
                # python3 (doesn't work) lineb = self.p.stdout.readline().encode("utf-8", "ignore")
                #print(lineb)
                #line = str(lineb)
                #print(line, "line")
                line = self.p.stdout.readline()
                
                if line == "":
                    if gv.verbose:
                        print(e + "eof reached")
                    if gv.verbose:
                        print(e + "stderr:", self.p.stderr.read())
                    break
                #line = line[2:-3]
                #print(line)
                line = line.strip()
                
                if gv.verbose or gv.verbose_usi:
                    print(e + line)
                GObject.idle_add(self.engine_debug.add_to_log, e+line)
                if line.startswith("info"):
                    GObject.idle_add(
                        self.engine_output.add_to_log, self.side,
                        self.get_running_engine().strip(), line)
                self.op.append(line)
            except Exception as e:
                # line = e + "error"
                print("subprocess error in usi.py read_stdout:", e, "at:", line)
                

    def check_running(self):
        # check if engine has changed since last use
        if self.engine != self.running_engine:
            if self.engine_running:
                self.stop_engine()
                self.start_engine(None)
                return

        if not self.engine_running:
            self.start_engine(None)
        else:
            if self.p.poll() is not None:
                print("warning engine has stopped running - attempting " \
                      "to restart")
                self.start_engine(None)

    def set_newgame(self):
        self.newgame = True

    # Ask engine to make move
    def cmove(self, movelist, side_to_move):
        self.check_running()

        if self.newgame:
            self.command("usinewgame\n")
            self.newgame = False

        startpos = gv.gshogi.get_startpos()

        # if not startpos must be sfen
        if startpos != "startpos":
            startpos = "sfen " + startpos

        ml = ""
        for move in movelist:
            ml = ml + move + " "
        if ml == "":
            b = "position " + startpos + "\n"
        else:
            b = "position " + startpos + " moves " + ml.strip() + "\n"

        # b = "position sfen lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/" \
        #     "1B5R1/LNSGKGSNL b - 1 moves " + ml.strip() +  "\n"
        # b = "position sfen 8l/1l+R2P3/p2pBG1pp/kps1p4/Nn1P2G2/P1P1P2PP/" \
        #     "1PS6/1KSG3+r1/LN2+p3L w Sbgn3p 124 moves " + ml.strip() +  "\n"

        # Send the board position to the engine
        self.command(b)

        # times in milliseconds
        # btime = time_left[0]
        # wtime = time_left[1]
        # byoyomi = time_left[2]

        # clear the engine output window ready for next move
        GObject.idle_add(
            self.engine_output.clear, self.side,
            self.get_running_engine().strip())

        # print "calling time control module from usi module to get go command"
        gocmnd = gv.tc.get_go_command(side_to_move)
        self.gocmnd = gocmnd        # save for possible ponder
        # print "go command:", gocmnd

        # start the clock
        # print "starting clock from usi.py"
        gv.tc.start_clock(side_to_move)

        # send the engine the command to do the move
        self.command(gocmnd + "\n")

        # self.command(
        #   "go btime " + str(btime) +" wtime " + str(wtime) + " byoyomi " +
        #   str(byoyomi) + "\n")

        # Wait for move from engine
        i = 0
        bestmove = False
        while True:

            time.sleep(0.5)

            # i += 1
            # print "in cmove i=",i

            # if stop command sent while engine was thinking then return
            if not self.engine_running or self.stop_pending:
                return None, None

            for l in self.op:
                l = l.strip()
                if l.startswith("bestmove"):
                    bestmove = l[9:].strip()
                    if gv.verbose:
                        print("bestmove is ", bestmove)

                    # get ponder move if present
                    self.ponder_move = None
                    s = bestmove.find("ponder")
                    if s != -1:
                        self.ponder_move = bestmove[s + 7:].strip()
                        GObject.idle_add(
                            self.engine_output.set_ponder_move,
                            # set ponder move in engine output window
                            self.ponder_move, self.side)

                    # get bestmove
                    s = bestmove.find(" ")
                    if s != -1:
                        bestmove = bestmove[:s]
                    self.op = []

                    # update time for last move
                    GObject.idle_add(gv.tc.update_clock)
                    GObject.idle_add(gv.gui.set_side_to_move, side_to_move)
                    # Allow above update_clock to complete
                    # This must complete before we do start_clock for 
                    # human in gshogi.py  
                    time.sleep(0.1)
                    
                    return bestmove, self.ponder_move
            self.op = []

    def stop_ponder(self):
        # return if not pondering
        # if self.ponder_move is None:
        #    return
        # stop pondering
        self.command("stop\n")
        # Wait for move from engine
        i = 0
        bestmove = False
        while True:

            time.sleep(0.5)

            # i += 1
            # print "in stop ponder i=",i

            # if stop command sent while engine was thinking then return
            if not self.engine_running or self.stop_pending:
                return None, None

            for l in self.op:
                l = l.strip()
                if l.startswith("bestmove"):
                    bestmove = l[9:].strip()
                    if gv.verbose:
                        print("ponder bestmove is ", bestmove)

                    # get ponder move if present
                    ponder_move = None
                    s = bestmove.find("ponder")
                    if s != -1:
                        ponder_move = bestmove[s + 7:].strip()

                    # get bestmove
                    s = bestmove.find(" ")
                    if s != -1:
                        bestmove = bestmove[:s]
                    self.op = []

                    return bestmove, ponder_move
            self.op = []

    def send_ponderhit(self, side_to_move):

        # start the clock
        gv.tc.start_clock(side_to_move)

        self.command("ponderhit\n")
        # Wait for move from engine
        i = 0
        bestmove = False
        while True:

            time.sleep(0.5)

            # i += 1
            # print "in send ponder i,side=",i,self.side

            # if stop command sent while engine was thinking then return
            if not self.engine_running or self.stop_pending:
                return None, None

            for l in self.op:
                l = l.strip()
                if l.startswith("bestmove"):
                    bestmove = l[9:].strip()
                    if gv.verbose:
                        print("bestmove is ", bestmove)

                    # get ponder move if present
                    self.ponder_move = None
                    s = bestmove.find("ponder")
                    if s != -1:
                        self.ponder_move = bestmove[s + 7:].strip()
                        GObject.idle_add(
                            self.engine_output.set_ponder_move,
                            # set ponder move in engine output window
                            self.ponder_move, self.side)

                    # get bestmove
                    s = bestmove.find(" ")
                    if s != -1:
                        bestmove = bestmove[:s]
                    self.op = []

                    # update time for last move
                    # print "updating clock from usi.py"
                    GLib.idle_add(gv.tc.update_clock)
                    GLib.idle_add(gv.gui.set_side_to_move, side_to_move)

                    return bestmove, self.ponder_move
            self.op = []

    def start_ponder(self, pondermove, movelist, cmove):

        startpos = gv.gshogi.get_startpos()

        # if not startpos must be sfen
        if startpos != "startpos":
            startpos = "sfen " + startpos

        ml = ""
        for move in movelist:
            ml = ml + move + " "
        # if ml == "":
        #    print "error empty movelist in ponder in usi.py"
        #    return

        ml = ml.strip()
        ml = ml + " " + cmove + " " + pondermove
        ml = ml.strip()

        # create the position string with the ponder move added
        b = "position " + startpos + " moves " + ml + "\n"

        # Send the board position to the engine
        self.command(b)

        pondercmd = "go ponder" + self.gocmnd[2:]
        self.command(pondercmd + "\n")

        # clear the engine output window ready for next move
        GObject.idle_add(
            self.engine_output.clear, self.side,
            self.get_running_engine().strip())

        return

    def get_options(self):
        return self.usi_option

    def set_options(self, options):
        self.usi_option = options

    def set_option(self, option):
        option = option + "\n"
        self.command(option)

    # used when adding new engines in engine_manager
    def test_engine(self, path):
        msg = ""
        name = ""

        # path is the path to the USI engine executable
        if not os.path.isfile(path):
            msg = "invalid path " + path
            return msg, name

        running = self.engine_running
        if running:
            self.stop_engine()

        # Attempt to start the engine as a subprocess
        engine_wdir = os.path.dirname(path)
        try:
            if os.name == 'nt':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.Popen(
                    path,bufsize = 1,   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, cwd=engine_wdir,
                    universal_newlines=True,startupinfo=si)
            else:
                p = subprocess.Popen(
                    path,bufsize = 1,   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, cwd=engine_wdir,
                    universal_newlines=True)  
        except OSError as oe:
            msg = "error starting engine: " + "OSError" + str(oe)
            return msg, name
        self.p = p

        # check process is running
        i = 0
        while (p.poll() is not None):
            i += 1
            if i > 40:
                msg = "not a valid USI engine"
                return msg, name
            time.sleep(0.25)

        # start thread to read stdout commented out (double?)
        self.op = []
        self.soutt = _thread.start_new_thread(self.read_stdout, ())

        # Tell engine to use the USI (universal shogi interface).
        self.command("usi\n")

        # wait for reply
        self.uservalues=gv.engine_manager.get_uservalues(self.engine)
        self.usi_option = []
        usi_ok = False
        i = 0
        while True:
            for l in self.op:
                l = l.strip()
                if l.startswith("id "):
                    w = l.split()
                    if w[1] == "name":
                        w.pop(0)
                        w.pop(0)
                        for j in w:
                            name = name + j + " "
                        name.strip()
                elif l.startswith("option"):    
                    self.usi_option.append(self.option_parse(l))
                elif l == "usiok":
                    usi_ok = True
            self.op = []
            if usi_ok:
                break
            i += 1
            if i > 40:
                msg = "not a valid USI engine"
                return msg, name
            time.sleep(0.25)

        try:
            self.command("quit\n")
            self.p.terminate()
        except:
            pass

        return msg, name

    def set_engine(self, ename, path):
        self.engine = ename
        if path is None:
            self.path = gv.engine_manager.get_path(ename)
        else:
            self.path = path

    def set_path(self, epath):
        self.path = epath

    def get_engine(self):
        return self.engine

    def get_running_engine(self):
        if self.running_engine == "":
            return self.engine
        else:
            return self.running_engine

    def USI_options(self):
        self.check_running()
        options = self.get_options()
        # option
        # [name, otype, default, minimum, maximum, uvars, userval]
        wdgts = []
        opt_i = -1
        for option in options:
            opt_i += 1
            name = option[0]
            otype = option[1]
            default = option[2]
            minimum = option[3]
            maximum = option[4]
            uvars = option[5]
            userval = option[6]
            # if in common engine settings then skip
            #if name in ("Hash", "Ponder"):
            #    continue
            wdgts.append((
                opt_i, name, otype, default, minimum, maximum, uvars, userval))

        diagtitle = self.get_engine()
        dialog = Gtk.Dialog(
            diagtitle, gv.gui.get_window(), 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        sw = Gtk.ScrolledWindow.new(None, None)
        dialog.vbox.pack_start(sw, True, True, 0)

        vb=Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        sw.add(vb)

        sw.show()
        vb.show()

        wlist = []
        for w in wdgts:
            opt_i, name, otype, default, minimum, maximum, uvars, userval = w
            #print(name)
            if otype == "spin":
                if minimum == "":
                    minimum = 0
                if maximum == "":
                    maximum = 10
                if default == "":
                    default = minimum
                if userval != "":
                    default = userval
                adj = Gtk.Adjustment(
                    value=float(default), lower=float(minimum), upper=float(maximum),
                    step_increment=1, page_increment=5, page_size=0)
                spinner = Gtk.SpinButton.new(adj, 1.0, 0)
                # spinner.set_width_chars(14)
                al = Gtk.Alignment.new(
                    xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
                al.add(spinner)

                lbl = Gtk.Label(label=name + ":")

                hb = Gtk.HBox(False, 0)
                hb.pack_start(lbl, False, False, 0)
                hb.pack_start(al, True, True, 10)

                vb.pack_start(hb, False, True, 0)

                v = (opt_i, adj, name, otype)
                wlist.append(v)

                lbl.show()
                spinner.show()
                al.show()
                hb.show()
            elif otype == "string":
                ent = Gtk.Entry()
                if userval != "":
                    default = userval
                ent.set_text(default)

                al = Gtk.Alignment.new(
                    xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
                al.add(ent)

                lbl = Gtk.Label(label=name + ":")

                hb = Gtk.HBox(False, 0)
                hb.pack_start(lbl, False, False, 0)
                hb.pack_start(al, True, True, 10)

                vb.pack_start(hb, False, True, 0)

                v = (opt_i, ent, name, otype)
                wlist.append(v)

                lbl.show()
                ent.show()
                al.show()
                hb.show()
            elif otype == "check":
                cb = Gtk.CheckButton(label=None)
                if userval != "":
                    default = userval
                if default == "true":
                    cb.set_active(True)
                else:
                    cb.set_active(False)
                al = Gtk.Alignment.new(
                    xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
                al.add(cb)

                lbl = Gtk.Label(label=name + ":")
                hb = Gtk.HBox(False, 0)
                hb.pack_start(lbl, False, False, 0)
                hb.pack_start(al, True, True, 10)

                vb.pack_start(hb, False, True, 0)

                v = (opt_i, cb, name, otype)
                wlist.append(v)

                lbl.show()
                cb.show()
                al.show()
                hb.show()
            elif otype == "combo":
                if userval != "":
                    default = userval
                combobox = Gtk.ComboBoxText()
                i = 0
                for v in uvars:
                    combobox.append_text(v)
                    if v == default:
                        combobox.set_active(i)
                    i += 1

                al = Gtk.Alignment.new(
                    xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
                al.add(combobox)
                al.show()
                combobox.show()

                lbl = Gtk.Label(label=name + ":")
                hb = Gtk.HBox(False, 0)
                hb.pack_start(lbl, False, False, 0)
                hb.pack_start(al, True, True, 10)

                vb.pack_start(hb, False, True, 0)

                v = (opt_i, combobox, name, otype)
                wlist.append(v)

                lbl.show()
                hb.show()
            elif otype == "button":
                b = Gtk.Button(label=name)
                al = Gtk.Alignment.new(
                    xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
                al.add(b)

                b.connect(
                    "clicked",
                    lambda widget: self.command(
                        "setoption name " +
                        widget.get_label() + "\n"))

                lbl = Gtk.Label(label=name + ":")
                hb = Gtk.HBox(False, 0)
                hb.pack_start(lbl, False, False, 0)
                hb.pack_start(al, True, True, 10)
                vb.pack_start(hb, False, True, 0)
                lbl.show()
                b.show()
                al.show()
                hb.show()
            else:
                if gv.verbose:
                    print("type ignored - ", otype)
                  
        # set size of scrollwindow to size of child            
        minsize, naturalsize = vb.get_preferred_size()
        sw.set_size_request(minsize.width+20, min(minsize.height, 500))

        dialog.set_default_response(Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            for w in wlist:
                opt_i, widge, name, otype = w
                if otype == "spin":
                    av = int(widge.get_value())
                elif otype == "string":
                    av = widge.get_text()
                elif otype == "check":
                    if widge.get_active():
                        av = "true"
                    else:
                        av = "false"
                elif otype == "combo":
                    av = widge.get_active_text()
                else:
                    if gv.verbose:
                        print("unknown type", otype)
                # setoption name <id> [value <x>]
                # usi.set_option(
                #   "option name LimitDepth type spin default 10 min 4 max 10")
                a = "setoption name " + name + " value " + str(av)
                self.set_option(a)
                # update user value
                options[opt_i][6] = str(av)
            self.set_options(options)
            gv.engine_manager.set_uservalues(self.engine, options)
        dialog.destroy()
        self.stop_engine()
