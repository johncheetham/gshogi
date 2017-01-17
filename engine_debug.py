#
#   engine_debug.py - Display USI Engine Debug Window
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
from gi.repository import GObject
import os

from .constants import WHITE, BLACK
from . import gv


class Engine_Debug:

    engine_debug_ref = None

    def __init__(self):
        glade_dir = gv.gshogi.get_glade_dir()
        self.glade_file = os.path.join(glade_dir, "engine_debug.glade")
        Engine_Debug.engine_debug_ref = self

        self.debug_text = ""
        self.window = None

    def clear_text(self, b):
        self.tb.set_text("")

    # send command to engine1 (white)
    def engine1_button_clicked(self, b):

        player = gv.gshogi.get_player(WHITE)
        if player == "Human" or player == "gshogi":
            GObject.idle_add(
                self.add_to_log,
                "# command not sent - player 1 (white) is not a USI engine")
            return

        cmd = self.cmd_entry.get_text() + "\n"
        gv.usiw.command(cmd)

    # send command to engine2 (black)
    def engine2_button_clicked(self, b):

        player = gv.gshogi.get_player(BLACK)
        if player == "Human" or player == "gshogi":
            GObject.idle_add(
                self.add_to_log,
                "# command not sent - player 2 (black) is not a USI engine")
            return

        cmd = self.cmd_entry.get_text() + "\n"
        gv.usib.command(cmd)

    # user has closed the window
    # just hide it
    def delete_event(self, widget, event):
        self.window.hide()
        return True  # do not propagate to other handlers

    def add_to_log(self, msg):
        msg = msg + "\n"
        try:
            # append to end of buffer
            end_iter = self.tb.get_end_iter()
            self.tb.insert(end_iter, msg)
            # scroll to end
            GObject.idle_add(self.scroll_to_end)
        except AttributeError:
            # engine debug window has not been opened. Append the debug
            # messages until it is opened
            self.debug_text += msg

    def show_debug_window(self, b):

        # window already exists and is hidden so just show it
        if self.window is not None:
            # "present" will show the window if it is hidden
            # if not hidden it will raise it to the top
            self.window.present()
            return

        # This is the first time the user has opened the engine debug
        # window so need to create it.
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(gv.domain)
        self.builder.add_from_file(self.glade_file)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("engine_debug_window")
        self.tv = self.builder.get_object("engine_debug_textview")
        self.tv.set_editable(False)
        self.tb = self.tv.get_buffer()
        self.tb.set_text(self.debug_text)
        self.debug_text = ""

        # used to type commands and send them to the engine
        self.cmd_entry = self.builder.get_object("engine_debug_entry")

        self.window.show_all()

        # scroll to end
        GObject.idle_add(self.scroll_to_end)

    def scroll_to_end(self):
        within_margin = 0.2
        end_iter = self.tb.get_end_iter()
        self.tv.scroll_to_iter(end_iter, within_margin, False, 0.5, 0.5)


def get_ref():
    if Engine_Debug.engine_debug_ref is None:
        Engine_Debug.engine_debug_ref = Engine_Debug()
    return Engine_Debug.engine_debug_ref
