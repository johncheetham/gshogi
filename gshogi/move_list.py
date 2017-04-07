#
#   move_list.py - Display Move List Window
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

from . import gv
#from . import gui
if gv.installed:
    from gshogi import engine
else:
    import engine
from . import comments

class Move_List:

    move_list_ref = None

    def __init__(self):
        glade_dir = gv.gshogi.get_glade_dir()
        self.glade_file = os.path.join(glade_dir, "move_list.glade")
        Move_List.move_list_ref = self
        self.comments = comments.get_ref()

        self.saved_move_list = []

        # create move list window
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(gv.domain)
        self.builder.add_from_file(self.glade_file)
        self.builder.connect_signals(self)
        
        self.window = self.builder.get_object("move_list_window")
        self.vbox = self.builder.get_object("vbox1") #man
        self.treeview = Gtk.TreeView()  #man
        self.liststore = self.builder.get_object("liststore1")
        
        self.scrolled_window = Gtk.ScrolledWindow()
        #self.scrolled_window.set_size_request(150,300)
        self.treeview.set_model(self.liststore)
        self.scrolled_window.add(self.treeview)           
        self.vbox.add(self.scrolled_window)        
        self.comments_button = self.builder.get_object("comments_button")
        #self.builder.connect("button_press_event",self.comments_button_clicked_cb)
        
        cell0 = Gtk.CellRendererText()
        # cell0.set_property("cell-background", Gdk.color_parse("#F8F8FF"))
        tvcolumn0 = Gtk.TreeViewColumn("#")
        self.treeview.append_column(tvcolumn0)
        tvcolumn0.pack_start(cell0, True)
        tvcolumn0.set_min_width(50)
        tvcolumn0.set_attributes(cell0, text=0)

        cell1 = Gtk.CellRendererText()
        # cell1.set_property("cell-background", Gdk.color_parse("#F8F8FF"))
        tvcolumn1 = Gtk.TreeViewColumn(_("Move"))
        self.treeview.append_column(tvcolumn1)
        tvcolumn1.pack_start(cell1, True)
        tvcolumn1.set_min_width(100)
        tvcolumn1.set_attributes(cell1, text=1)

        cell2 = Gtk.CellRendererText()
        # cell1.set_property("cell-background", Gdk.color_parse("#F8F8FF"))
        tvcolumn2 = Gtk.TreeViewColumn(_("Cmt"))
        self.treeview.append_column(tvcolumn2)
        tvcolumn2.pack_start(cell2, True)
        tvcolumn2.set_min_width(20)
        tvcolumn2.set_attributes(cell2, text=2)
        
        
        self.tree_selection = self.treeview.get_selection()
        self.treeview.connect("button_press_event", self.treeview_button_press)
        self.treeview.connect("key_press_event", self.treeview_key_press)
        self.update()

    # user has closed the window
    # just hide it
    def delete_event(self, widget, event):
        self.window.hide()
        return True  # do not propagate to other handlers

    def show_movelist_window(self, b):
        # "present" will show the window if it is hidden
        # if not hidden it will raise it to the top
        self.window.show_all()
        self.window.present()
        return

    # update the move list
    # called when the number of moves in the list has changed
    def update(self):

        # update liststore
        self.liststore.clear()
        if gv.show_moves == True:
            gv.gui.movestore.clear()
        self.liststore.append(("0.", _("Start Pos"), " "))
        mvstr = engine.getmovelist()
        #
        
        moveno = 1
        if mvstr != "":
            mlst = mvstr.split(",")
            moveno = 1
            for m in mlst:

                (capture, ispromoted, move) = m.split(";")

                if move.find("*") == -1:
                    m1 = move[0:3]
                    m2 = move[3:]
                    move = m1 + capture + m2
                    if ispromoted == "+":
                        move = "+" + move
                comment = self.comments.get_comment(moveno)
                if gv.show_moves == True:
                    gv.gui.comment_view.get_buffer().set_text("-")
                                    
                if comment != "":
                    cind = "..."
                else:
                    cind = " "
                e = str(moveno) + ".", move, cind
                e1 = str(moveno) + "." + " " + move +" " + cind #+"\n"
                le = []
                # to move_view box
                le.append(e1)
                # to move_list window
                self.liststore.append(e)
                if gv.show_moves == True:                    
                                      
                    gv.gui.move_view.get_model().append(le)
                                     
                     
                moveno += 1
        comment = self.comments.get_comment(moveno)
        
        if gv.show_moves == True:
            #if gv.gui.comment_view.get_buffer() in not None:
                gv.gui.comment_view.get_buffer().set_text(comment)
        GObject.idle_add(self.scroll_to_end)

    # sets the move at move_idx as the selected line
    # called from gshogi.py for undo/redo move
    def set_move(self, move_idx):
        path = (move_idx,)
        #self.tree_selection.select_path(path)  to be bypasses if cursor_changed as event in moves_clicked
        self.comments.set_moveno(move_idx)
        if gv.show_moves == True:
            if move_idx > 0:
                path = str(move_idx-1)
            #gv.gui.move_view.set_cursor(path, None,False) 
            if path[0]!=0 and path!='0':
                GObject.idle_add(gv.gui.move_view.scroll_to_cell,path,None, False, 0,0)  #arguments must be in list
            
        return

    def scroll_to_end(self):
        adj = self.scrolled_window.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False

    def treeview_key_press(self, treeview, event):

        # to print list of key values do:
        #     print dir(Gtk.keysyms)

        # if up or down pressed then position the board at the move
        if event.keyval == Gdk.KEY_Up or event.keyval == Gdk.KEY_Down:
            self.treeview_button_press(None, None)

    # user clicked on the move list
    def treeview_button_press(self, treeview, event):
        if gv.gshogi.get_stopped():
            GObject.idle_add(self.process_tree_selection)
        else:
            GObject.idle_add(self.tree_selection.unselect_all)

    # set the board position at the move the user clicked on
    def move_box_selection(self):
        if gv.gshogi.get_stopped():
                       
            (treemodel, treeiter) = gv.gui.move_view.get_selection().get_selected()
            if treeiter is not None:
                k = gv.gui.movestore.get_value(treeiter,0).find(".")      
                nmove = int(gv.gui.movestore.get_value(treeiter,0)[0:k])
                self.comments.set_moveno(nmove)
                # now call a method in gshogi.py to position it at the move
                # clicked on
                gv.gshogi.goto_move(nmove)  
             
                path = str(nmove)
                self.treeview.set_cursor(path, None,False)  
                GObject.idle_add(self.treeview.scroll_to_cell,path,None, False, 0,0)  #arguments must be in list
                
        else:
            GObject.idle_add(gv.gui.move_view.get_selection().unselect_all)            
    
    def process_tree_selection(self):
        (treemodel, treeiter) = self.tree_selection.get_selected()
        if treeiter is not None:
            move_str = treemodel.get_value(treeiter, 0)
            move_str = move_str[0: len(move_str) - 1]
            move_idx = int(move_str)
            self.comments.set_moveno(move_idx)
            # now call a method in gshogi.py to position it at the move
            # clicked on
            gv.gshogi.goto_move(move_idx)
        #else:
            #self.tree_selection.unselect_all()

    def set_comment(self, index, text):
        self.comments.set_comment(index,text)
            

    def set_comment_ind(self, ind):
        if ind:
            cind = "..."
        else:
            cind = " "
        (treemodel, treeiter) = self.tree_selection.get_selected()
        if treeiter is not None:
            self.liststore.set_value(treeiter, 2, cind)

    def comments_button_clicked_cb(self, button):
        self.comments.show_comments_window()


def get_ref():
    if Move_List.move_list_ref is None:
        Move_List.move_list_ref = Move_List()
    return Move_List.move_list_ref
