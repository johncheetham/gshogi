#
#   comments.py - View/Edit Comments
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
import os

import gshogi.move_list
from . import gv



class Comments:

    comments_ref = None

    def __init__(self):

        glade_dir = gv.gshogi.get_glade_dir()
        self.glade_file = os.path.join(glade_dir, "comments.glade")
        self.move_list = gshogi.move_list.get_ref()
 

        # create comments window
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(gv.domain)
        self.builder.add_from_file(self.glade_file)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("comments_window")
        self.window.hide()

        self.moveno = 0  # the moveno the comment applies to

        tv = self.builder.get_object("comments_textview")
        tv.set_editable(True)
        tv.set_wrap_mode(Gtk.WrapMode.WORD)
        self.tb = tv.get_buffer()
        self.tb.connect("changed", self.text_changed)
        self.comment_list = []

    # user has closed the window
    # just hide it
    def delete_event(self, widget, event):
        self.window.hide()
        return True  # do not propagate to other handlers

    # called from comments_button_clicked_cb in move_list.py
    def show_comments_window(self):
        # "present" will show the window if it is hidden
        # if not hidden it will raise it to the top
        self.window.present()
        return

    # Called from move_list.py when selected move changes
    # change the comment window to show the comment for the
    # selected move
    def set_moveno(self, moveno):
        max = moveno
        if max < self.moveno:
            max = self.moveno
        # extend comment list if it is shorter than movelist
        while len(self.comment_list) <= max:
            self.comment_list.append("")

        # get current text from comments window
        start_iter = self.tb.get_start_iter()
        end_iter = self.tb.get_end_iter()
        text = self.tb.get_text(start_iter, end_iter, False)
        # save it
        # self.comment_list[self.moveno] = text

        self.moveno = moveno

        # set the comment in the window to that of the newly selected
        # move
        self.tb.set_text(self.comment_list[moveno])
        if gv.show_moves == True:
            start, end =gv.gui.comment_view.get_buffer().get_bounds()
            gv.gui.comment_view.get_buffer().delete(start,end)
            gv.gui.comment_view.get_buffer().insert(start,text)

        # show the moveno the comment relates to in the window title
        self.window.set_title(_("Comment for Move ") + str(moveno))  

        # self.moveno = moveno
    def get_comment_text(self,moveno):
        return self.comment_list[moveno]
        
    
        
    
    def text_changed(self, textbuffer):
        # get text
        start_iter = textbuffer.get_start_iter()
        end_iter = textbuffer.get_end_iter()
        text = textbuffer.get_text(start_iter, end_iter, False)

        # extend comment list if it is shorter than movelist
        while len(self.comment_list) <= self.moveno:
            self.comment_list.append("")

        # save it
        # print "saving to move;",self.moveno
        # print "text=",text
        self.comment_list[self.moveno] = text
        if text != "":
            self.move_list.set_comment_ind(True)
        else:
            self.move_list.set_comment_ind(False)

    # Clear the comment window when clear button is clicked
    def clear_button_clicked_cb(self, button):
        text = ""
        # extend comment list if it is shorter than movelist
        while len(self.comment_list) <= self.moveno:
            self.comment_list.append("")
        self.comment_list[self.moveno] = text
        self.tb.set_text(text)
        if gv.show_moves == True:
            start, end =gv.gui.comment_view.get_buffer().get_bounds()
            gv.gui.comment_view.get_buffer().delete(start,end)
            gv.gui.comment_view.get_buffer().insert(start,"-")        
    # clear all comments.
    # Called from load_save.py when a new game is loaded
    def clear_comments(self):
        self.moveno = 0
        self.comment_list = [""]
        self.tb.set_text("")
        self.window.set_title(_("Comment for Move ") + "0")
        if gv.show_moves == True:
            start, end =gv.gui.comment_view.get_buffer().get_bounds()
            gv.gui.comment_view.get_buffer().delete(start,end)
            gv.gui.comment_view.get_buffer().insert(start,"-")           
    # called by load_save.py when loading file in PSN format
    def set_comment(self, moveno, comment):
        while len(self.comment_list) <= moveno:
            self.comment_list.append("")
        self.comment_list[moveno] = comment

    # called by load_save.py when saving file in PSN format
    def get_comment(self, moveno):
        while len(self.comment_list) <= moveno:
            self.comment_list.append("")
        return self.comment_list[moveno]

    # called by load_save.py when saving file to check if there are
    # comments on it when saving in gshog format
    def has_comments(self):
        for comment in self.comment_list:
            if len(comment) > 0:
                return True
        return False


def get_ref():
    if Comments.comments_ref is None:
        Comments.comments_ref = Comments()
    return Comments.comments_ref
