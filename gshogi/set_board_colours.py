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

import gtk
import gobject
import os

import utils

class Set_Board_Colours:

    set_board_colours_ref = None

    def __init__(self):
        self.verbose = False
        if self.verbose: print "set_board_colours - init"                      
        self.gui = utils.get_gui_ref()        
        self.game = utils.get_game_ref()
        self.pieces = utils.get_pieces_ref()
        self.board = utils.get_board_ref()
        glade_dir = self.game.get_glade_dir()
        self.glade_file = os.path.join(glade_dir, "set_colours.glade")
        self.pieces_glade_file = os.path.join(glade_dir, "set_pieces.glade")
        if Set_Board_Colours.set_board_colours_ref is not None:
            print "error - already have a _set_board_colours instance"       
        Set_Board_Colours.set_board_colours_ref = self
        self.use_presets = True      
        self.combo_idx = 0
        self.dialog = None
        self.text_colour_temp = None
       
        # default colour settings
        self.bg_colour = '#645452'
        self.komadai_colour = '#c5b358'
        self.square_colour = '#ebdfb0'
        self.text_colour = '#fffdd0'        
        self.piece_fill_colour = '#ffffd7'
        self.piece_outline_colour = '#000000'
        self.piece_kanji_colour = '#000001'        
        self.border_colour ='#ebdfb0'
        self.grid_colour = '#000000'


    def get_colours(self):
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


    def get_square_colour(self):
        if self.use_presets:
            # preset is in use                 
            presets = self.get_presets()
            theme = presets[self.combo_idx]
            #(bg_colour, komadai_colour, square_colour, text_colour, piece_fill_colour, piece_outline_colour, piece_kanji_colour) = theme[1]
            square_colour = theme[1][2]
            return square_colour
        else:
            # custom colours are in use          
            return self.square_colour

 
    def set_colours(self, board_bg_colour, board_komadai_colour, \
      board_square_colour, board_text_colour, piece_fill_colour, \
      piece_outline_colour, piece_kanji_colour, border_colour, grid_colour):
        if self.verbose: print "set_board_colours - set_colours"
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
            #(bg_colour, komadai_colour, square_colour, text_colour, piece_fill_colour, piece_outline_colour, piece_kanji_colour) = theme[1]
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

        presets = [
          #    0               1          2          3          4          5          6          7          8          9
          [ 'Standard',   ('#645452', '#C5B358', '#EBDFB0', '#000000',  '#FFFFD7', '#000000', '#000001', '#EBDFB0', '#000000') ],
          [ 'Black',      ('#BEBEBE', '#C0C0C0', '#C0C0C0', '#000000',  '#000000', '#FFFFFF', '#FFFFFF', '#C0C0C0', '#000000') ],  # black
          [ 'Gold',       ('#50404D', '#E3A857', '#E3A857', '#FADA5E',  '#FADA5E', '#4B3621', '#FE6F5E', '#E3A857', '#000000') ],  # gold        
          [ 'Mint',       ('#2F4F4F', '#00A693', '#00A693', '#FFFFFF',  '#AAF0D1', '#465945', '#195905', '#00A693', '#000000') ],  # mint        
          [ 'Brown',      ('#645452', '#C19A6B', '#C19A6B', '#FFFDD0',  '#F5DEB3', '#000000', '#1A1110', '#B5651D', '#000000') ],  # brown
          [ 'Custom1',    ('#645452', '#D7AD7C', '#D7AD7C', '#FFFDD0',  '#F5DEB3', '#000000', '#1A1110', '#D7AD7C', '#000000') ]   # custom1

          #[ 'Brown',      ('#E5B73B', '#C19A6B', '#C19A6B', '#FFFDD0',  '#B5651D', '#000000', '#1A1110') ]  # brown
          #[ 'Brown',      ('#B5651D', '#C19A6B', '#C19A6B', '#FFFDD0',  '#F5DEB3', '#000000', '#1A1110', '#C19A6B', '#000000') ]  # brown
          #[ 'Peach',     ('#BEBEBE', '#ACE1AF', '#ACE1AF', '#195905', '#465945', '#A0785A' ],  # peach                       
          #[ 'Silver',    ('#BEBEBE', '#ACE1AF', '#ACE1AF', '#195905', '#C0C0C0', '#465945', '#A0785A' ],  # silver          
          #[ 'new'   ,    ('#0000FF', '#FE6F5E', '#00FFFF', '#000000', '#FBAB60', '#E30022', '#000001' ]
          #[ 'Gold',       ('#50404D', '#E3A857', '#E3A857', '#FADA5E',  '#FADA5E', '#FE6F5E', '#4B3621') ],  # gold
          # [ 'Blue',      ('#00008B', '#ACE5EE', '#ACE5EE', '#FFFDD0', '#E6E8FA', '#71A6D2', '#446CCF') ],      # blizzard bue
          #[ 'Blue',      ('#E6E8FA', '#ACE5EE', '#ACE5EE', '#FFFDD0', '#E6E8FA', '#71A6D2', '#446CCF') ],      # blizzard bue

        ]
        return presets


    def show_dialog(self, gtkaction):
        
        # save original state so we can revert if user cancels out
        self.orig_bg_colour, self.orig_komadai_colour, \
          self.orig_square_colour, self.orig_text_colour, \
          self.orig_piece_fill_colour, self.orig_piece_outline_colour, \
          self.orig_piece_kanji_colour, self.orig_border_colour, \
          self.orig_grid_colour  = self.get_colours()
        self.orig_use_presets = self.use_presets
        self.orig_combo_idx = self.combo_idx

        self.text_colour_temp = None
 
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.glade_file)
        self.builder.connect_signals(self)

        self.dialog = self.builder.get_object('sc_dialog')
        self.presets_radio_button = self.builder.get_object('presets_radiobutton')
        self.custom_colours_radio_button = self.builder.get_object('custom_radiobutton')
        self.combobox = self.builder.get_object('sc_combobox') 

        self.custom_colours_table = self.builder.get_object('custom_colours_table')
       
        # make it equivalent of a 'new_text' combobox 
        liststore = gtk.ListStore(gobject.TYPE_STRING)
        self.combobox.set_model(liststore)
        cell = gtk.CellRendererText()
        self.combobox.pack_start(cell, True)
        self.combobox.add_attribute(cell, 'text', 0)
        
        # get buttons used to set custom colours 
        self.bg_colour_button = self.builder.get_object('BGcolorbutton')        
        self.komadai_colour_button = self.builder.get_object('Komadaicolorbutton')     
        self.square_colour_button = self.builder.get_object('Squarecolorbutton')       
        self.text_colour_button = self.builder.get_object('Textcolorbutton')        
        self.piece_fill_colour_button = self.builder.get_object('Piecefillcolorbutton')      
        self.piece_outline_colour_button = self.builder.get_object('Pieceoutlinecolorbutton')      
        self.piece_kanji_colour_button = self.builder.get_object('Piecekanjicolorbutton')
        self.border_colour_button = self.builder.get_object('Bordercolorbutton')
        self.grid_colour_button = self.builder.get_object('Gridcolorbutton')
 
       # set the colours in the buttons
        self.bg_colour_button.set_color(gtk.gdk.color_parse(self.bg_colour))
        self.komadai_colour_button.set_color(gtk.gdk.color_parse(self.komadai_colour))
        self.square_colour_button.set_color(gtk.gdk.color_parse(self.square_colour))
        self.text_colour_button.set_color(gtk.gdk.color_parse(self.text_colour))
        self.piece_fill_colour_button.set_color(gtk.gdk.color_parse(self.piece_fill_colour))
        self.piece_outline_colour_button.set_color(gtk.gdk.color_parse(self.piece_outline_colour))
        self.piece_kanji_colour_button.set_color(gtk.gdk.color_parse(self.piece_kanji_colour))
        self.border_colour_button.set_color(gtk.gdk.color_parse(self.border_colour)) 
        self.grid_colour_button.set_color(gtk.gdk.color_parse(self.grid_colour))    
           

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
            self.set_colours(self.orig_bg_colour, self.orig_komadai_colour, \
              self.orig_square_colour, self.orig_text_colour, \
              self.orig_piece_fill_colour, self.orig_piece_outline_colour, \
              self.orig_piece_kanji_colour, self.orig_border_colour, self.orig_grid_colour)

            self.use_presets = self.orig_use_presets
            self.combo_idx = self.orig_combo_idx

            self.apply_colour_settings()
            return  

        # save the settings so we can restore them next time in
        self.use_presets = self.presets_radio_button.get_active()
        self.combo_idx = self.combobox.get_active()

        # save the colour button settings
        self.bg_colour = self.get_button_colour(self.bg_colour_button)
        self.komadai_colour = self.get_button_colour(self.komadai_colour_button)
        self.square_colour = self.get_button_colour(self.square_colour_button)
        self.text_colour = self.get_button_colour(self.text_colour_button)
        self.piece_fill_colour = self.get_button_colour(self.piece_fill_colour_button)
        self.piece_outline_colour = self.get_button_colour(self.piece_outline_colour_button)
        self.piece_kanji_colour = self.get_button_colour(self.piece_kanji_colour_button)        
        self.border_colour = self.get_button_colour(self.border_colour_button)
        self.grid_colour = self.get_button_colour(self.grid_colour_button) 
 
        self.dialog.destroy()
        self.apply_colour_settings()
        return


    def apply_colour_settings(self):
        if self.verbose: print "set_board_colours - apply_colour_settings"        
        self.text_colour_temp = None
        if self.use_presets:                 
             presets = self.get_presets()
             theme = presets[self.combo_idx]
             (bg_colour, komadai_colour, square_colour, text_colour, piece_fill_colour, piece_outline_colour, piece_kanji_colour, border_colour, grid_colour) = theme[1]            
        else:
             (bg_colour, komadai_colour, square_colour, text_colour, piece_fill_colour, \
              piece_outline_colour, piece_kanji_colour, border_colour, grid_colour) = \
                (self.bg_colour, self.komadai_colour, \
                   self.square_colour, self.text_colour, self.piece_fill_colour, \
                   self.piece_outline_colour, self.piece_kanji_colour, self.border_colour, self.grid_colour)
                
        try:            
            self.gui.set_colours(bg_colour, komadai_colour, square_colour, text_colour, piece_fill_colour, piece_outline_colour, piece_kanji_colour, border_colour, grid_colour)
        except Exception, e:
            print "set_board_colours.py - call to gui set_colours failed: ", e
        

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
        piece_fill_colour = self.get_button_colour(self.piece_fill_colour_button)
        piece_outline_colour = self.get_button_colour(self.piece_outline_colour_button)
        piece_kanji_colour = self.get_button_colour(self.piece_kanji_colour_button)
        border_colour = self.get_button_colour(self.border_colour_button)
        grid_colour = self.get_button_colour(self.grid_colour_button)
         
        self.text_colour_temp = text_colour
        self.gui.set_colours(bg_colour, komadai_colour, square_colour, text_colour, piece_fill_colour, piece_outline_colour, piece_kanji_colour, border_colour, grid_colour)       
        

    def get_button_colour(self, colour_button):
        colour = colour_button.get_color()
        colour = colour.to_string()  # colour is 12 hex digits #rrrrggggbbbb        
        colour = '#' + colour[1:3] + colour[5:7] + colour[9:11]  # now it is 6 hex digits #rrggbb
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

        (bg_colour, komadai_colour, square_colour, text_colour, piece_fill_colour, piece_outline_colour, piece_kanji_colour, border_colour, grid_colour) = theme[1]
        
        self.text_colour_temp = text_colour
        self.gui.set_colours(bg_colour, komadai_colour, square_colour, text_colour, piece_fill_colour, piece_outline_colour, piece_kanji_colour, border_colour, grid_colour)


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
        return (self.bg_colour, \
                self.komadai_colour, \
                self.square_colour, \
                self.text_colour, \
                self.piece_fill_colour, \
                self.piece_outline_colour, \
                self.piece_kanji_colour, \
                self.border_colour, \
                self.grid_colour, \
                self.use_presets, \
                self.combo_idx)


    #
    # restore the colour settings to the values from the previous game when starting up gshogi
    #
    def restore_colour_settings(self, colour_settings):             
        (self.bg_colour, \
         self.komadai_colour, \
         self.square_colour, \
         self.text_colour, \
         self.piece_fill_colour, \
         self.piece_outline_colour, \
         self.piece_kanji_colour, \
         self.border_colour, \
         self.grid_colour, \
         self.use_presets, \
         self.combo_idx) = colour_settings
       
        self.apply_colour_settings()        


    #
    # The following functions are for the set pieces dialog (not set board colours)
    #
    def show_pieces_dialog(self, gtkaction):
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.pieces_glade_file)
        self.builder.connect_signals(self)        
        self.pieces_dialog = self.builder.get_object('pieces_dialog')
        self.eastern_radio_button = self.builder.get_object('eastern_radiobutton')
        self.western_radio_button = self.builder.get_object('western_radiobutton')
        self.custom_radio_button = self.builder.get_object('custom_radiobutton')

        self.orig_pieceset = self.pieces.get_pieceset()
        if self.orig_pieceset == 'eastern':
            self.eastern_radio_button.set_active(True)
        elif self.orig_pieceset == 'western':
            self.western_radio_button.set_active(True)
        elif self.orig_pieceset == 'custom':
            self.custom_radio_button.set_active(True)

        if not self.pieces.custom_pieces_loaded():            
            self.custom_radio_button.set_sensitive(False)

        response_cancel = 1
        response_ok = 2      
     
        # If user hasn't clicked on OK then exit now
        if self.pieces_dialog.run() != response_ok:            
            self.pieces_dialog.destroy()
            self.board.use_pieceset(self.orig_pieceset)  # user cancelled so restore pieceset to what it was 
        self.pieces_dialog.destroy()
         

    # callback for when piecset radiobutton changed
    def pieces_radio_button_changed(self, pieces_radio_button):
        if not pieces_radio_button.get_active():
            return        
        name = pieces_radio_button.get_label()
        if name == 'Use Western Pieces':
            pieceset = 'western'
        elif name == 'Use Eastern Pieces':
            pieceset = 'eastern'
        elif name == 'Use Custom Pieces':
            pieceset = 'custom'
        else:
            print "invalid pieceset in pieces_radio_button_changed in set_board_colours.py:",name
            pieceset = 'eastern'

        self.board.use_pieceset(pieceset)


    # called when user clicks the load custom pieces button
    def load_custom_pieces_button_clicked_cb(self, gtk_button):       
        dialog = gtk.FileChooserDialog("Load Custom Pieces",
                               None,
                               gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response != gtk.RESPONSE_OK:
            dialog.destroy()
            return

        fname = dialog.get_filename()
        dialog.destroy()        
        
        errmsg = self.pieces.load_custom_pieces(fname) 
        if errmsg is not None:
            self.gui.info_box(errmsg)            
        else:
            self.gui.info_box('Pieces Loaded')            

        if self.pieces.custom_pieces_loaded():
            self.custom_radio_button.set_sensitive(True)
        else:
            self.custom_radio_button.set_sensitive(False)

def get_ref():
    if Set_Board_Colours.set_board_colours_ref is None:
        Set_Board_Colours.set_board_colours_ref = Set_Board_Colours()
    return Set_Board_Colours.set_board_colours_ref



