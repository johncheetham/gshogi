#
#   set_board_colours.py - Gui Dialog to Change the Bopard Colours
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
import cairo
import os

from . import gv


class Set_Board_Colours:

    def __init__(self, prefix):
        if gv.verbose:
            print("set_board_colours - init")
        glade_dir = gv.gshogi.get_glade_dir()
        self.glade_file = os.path.join(glade_dir, "set_colours.glade")
        self.pieces_glade_file = os.path.join(glade_dir, "set_pieces.glade")
        self.dialog = None
        self.text_colour_temp = None

        # wood texture colour scheme
        path = os.path.join(prefix, "images", "wood1.png")
        self.wood1 = cairo.ImageSurface.create_from_png(path)
        path = os.path.join(prefix, "images", "wood1_hl.png")
        self.wood1_hl = cairo.ImageSurface.create_from_png(path)

        # default settings
        # these get overridden by settings from previous game (if any)
        self.bg_colour = "#645452"
        self.komadai_colour = "#c5b358"
        self.square_colour = "#ebdfb0"
        self.text_colour = "#fffdd0"
        self.piece_fill_colour = "#ffffd7"
        self.piece_outline_colour = "#000000"
        self.piece_kanji_colour = "#000001"
        self.border_colour = "#ebdfb0"
        self.grid_colour = "#000000"
        self.use_presets = True
        self.combo_idx = 0

    def get_colours(self):
        if self.use_presets:
            presets = self.get_presets()
            theme = presets[self.combo_idx]
            return theme[1]
        return \
            self.bg_colour, \
            self.komadai_colour, \
            self.square_colour, \
            self.text_colour, \
            self.piece_fill_colour, \
            self.piece_outline_colour, \
            self.piece_kanji_colour, \
            self.border_colour, \
            self.grid_colour

    # add inc to a hexstring
    # e.g. "f0" + 5 returns "f5"
    def addhex(self, h, inc):
        dec = int(h, 16) + inc
        if dec > 255:
            dec = 255
        hx1 = hex(dec)
        hx = hx1[2:]
        if len(hx) == 1:
            hx = "0" + hx
        return hx

    def get_cairo_colour(self, col):
        p = Gdk.color_parse(col)
        r = p.red / 65536.0
        g = p.green / 65536.0
        b = p.blue / 65536.0
        return r, g, b

    def set_square_colour(self, cr, a, linewidth, hilite):
        if self.use_presets:
            # preset is in use
            if self.combo_idx == 0:
                if hilite:
                    image = self.wood1_hl
                else:
                    image = self.wood1
                cr.set_source_surface(image, 0, 0)
                cairo.Pattern.set_extend(cr.get_source(), cairo.EXTEND_REPEAT)
                cr.rectangle(1, 1 , a.width-linewidth, a.height-linewidth)
                cr.fill()
                return

            presets = self.get_presets()
            theme = presets[self.combo_idx]
            # (bg_colour, komadai_colour, square_colour, text_colour,
            #  piece_fill_colour, piece_outline_colour, piece_kanji_colour)
            #    = theme[1]
            square_colour = theme[1][2]
            if hilite:
                # get r, g, b of square colour
                r = square_colour[1:3]
                g = square_colour[3:5]
                b = square_colour[5:7]

                # modify it a bit to get r, g, b of hilite colour
                r = self.addhex(r, 30)
                g = self.addhex(g, 30)
                b = self.addhex(b, 30)
                square_colour = "#" + r + g + b
            #return square_colour
        else:
            # custom colours are in use
            square_colour = self.square_colour
            if hilite:
                # get r, g, b of square colour
                r = square_colour[1:3]
                g = square_colour[3:5]
                b = square_colour[5:7]

                # modify it a bit to get r, g, b of hilite colour
                r = self.addhex(r, 30)
                g = self.addhex(g, 30)
                b = self.addhex(b, 30)
                square_colour = "#" + r + g + b
            #return square_colour
        r, g, b = self.get_cairo_colour(square_colour)
        cr.set_source_rgb(r, g, b)
        cr.rectangle(1, 1 , a.width-linewidth, a.height-linewidth)
        cr.fill()

    def set_komadai_square_colour(self, cr, a):
        if self.use_presets:
            # preset is in use
            if self.combo_idx == 0:
                image = self.wood1
                cr.set_source_surface(image, 0, 0)
                cairo.Pattern.set_extend(cr.get_source(), cairo.EXTEND_REPEAT)
                cr.rectangle(1, 1 , a.width, a.height)
                cr.fill()
                return

            presets = self.get_presets()
            theme = presets[self.combo_idx]
            # (bg_colour, komadai_colour, square_colour, text_colour,
            #  piece_fill_colour, piece_outline_colour, piece_kanji_colour)
            #    = theme[1]
            square_colour = theme[1][1]
        else:
            # custom colours are in use
            square_colour = self.komadai_colour
        r, g, b = self.get_cairo_colour(square_colour)
        cr.set_source_rgb(r, g, b)
        cr.rectangle(0, 0 , a.width, a.height)
        cr.fill()

    def set_komadai_colour(self, cr, a):
        if self.use_presets:
            # preset is in use
            if self.combo_idx == 0:
                image = self.wood1
                cr.set_source_surface(image, 0, 0)
                cairo.Pattern.set_extend(cr.get_source(), cairo.EXTEND_REPEAT)
                cr.rectangle(0, 0 , a.width, a.height)
                cr.fill()
                return
            presets = self.get_presets()
            theme = presets[self.combo_idx]
            # (bg_colour, komadai_colour, square_colour, text_colour,
            #  piece_fill_colour, piece_outline_colour, piece_kanji_colour)
            #    = theme[1]
            komadai_colour = theme[1][1]
            #return border_colour
        else:
            # custom colours are in use
            komadai_colour = self.komadai_colour
            #return self.border_colour
        r, g, b = self.get_cairo_colour(komadai_colour)
        cr.set_source_rgb(r, g, b)
        cairo.Pattern.set_extend(cr.get_source(), cairo.EXTEND_REPEAT)
        cr.rectangle(0, 0 , a.width, a.height)
        cr.fill()

    def set_border_colour(self, cr, a):
        if self.use_presets:
            # preset is in use
            if self.combo_idx == 0:
                image = self.wood1
                cr.set_source_surface(image, 0, 0)
                cairo.Pattern.set_extend(cr.get_source(), cairo.EXTEND_REPEAT)
                cr.rectangle(0, 0 , a.width, a.height)
                cr.fill()
                return
            presets = self.get_presets()
            theme = presets[self.combo_idx]
            # (bg_colour, komadai_colour, square_colour, text_colour,
            #  piece_fill_colour, piece_outline_colour, piece_kanji_colour)
            #    = theme[1]
            border_colour = theme[1][7]
            #return border_colour
        else:
            # custom colours are in use
            border_colour = self.border_colour
            #return self.border_colour
        r, g, b = self.get_cairo_colour(border_colour)
        cr.set_source_rgb(r, g, b)
        cairo.Pattern.set_extend(cr.get_source(), cairo.EXTEND_REPEAT)
        cr.rectangle(0, 0 , a.width, a.height)
        cr.fill()

    def set_colours(self, board_bg_colour, board_komadai_colour,
                    board_square_colour, board_text_colour, piece_fill_colour,
                    piece_outline_colour, piece_kanji_colour, border_colour,
                    grid_colour):
        if gv.verbose:
            print("set_board_colours - set_colours")
        self.bg_colour = board_bg_colour
        self.komadai_colour = board_komadai_colour
        self.square_colour = board_square_colour
        self.text_colour = board_text_colour
        self.piece_fill_colour = piece_fill_colour
        self.piece_outline_colour = piece_outline_colour
        self.piece_kanji_colour = piece_kanji_colour
        self.border_colour = border_colour
        self.grid_colour = grid_colour

    def get_text_colour(self):
        if self.text_colour_temp is not None:
            return self.text_colour_temp
        if self.use_presets:
            # preset is in use
            presets = self.get_presets()
            theme = presets[self.combo_idx]
            # (bg_colour, komadai_colour, square_colour, text_colour,
            #  piece_fill_colour, piece_outline_colour, piece_kanji_colour)
            #   = theme[1]
            text_colour = theme[1][3]
            return text_colour
        else:
            # custom colours are in use
            return self.text_colour

    def get_presets(self):
        # presets contains a list of colour themes
        #     0: theme name
        #     1: bg colour            (self.board_bg_colour)
        #     2: komadai colour       (self.board_komadai_colour)
        #     3: square colour        (self.board_square_colour)
        #     4: text colour          (self.board_text_colour)
        #     5: piece fill colour
        #     6: piece outline colour
        #     7: piece kanji colour
        #     8: border colour
        #     9: grid colour

        #      0           1          2          3          4          5
        #      6           7          8          9
        presets = [
          ["Wood",
           ("#888a85", "#C5B358", "#EBDFB0", "#000000",  "#FFFFD7", "#000000",
            "#000001", "#EBDFB0", "#000000")],
          ["Standard",
           ("#645452", "#C5B358", "#EBDFB0", "#000000",  "#FFFFD7", "#000000",
            "#000001", "#EBDFB0", "#000000")],
          ["Gold",
           ("#50404D", "#C5B358", "#E3A857", "#FFFDD0",  "#FADA5E", "#4B3621",
            "#FE6F5E", "#E3A857", "#000000")],
          ["Brown",
           ("#645452", "#C19A6B", "#C19A6B", "#FFFDD0",  "#F5DEB3", "#000000",
            "#1A1110", "#B5651D", "#000000")],
          [ "Peach",
          ('#645452', '#D7AD7C', '#D7AD7C', '#FFFDD0',  '#F5DEB3', '#000000',
          '#1A1110', '#D7AD7C', '#000000' )],  # peach
           [ "Blue", 
           ("#00008B", "#ACE5EE", "#ACE5EE", "#FFFDD0", "#E6E8FA",
           "#71A6D2", "#446CCF" ,"#EBDFB0", "#000000") ] ,   # blizzard bue
             [ 'Mint',       ('#2F4F4F', '#00A693', '#00A693', '#FFFFFF',  '#AAF0D1',
             '#465945', '#195905', '#00A693', '#000000') ],  # mint  
           [ 'Black',      ('#BEBEBE', '#C0C0C0', '#C0C0C0', '#000000',  '#000000',
           '#FFFFFF', '#FFFFFF', '#C0C0C0', '#000000') ],  # black     
        ]
        return presets

    def show_dialog(self, gtkaction):

        # save original state so we can revert if user cancels out
        self.orig_bg_colour, self.orig_komadai_colour, \
          self.orig_square_colour, self.orig_text_colour, \
          self.orig_piece_fill_colour, self.orig_piece_outline_colour, \
          self.orig_piece_kanji_colour, self.orig_border_colour, \
          self.orig_grid_colour = self.get_colours()
        self.orig_use_presets = self.use_presets
        self.orig_combo_idx = self.combo_idx

        self.text_colour_temp = None

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(gv.domain)
        self.builder.add_from_file(self.glade_file)
        self.builder.connect_signals(self)

        self.dialog = self.builder.get_object("sc_dialog")
        self.dialog.set_transient_for(gv.gui.get_window())
        self.presets_radio_button = self.builder.get_object(
            "presets_radiobutton")
        self.custom_colours_radio_button = self.builder.get_object(
            "custom_radiobutton")
        self.combobox = self.builder.get_object("sc_comboboxtext")
        self.combobox.set_entry_text_column(0)

        self.custom_colours_table = self.builder.get_object(
            "custom_colours_table")

        # get buttons used to set custom colours
        self.bg_colour_button = self.builder.get_object("BGcolorbutton")
        self.komadai_colour_button = self.builder.get_object(
            "Komadaicolorbutton")
        self.square_colour_button = self.builder.get_object(
            "Squarecolorbutton")
        self.text_colour_button = self.builder.get_object(
            "Textcolorbutton")
        self.piece_fill_colour_button = self.builder.get_object(
            "Piecefillcolorbutton")
        self.piece_outline_colour_button = self.builder.get_object(
            "Pieceoutlinecolorbutton")
        self.piece_kanji_colour_button = self.builder.get_object(
            "Piecekanjicolorbutton")
        self.border_colour_button = self.builder.get_object(
            "Bordercolorbutton")
        self.grid_colour_button = self.builder.get_object("Gridcolorbutton")

        # set the colours in the buttons
        self.bg_colour_button.set_color(Gdk.color_parse(self.bg_colour))
        self.komadai_colour_button.set_color(
            Gdk.color_parse(self.komadai_colour))
        self.square_colour_button.set_color(
            Gdk.color_parse(self.square_colour))
        self.text_colour_button.set_color(Gdk.color_parse(self.text_colour))
        # self.piece_fill_colour_button.set_color(
        #   Gdk.color_parse(self.piece_fill_colour))
        # self.piece_outline_colour_button.set_color(
        #   Gdk.color_parse(self.piece_outline_colour))
        # self.piece_kanji_colour_button.set_color(
        #   Gdk.color_parse(self.piece_kanji_colour))
        self.border_colour_button.set_color(
            Gdk.color_parse(self.border_colour))
        self.grid_colour_button.set_color(Gdk.color_parse(self.grid_colour))

        presets = self.get_presets()
        self.theme = presets[0]

        for theme in presets:
            theme_name = theme[0]
            self.combobox.append_text(theme_name)

        self.combobox.set_active(self.combo_idx)

        if self.use_presets:
            self.presets_radio_button.set_active(True)
            self.custom_colours_table.set_sensitive(False)
            self.combobox.set_sensitive(True)
        else:
            self.custom_colours_radio_button.set_active(True)
            self.custom_colours_table.set_sensitive(True)
            self.combobox.set_sensitive(False)

        response_cancel = 1
        response_ok = 2

        # If user hasn't clicked on OK then exit now
        if self.dialog.run() != response_ok:
            self.dialog.destroy()

            # restore original colours
            self.set_colours(
                self.orig_bg_colour, self.orig_komadai_colour,
                self.orig_square_colour, self.orig_text_colour,
                self.orig_piece_fill_colour, self.orig_piece_outline_colour,
                self.orig_piece_kanji_colour, self.orig_border_colour,
                self.orig_grid_colour)

            self.use_presets = self.orig_use_presets
            self.combo_idx = self.orig_combo_idx

            self.apply_colour_settings()
            return

        # save the settings so we can restore them next time in
        self.use_presets = self.presets_radio_button.get_active()
        self.combo_idx = self.combobox.get_active()

        # save the colour button settings
        self.bg_colour = self.get_button_colour(self.bg_colour_button)
        self.komadai_colour = self.get_button_colour(
            self.komadai_colour_button)
        self.square_colour = self.get_button_colour(self.square_colour_button)
        self.text_colour = self.get_button_colour(self.text_colour_button)
        # self.piece_fill_colour = self.get_button_colour(
        #   self.piece_fill_colour_button)
        # self.piece_outline_colour = self.get_button_colour(
        #   self.piece_outline_colour_button)
        # self.piece_kanji_colour = self.get_button_colour(
        #   self.piece_kanji_colour_button)
        self.border_colour = self.get_button_colour(self.border_colour_button)
        self.grid_colour = self.get_button_colour(self.grid_colour_button)

        self.dialog.destroy()
        self.apply_colour_settings()
        return

    def apply_colour_settings(self):
        if gv.verbose:
            print("set_board_colours - apply_colour_settings")
        self.text_colour_temp = None
        if self.use_presets:
            presets = self.get_presets()
            theme = presets[self.combo_idx]
            (bg_colour, komadai_colour, square_colour, text_colour,
             piece_fill_colour, piece_outline_colour, piece_kanji_colour,
             border_colour, grid_colour) = theme[1]
        else:
            (bg_colour, komadai_colour, square_colour, text_colour,
             piece_fill_colour, piece_outline_colour, piece_kanji_colour,
             border_colour, grid_colour) = (
                self.bg_colour, self.komadai_colour,
                self.square_colour, self.text_colour, self.piece_fill_colour,
                self.piece_outline_colour, self.piece_kanji_colour,
                self.border_colour, self.grid_colour)

        try:
            # gv.gui.set_colours(bg_colour, komadai_colour, square_colour,
            #                    text_colour, piece_fill_colour,
            #                    piece_outline_colour, piece_kanji_colour,
            #                    border_colour, grid_colour)
            gv.gui.set_colours(
                bg_colour, komadai_colour, square_colour, text_colour,
                border_colour, grid_colour)
        except Exception as e:
            print("set_board_colours.py - call to gui set_colours failed: ", e)

    # Callback called when the user has selected a custom colour
    def custom_colour_changed(self, colour_button):

        # if set to se presets then exit
        if self.presets_radio_button.get_active():
            return

        # get the colours from the buttons
        bg_colour = self.get_button_colour(self.bg_colour_button)
        komadai_colour = self.get_button_colour(self.komadai_colour_button)
        square_colour = self.get_button_colour(self.square_colour_button)
        text_colour = self.get_button_colour(self.text_colour_button)
        # piece_fill_colour = self.get_button_colour(
        #   self.piece_fill_colour_button)
        # piece_outline_colour = self.get_button_colour(
        #   self.piece_outline_colour_button)
        # piece_kanji_colour = self.get_button_colour(
        #   self.piece_kanji_colour_button)
        border_colour = self.get_button_colour(self.border_colour_button)
        grid_colour = self.get_button_colour(self.grid_colour_button)

        self.text_colour_temp = text_colour
        # gv.gui.set_colours(bg_colour, komadai_colour, square_colour,
        #                    text_colour, piece_fill_colour,
        #                    piece_outline_colour, piece_kanji_colour,
        #                    border_colour, grid_colour)
        #gv.gui.set_colours(
        #    bg_colour, komadai_colour, square_colour, text_colour,
        #    border_colour, grid_colour)

    def get_button_colour(self, colour_button):
        colour = colour_button.get_color()
        colour = colour.to_string()  # colour is 12 hex digits #rrrrggggbbbb
        # now it is 6 hex digits #rrggbb
        colour = "#" + colour[1:3] + colour[5:7] + colour[9:11]
        return colour

    # Callback called when the presets combobox item selected is changed
    def preset_changed(self, combobox):

        # if not set to se presets then exit
        if not self.presets_radio_button.get_active():
            return

        presets = self.get_presets()

        idx = self.combobox.get_active()
        if idx == -1:
            idx = 0

        # change the board/piece colours to what the user has selected
        theme = presets[idx]

        (bg_colour, komadai_colour, square_colour, text_colour,
         piece_fill_colour, piece_outline_colour, piece_kanji_colour,
         border_colour, grid_colour) = theme[1]

        self.text_colour_temp = text_colour
        # gv.gui.set_colours(bg_colour, komadai_colour, square_colour,
        #   text_colour, piece_fill_colour, piece_outline_colour,
        #   piece_kanji_colour, border_colour, grid_colour)
        #gv.gui.set_colours(
        #    bg_colour, komadai_colour, square_colour, text_colour,
        #    border_colour, grid_colour)

    # use presets radio button has been toggled
    def radio_button_changed(self, radio_button):
        if radio_button.get_active():
            self.custom_colours_table.set_sensitive(False)
            self.combobox.set_sensitive(True)
            self.preset_changed(self.combobox)
        else:
            self.combobox.set_sensitive(False)
            self.custom_colours_table.set_sensitive(True)
            self.custom_colour_changed(self.bg_colour_button)

    def get_settings(self):
        return (self.bg_colour,
                self.komadai_colour,
                self.square_colour,
                self.text_colour,
                self.piece_fill_colour,
                self.piece_outline_colour,
                self.piece_kanji_colour,
                self.border_colour,
                self.grid_colour,
                self.use_presets,
                self.combo_idx)

    #
    # restore the colour settings to the values from the previous game when
    # starting up gshogi
    #
    def restore_colour_settings(self, colour_settings):
        """
        (self.bg_colour,
         self.komadai_colour,
         self.square_colour,
         self.text_colour,
         self.piece_fill_colour,
         self.piece_outline_colour,
         self.piece_kanji_colour,
         self.border_colour,
         self.grid_colour,
         self.use_presets,
         self.combo_idx) = colour_settings
        """

        try:
            # get settings saved from previous game if any
            (self.bg_colour,
             self.komadai_colour,
             self.square_colour,
             self.text_colour,
             self.piece_fill_colour,
             self.piece_outline_colour,
             self.piece_kanji_colour,
             self.border_colour,
             self.grid_colour,
             self.use_presets,
             self.combo_idx) = colour_settings
        except AttributeError:
            # default colour settings
            self.bg_colour = "#645452"
            self.komadai_colour = "#c5b358"
            self.square_colour = "#ebdfb0"
            self.text_colour = "#fffdd0"
            self.piece_fill_colour = "#ffffd7"
            self.piece_outline_colour = "#000000"
            self.piece_kanji_colour = "#000001"
            self.border_colour = "#ebdfb0"
            self.grid_colour = "#000000"
            self.use_presets = True
            self.combo_idx = 0
        # check index in range
        try:
            presets = self.get_presets()
            theme = presets[self.combo_idx]
        except IndexError as ie:
            self.combo_idx = 0        

    #
    # The following functions are for the set pieces dialog (not set board
    # colours)
    #
    def show_pieces_dialog(self, gtkaction):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(gv.domain)
        self.builder.add_from_file(self.pieces_glade_file)
        self.builder.connect_signals(self)
        pieces_dialog = self.builder.get_object("pieces_dialog")
        pieces_dialog.set_transient_for(gv.gui.get_window())
        self.gshogi_radio_button = self.builder.get_object(
            "gshogi_radiobutton")
        self.eastern_radio_button = self.builder.get_object(
            "eastern_radiobutton")
        self.western_radio_button = self.builder.get_object(
            "western_radiobutton")
        self.custom_radio_button = self.builder.get_object(
            "custom_radiobutton")

        self.orig_pieceset = gv.pieces.get_pieceset()
        if self.orig_pieceset == "gshogi":
            self.gshogi_radio_button.set_active(True)
        elif self.orig_pieceset == "eastern":
            self.eastern_radio_button.set_active(True)
        elif self.orig_pieceset == "western":
            self.western_radio_button.set_active(True)
        elif self.orig_pieceset == "custom":
            self.custom_radio_button.set_active(True)

        if not gv.pieces.custom_pieces_loaded():
            self.custom_radio_button.set_sensitive(False)

        response_cancel = 1
        response_ok = 2

        # If user hasn't clicked on OK then exit now
        if pieces_dialog.run() != response_ok:
            pieces_dialog.destroy()
            # user cancelled so restore pieceset to what it was
            gv.board.use_pieceset(self.orig_pieceset)
        else:
            pieces_dialog.destroy()

    # callback for when piecset radiobutton changed
    def pieces_radio_button_changed(self, pieces_radio_button):
        if not pieces_radio_button.get_active():
            return
        name = pieces_radio_button.get_label()
        if name == "gshogi":
            pieceset = "gshogi"
        elif name == "GNU Shogi western":
            pieceset = "western"
        elif name == "GNU Shogi eastern":
            pieceset = "eastern"
        elif name == "Custom":
            pieceset = "custom"
        else:
            print("invalid pieceset in pieces_radio_button_changed in "
                  "set_board_colours.py:", name)
            pieceset = "eastern"

        gv.board.use_pieceset(pieceset)

    # called when user clicks the load custom pieces button
    def load_custom_pieces_button_clicked_cb(self, gtk_button):
        dialog = Gtk.FileChooserDialog(
            "Load Custom Pieces", None,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            dialog.destroy()
            return

        fname = dialog.get_filename()
        dialog.destroy()

        errmsg = gv.pieces.load_custom_pieces(fname)
        if errmsg is not None:
            gv.gui.info_box(errmsg)
        else:
            gv.gui.info_box("Pieces Loaded")

        if gv.pieces.custom_pieces_loaded():
            self.custom_radio_button.set_sensitive(True)
        else:
            self.custom_radio_button.set_sensitive(False)
