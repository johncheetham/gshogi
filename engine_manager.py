#
#   engine_manager.py
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
from gi.repository import Gdk
from gi.repository import GObject
import os

from . import usi
from .constants import WHITE, BLACK
from . import gv


class Engine_Manager:

    def __init__(self):
        # engine list is list of (name, path) pairs
        self.engine_list = [("gshogi", "")]
        self.glade_file = None
        self.hash_value = 256
        self.ponder = False

    def common_settings(self, b):

        glade_dir = gv.gshogi.get_glade_dir()
        self.glade_file = os.path.join(glade_dir,
                                       "common_engine_settings.glade")
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(gv.domain)
        self.builder.add_from_file(self.glade_file)
        self.builder.connect_signals(self)

        dialog = self.builder.get_object("common_engine_settings")
        dialog.set_transient_for(gv.gui.get_window())
        # ponder check button
        checkbutton = self.builder.get_object("ponderbutton")
        checkbutton.set_active(self.ponder)

        # hash value
        adj = self.builder.get_object("adjustment1")
        adj.set_value(self.hash_value)
        adj.set_lower(0.00)
        adj.set_upper(10000.00)
        adj.set_step_increment(1)
        adj.set_page_increment(10)
        adj.set_page_size(0)

        response = dialog.run()

        resp_cancel = 1
        resp_ok = 2
        if response == resp_ok:
            self.hash_value = int(adj.get_value())
            self.ponder = checkbutton.get_active()

        dialog.destroy()

    def get_ponder(self):
        return self.ponder

    def set_ponder(self, ponder):
        self.ponder = ponder

    def get_hash_value(self):
        return self.hash_value

    def set_hash_value(self, hash_value):
        self.hash_value = hash_value

    def engines(self, b):

        # self.usi1.stop_engine()
        # self.usi2.stop_engine()
        engine_list = self.get_engine_list()

        dialog = Gtk.Dialog(
            _("Engines"), gv.gui.get_window(), 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK,
             Gtk.ResponseType.OK)
        )

        hb = Gtk.HBox(False, 20)
        hb.show()

        fr = Gtk.Frame()
        fr.show()
        liststore = Gtk.ListStore(str, str)
        for e in engine_list:
            engine_name, path = e
            liststore.append(e)
        self.liststore = liststore

        treeview = Gtk.TreeView(liststore)
        self.treeview = treeview
        tvcolumn = Gtk.TreeViewColumn(_("Select an Engine:"))
        treeview.append_column(tvcolumn)
        cell = Gtk.CellRendererText()
        # cell.set_property("cell-background", Gdk.color_parse("#F8F8FF"))
        cell.set_property("cell-background-gdk", Gdk.color_parse("#F8F8FF"))
        tvcolumn.pack_start(cell, True)
        tvcolumn.set_min_width(200)
        tvcolumn.set_attributes(cell, text=0)
        treeview.show()
        fr.add(treeview)
        hb.pack_start(fr, True, True, 20)
        treeview.connect("button-press-event", self.engine_changed)

        bb = Gtk.VButtonBox()
        bb.set_layout(Gtk.ButtonBoxStyle.START)
        bb.show()

        al = Gtk.Alignment.new(xalign=0.0, yalign=0.5, xscale=0.0, yscale=0.0)
        al.add(bb)
        al.show()

        add_button = Gtk.Button(_("Add"))
        add_button.show()
        bb.add(add_button)
        add_button.connect("clicked", self.add_engine, "add engine")

        self.delete_button = Gtk.Button(_("Delete"))
        self.delete_button.set_sensitive(False)
        self.delete_button.show()
        bb.add(self.delete_button)
        self.delete_button.connect("clicked",
                                   self.delete_engine, "delete engine")

        self.rename_button = Gtk.Button(_("Rename"))
        self.rename_button.set_sensitive(False)
        self.rename_button.show()
        bb.add(self.rename_button)
        self.rename_button.connect("clicked",
                                   self.rename_engine, "rename engine")

        hb.pack_start(al, False, True, 0)

        dialog.vbox.pack_start(hb, True, True, 15)

        dialog.set_default_response(Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            elist = []
            tm = self.treeview.get_model()
            l_iter = tm.get_iter_first()
            while (l_iter is not None):
                name = tm.get_value(l_iter, 0)
                path = tm.get_value(l_iter, 1)
                elist.append((name, path))
                l_iter = tm.iter_next(l_iter)
            self.set_engine_list(elist)

        dialog.destroy()

    def engine_changed(self, widget, event):
        GObject.idle_add(self.engine_changed2)

    def engine_changed2(self):
        name, path = self.get_selected_engine()
        if name == "gshogi":
            self.delete_button.set_sensitive(False)
            self.rename_button.set_sensitive(False)
        else:
            self.delete_button.set_sensitive(True)
            self.rename_button.set_sensitive(True)

    def get_selected_engine(self):
        ts = self.treeview.get_selection()
        # get liststore object/iter
        lso, l_iter = ts.get_selected()
        tm = self.treeview.get_model()
        try:
            name = tm.get_value(l_iter, 0)
            path = tm.get_value(l_iter, 1)
        except:
            l_iter = tm.get_iter_first()
            ts.select_iter(l_iter)
            name = tm.get_value(l_iter, 0)
            path = tm.get_value(l_iter, 1)

        return name, path

    def add_engine(self, widget, data=None):
        dialog = Gtk.FileChooserDialog(
            _("Add USI Engine.."),
            gv.gui.get_window(),
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            fname = dialog.get_filename()
            # print "attempting to add new engine"
            path = dialog.get_filename()
            # use a new usi object so not to mess with main game engine
            u = usi.Usi("0")
            u.set_engine("addengine", path)
            errmsg, name = u.test_engine(path)
            if errmsg != "":
                err_dialog = Gtk.Dialog(_("Error Adding Engine"), None, 0,
                                        (Gtk.STOCK_OK, Gtk.ResponseType.OK))
                err_dialog.set_default_size(380, -1)
                lbl = Gtk.Label(label=errmsg)
                lbl.show()
                al = Gtk.Alignment.new(xalign=0.0, yalign=0.5,
                                       xscale=0.0, yscale=0.0)
                al.set_padding(20, 20, 20, 20)
                al.add(lbl)
                al.show()
                err_dialog.vbox.pack_start(al, True, False, 0)
                response = err_dialog.run()
                err_dialog.destroy()
            else:
                self.liststore.append([name, path])
                self.add_engine_to_list([name, path])

        dialog.destroy()

    def configure_engine(self, widget, data=None):
        if widget.get_name() == "ConfigureEngine1":
            player = WHITE
            usi = gv.usiw
        else:
            player = BLACK
            usi = gv.usib

        # If not an engine return
        if gv.gshogi.get_player(player) == "Human":
            gv.gui.info_box(_("No options to configure"))
            return

        if usi.get_engine() == "gshogi":
            # gv.gshogi.set_level(widget)
            gv.gui.info_box(_("No options to configure"))
            return
        else:
            usi.USI_options(widget)

    def delete_engine(self, widget, data=None):

        ts = self.treeview.get_selection()

        # get liststore object/iter
        lso, l_iter = ts.get_selected()
        tm = self.treeview.get_model()

        if l_iter is None:
            gv.gui.info_box(_("no engine selected"))
            return

        name = tm.get_value(l_iter, 0)
        path = tm.get_value(l_iter, 1)

        if name == "gshogi":
            gv.gui.info_box(_("delete of gshogi engine not permitted"))
            return

        if not lso.remove(l_iter):
            # set to 1st engine after a delete if iter no longer valid
            l_iter = tm.get_iter_first()

        ts.select_iter(l_iter)

    def rename_engine(self, widget, data=None):

        ts = self.treeview.get_selection()

        # get liststore object/iter
        lso, l_iter = ts.get_selected()
        tm = self.treeview.get_model()

        if l_iter is None:
            gv.gui.info_box(_("no engine selected"))
            return

        name = tm.get_value(l_iter, 0)
        path = tm.get_value(l_iter, 1)

        if name == "gshogi":
            gv.gui.info_box(_("rename of gshogi engine not permitted"))
            return

        dialog = Gtk.MessageDialog(
            None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.OK_CANCEL,
            None)

        markup = "<b>" + _("Rename Engine") + "</b>"
        dialog.set_markup(markup)

        # create the text input fields
        entry = Gtk.Entry()
        entry.set_text(name)
        entry.set_max_length(30)
        entry.set_width_chars(30)

        tbl = Gtk.Table(1, 2, True)
        tbl.attach(Gtk.Label(label=_("Engine Name: ")), 0, 1, 0, 1)
        tbl.attach(entry, 1, 2, 0, 1)

        dialog.vbox.add(tbl)

        dialog.show_all()

        # If user hasn't clicked on OK then exit now
        if dialog.run() != Gtk.ResponseType.OK:
            dialog.destroy()
            return

        # user clicked OK so update with the values entered
        newname = entry.get_text()
        lso.set_value(l_iter, 0, newname)
        dialog.destroy()

    def get_path(self, engine_name):
        for (ename, path) in self.engine_list:
            if ename == engine_name:
                return path
        return None

    def add_engine_to_list(self, engine_data):
        self.engine_list.append(engine_data)

    def get_engine_list(self):
        return self.engine_list

    def set_engine_list(self, engine_list):
        self.engine_list = engine_list
