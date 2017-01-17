#
#   time_control.py
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

from gi.repository import Gtk
import time

from . import gv
if gv.installed:
    from gshogi import engine
else:
    import engine
from .constants import WHITE, BLACK


class Time_Control:

    def __init__(self):

        # time control defaults
        self.type = 0

        # byoyomi
        self.byo_hours = 0
        self.byo_minutes = 45
        self.byo_byoyomi = 10

        # classical
        self.init_cls_settings()

        # incremental
        self.inc_hours = 0
        self.inc_minutes = 45
        self.inc_bonus = 6

        # fixed time per move
        self.ftpm_seconds = 5

        # search depth
        self.dpth_depth = 4

        # search nodes
        self.nodes_nodes = 50000

    def init_cls_settings(self):
        self.cls_max_sessions = 3
        self.cls_settings = []
        for i in range(0, self.cls_max_sessions):
            moves_to_go = 40
            minutes = 5
            if i == 0:
                repeat_times = 1
            else:
                repeat_times = 0
            self.cls_settings.append((moves_to_go, minutes, repeat_times))

    #
    # called to initialise the clocks at the start of a new game
    #
    def reset_clock(self):
        # fields for go command
        # byoyomi
        if self.type == 0:
            self.wtime = (
                self.byo_hours * 60 * 60 + self.byo_minutes * 60) * 1000
            self.btime = self.wtime
        # classical
        elif self.type == 1:
            # fields for go command
            self.cls_bsession = 0
            self.cls_wsession = 0
            # set session to first with non-zero repeat value
            for i in range(0, self.cls_max_sessions):
                moves_to_go, mins, rep = self.cls_settings[i]
                if rep != 0:
                    self.cls_bsession = i
                    self.cls_wsession = i
                    break

            (moves_to_go, minutes, repeat_times) = self.cls_settings[
                                                        self.cls_bsession]
            self.wtime = int((minutes * 60) * 1000)
            self.btime = self.wtime
            self.wmoves_to_go = int(moves_to_go)
            self.bmoves_to_go = int(moves_to_go)
            self.wrepeat = repeat_times
            self.brepeat = repeat_times
        # incremental
        elif self.type == 2:
            self.wtime = (
                self.inc_hours * 60 * 60 + self.inc_minutes * 60) * 1000
            self.btime = self.wtime
        # fixed time per move
        elif self.type == 3:
            self.wtime = int(self.ftpm_seconds) * 1000
            self.btime = self.wtime

        self.set_toolbar_time_control(self.type, 0, WHITE)
        self.set_toolbar_time_control(self.type, 0, BLACK)

    #
    # get clock settings so they can be saved when quitting gshogi
    #
    def get_clock_settings(self):
        return (
            self.type, self.byo_hours, self.byo_minutes, self.byo_byoyomi,
            self.inc_hours, self.inc_minutes, self.inc_bonus,
            self.cls_settings, self.ftpm_seconds, self.dpth_depth,
            self.nodes_nodes)

    #
    # restore the clock settings to the values from the previous game when
    # starting up gshogi
    #
    def restore_clock_settings(self, clock_settings):
        (
            self.type, self.byo_hours, self.byo_minutes, self.byo_byoyomi,
            self.inc_hours, self.inc_minutes, self.inc_bonus, cls_settings,
            self.ftpm_seconds, self.dpth_depth, self.nodes_nodes
        ) = clock_settings

        # if classical settings can't be restored then init them to default
        # values
        if len(cls_settings) == 0:
            self.init_cls_settings()
        else:
            self.cls_settings = cls_settings

        # wtime/btime for go command
        # byoyomi
        if self.type == 0:
            self.wtime = (
                self.byo_hours * 60 * 60 + self.byo_minutes * 60) * 1000
            self.btime = self.wtime
        # incremental
        elif self.type == 2:
            self.wtime = (
                self.inc_hours * 60 * 60 + self.inc_minutes * 60) * 1000
            self.btime = self.wtime
        else:
            self.wtime = (
                self.byo_hours * 60 * 60 + self.byo_minutes * 60) * 1000
            self.btime = self.wtime

    #
    # gui for changing time control settings
    #
    def time_control(self, b):
        dialog = Gtk.Dialog(
            "Time Control", gv.gui.get_window(), 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK,
             Gtk.ResponseType.OK))
        dialog.set_title("Time Control")
        dialog.vbox.set_spacing(20)

        # list of time control types
        combobox = Gtk.ComboBoxText()
        combobox.append_text("Byoyomi")
        combobox.append_text("Classical")
        combobox.append_text("Incremental")
        combobox.append_text("Fixed Time Per Move")
        combobox.append_text("Fixed Search Depth")
        combobox.append_text("Infinite Search")
        combobox.append_text("Nodes")
        combobox.set_active(self.type)

        al = Gtk.Alignment.new(xalign=0.0, yalign=1.0, xscale=0.0, yscale=0.5)
        # top, bottom, left, right
        al.set_padding(9, 0, 9, 9)
        al.add(combobox)
        dialog.vbox.pack_start(al, False, True, 5)
        self.combobox = combobox

        dialog.connect("draw", self.dialog_expose_event)

        #
        # settings for the byoyomi time control type
        #
        #   byoyomi
        #       e.g. 60 mins available time plus 10 seconds byoyomi
        #       go btime 3600000 wtime 3600000 byoyomi 10000
        #

        # list of time control vboxes. 1 per time control type
        self.tcvb = [Gtk.VBox(False, 0) for x in range(8)]

        byo_frame1 = Gtk.Frame.new("Available Time")
        vb = Gtk.VBox(False, 0)
        byo_frame1.add(vb)

        # available time - hours
        minimum = 0
        maximum = 10
        default = self.byo_hours
        byo_adj_hours = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(byo_adj_hours, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        hb = Gtk.HBox(False, 0)
        hb.pack_start(Gtk.Label("Hours:"), False, False, 0)
        hb.pack_start(al, True, True, 10)
        vb.pack_start(hb, False, True, 0)

        # available time - minutes
        minimum = 0
        maximum = 59
        default = self.byo_minutes
        byo_adj_mins = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(byo_adj_mins, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        lbl = Gtk.Label(label="Minutes :")
        hb = Gtk.HBox(False, 0)
        hb.pack_start(lbl, False, False, 0)
        hb.pack_start(al, True, True, 10)
        vb.pack_start(hb, False, True, 0)

        # byoyomi - seconds
        byo_frame2 = Gtk.Frame.new("Byoyomi")
        minimum = 0
        maximum = 60
        default = self.byo_byoyomi
        byo_adj_byoyomi = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(byo_adj_byoyomi, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        hb = Gtk.HBox(False, 0)
        hb.pack_start(Gtk.Label("Seconds:"), False, False, 0)
        hb.pack_start(al, True, True, 10)
        byo_frame2.add(hb)

        self.tcvb[0].pack_start(byo_frame1, False, False, 0)
        self.tcvb[0].pack_start(byo_frame2, False, False, 0)
        self.tcvb[0].set_spacing(20)

        #
        # settings for the classical time control type
        #
        #   classical
        #       e.g. 40 moves in 5 minutes
        #       go wtime 300000 btime 300000 movestogo 40
        #

        cls_frame1 = Gtk.Frame()
        vb = Gtk.VBox(False, 0)
        cls_frame1.add(vb)

        adj_cls_settings = []

        for i in range(0, self.cls_max_sessions):

            (moves_to_go, minutes, repeat_times) = self.cls_settings[i]

            # session
            hb = Gtk.HBox(False, 0)
            if i != 0:
                vb.pack_start(Gtk.HSeparator(), False, True, 0)
            hb.pack_start(Gtk.Label("#" + str(i + 1)), False, False, 0)
            # if i != 0:
            #   hb.pack_start(Gtk.CheckButton(, True, True, 0), True, True, 10)
            vb.pack_start(hb, False, True, 0)

            # moves
            minimum = 1
            maximum = 200
            default = moves_to_go
            # default = 40
            # if i == 0:
            #    default = 40
            # else:
            #    default = 0
            adj_moves_to_go = Gtk.Adjustment(
                value=default, lower=minimum, upper=maximum,
                step_increment=1, page_increment=5, page_size=0)
            spinner = Gtk.SpinButton.new(adj_moves_to_go, 1.0, 0)
            al = Gtk.Alignment.new(
                xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
            al.add(spinner)
            hb = Gtk.HBox(False, 0)
            hb.pack_start(Gtk.Label("Moves:"), False, False, 0)
            hb.pack_start(al, True, True, 10)
            vb.pack_start(hb, False, True, 0)

            # minutes
            minimum = 0
            maximum = 500
            # default = 5
            default = minutes
            # if i == 0:
            #    default = 5
            # else:
            #    default = 0
            adj_cls_mins = Gtk.Adjustment(
                value=default, lower=minimum, upper=maximum,
                step_increment=1, page_increment=5, page_size=0)
            spinner = Gtk.SpinButton.new(adj_cls_mins, 1.0, 0)
            al = Gtk.Alignment.new(
                xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
            al.add(spinner)
            lbl = Gtk.Label(label="Minutes :")
            hb = Gtk.HBox(False, 0)
            hb.pack_start(lbl, False, False, 0)
            hb.pack_start(al, True, True, 10)
            vb.pack_start(hb, False, True, 0)

            # repeating
            minimum = 0
            maximum = 9
            default = repeat_times
            # if i == 0:
            #    default = 1
            # else:
            #    default = 0
            adj_cls_repeat = Gtk.Adjustment(
                value=default, lower=minimum, upper=maximum,
                step_increment=1, page_increment=5, page_size=0)
            spinner = Gtk.SpinButton.new(adj_cls_repeat, 1.0, 0)
            al = Gtk.Alignment.new(
                xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
            al.add(spinner)
            lbl = Gtk.Label(label="Count :")
            hb = Gtk.HBox(False, 0)
            hb.pack_start(lbl, False, False, 0)
            hb.pack_start(al, True, True, 10)
            vb.pack_start(hb, False, True, 0)

            # enabled
            # lbl = Gtk.Label(label="Enabled :")
            # hb = Gtk.HBox(False, 0)
            # hb.pack_start(lbl, False, False, 0)
            # hb.pack_start(Gtk.CheckButton(, True, True, 0), True, True, 10)
            # vb.pack_start(hb, False, True, 0)

            adj_cls_settings.append((
                adj_moves_to_go, adj_cls_mins, adj_cls_repeat))

        self.tcvb[1].pack_start(cls_frame1, False, False, 0)

        # Blitz (incremental)
        # e.g. 2 mins 0 seconds for whole game, 6 seconds 0 milliseconds bonus
        # per move
        # base is for whole game, bonus will be given for every move made
        # go wtime 126000 btime 120000 winc 6000 binc 6000
        # go wtime 130591 btime 118314 winc 6000 binc 6000
        # go wtime 135329 btime 118947 winc 6000 binc 6000

        inc_frame1 = Gtk.Frame.new("Time")
        vb = Gtk.VBox(False, 0)
        inc_frame1.add(vb)

        # available time - hours
        minimum = 0
        maximum = 10
        default = self.inc_hours
        inc_adj_hours = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(inc_adj_hours, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        hb = Gtk.HBox(False, 0)
        hb.pack_start(Gtk.Label("Hours:"), False, False, 0)
        hb.pack_start(al, True, True, 10)
        vb.pack_start(hb, False, True, 0)

        # available time - minutes
        minimum = 0
        maximum = 59
        default = self.inc_minutes
        inc_adj_mins = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(inc_adj_mins, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        lbl = Gtk.Label(label="Minutes :")
        hb = Gtk.HBox(False, 0)
        hb.pack_start(lbl, False, False, 0)
        hb.pack_start(al, True, True, 10)
        vb.pack_start(hb, False, True, 0)

        # bonus time per move - seconds
        inc_frame2 = Gtk.Frame.new("Bonus Time per Move")
        minimum = 0
        maximum = 60
        default = self.inc_bonus
        inc_adj_bonus = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(inc_adj_bonus, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        hb = Gtk.HBox(False, 0)
        hb.pack_start(Gtk.Label("Seconds:"), False, False, 0)
        hb.pack_start(al, True, True, 10)
        inc_frame2.add(hb)

        self.tcvb[2].pack_start(inc_frame1, False, False, 0)
        self.tcvb[2].pack_start(inc_frame2, False, False, 0)
        self.tcvb[2].set_spacing(20)

        #
        # settings for the fixed time per move time control type
        #
        #   fixed time per move
        #       e.g. 6 seconds per move
        #       go movetime 6000

        # ftpm_frame1 = Gtk.Frame("Fixed Time Per Move")
        ftpm_frame1 = Gtk.Frame()
        ftpm_frame1.set_shadow_type(Gtk.ShadowType.NONE)
        vb = Gtk.VBox(False, 0)
        ftpm_frame1.add(vb)

        # seconds per move
        minimum = 0
        maximum = 10000
        default = self.ftpm_seconds
        adj_ftpm_secs = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(adj_ftpm_secs, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        lbl = Gtk.Label(label="Seconds :")
        hb = Gtk.HBox(False, 0)
        hb.pack_start(lbl, False, False, 0)
        hb.pack_start(al, True, True, 10)
        vb.pack_start(hb, False, True, 0)

        self.tcvb[3].pack_start(ftpm_frame1, False, False, 0)

        #
        # settings for the fixed search depth time control type
        #
        #   fixed search depth
        #       e.g.
        #       go depth 8
        dpth_frame1 = Gtk.Frame()
        dpth_frame1.set_shadow_type(Gtk.ShadowType.NONE)
        vb = Gtk.VBox(False, 0)
        dpth_frame1.add(vb)

        # depth
        minimum = 0
        maximum = 999
        default = self.dpth_depth
        adj_dpth_depth = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(adj_dpth_depth, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        lbl = Gtk.Label(label="Search Depth :")
        hb = Gtk.HBox(False, 0)
        hb.pack_start(lbl, False, False, 0)
        hb.pack_start(al, True, True, 10)
        vb.pack_start(hb, False, True, 0)

        self.tcvb[4].pack_start(dpth_frame1, False, False, 0)

        # calculate to engines maximum search depth
        # (sends back bestmove if it gets the stop command)
        # go infinite

        # there are no cutomisable options for go infinite
        self.tcvb[5].pack_start(
            Gtk.Label("No customisable options"), True, True, 0)

        #
        # settings for the fixed no. of nodes time control type
        #
        #   fixed no. of nodes
        #       e.g. search for 1 million nodes
        #       go nodes 1000000
        nodes_frame1 = Gtk.Frame()
        nodes_frame1.set_shadow_type(Gtk.ShadowType.NONE)
        vb = Gtk.VBox(False, 0)
        nodes_frame1.add(vb)

        # nodes
        minimum = 1
        maximum = 2000000000
        default = self.nodes_nodes
        adj_nodes_nodes = Gtk.Adjustment(
            value=default, lower=minimum, upper=maximum,
            step_increment=1, page_increment=5, page_size=0)
        spinner = Gtk.SpinButton.new(adj_nodes_nodes, 1.0, 0)
        al = Gtk.Alignment.new(xalign=1.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(spinner)
        lbl = Gtk.Label(label="No. of Nodes to Search :")
        hb = Gtk.HBox(False, 0)
        hb.pack_start(lbl, False, False, 0)
        hb.pack_start(al, True, True, 10)
        vb.pack_start(hb, False, True, 0)

        self.tcvb[6].pack_start(nodes_frame1, False, False, 0)

        # mate search
        # e.g. look for mate in 5 moves
        # go mate 5

        self.al = Gtk.Alignment.new(
            xalign=0.5, yalign=0.5, xscale=1.0, yscale=0.0)
        # top, bottom, left, right
        self.al.set_padding(0, 0, 9, 9)
        self.al.add(self.tcvb[self.type])
        dialog.vbox.pack_start(self.al, False, True, 0)

        combobox.connect("changed", self.tc_method_changed, dialog)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        self.set_frame_visibility(self.type)

        while True:
            response = dialog.run()
            if response != Gtk.ResponseType.OK:
                # cancelled - exit loop
                break
            # OK pressed - validate input"
            # print "ok pressed"

            self.type = combobox.get_active()
            # byoyomi
            if self.type == 0:
                byo_hours = int(byo_adj_hours.get_value())
                byo_minutes = int(byo_adj_mins.get_value())
                byo_byoyomi = int(byo_adj_byoyomi.get_value())
                if byo_hours == 0 and byo_minutes == 0 and byo_byoyomi == 0:
                    gv.gui.info_box("Time fields cannot all be zero!")
                else:
                    # input ok - exit loop
                    self.byo_hours = byo_hours
                    self.byo_minutes = byo_minutes
                    self.byo_byoyomi = byo_byoyomi

                    self.reset_clock()

                    self.set_toolbar_time_control(self.type, 0, WHITE)
                    self.set_toolbar_time_control(self.type, 0, BLACK)
                    break
            # classical
            elif self.type == 1:
                self.cls_settings = []
                rep_zero = True
                for i in range(0, self.cls_max_sessions):
                    moves_to_go, mins, rep = adj_cls_settings[i]
                    if rep.get_value() != 0:
                        rep_zero = False
                if rep_zero:
                    gv.gui.info_box("Count fields cannot all be zero!")
                else:
                    for i in range(0, self.cls_max_sessions):
                        moves_to_go, mins, rep = adj_cls_settings[i]
                        self.cls_settings.append((
                            moves_to_go.get_value(), mins.get_value(),
                            rep.get_value()))

                    # fields for go command
                    self.reset_clock()

                    self.set_toolbar_time_control(self.type, 0, WHITE)
                    self.set_toolbar_time_control(self.type, 0, BLACK)
                    break
            # incremental
            if self.type == 2:
                inc_hours = int(inc_adj_hours.get_value())
                inc_minutes = int(inc_adj_mins.get_value())
                inc_bonus = int(inc_adj_bonus.get_value())
                if inc_hours == 0 and inc_minutes == 0 and inc_bonus == 0:
                    gv.gui.info_box(
                        "Incremental Time fields cannot all be zero!")
                else:
                    # input ok - exit loop
                    self.inc_hours = inc_hours
                    self.inc_minutes = inc_minutes
                    self.inc_bonus = inc_bonus

                    self.reset_clock()

                    self.set_toolbar_time_control(self.type, 0, WHITE)
                    self.set_toolbar_time_control(self.type, 0, BLACK)
                    break
            # fixed time per move
            elif self.type == 3:
                self.ftpm_seconds = int(adj_ftpm_secs.get_value())

                # fields for go command
                self.reset_clock()

                self.set_toolbar_time_control(self.type, 0, WHITE)
                self.set_toolbar_time_control(self.type, 0, BLACK)
                break
            # fixed search depth
            elif self.type == 4:
                self.dpth_depth = int(adj_dpth_depth.get_value())

                # fields for go command
                self.reset_clock()

                self.set_toolbar_time_control(self.type, 0, WHITE)
                self.set_toolbar_time_control(self.type, 0, BLACK)
                break
            # infinite search
            elif self.type == 5:
                break
            # fixed number of nodes search
            elif self.type == 6:
                self.nodes_nodes = int(adj_nodes_nodes.get_value())

                # fields for go command
                self.reset_clock()

                self.set_toolbar_time_control(self.type, 0, WHITE)
                self.set_toolbar_time_control(self.type, 0, BLACK)
                break

        dialog.destroy()

    def tc_method_changed(self, b, dialog):
        tc_type = b.get_active()

        self.set_frame_visibility(tc_type)

        chd = self.al.get_children()
        for c in chd:
            self.al.remove(c)
        self.al.add(self.tcvb[tc_type])
        self.tcvb[tc_type].show()

        dialog.size_allocate(self.area)
        dialog.check_resize()
        dialog.show_all()

    def set_frame_visibility(self, tc_type):
        for v in self.tcvb:
            v.hide()
        self.tcvb[tc_type].show()

    def dialog_expose_event(self, widget, context):
        # self.area = event.area
        a = widget.get_allocation()
        self.area = a
        # self.area = a.x, a.y, a.width, a.height
        # print self.area

    #
    # called before each move
    #
    def start_clock(self, stm):
        # print "starting clock in tc.py"
        self.clock_start_time = time.time()
        self.clock_stm = stm
        if self.type == 3:
            if stm == WHITE:
                self.wtime = self.ftpm_seconds * 1000
            else:
                self.btime = self.ftpm_seconds * 1000
        self.set_toolbar_time_control(self.type, 0, self.clock_stm)

    #
    # called when the red stop button is clicked
    #
    def stop_clock(self):
        elapsed_time = (time.time() - self.clock_start_time) * 1000
        if self.clock_stm == WHITE:
            self.wtime = int(self.wtime - elapsed_time)
            if self.wtime < 0:
                self.wtime = 0
        else:
            self.btime = int(self.btime - elapsed_time)
            if self.btime < 0:
                self.btime = 0

        # print "calling set_toolbar_time_control from stop_clock"
        self.set_toolbar_time_control(self.type, 0, self.clock_stm)

    #
    # This routine is called after a move from usi.py (if USI engine) or
    # gshogi.py
    #
    def update_clock(self):
        # set btime/wtime
        elapsed_time = (time.time() - self.clock_start_time) * 1000
        if self.clock_stm == WHITE:
            self.wtime = int(self.wtime - elapsed_time)
            if self.wtime < 0:
                self.wtime = 0
        else:
            self.btime = int(self.btime - elapsed_time)
            if self.btime < 0:
                self.btime = 0

        # set moves to go for classical TC
        if self.type == 1:
            if self.clock_stm == WHITE:
                self.wmoves_to_go -= 1
                if self.wmoves_to_go < 1:
                    self.wrepeat -= 1
                    while self.wrepeat < 1:
                        self.cls_wsession += 1
                        if self.cls_wsession >= self.cls_max_sessions:
                            self.cls_wsession = 0
                        self.wrepeat = self.cls_settings[self.cls_wsession][2]

                    (moves_to_go, minutes, repeat_times) = self.cls_settings[
                        self.cls_wsession]
                    rem_time = self.wtime
                    self.wtime = int((minutes * 60) * 1000) + rem_time
                    self.wmoves_to_go = int(moves_to_go)
            else:
                self.bmoves_to_go -= 1
                if self.bmoves_to_go < 1:
                    self.brepeat -= 1
                    while self.brepeat < 1:
                        self.cls_bsession += 1
                        if self.cls_bsession >= self.cls_max_sessions:
                            self.cls_bsession = 0
                        self.brepeat = self.cls_settings[self.cls_bsession][2]

                    (moves_to_go, minutes, repeat_times) = self.cls_settings[
                        self.cls_bsession]
                    rem_time = self.btime
                    self.btime = int((minutes * 60) * 1000) + rem_time
                    self.bmoves_to_go = int(moves_to_go)
        # incremental
        elif self.type == 2:
            if self.clock_stm == WHITE:
                self.wtime += self.inc_bonus * 1000
            else:
                self.btime += self.inc_bonus * 1000

        if self.type != 0:
            # print "calling set_toolbar_time_control from update_clock"
            self.set_toolbar_time_control(self.type, 0, self.clock_stm)

        # set stm to None
        # This prevents show_time from putting erroneous values in for the side
        # that has just moved
        # It will get set to the next side to move when start_clock is called
        # from usi.py
        self.clock_stm = None

    #
    # timer to countdown the clock on the screen during a move
    # called once per second while the player is thinking
    #
    def show_time(self):
        self.timer_active = True
        # don't refresh clock if stm is not set
        if self.clock_stm is None:
            return True
        if gv.gshogi.get_stopped():
            self.timer_active = False
            return False
        elapsed_time = int((time.time() - self.clock_start_time) * 1000)

        # print "calling set_toolbar_time_control from show_time"
        self.set_toolbar_time_control(self.type, elapsed_time, self.clock_stm)

        return True

    def get_go_command(self, stm):
        # byoyomi
        if self.type == 0:
            # times in milliseconds
            btime = self.btime
            wtime = self.wtime
            byoyomi = self.byo_byoyomi * 1000
            cmd = ("go btime " + str(btime) + " wtime " + str(wtime) +
                   " byoyomi " + str(byoyomi))
        # classical (e.g. 40 moves in 5 minutes)
        elif self.type == 1:
            if stm == WHITE:
                cmd = ("go btime " + str(self.btime) + " wtime " +
                       str(self.wtime) + " movestogo " +
                       str(self.wmoves_to_go))
            else:
                cmd = ("go btime " + str(self.btime) + " wtime " +
                       str(self.wtime) + " movestogo " +
                       str(self.bmoves_to_go))
        # incremental
        elif self.type == 2:
            # times in milliseconds
            btime = self.btime
            wtime = self.wtime
            bonus = self.inc_bonus * 1000
            cmd = ("go btime " + str(btime) + " wtime " + str(wtime) +
                   " binc " + str(bonus) + " winc " + str(bonus))
        # fixed time per move
        elif self.type == 3:
            cmd = "go movetime " + str(self.ftpm_seconds * 1000)
        elif self.type == 4:
            cmd = "go depth " + str(self.dpth_depth)
        elif self.type == 5:
            cmd = "go infinite"
        elif self.type == 6:
            cmd = "go nodes " + str(self.nodes_nodes)
        else:
            # times in milliseconds
            btime = self.btime
            wtime = self.wtime
            byoyomi = self.byo_byoyomi * 1000
            cmd = ("go btime " + str(btime) + " wtime " + str(wtime) +
                   " byoyomi " + str(byoyomi))

        return cmd

    # set the time limit/level when using the builtin gshogi engine
    def set_gshogi_time_limit(self, stm):

        #
        # set engine depth/nodes/time to maximum
        #
        engine.depth(39)
        engine.nodes(0)
        engine.command("level 0 59:59")

        # byoyomi
        if self.type == 0:
            if stm == WHITE:
                gs_movetime = self.wtime
            else:
                gs_movetime = self.btime
            gs_byoyomi = self.byo_byoyomi * 1000
            if gs_movetime > 0:
                gs_movetime = int(gs_movetime / 80)
            elif gs_byoyomi > 0:
                gs_movetime = gs_byoyomi
            else:
                # no time left - set to 1 second
                gs_movetime = 1000

            # if less than 1 second set to 1 second
            if gs_movetime < 1000:
                gs_movetime = 1000

            gs_secs = int(gs_movetime / 1000)
            gs_mins = int(gs_secs / 60)
            if gs_mins > 59:
                gs_mins = 59
                gs_secs = 59
            elif gs_mins > 0:
                gs_secs = gs_secs % (gs_mins * 60)

            gs_mins = int(gs_mins)
            gs_secs = int(gs_secs)

            gs_mins_str = str(gs_mins)
            gs_secs_str = str(gs_secs)
            if gs_mins < 10:
                gs_mins_str = "0" + gs_mins_str
            if gs_secs < 10:
                gs_secs_str = "0" + gs_secs_str

            gs_level = gs_mins_str + ":" + gs_secs_str

            if gv.verbose:
                print(("using byoyomi TC - wtime:", self.wtime, ", btime:",
                      self.btime, ", byoyomi:", self.byo_byoyomi * 1000,
                      ", stm:", stm, ", time for move (ms):", gs_movetime))
            command = "level 0 " + gs_level
            # print "gshogi time limit:",command

            # e.g.
            # time limit of 10 seconds per move
            # level 0 00:10
            #
            # time limit of 10 moves in 2 minutes
            # level 10 2
            engine.command(command)
        # classical
        elif self.type == 1:
            if stm == WHITE:
                gs_movetime = self.wtime
            else:
                gs_movetime = self.btime
            # if less than 1 second set to 1 second
            if gs_movetime < 1000:
                gs_movetime = 1000

            gs_secs = int(gs_movetime / 1000)
            gs_mins = int(gs_secs / 60)
            if gs_mins > 0:
                gs_secs = gs_secs % (gs_mins * 60)

            gs_mins = int(gs_mins)
            gs_secs = int(gs_secs)

            gs_mins_str = str(gs_mins)
            gs_secs_str = str(gs_secs)
            if gs_mins < 10:
                gs_mins_str = "0" + gs_mins_str
            if gs_secs < 10:
                gs_secs_str = "0" + gs_secs_str

            gs_level = gs_mins_str + ":" + gs_secs_str
            if gv.verbose:
                print(("using classical TC - wtime:", self.wtime, ", btime:",
                      self.btime, ", movestogo:", str(self.wmoves_to_go),
                      ", stm:", stm, ", time for move (ms):", gs_movetime))
                print(("                   - ", str(self.wmoves_to_go),
                      " moves in ", gs_mins_str, "minutes", gs_secs_str,
                      " seconds"))

            if self.wmoves_to_go == 1:
                command = "level 0 " + gs_level
            else:
                command = "level " + str(self.wmoves_to_go) + " " + gs_level
            engine.command(command)
        # incremental
        elif self.type == 2:
            if stm == WHITE:
                gs_movetime = self.wtime
            else:
                gs_movetime = self.btime

            if gs_movetime > 0:
                gs_movetime = int(gs_movetime / 80)
            else:
                # no time left - set to 1 second
                gs_movetime = 1000

            gs_secs = int(gs_movetime / 1000)
            gs_mins = int(gs_secs / 60)
            if gs_mins > 0:
                gs_secs = gs_secs % (gs_mins * 60)

            gs_mins = int(gs_mins)
            gs_secs = int(gs_secs)

            if gs_mins <= 0 and gs_secs < 1:
                gs_secs = 1

            gs_mins_str = str(gs_mins)
            gs_secs_str = str(gs_secs)
            if gs_mins < 10:
                gs_mins_str = "0" + gs_mins_str
            if gs_secs < 10:
                gs_secs_str = "0" + gs_secs_str

            gs_level = gs_mins_str + ":" + gs_secs_str
            if gv.verbose:
                print(("using incremental TC - wtime:", self.wtime, ", btime:",
                      self.btime, ", winc/binc:", str(self.inc_bonus * 1000),
                      ", stm:", stm, ", time for move (ms):", gs_movetime))

            command = "level 0 " + gs_level
            engine.command(command)
        # fixed time per move
        elif self.type == 3:
            gs_movetime = self.ftpm_seconds * 1000

            gs_secs = int(gs_movetime / 1000)
            gs_mins = int(gs_secs / 60)
            if gs_mins > 0:
                gs_secs = gs_secs % (gs_mins * 60)

            gs_mins = int(gs_mins)
            gs_secs = int(gs_secs)

            if gs_mins <= 0 and gs_secs < 1:
                gs_secs = 1

            gs_mins_str = str(gs_mins)
            gs_secs_str = str(gs_secs)
            if gs_mins < 10:
                gs_mins_str = "0" + gs_mins_str
            if gs_secs < 10:
                gs_secs_str = "0" + gs_secs_str

            gs_level = gs_mins_str + ":" + gs_secs_str
            if gv.verbose:
                print(("using fixed time per move TC - wtime:", self.wtime,
                      ", btime:", self.btime, " stm:", stm,
                      ", time for move (ms):", gs_movetime))

            command = "level 0 " + gs_level
            engine.command(command)
        # fixed search depth
        elif self.type == 4:
            idepth = self.dpth_depth
            if idepth > 39:
                if gv.verbose:
                    print(("search depth (", idepth,
                          ") exceeds max for gshogi engine, setting to 39"))
                idepth = 39
            if gv.verbose:
                print("setting depth for gshogi engine to", idepth)
            engine.depth(idepth)
        # fixed nodes search
        elif self.type == 6:
            inodes = self.nodes_nodes

            if gv.verbose:
                print("setting nodes for gshogi engine to", inodes)
                print("time=", time.time())
            engine.nodes(inodes)
            command = "level 0 59:59"
            engine.command(command)

    def update_gui_time_control(self, stm):
        self.set_toolbar_time_control(self.type, 0, stm)

    def set_toolbar_time_control(self, tc_type, move_time, stm):
        if tc_type == 0:
            self.set_toolbar_time_control0(move_time, stm)
        elif tc_type == 1:
            self.set_toolbar_time_control1(move_time, stm)
        elif tc_type == 2:
            self.set_toolbar_time_control2(move_time, stm)
        elif tc_type == 3:
            self.set_toolbar_time_control3(move_time, stm)
        elif tc_type == 4 or tc_type == 5 or tc_type == 6:
            self.set_toolbar_time_control4(move_time, stm)
        else:
            print("invalid tc type", tc_type)

    # update gui clock for byoyomi TC
    def set_toolbar_time_control0(self, move_time, side_to_move):

        if side_to_move == WHITE:
            time_left = self.wtime
        else:
            time_left = self.btime

        # subtract the move time from the players available time
        new_time = time_left - move_time

        byoyomi = self.byo_byoyomi * 1000

        # If no available time use byoyomi time
        if new_time <= 0:
            hours = 0
            mins = 0
            secs = 0
            if time_left > 0:
                byo = byoyomi - move_time + time_left
            else:
                byo = byoyomi - move_time
            if byo < 0:
                byo = 0
        else:
            secs = int(new_time / 1000)
            hours = int(secs / 3600)
            secs = secs - (hours * 3600)
            mins = int(secs / 60)
            secs = int(secs - (mins * 60))
            byo = 0

        byoyomi = int(byoyomi / 1000)
        byo = int(byo / 1000)

        shours = str(hours)
        if len(shours) < 2:
            shours = "0" + shours

        smins = str(mins)
        if len(smins) < 2:
            smins = "0" + smins

        ssecs = str(secs)
        if len(ssecs) < 2:
            ssecs = "0" + ssecs

        sbyo = str(byo)
        if len(sbyo) < 2:
            sbyo = "0" + sbyo
        sbyoyomi = str(byoyomi)
        if len(sbyoyomi) < 2:
            sbyoyomi = "0" + sbyoyomi

        txt = shours + ":" + smins + ":" + ssecs + "  " + sbyo + "/" + sbyoyomi
        gv.gui.set_toolbar_time_control(txt, side_to_move)

    # update gui clock for classical TC
    def set_toolbar_time_control1(self, move_time, side_to_move):
        if side_to_move == WHITE:
            time_left = self.wtime
            moves_to_go = self.wmoves_to_go
        else:
            time_left = self.btime
            moves_to_go = self.bmoves_to_go

        # subtract the move time from the players available time
        new_time = time_left - move_time

        if new_time <= 0:
            hours = 0
            mins = 0
            secs = 0
        else:
            secs = int(new_time / 1000)
            hours = int(secs / 3600)
            secs = secs - (hours * 3600)
            mins = int(secs / 60)
            secs = int(secs - (mins * 60))

        shours = str(hours)
        if len(shours) < 2:
            shours = "0" + shours

        smins = str(mins)
        if len(smins) < 2:
            smins = "0" + smins

        ssecs = str(secs)
        if len(ssecs) < 2:
            ssecs = "0" + ssecs

        txt = shours + ":" + smins + ":" + ssecs + " " + str(moves_to_go)
        gv.gui.set_toolbar_time_control(txt, side_to_move)

    # update gui clock for incremental TC
    def set_toolbar_time_control2(self, move_time, side_to_move):
        if side_to_move == WHITE:
            time_left = self.wtime
        else:
            time_left = self.btime

        # subtract the move time from the players available time
        new_time = time_left - move_time

        # If no available time use byoyomi time
        if new_time <= 0:
            hours = 0
            mins = 0
            secs = 0
        else:
            secs = int(new_time / 1000)
            hours = int(secs / 3600)
            secs = secs - (hours * 3600)
            mins = int(secs / 60)
            secs = int(secs - (mins * 60))

        shours = str(hours)
        if len(shours) < 2:
            shours = "0" + shours

        smins = str(mins)
        if len(smins) < 2:
            smins = "0" + smins

        ssecs = str(secs)
        if len(ssecs) < 2:
            ssecs = "0" + ssecs

        txt = shours + ":" + smins + ":" + ssecs
        gv.gui.set_toolbar_time_control(txt, side_to_move)

    # update gui clock for fixed time per move TC
    def set_toolbar_time_control3(self, move_time, side_to_move):
        if side_to_move == WHITE:
            time_left = self.wtime
        else:
            time_left = self.btime

        # subtract the move time from the players available time
        new_time = time_left - move_time

        # If no available time use byoyomi time
        if new_time <= 0:
            hours = 0
            mins = 0
            secs = 0
        else:
            secs = int(new_time / 1000)
            hours = int(secs / 3600)
            secs = secs - (hours * 3600)
            mins = int(secs / 60)
            secs = int(secs - (mins * 60))

        shours = str(hours)
        if len(shours) < 2:
            shours = "0" + shours

        smins = str(mins)
        if len(smins) < 2:
            smins = "0" + smins

        ssecs = str(secs)
        if len(ssecs) < 2:
            ssecs = "0" + ssecs

        txt = shours + ":" + smins + ":" + ssecs
        gv.gui.set_toolbar_time_control(txt, side_to_move)

    # update gui clock for fixed search depth TC
    def set_toolbar_time_control4(self, move_time, side_to_move):

        new_time = move_time

        # If no available time use byoyomi time
        if new_time <= 0:
            hours = 0
            mins = 0
            secs = 0
        else:
            secs = int(new_time / 1000)
            hours = int(secs / 3600)
            secs = secs - (hours * 3600)
            mins = int(secs / 60)
            secs = int(secs - (mins * 60))

        shours = str(hours)
        if len(shours) < 2:
            shours = "0" + shours

        smins = str(mins)
        if len(smins) < 2:
            smins = "0" + smins

        ssecs = str(secs)
        if len(ssecs) < 2:
            ssecs = "0" + ssecs

        txt = shours + ":" + smins + ":" + ssecs
        gv.gui.set_toolbar_time_control(txt, side_to_move)
