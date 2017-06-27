#
#   gui.py
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
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import Pango
import os
import cairo
from datetime import date

from . import engine_debug
from . import engine_output
from . import move_list
from . import drag_and_drop
from . import set_board_colours
from . import load_save
from . import utils
from . import gamelist
from . import comments
from .constants import WHITE, BLACK, NAME, VERSION, TARGET_TYPE_TEXT
from . import gv


class Gui:

    gui_ref = None

    def __init__(self):
        if Gui.gui_ref is not None:
            raise RuntimeError("Attempt to create second gui instance")
        Gui.gui_ref = self

    def build_gui(self):

        self.gobactive = False
        self.engine_debug = engine_debug.get_ref()
        self.engine_output = engine_output.get_ref()
        # has to be implemented before Move_list because of update()
        if gv.show_moves == True:
            self.comment_view = Gtk.TextView()
            self.movestore = Gtk.ListStore(GObject.TYPE_STRING)  #model for Treeview 
        self.move_list = move_list.get_ref()
        self.gamelist = gamelist.get_ref()
        self.drag_and_drop = drag_and_drop.get_ref()
        self.enable_dnd = True
        self.load_save = load_save.get_ref()
        self.show_coords = True
        self.highlight_moves = True
        self.lastdir = os.path.expanduser("~") # Filehandling
        # Create Main Window
        glade_dir = gv.gshogi.get_glade_dir()
        self.glade_file = os.path.join(glade_dir, "main_window.glade")
        self.glade_file_preferences = os.path.join(
            glade_dir, "preferences.glade")
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(gv.domain)
        self.builder.add_from_file(self.glade_file)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("main_window")
        screen = self.window.get_screen()
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.set_window_size()

     
        self.window.set_title(NAME + " " + VERSION)

        # 1 eventbox per board square
        self.eb = [[Gtk.EventBox() for x in range(9)] for x in range(9)]

        # 1 eventbox per komadai board square
        self.keb = [[Gtk.EventBox() for x in range(7)] for x in range(2)]

        # Set a handler for delete_event that immediately exits GTK.
        self.window.connect("delete_event", gv.gshogi.delete_event)

        main_vbox = self.builder.get_object("main_vbox")
        main_vbox.show()

        # menu
        # Create a UIManager instance
        uimanager = Gtk.UIManager()

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)

        # main action group
        actiongroup = Gtk.ActionGroup("UIManagerAG")
        self.actiongroup = actiongroup

        # action group for toggleactions
        ta_action_group = Gtk.ActionGroup("AGPromoteMode")
        ta_action_group.add_toggle_actions([(
            "promotemode", None, _("_Ask Before Promoting"), None, None,
            self.promote_mode)])
             
        self.ta_action_group = ta_action_group

        # Create actions
        actiongroup.add_actions([
            # NewGame and the handicap names are used in gshogi.py NewGame
            # routine. don't change them.
            ("NewGame", Gtk.STOCK_NEW, _("_New Game"), None, _("New Game"),
             gv.gshogi.new_game_cb),
            ("LanceHandicap", None, _("_Lance"), None,
             _("Lance Handicap"), gv.gshogi.new_game_cb),
            ("BishopHandicap", None, _("_Bishop"), None,
             _("Bishop Handicap"), gv.gshogi.new_game_cb),
            ("RookHandicap", None, _("_Rook"), None,
             _("Rook Handicap"), gv.gshogi.new_game_cb),
            ("RookandLanceHandicap", None, _("_Rook and Lance"), None,
             _("Rook and Lance Handicap"), gv.gshogi.new_game_cb),
            ("TwoPieceHandicap", None, _("_2 Pieces"), None,
             _("Two Piece Handicap"), gv.gshogi.new_game_cb),
            ("FourPieceHandicap", None, _("_4 Pieces"), None,
             _("Four Piece Handicap"), gv.gshogi.new_game_cb),
            ("SixPieceHandicap", None, _("_6 Pieces"), None,
             _("Six Piece Handicap"), gv.gshogi.new_game_cb),
            ("EightPieceHandicap", None, _("_8 Pieces"), None,
             _("Eight Piece Handicap"), gv.gshogi.new_game_cb),
            ("TenPieceHandicap", None, _("_10 Pieces"), None,
             _("Ten Piece Handicap"), gv.gshogi.new_game_cb),
            ("ThreePawnHandicap", None, _("_3 Pawns"), None,
            _("Three Pawn Handicap"), gv.gshogi.new_game_cb),
            ("NewHandicapGame", None, _("_New Handicap Game")),
            #
            ("Quit", Gtk.STOCK_QUIT, _("_Quit"), None,
             _("Quit the Program"), gv.gshogi.quit_game),
            ("LoadGame", Gtk.STOCK_OPEN, _("_Load Game"), None,
             _("Load Game"), self.load_save.load_game),
            ("SaveGame", Gtk.STOCK_SAVE, _("_Save Game"), None,
             _("Save Game"), self.load_save.save_game),
            ("File", None, _("_File")),
            ("Edit", None, _("_Edit")),
            ("Undo", Gtk.STOCK_UNDO, _("_Undo Move"), "<Control>U",
             _("Undo Move"), gv.gshogi.undo_single_move),
            ("Redo", Gtk.STOCK_REDO, _("_Redo Move"), "<Control>R",
             _("Redo Move"), gv.gshogi.redo_single_move),
            ("MoveNow", None, _("_Move Now"), "<Control>M",
             _("Move Now"), gv.gshogi.move_now),
            ("SetBoardColours", None, _("_Set Board Colours"), None,
             _("Set Board Colours"), gv.set_board_colours.show_dialog),
            ("SetPieces", None, _("_Set Pieces"), None,
             _("Set Pieces"), gv.set_board_colours.show_pieces_dialog),
            ("TimeControl", None, _("_Time Control"), None,
             _("Time Control"), gv.tc.time_control),
            # ConfigureEngine1 - this name is used in engine_manager.
            # don't change it.
            ("ConfigureEngine1", None, _("_Configure Engine 1"), None,
             _("Configure Engine 1"), gv.engine_manager.configure_engine),
            ("ConfigureEngine2", None, _("_Configure Engine 2"), None,
             _("Configure Engine 2"), gv.engine_manager.configure_engine),
            ("Players", None, _("_Players"), None,
             _("Players"), gv.gshogi.set_players),
            ("Engines", None, _("_Engines"), None,
             _("Engines"), gv.engine_manager.engines),
            ("CommonEngineSettings", None, _("_Common Engine Settings"), None,
             _("Common Engine Settings"), gv.engine_manager.common_settings),
            ("MoveList", None, _("_Move List"), None,
             _("Move List"), self.move_list.show_movelist_window),
            ("GameList", None, _("_Game List"), None,
             _("Game List"), self.gamelist.show_gamelist_window_cb),
            ("EngineOutput", None, _("_Engine Output"), None,
             _("Engine Output"), self.engine_output.show_engine_output_window),
            ("EngineDebug", None, _("_Engine Debug"), None,
             _("Engine Debug"), self.engine_debug.show_debug_window),
            ("Options", None, _("_Options")),
            ("View", None, _("_View")),
            ("About", Gtk.STOCK_ABOUT, _("_About"), None,
             _("Show About Box"), self.about_box),
            ("Help", None, _("_Help")),
            ("CopyPosition", None, _("_Copy Position"), None,
             _("Copy Position"), utils.copy_SFEN_to_clipboard),
            ("PastePosition", None, _("_Paste Position"), None,
             _("Paste Position"), utils.paste_clipboard_to_SFEN),
            ("CopyGame", None, _("_Copy Game"), None,
             _("Copy Game"), utils.copy_game_to_clipboard),
            ("PasteGame", None, _("_Paste Game"), None,
             _("Paste Game"), utils.paste_game_from_clipboard),
            ("EditPosition", None, _("_Edit Position"), None,
             _("Edit Position"), self.enable_edit_mode),
            ("Preferences", None, _("_Preferences"), None,
             _("Preferences"), self.preferences),
            ]
        )

        # Add the actiongroups to the uimanager
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.insert_action_group(ta_action_group, 1)

        ui = """<ui>
        <menubar name="MenuBar">
            <menu action="File">
                <menuitem action="NewGame"/>
                <menu action="NewHandicapGame">
                    <menuitem action="LanceHandicap"/>
                    <menuitem action="BishopHandicap"/>
                    <menuitem action="RookHandicap"/>
                    <menuitem action="RookandLanceHandicap"/>
                    <menuitem action="TwoPieceHandicap"/>
                    <menuitem action="FourPieceHandicap"/>
                    <menuitem action="SixPieceHandicap"/>
                    <menuitem action="EightPieceHandicap"/>
                    <menuitem action="TenPieceHandicap"/>
                    <menuitem action="ThreePawnHandicap"/>
                </menu>
                <separator/>
                <menuitem action="LoadGame"/>
                <menuitem action="SaveGame"/>
                <separator/>
                <menuitem action="Quit"/>
            </menu>
            <menu action="Edit">
                <menuitem action="CopyPosition"/>
                <menuitem action="PastePosition"/>
                <separator/>
                <menuitem action="CopyGame"/>
                <menuitem action="PasteGame"/>
                <separator/>
                <menuitem action="EditPosition"/>
                <separator/>
                <menuitem action="Preferences"/>
            </menu>
            <menu action="Options">
                <menuitem action="Undo"/>
                <menuitem action="Redo"/>
                <menuitem action="MoveNow"/>
                <separator/>
                <menuitem action="promotemode"/>
                <menuitem action="SetBoardColours"/>
                <menuitem action="SetPieces"/>
                <separator/>
                <menuitem action="TimeControl"/>
                <menuitem action="ConfigureEngine1"/>
                <menuitem action="ConfigureEngine2"/>
                <menuitem action="Players"/>
                <menuitem action="Engines"/>
                <menuitem action="CommonEngineSettings"/>
            </menu>
            <menu action="View">
                <menuitem action="MoveList"/>
                <menuitem action="GameList"/>
                <menuitem action="EngineOutput"/>
                <menuitem action="EngineDebug"/>
            </menu>
            <menu action="Help">
                <menuitem action="About"/>
            </menu>
        </menubar>
        </ui>"""

        # Add a UI description
        uimanager.add_ui_from_string(ui)

        # Use an event box and set its background colour.
        # This was needed on Ubuntu 12.04 to set the toolbar bg colour.
        # Otherwise ubuntu uses the window bg colour which is not
        # correct.
        # don't need this on Fedora though.
        eb_1 = self.builder.get_object("eb_1")
        # eb_1 = Gtk.EventBox()
        vbox2 = Gtk.VBox(False, 0)
        # main_vbox.pack_start(vbox2, False)
        # main_vbox.pack_start(eb_1, False)
        eb_1.add(vbox2)
        eb_1.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#EDECEB"))##EDECEB
        # Create a MenuBar
        menubar = uimanager.get_widget("/MenuBar")
        vbox2.pack_start(menubar, False, True, 0)

        # create a toolbar
        toolbar = Gtk.Toolbar()
        vbox2.pack_start(toolbar, False, True, 0)

        # populate toolbar
        toolitem = Gtk.ToolItem()

        # 2 rows, 4 columns, not homogeneous
        tb = Gtk.Table(5, 8, False)

        # Gtk.ShadowType.NONE, SHADOW_IN, SHADOW_OUT, SHADOW_ETCHED_IN,
        # SHADOW_ETCHED_OUT

        self.side_to_move = [
            Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.ETCHED_IN),
            Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.ETCHED_IN)]
        self.side_to_move[BLACK].set_alignment(0.5, 0.4)
        self.side_to_move[WHITE].set_alignment(0.5, 0.4)

        tb.attach(self.side_to_move[WHITE], 0, 1, 1,2)
        tb.attach(self.side_to_move[BLACK], 0, 1, 2,3)
        #self.side_to_move.set_tooltip_text(_("Header from loaded file"))

        ue1 =Gtk.Label(label=_("Active:"))
        lw = Gtk.Label(label=_("White ") + ": ")
        lb = Gtk.Label(label=_("Black ") + ": ")
        ue1.set_alignment(0, 0.5)
        lw.set_alignment(0, 0.5)
        lb.set_alignment(0, 0.5)
        tb.attach(ue1, 1, 2, 0, 1)
        tb.attach(lw, 1, 2, 1, 2)
        tb.attach(lb, 1, 2, 2, 3)

        self.engines_lblw = Gtk.Label(label=" ") # This blank is mandatory, otherwise a fileheader will be written, reason not clear b.wille
        self.engines_lblw.set_use_markup(True)
        self.engines_lblw.set_alignment(0, 0.5)

        self.engines_lblb = Gtk.Label(label=_(" "))
        self.engines_lblb.set_use_markup(True)
        self.engines_lblb.set_alignment(0, 0.5)

        tb.attach(self.engines_lblw, 2, 3, 1, 2)
        tb.attach(self.engines_lblb, 2, 3, 2, 3)
        
        #Engines
        self.engines_lblw = Gtk.Label(label="gshogi")
        self.engines_lblw.set_use_markup(True)
        self.engines_lblw.set_alignment(0, 0.5)

        self.engines_lblb = Gtk.Label(label=_("human"))
        self.engines_lblb.set_use_markup(True)
        self.engines_lblb.set_alignment(0, 0.5)

        tb.attach(self.engines_lblw, 2, 3, 1, 2)
        tb.attach(self.engines_lblb, 2, 3, 2, 3)
        # time control
        self.tc_lbl = [
            Gtk.Label(label="00:45:00 00/10"),
            Gtk.Label(label="00:45:00 00/10")]
        self.tc_lbl[BLACK].set_alignment(0, 0.5)
        self.tc_lbl[WHITE].set_alignment(0, 0.5)

        tb.attach(self.tc_lbl[WHITE], 3, 4, 1, 2)
        tb.attach(self.tc_lbl[BLACK], 3, 4, 2, 3)
        tb.set_tooltip_text(_("Side to move(>), engines and time"))
        toolitem.add(tb)
        toolbar.insert(toolitem, -1)          
        if  gv.show_header == True:
            # add a vertical separator
            hb = Gtk.HBox(False, 0)
            toolitem = Gtk.ToolItem()
            vsep = Gtk.VSeparator()
            hb.pack_start(vsep, True, True, 10)
            toolitem.add(hb)
            toolbar.insert(toolitem, -1)               

              

        # Header
        tb = Gtk.Table(5, 8, False)
        if  gv.show_header == True:                 
    
            self.header_lue = Gtk.Label(label=_("     From file: "))
            self.header_lsente = Gtk.Label(label=_("     Sente(Blk)") + ": ")
            self.header_lgote = Gtk.Label(label= _("     Gote (Whi)") + ": ")
            self.header_levent = Gtk.Label(label=_("     Event") + ": ")
            self.header_ldate = Gtk.Label(label=_("     Date") + ": ")
            self.header_lue.set_alignment(0, 0.5)
            self.header_lsente.set_alignment(0, 0.5)
            self.header_lgote.set_alignment(0, 0.5)
            self.header_levent.set_alignment(0, 0.5)
            self.header_ldate.set_alignment(0, 0.5)
            tb.attach(self.header_lue, 5, 6, 0, 1)
            tb.attach(self.header_levent, 5, 6, 1, 2)
            tb.attach(self.header_ldate, 5, 6, 2, 3)
            tb.attach(self.header_lsente, 5, 6, 4,5)
            tb.attach(self.header_lgote, 5,  6, 3, 4)
            self.header_lblsente = Gtk.Label(label=_(" ") )
            self.header_lblgote = Gtk.Label(label=_(" ")  )
            self.header_lblevent = Gtk.Label(label=_("None"))
            self.header_lbldate = Gtk.Label(label=str(date.today().day)+ _(".")+ str(date.today().month) + _(".") +str(date.today().year))
            self.header_lblsente.set_alignment(0, 0.5)
            self.header_lblgote.set_alignment(0, 0.5)
            self.header_lblevent.set_alignment(0, 0.5)
            self.header_lbldate.set_alignment(0, 0.5)
            tb.attach(self.header_lblevent, 7, 8, 1, 2)
            tb.attach(self.header_lbldate, 7, 8, 2, 3)
            tb.attach(self.header_lblsente, 7,  8, 4, 5)
            tb.attach(self.header_lblgote, 7, 8, 3, 4)
            tb.set_tooltip_text(_("Header from loaded file"))
            toolitem = Gtk.ToolItem()
            toolitem.add(tb)
            toolbar.insert(toolitem, -1)


        # add a vertical separator
        hb = Gtk.HBox(False, 0)
        toolitem = Gtk.ToolItem()
        vsep = Gtk.VSeparator()
        hb.pack_start(vsep, True, True, 10)
        toolitem.add(hb)
        toolbar.insert(toolitem, -1)

        # stop/go buttons
        hb = Gtk.HBox(False, 0)
        self.gobutton = Gtk.ToolButton(Gtk.STOCK_YES)
        self.gobutton.connect("clicked", gv.gshogi.go_clicked)
        self.stopbutton = Gtk.ToolButton(Gtk.STOCK_NO)
        self.stopbutton.connect("clicked", gv.gshogi.stop_clicked)
        self.gobutton.set_tooltip_text(_("go"))
        self.stopbutton.set_tooltip_text(_("stop"))
        hb.pack_start(self.stopbutton, False, True, 0)
        hb.pack_start(self.gobutton, False, True, 0)
        
        toolitem = Gtk.ToolItem()
        toolitem.add(hb)
        toolbar.insert(toolitem, -1)

        # add a vertical separator
        hb = Gtk.HBox(False, 0)
        toolitem = Gtk.ToolItem()
        vsep = Gtk.VSeparator()
        hb.pack_start(vsep, True, True, 10)
        toolitem.add(hb)
        toolbar.insert(toolitem, -1)

        # game review buttons
        hb = Gtk.HBox(False, 0)
        self.go_first = Gtk.ToolButton(Gtk.STOCK_GOTO_FIRST)
        self.go_first.connect("clicked", gv.gshogi.undo_all)

        self.go_back = Gtk.ToolButton(Gtk.STOCK_GO_BACK)
        self.go_back.connect("clicked", gv.gshogi.undo_single_move)

        self.go_forward = Gtk.ToolButton(Gtk.STOCK_GO_FORWARD)
        self.go_forward.connect("clicked", gv.gshogi.redo_single_move)

        self.go_last = Gtk.ToolButton(Gtk.STOCK_GOTO_LAST)
        self.go_last.connect("clicked", gv.gshogi.redo_all)
        hb.set_tooltip_text(_("Moves"))
        hb.pack_start(self.go_first, False, True, 0)
        hb.pack_start(self.go_back, False, True, 0)
        hb.pack_start(self.go_forward, False, True, 0)
        hb.pack_start(self.go_last, False, True, 0)

        toolitem = Gtk.ToolItem()
        toolitem.add(hb)
        toolbar.insert(toolitem, -1)

        # add a vertical separator
        hb = Gtk.HBox(False, 0)
        toolitem = Gtk.ToolItem()
        vsep = Gtk.VSeparator()
        hb.pack_start(vsep, True, True, 10)
        toolitem.add(hb)
        toolbar.insert(toolitem, -1)

        main_grid = self.builder.get_object("grid1")
        main_grid.set_row_homogeneous(True)
        main_grid.set_column_homogeneous(True)
       #Insert comment-editing buttons
        if gv.show_moves == True:
            hb = Gtk.HBox(False, 0)
            self.cedit = Gtk.ToolButton(Gtk.STOCK_EDIT)
            self.cedit.connect("clicked", self.set_cedit)
            hb.set_tooltip_text(_("Comments"))
            self.csave = Gtk.ToolButton(Gtk.STOCK_SAVE)
            self.csave.connect("clicked", self.set_csave)
        
            self.ccancel = Gtk.ToolButton(Gtk.STOCK_CANCEL)
            self.ccancel.connect("clicked", self.set_ccancel)
            
            hb.pack_start(self.cedit, False, True, 0)
            hb.pack_start(self.ccancel, False, True, 0)
            hb.pack_start(self.csave, False, True, 0)
                          
            toolitem = Gtk.ToolItem()
            toolitem.add(hb)
            toolbar.insert(toolitem, -1)
            self.ccancel.set_sensitive(False)
            self.csave.set_sensitive(True)
          
        main_grid = self.builder.get_object("grid1")
        main_grid.set_row_homogeneous(True)
        main_grid.set_column_homogeneous(True)       
        # Insert Movebox
        if gv.show_moves == True:
            self.move_box = Gtk.ScrolledWindow()
            self.move_view = Gtk.TreeView()
            #mlabel = Gtk.Label("Moves")
            mframe = Gtk.Frame()
            mframe.set_label("Moves")
            mframe.add(self.move_box)
            self.move_box.add(self.move_view)             #omitted viewport
            main_grid.attach(mframe, 0, 14, 4, 6)  #Synthax: left, top, width, height
            self.move_box.set_policy(1,1)
            self.move_view.set_headers_visible(False)
            #main_grid.attach(mlabel,0,14,4,1)
            #model
            #has to be implemented in init
            #self.movestore = Gtk.ListStore(GObject.TYPE_STRING)  #model for Treeview 
            self.move_view.set_model(self.movestore)
            self.move_view.set_tooltip_text(_("Moves: click to jump to"))
            self.comment_box = Gtk.ScrolledWindow()
            #has to be implemented in init
            #self.comment_view = Gtk.TextView()
            #clabel = Gtk.Label("Comments")
            cframe = Gtk.Frame()
            cframe.set_label("Comments")
            cframe.add(self.comment_box)
            self.comment_box.add_with_viewport(self.comment_view)
            gv.gui.comment_view.modify_bg(
                        Gtk.StateType.NORMAL, Gdk.color_parse(gv.set_board_colours.bg_colour))                        
            gv.gui.move_view.modify_bg(
                    Gtk.StateType.NORMAL, Gdk.color_parse(gv.set_board_colours.bg_colour))            #angleichen an grid                 
            self.comment_view.set_wrap_mode(2)   #GTK_WRAP_WORD)
            g = self.comment_view.get_wrap_mode()
            self.comment_view.set_tooltip_text(_("Comments: Button in right part of menu to edit")) 
            
            main_grid.attach(cframe, 28, 0, 4, 6)        
            #main_grid.attach(clabel,28,0,4,1)
            #self.move_view.set_editable(False)
            cell0 = Gtk.CellRendererText()
            # cell0.set_property("cell-background", Gdk.color_parse("#F8F8FF"))
            mvcolumn0 = Gtk.TreeViewColumn("#")
            self.move_view.append_column(mvcolumn0)
            mvcolumn0.pack_start(cell0, True)
            mvcolumn0.set_min_width(30)
            mvcolumn0.set_attributes(cell0, text=0)            
            self.comment_view.set_editable(False)
            self.comment_view.set_cursor_visible(False)
            self.move_view.connect("cursor_changed", self.moves_clicked)
    # Create komadai grids for captured pieces
        self.setup_komadai(WHITE, main_grid)
        self.setup_komadai(BLACK, main_grid)

        # Create a 9x9 table for the main board
        self.boardgrid = Gtk.Grid.new()
        self.boardgrid.set_row_homogeneous(True)
        self.boardgrid.set_column_homogeneous(True)
        self.boardgrid.set_border_width(1)

        #
        # init board squares (add event box, set up drag and drop,
        # button clicks)
        # x, y = 0, 0 is the top left square of the board
        #
        for x in range(9):
            for y in range(9):
                self.init_board_square(x, y)

        eb2 = Gtk.EventBox()

        eb2.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))
        eb2.add(self.boardgrid)
        eb = Gtk.EventBox()
        eb.add(eb2)
        eb.show()

        aspect_frame = Gtk.AspectFrame(label=None, xalign=0.5, yalign=0.5,
                                       ratio=1.0, obey_child=False)
        aspect_frame.add(eb)

        eb2.set_border_width(20)
        self.grid_eb = eb2

        main_grid.attach(aspect_frame, 6, 0, 20, 20)
        #aspect_frame.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))

        eb.connect("draw", self.draw_border)
        self.border_eb = eb

        # status bar
        self.status_bar = self.builder.get_object("status_bar")

        # set status bar bg color
        # Use an event box and set its background colour.
        # This was needed on Fedora 19 to set the statusbar bg colour.
        # Otherwise it uses the window bg colour which is not
        # correct. This was not needed on F17.
        eb_2 = self.builder.get_object("eb_2")
        #eb_2.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse(bg_colour)) ##EDECEB
        self.status_bar = Gtk.Statusbar()
        main_vbox.pack_start(self.status_bar, False, False, 0)
        self.context_id = self.status_bar.get_context_id("gshogi statusbar")

        self.actiongroup.get_action("MoveNow").set_sensitive(False)

        self.window.show_all()
        self.side_to_move[WHITE].hide()
        self.gobutton.set_sensitive(False)
        self.stopbutton.set_sensitive(False)

        # mask = Gdk.WindowHints.BASE_SIZE|
        #            Gdk.WindowHints.MIN_SIZE|
        #            Gdk.WindowHints.MAX_SIZE|
        #            Gdk.WindowHints.RESIZE_INC|Gdk.WindowHints.ASPECT
        #mask = Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE
        mask = Gdk.WindowHints.MIN_SIZE
        geometry = Gdk.Geometry()
        # geometry.base_width = -1
        # geometry.base_height = -1
        # geometry.max_width = -1
        # geometry.max_height = -1
        geometry.min_width = 378
        geometry.min_height = 378
        # geometry.width_inc = -1
        # geometry.height_inc = -1
        # geometry.min_aspect = -1.0
        # geometry.max_aspect = -1.0
        #self.window.set_geometry_hints(self.window, geometry, mask)
        # self.window.set_geometry_hints(
        #   self.window, min_width=378, min_height=378, max_width=-1,
        #   max_height=-1, base_width=-1, base_height=-1, width_inc=-1,
        #   height_inc=-1, min_aspect=-1.0, max_aspect=-1.0)

        self.build_edit_popup()
    
       
    def moves_clicked(self, widget, data=None):
        self.moves_clicked_(0)
    
    def moves_clicked_(self, incr):
        model, triter = self.move_view.get_selection().get_selected()
        if triter != None: 
            k = self.movestore.get_value(triter,0).find(".")      
            nmove = int(self.movestore.get_value(triter,0)[0:k])   
            self.move_list.set_move(nmove)                                            
            self.move_list.move_box_selection()
    
    def set_cedit(self, widget):
        self.cedit.set_sensitive(False)
        self.ccancel.set_sensitive(True)
        self.csave.set_sensitive(True)
        self.comment_view.set_editable(True)
        self.comment_view.cursor_visible = True
        
        
    
    def set_csave(self, widget):
        self.cedit.set_sensitive(True)
        self.ccancel.set_sensitive(False)
        self.csave.set_sensitive(False)
        self.comment_view.set_editable(False)
        self.comment_view.cursor_visible = False       
        model, triter = self.move_view.get_selection().get_selected()
        if triter != None:
            k = self.movestore.get_value(triter,0).find(".")      
            nmove = int(self.movestore.get_value(triter,0)[0:k])
            start = self.comment_view.get_buffer().get_start_iter()
            end = self.comment_view.get_buffer().get_end_iter()
            self.move_list.set_comment(nmove,self.comment_view.get_buffer().get_text(start, end, False))
            self.move_list.set_comment_ind(True)
        #print("comment ",nmove)
        #save
    
    def set_ccancel(self, widget):   
        self.cedit.set_sensitive(True)
        self.ccancel.set_sensitive(False)
        self.csave.set_sensitive(False) 
        self.comment_view.set_editable(False)
        self.comment_view.set_editable(False)
        self.comment_view.cursor_visible = False          

      
    def draw_board_square(self, widget, cr, x, y):
        gv.board.set_image_cairo(x, y, cr=cr, widget=widget)

    def init_board_square(self, x, y):
        event_box = self.eb[x][y]
        event_box.connect("draw", self.draw_board_square, x, y)
        self.boardgrid.attach(event_box, x, y, 1, 1)
        event_box.set_hexpand(True)
        event_box.set_vexpand(True)
        event_box.show()
        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        data = (x, y)
        event_box.connect("button_press_event", gv.gshogi.square_clicked, data)
        event_box.connect("drag_data_get", self.drag_and_drop.sendCallback)
        event_box.connect_after(
            "drag_begin", self.drag_and_drop.drag_begin, (x, y))
        event_box.connect_after("drag_end", self.drag_and_drop.drag_end)

        # set up square as a destination square to receive drag data
        # from a drag & drop action
        event_box.connect(
            "drag_data_received", self.drag_and_drop.receiveCallback, (x, y))

    def dnd_set_source_square(self, x, y):
        self.targets = [
            Gtk.TargetEntry.new(
                "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]
        self.eb[x][y].drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

    def dnd_unset_source_square(self, x, y):
        self.eb[x][y].drag_source_unset()

    def dnd_set_dest_square(self, x, y):
        self.targets = [
            Gtk.TargetEntry.new(
                "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]
        self.eb[x][y].drag_dest_set(
            Gtk.DestDefaults.MOTION |
            #Gtk.DestDefaults.HIGHLIGHT |
            Gtk.DestDefaults.DROP,
            self.targets, Gdk.DragAction.COPY)

    def dnd_unset_dest_square(self, x, y):
        self.eb[x][y].drag_dest_unset()

    def dnd_unset_source_komadai_square(self, y):
        self.keb[BLACK][y].drag_source_unset()
        self.keb[WHITE][y].drag_source_unset()

    def dnd_set_source_bcap_square(self, y):
        self.targets = [
            Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP,
                                TARGET_TYPE_TEXT)]
        self.keb[BLACK][y].drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

    def dnd_set_source_wcap_square(self, y):
        self.targets = [
            Gtk.TargetEntry.new(
                "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]
        self.keb[WHITE][y].drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

    # set all squares so they cannot be used for drag and drop
    def unset_all_drag_and_drop_squares(self):
        # main board
        for x in range(9):
            for y in range(9):
                self.dnd_unset_source_square(x, y)
                self.dnd_unset_dest_square(x, y)

        # komadai
        for y in range(7):
            # set default to unset (no square can be dragged)
            self.dnd_unset_source_komadai_square(y)

    #
    # Look at each board square and set it as a valid drag and drop
    # source square or target square if applicable
    #
    def apply_drag_and_drop_settings(self, player, stm):

        if gv.verbose:
            print("in apply_drag_and_drop_settings")

        # If drag and drop not enabled then exit
        # if not self.ta_action_group.get_action("enableDND").get_active():
        if not self.enable_dnd:
            self.unset_all_drag_and_drop_squares
            return

        for x in range(9):
            for y in range(9):
                # set default to unset (no square can be dragged or dropped
                self.dnd_unset_source_square(x, y)
                self.dnd_unset_dest_square(x, y)

                # if not human to move then no drag and drop allowed on any
                # square
                if player != "Human":
                    continue

                # player is human so allow a square to be dragged if it
                # contains a piece for his side

                # human piece - set as valid source square for dnd
                if gv.board.valid_source_square(x, y, stm):
                    self.dnd_set_source_square(x, y)
                    self.dnd_unset_dest_square(x, y)
                else:
                    # valid target square for dnd
                    self.dnd_unset_source_square(x, y)
                    self.dnd_set_dest_square(x, y)

        wcap = gv.board.get_capturedw()
        bcap = gv.board.get_capturedb()

        # komadai
        for y in range(7):
            # set default to unset (no square can be dragged)
            self.dnd_unset_source_komadai_square(y)
            if player != "Human":
                continue

            # player is human so allow a square to be dragged if it
            # contains a piece for his side
            if gv.board.get_cap_piece(y, stm) != "-":
                if stm == WHITE:
                    self.dnd_set_source_wcap_square(y)
                else:
                    self.dnd_set_source_bcap_square(y)

    #
    # set up the komadai. This is a an area on the left of the screen
    # for white (right for black) to hold captured pieces
    #
    def setup_komadai(self, side, grid):
        komgrid = Gtk.Grid()
        komgrid.set_row_homogeneous(True)
        cap_label = gv.board.get_cap_label(side)

        eb2 = Gtk.EventBox()
        #eb2.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#000000"))

        eb = Gtk.EventBox()
        eb.add(komgrid)
        eb.show()
        eb.set_border_width(3)
        eb2.add(eb)
        if side == WHITE:
            grid.attach(eb2, 0, 0, 4, 14)
            self.komadaiw_eb = eb
            self.komadaiw_eb.connect("draw", self.draw_komadai)
        else:
            grid.attach(eb2, 28, 6, 4, 14)
            self.komadaib_eb = eb
            self.komadaib_eb.connect("draw", self.draw_komadai)
        komgrid.show()

        for y in range(7):
            self.init_komadai_square(
                y, cap_label[y], side, komgrid)

    def init_komadai_square(self, y, label, side, komgrid):
        hb = Gtk.HBox(False, 0)
        hb.show()
        event_box = self.keb[side][y]
        event_box.set_vexpand(True)
        event_box.set_hexpand(True)

        aspect_frame = Gtk.AspectFrame(label=None, xalign=0.5, yalign=0.5,
                                       ratio=1.0, obey_child=False)
        aspect_frame.set_shadow_type(Gtk.ShadowType.NONE)
        aspect_frame.add(event_box)

        event_box.connect("draw", self.draw_komadai_square, y, side)

        fontdesc = Pango.FontDescription("Monospace 15")
        label.modify_font(fontdesc)
        label.show()

        if side == WHITE:
            hb.pack_start(label, False, False, 0)
            hb.pack_start(aspect_frame, True, True, 0)
            komgrid.attach(hb, 0, y, 1, 1)
            event_box.set_name("wcap_eb")
        else:
            hb.pack_end(label, False, False, 0)
            hb.pack_end(aspect_frame, True, True, 0)
            komgrid.attach(hb, 0, y, 1, 1)
            event_box.set_name("bcap_eb")

        event_box.show()
        aspect_frame.show()
        #event_box.set_border_width(5)
        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        x = 0
        data = (x, y, side)
        event_box.connect(
            "button_press_event", gv.gshogi.cap_square_clicked, data)

        self.targets = [
            ("text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]
        event_box.connect("drag_data_get", self.drag_and_drop.sendCallback)
        event_box.connect_after(
            "drag_begin", self.drag_and_drop.drag_begin, (x, y))
        event_box.connect_after("drag_end", self.drag_and_drop.drag_end)

    def draw_komadai_square(self, wid, cr, y, side):
        piece = gv.board.get_cap_piece(y, side)
        piece = " " + piece
        gv.board.set_image_cairo_komadai(y, piece, side, wid, cr)

    def get_komadai_event_box(self, side, y):
        return self.keb[side][y]

    def get_event_box(self, x, y):
        return self.eb[x][y]

    # about box
    def about_box(self, widget):
        about = Gtk.AboutDialog(parent=self.window)
        #
        # set_program_name method is available in PyGTK 2.12 and above
        #
        try:
            about.set_program_name(NAME)
        except AttributeError:
            pass
        about.set_version(VERSION)
        about.set_copyright("Copyright \u00A9 2010-2017\nJohn Cheetham\nBernd Wille\nEric James Michael Ritz")
        about.set_comments(
            "gshogi is a program to play shogi (Japanese Chess).")
        about.set_authors(["John Cheetham", "Bernd Wille", "Eric James Michael Ritz"])
        about.set_website(
            "http://www.johncheetham.com/projects/gshogi/index.html")
        about.set_logo(
            GdkPixbuf.Pixbuf.new_from_file(
                os.path.join(gv.gshogi.prefix, "images/logo.png")))

        license = """gshogi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

gshogi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with gshogi.  If not, see <http://www.gnu.org/licenses/>."""

        about.set_license(license)
        about.run()
        about.destroy()

    def set_status_bar_msg(self, msg):
        if gv.gshogi.quitting:
            return
        self.context_id = self.status_bar.get_context_id("gshogi statusbar")
        self.status_bar.push(self.context_id, msg)
            
    # ask before promoting
    def promote_mode(self, w):
        if w.get_active():
            gv.gshogi.set_promotion_mode(True)
        else:
            gv.gshogi.set_promotion_mode(False)

    # disable some functionality if computer is thinking or in edit mode
    def disable_menu_items(self, mode=None):
        self.go_first.set_sensitive(False)
        self.go_back.set_sensitive(False)
        self.go_forward.set_sensitive(False)
        self.go_last.set_sensitive(False)

        self.actiongroup.get_action("NewGame").set_sensitive(False)
        self.actiongroup.get_action("NewHandicapGame").set_sensitive(False)
        self.actiongroup.get_action("LoadGame").set_sensitive(False)
        self.actiongroup.get_action("SaveGame").set_sensitive(False)

        if mode == "editmode":
            # edit menu
            self.actiongroup.get_action("CopyPosition").set_sensitive(False)
            self.actiongroup.get_action("PastePosition").set_sensitive(False)
            self.actiongroup.get_action("CopyGame").set_sensitive(False)
            self.actiongroup.get_action("PasteGame").set_sensitive(False)
            self.actiongroup.get_action("EditPosition").set_sensitive(True)

            # if edit mode disable all options menu
            self.actiongroup.get_action("Options").set_sensitive(False)
            self.gobutton.set_sensitive(False)
            self.stopbutton.set_sensitive(False)
        else:
            self.actiongroup.get_action("Edit").set_sensitive(False)
            # set items in options menu
            self.actiongroup.get_action("Undo").set_sensitive(False)
            self.actiongroup.get_action("Redo").set_sensitive(False)
            self.actiongroup.get_action("MoveNow").set_sensitive(True)
            self.actiongroup.get_action("SetBoardColours").set_sensitive(False)
            self.actiongroup.get_action("TimeControl").set_sensitive(False)
            self.actiongroup.get_action(
                "ConfigureEngine1").set_sensitive(False)
            self.actiongroup.get_action(
                "ConfigureEngine2").set_sensitive(False)
            self.actiongroup.get_action("Players").set_sensitive(False)
            self.actiongroup.get_action("Engines").set_sensitive(False)
            self.actiongroup.get_action(
                "CommonEngineSettings").set_sensitive(False)

            self.gobutton.set_sensitive(False)
            self.stopbutton.set_sensitive(True)

    # enable some functionality when computer is finished thinking
    def enable_menu_items(self, mode=None):
        self.go_first.set_sensitive(True)
        self.go_back.set_sensitive(True)
        self.go_forward.set_sensitive(True)
        self.go_last.set_sensitive(True)
        # self.ta_action_group.get_action("enableDND").set_sensitive(True)
        self.actiongroup.get_action("Undo").set_sensitive(True)
        self.actiongroup.get_action("Redo").set_sensitive(True)
        self.actiongroup.get_action("ConfigureEngine1").set_sensitive(True)
        self.actiongroup.get_action("ConfigureEngine2").set_sensitive(True)
        self.actiongroup.get_action("NewGame").set_sensitive(True)
        self.actiongroup.get_action("NewHandicapGame").set_sensitive(True)
        self.actiongroup.get_action("LoadGame").set_sensitive(True)
        self.actiongroup.get_action("SaveGame").set_sensitive(True)
        self.actiongroup.get_action("Engines").set_sensitive(True)
        self.actiongroup.get_action("Players").set_sensitive(True)
        self.actiongroup.get_action("TimeControl").set_sensitive(True)
        self.actiongroup.get_action("MoveNow").set_sensitive(False)
        self.actiongroup.get_action("CommonEngineSettings").set_sensitive(True)
        self.actiongroup.get_action("SetBoardColours").set_sensitive(True)

        self.actiongroup.get_action("Edit").set_sensitive(True)
        # edit menu
        self.actiongroup.get_action("CopyPosition").set_sensitive(True)
        self.actiongroup.get_action("PastePosition").set_sensitive(True)
        self.actiongroup.get_action("CopyGame").set_sensitive(True)
        self.actiongroup.get_action("PasteGame").set_sensitive(True)
        self.actiongroup.get_action("EditPosition").set_sensitive(True)

        self.gobutton.set_sensitive(True)
        self.stopbutton.set_sensitive(False)

        if mode == "editmode":
            # if edit mode disable all options menu
            self.actiongroup.get_action("Options").set_sensitive(True)

    def enable_go_button(self):
        self.gobutton.set_sensitive(True)

    def disable_go_button(self):
        self.gobutton.set_sensitive(False)

    def disable_stop_button(self):
        self.stopbutton.set_sensitive(False)

    def enable_stop_button(self):
        self.stopbutton.set_sensitive(True)

    def promote_popup(self):

        dialog = Gtk.Dialog(
            _("Promotion"),
            None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (_("Yes"), Gtk.ResponseType.YES,
             _("No"), Gtk.ResponseType.NO,
             _("Cancel"), Gtk.ResponseType.CANCEL))

        dialog.vbox.pack_start(Gtk.Label("\n" + _("Promote piece?") + "\n"), True, True, 0)

        dialog.show_all()

        response = dialog.run()
        dialog.destroy()

        return response

    def update_toolbar(self, player):
        self.engines_lblw.set_markup("<b>" + player[WHITE][:25] + " </b>")
        self.engines_lblb.set_markup("<b>" + player[BLACK][:25] + " </b>")

    #
    # Update the clocks on the display
    # These countdown the time while the player is thinking
    #
    def set_toolbar_time_control(self, txt, side_to_move):
        if side_to_move is None:
            return
        GLib.idle_add(self.tc_lbl[side_to_move].set_text, txt)

    def info_box(self, msg):
        dialog = Gtk.MessageDialog(
            self.window,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            None)

        # markup = "<b>" + msg + "</b>"
        markup = msg
        dialog.set_markup(markup)
        dialog.set_title(_("Info"))

        # some secondary text
        markup = msg

        # dialog.format_secondary_markup(markup)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def ok_cancel_box(self, msg):
        dialog = Gtk.MessageDialog(
            None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK_CANCEL,
            None)

        # markup = "<b>" + msg + "</b>"
        markup = msg
        dialog.set_markup(markup)
        dialog.set_title(_("Ok/Cancel"))

        # some secondary text
        markup = msg

        # dialog.format_secondary_markup(markup)

        dialog.show_all()
        resp = dialog.run()
        dialog.destroy()

        return resp

    def set_side_to_move(self, stm):
        self.side_to_move[stm].show()
        self.side_to_move[stm ^ 1].hide()

    # set the base window size at startup
    def set_window_size(self):
        if self.screen_width > 918 and self.screen_height > 724:
            w = 918
            h = 724
        elif self.screen_width > 658 and self.screen_height > 523:
            w = 658
            h = 523
        else:
            w = 511
            h = 406
        #w = 300
        #h = 300
        #self.window.set_default_size(w, h)
        self.window.resize(w, h)

    def set_colours(self, bg_colour, komadai_colour, square_colour,
                    text_colour, border_colour, grid_colour):
        if gv.verbose:
            print("in gui set_colours with these parms:")
            print("  bg_colour=", bg_colour)
            print("  komadai_colour=", komadai_colour)
            print("  square_colour=", square_colour)
            print("  text_colour=", text_colour)
            # print "  piece_fill_colour=", piece_fill_colour
            # print "  piece_outline_colour=", piece_outline_colour
            # print "  piece_kanji_colour=", piece_kanji_colour
            print("  border_colour=", border_colour)
            print("  grid_colour=", grid_colour)

        self.get_window().modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(bg_colour))
        eb_2 = self.builder.get_object("eb_2")
        eb_2.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse(bg_colour)) #modif 17.1.17
        #self.komadaiw_eb.modify_bg(
        #    Gtk.StateType.NORMAL, Gdk.color_parse(komadai_colour))
        #self.komadaib_eb.modify_bg(
        #    Gtk.StateType.NORMAL, Gdk.color_parse(komadai_colour))
        self.komadaiw_eb.queue_draw()
        self.komadaib_eb.queue_draw()

        # square/komadai square colours are set in board.py in
        # set_image_cairo_komadai and set_image_cairo

        # border surrounds the board and contains the co-ordinates
        #self.border_eb.modify_bg(
        #    Gtk.StateType.NORMAL, Gdk.color_parse(border_colour))
        self.border_eb.queue_draw()

        self.grid_eb.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(grid_colour))

        gv.board.refresh_screen()

    def build_edit_popup(self):
        self.edit_mode = False

        popup_items = ["Separator",
                       _("Empty"),
                       _("Pawn"),
                       _("Bishop"),
                       _("Rook"),
                       _("Lance"),
                       _("Knight"),
                       _("Silver"),
                       _("Gold"),
                       _("King"),
                       "Separator",
                       _("+Pawn"),
                       _("+Bishop"),
                       _("+Rook"),
                       _("+Lance"),
                       _("+Knight"),
                       _("+Silver"),
                       "Separator",
                       _("Black to Move"),
                       _("White to Move"),
                       "Separator",
                       _("Clear Board"),
                       "Separator",
                       _("Cancel"),
                       _("End")]

        # set up menu for black
        self.bmenu = Gtk.Menu()
        menuitem = Gtk.MenuItem(_("Black"))
        menuitem.set_sensitive(False)
        self.bmenu.append(menuitem)
        # self.bmenu.append(Gtk.SeparatorMenuItem())
        for item_name in popup_items:
            if item_name == "Separator":
                self.bmenu.append(Gtk.SeparatorMenuItem())
                continue
            menuitem = Gtk.MenuItem(item_name)
            self.bmenu.append(menuitem)
            menuitem.connect("activate", self.edit_popup_callback, BLACK)

        # set up menu for white
        self.wmenu = Gtk.Menu()
        menuitem = Gtk.MenuItem(_("White"))
        menuitem.set_sensitive(False)
        self.wmenu.append(menuitem)
        # self.wmenu.append(Gtk.SeparatorMenuItem())
        for item_name in popup_items:
            if item_name == "Separator":
                self.wmenu.append(Gtk.SeparatorMenuItem())
                continue
            menuitem = Gtk.MenuItem(item_name)
            self.wmenu.append(menuitem)
            menuitem.connect("activate", self.edit_popup_callback, WHITE)

    # called when the user clicks on an item in the popup menu when editing
    # the board
    def edit_popup_callback(self, menuitem, colour):

        try:
            piece_name = menuitem.get_label()
        except AttributeError as ae:
            self.info_box(
                "Unable to edit board - you need a newer version of pygtk"
                "(version 2.16 or above)")
            return

        if piece_name == _("Clear Board"):
            gv.board.clear_board()
            return

        if piece_name == _("Black to Move"):
            gv.gshogi.set_side_to_move(BLACK)
            self.set_side_to_move(BLACK)   # update ind in gui
            return

        if piece_name == _("White to Move"):
            gv.gshogi.set_side_to_move(WHITE)
            self.set_side_to_move(WHITE)   # update ind in gui
            return

        if piece_name == _("Cancel"):
            self.edit_mode = False
            gv.gshogi.set_side_to_move(self.orig_stm)
            self.set_side_to_move(self.orig_stm)
            gv.board.update()            # restore board to its pre-edit state
            self.enable_menu_items(mode="editmode")
            return

        if piece_name == _("End"):
            self.end_edit()
            return

        # pieces contains the list of possible pieces in self.board_position
        # pieces = [
        #    " -", " p", " l", " n", " s", " g", " b", " r", " k", "+p", "+l",
        #    "+n", "+s", "+b", "+r", " P", " L", " N", " S", " G", " B", " R",
        #    " K", "+P", "+L", "+N", "+S", "+B", "+R"]

        piece_dict = {
            _("Empty"): " -", _("Pawn"): " p", _("Lance"): " l", _("Knight"): " n",
            _("Silver"): " s", _("Gold"): " g", _("Bishop"): " b", _("Rook"): " r",
            _("King"): " k", _("+Pawn"): "+p", _("+Lance"): "+l", _("+Knight"): "+n",
            _("+Silver"): "+s", _("+Bishop"): "+b", _("+Rook"): "+r"}

        piece = piece_dict[piece_name]
        if colour == WHITE:
            piece = piece.upper()
        # add piece to main board
        gv.board.set_piece_at_square(self.ed_x, self.ed_y, piece)

    # save position and exit edit mode
    def end_edit(self):
        self.edit_mode = False
        sfen = gv.board.get_sfen()
        load_save_ref = load_save.get_ref()
        load_save_ref.init_game(sfen)      # update board to reflect edit
        self.enable_menu_items(mode="editmode")

    def enable_edit_mode(self, action):
        # if already in edit mode then save edit position and exit edit mode
        if self.edit_mode:
            self.end_edit()
            return
        self.edit_mode = True
        self.orig_stm = gv.gshogi.get_side_to_move()
        self.set_status_bar_msg("Edit Mode")
        self.disable_menu_items(mode="editmode")
        gv.board.set_komadai_for_edit()

    def get_edit_mode(self):
        return self.edit_mode

    # called from gshogi.py when square clicked to popup the menu when
    # in edit board mode.
    def show_edit_popup(self, event, x, y):
        self.ed_x = x
        self.ed_y = y
        if event.button == 1:
            # left mouse button - display popup menu for black
            self.bmenu.popup(None, None, None, None, event.button, event.time)
            self.bmenu.show_all()
        elif event.button == 3:
            # right mouse button - display popup menu for white
            self.wmenu.popup(None, None, None, None, event.button, event.time)
            self.wmenu.show_all()

    # Fill in the colour or texture of the border that surrounds the board
    # and add co-ordinates
    def draw_komadai(self, widget, cr):
        a = widget.get_allocation()
        gv.set_board_colours.set_komadai_colour(cr, a)

    # Fill in the colour or texture of the border that surrounds the board
    # and add co-ordinates
    def draw_border(self, widget, cr):
        a = widget.get_allocation()
        gv.set_board_colours.set_border_colour(cr, a)
        if not self.show_coords:
            return

        cr = widget.get_window().cairo_create()

        # cr.set_source_rgb(0.0, 0.0, 0.0)  # black
        col = gv.set_board_colours.get_text_colour()
        r = col[1:3]
        g = col[3:5]
        b = col[5:7]
        r_int = int(r, 16)
        g_int = int(g, 16)
        b_int = int(b, 16)
        cr.set_source_rgb(
            float(r_int) / 255, float(g_int) / 255, float(b_int) / 255)

        cr.select_font_face(
            "Monospace", cairo.FONT_SLANT_OBLIQUE, cairo.FONT_WEIGHT_NORMAL)

        tb_x = self.boardgrid.get_allocation().x
        tb_y = self.boardgrid.get_allocation().y
        tb_width = self.boardgrid.get_allocation().width
        tb_height = self.boardgrid.get_allocation().height

        sq_size = int(tb_width / 9)

        if sq_size > 75:
            font_size = 11
        elif sq_size > 56:
            font_size = 10
        elif sq_size > 40:
            font_size = 9
        elif sq_size > 30:
            font_size = 8
        else:
            font_size = 7

        cr.set_font_size(font_size)

        # xpos = event.area.x + (event.area.width - tb_width) / 2 + sq_size / 2
        #xpos = widget.get_allocation().x + (
        #    widget.get_allocation().width - tb_width) / 2 + sq_size / 2
        xpos = int((widget.get_allocation().width - tb_width) / 2) + int(sq_size / 2)
        # ypos = event.area.y + 14
        # ypos = widget.get_allocation().y + 14
        ypos = 14
        # show co-ordinate numbers above the board
        for num in range(1, 10):
            cr.move_to(xpos, ypos)
            cr.show_text(str(10 - num))
            xpos = xpos + sq_size

        # show co-ordinate letters to right of board
        # xpos = event.area.x + event.area.width - 14
        # xpos = widget.get_allocation().x = widget.get_allocation().width -14
        xpos = widget.get_allocation().width - 14
        # ypos = event.area.y + (
        #   event.area.height - tb_height) / 2 + sq_size / 2
        # ypos = widget.get_allocation().y + (
        #   widget.get_allocation().height - tb_height) / 2 + sq_size / 2
        ypos = int((widget.get_allocation().height - tb_height) / 2) + int(sq_size / 2)
        let = "abcdefghi"
        for num in range(1, 10):
            cr.move_to(xpos, ypos)
            cr.show_text(let[num - 1])
            ypos = ypos + sq_size
        a=1
        #for debugging purposes

    def preferences(self, action):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(gv.domain)
        self.builder.add_from_file(self.glade_file_preferences)
        self.builder.connect_signals(self)
        dialog = self.builder.get_object("preferences")
        dialog.set_transient_for(self.window)
        # show co-ords
        coords_checkbutton = self.builder.get_object("coords_checkbutton")
        coords_checkbutton.set_active(self.show_coords)

        # highlight moves
        highlight_moves_checkbutton = self.builder.get_object(
            "highlight_checkbutton")

        highlight_moves_checkbutton.set_active(self.highlight_moves)

        response = dialog.run()

        resp_cancel = 1
        resp_ok = 2
        if response == resp_ok:
            self.show_coords = coords_checkbutton.get_active()
            self.highlight_moves = highlight_moves_checkbutton.get_active()
            # rect = self.border_eb.get_allocation()
            # gv.board.update()
            self.border_eb.queue_draw()
        dialog.destroy()

    def set_show_coords(self, coords):
        self.show_coords = coords

    def set_highlight_moves(self, highlight_moves):
        self.highlight_moves = highlight_moves

    def get_highlight_moves(self):
        return self.highlight_moves

    def get_show_coords(self):
        return self.show_coords

    def get_window(self):
        return self.window
