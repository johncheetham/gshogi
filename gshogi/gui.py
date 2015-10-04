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
from gi.repository import GdkPixbuf
from gi.repository import Pango
import os
# import inspect
import cairo

import engine_debug
import engine_output
import move_list
import set_board_colours
import drag_and_drop
import load_save
import utils
import gamelist
from constants import WHITE, BLACK, NAME, VERSION, TARGET_TYPE_TEXT
import gv


class Gui:

    gui_ref = None

    def __init__(self):
        if Gui.gui_ref is not None:
            raise RuntimeError("Attempt to create second gui instance")
        Gui.gui_ref = self
        self.highlighted = []  # list of highlighted squares

    def build_gui(self):

        self.gobactive = False
        self.engine_debug = engine_debug.get_ref()
        self.engine_output = engine_output.get_ref()
        self.move_list = move_list.get_ref()
        self.gamelist = gamelist.get_ref()
        self.set_board_colours = set_board_colours.get_ref()
        self.drag_and_drop = drag_and_drop.get_ref()
        self.enable_dnd = True
        self.load_save = load_save.get_ref()
        self.show_coords = True
        self.highlight_moves = True

        # Board Colours
        (self.board_bg_colour, self.board_komadai_colour,
         self.board_square_colour, self.board_text_colour,
         self.piece_fill_colour, self.piece_outline_colour,
         self.piece_kanji_colour, self.border_colour,
         self.grid_colour) = (
            self.set_board_colours.get_colours())

        # Create Main Window
        glade_dir = gv.gshogi.get_glade_dir()
        self.glade_file = os.path.join(glade_dir, "main_window.glade")
        self.glade_file_preferences = os.path.join(
            glade_dir, "preferences.glade")
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.glade_file)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("main_window")

        # self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_title(NAME + " " + VERSION)
        self.window.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.board_bg_colour))

        # 1 eventbox per board square
        self.eb = [[Gtk.EventBox() for x in range(9)] for x in range(9)]

        # 1 eventbox per white komadai board square
        self.web = [Gtk.EventBox() for x in range(7)]
        self.wcap_label = [Gtk.Label() for x in range(7)]

        # 1 eventbox per black komadai board square
        self.beb = [Gtk.EventBox() for x in range(7)]
        self.bcap_label = [Gtk.Label() for x in range(7)]

        # Set a handler for delete_event that immediately exits GTK.
        self.window.connect("delete_event", gv.gshogi.delete_event)

        # connect to configure event so pieces can be resized when user
        # resizes the window
        self.window.connect("configure_event", self.configure_event)

        main_vbox = self.builder.get_object("main_vbox")
        # main_vbox = Gtk.VBox(False, 0)
        # self.window.add(main_vbox)
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
            "promotemode", None, "_Ask Before Promoting", None, None,
            self.promote_mode)])
        # ta_action_group.add_toggle_actions(
        #   [("enableDND", None, "_Enable Drag and Drop", None, None,
        #                                       self.enable_drag_and_drop)])
        self.ta_action_group = ta_action_group

        # Create actions
        actiongroup.add_actions([
            # NewGame and the handicap names are used in gshogi.py NewGame
            # routine. don't change them.
            ("NewGame", Gtk.STOCK_NEW, "_New Game", None, "New Game",
             gv.gshogi.new_game_cb),
            ("LanceHandicap", None, "_Lance", None,
             "Lance Handicap", gv.gshogi.new_game_cb),
            ("BishopHandicap", None, "_Bishop", None,
             "Bishop Handicap", gv.gshogi.new_game_cb),
            ("RookHandicap", None, "_Rook", None,
             "Rook Handicap", gv.gshogi.new_game_cb),
            ("RookandLanceHandicap", None, "_Rook and Lance", None,
             "Rook and Lance Handicap", gv.gshogi.new_game_cb),
            ("TwoPieceHandicap", None, "_2 Pieces", None,
             "Two Piece Handicap", gv.gshogi.new_game_cb),
            ("FourPieceHandicap", None, "_4 Pieces", None,
             "Four Piece Handicap", gv.gshogi.new_game_cb),
            ("SixPieceHandicap", None, "_6 Pieces", None,
             "Six Piece Handicap", gv.gshogi.new_game_cb),
            ("EightPieceHandicap", None, "_8 Pieces", None,
             "Eight Piece Handicap", gv.gshogi.new_game_cb),
            ("TenPieceHandicap", None, "_10 Pieces", None,
             "Ten Piece Handicap", gv.gshogi.new_game_cb),
            ("NewHandicapGame", None, "_New Handicap Game"),
            #
            ("Quit", Gtk.STOCK_QUIT, "_Quit", None,
             "Quit the Program", gv.gshogi.quit_game),
            ("LoadGame", Gtk.STOCK_OPEN, "_Load Game", None,
             "Load Game", self.load_save.load_game),
            ("SaveGame", Gtk.STOCK_SAVE, "_Save Game", None,
             "Save Game", self.load_save.save_game),
            ("File", None, "_File"),
            ("Edit", None, "_Edit"),
            ("Undo", Gtk.STOCK_UNDO, "_Undo Move", "<Control>U",
             "Undo Move", gv.gshogi.undo_single_move),
            ("Redo", Gtk.STOCK_REDO, "_Redo Move", "<Control>R",
             "Redo Move", gv.gshogi.redo_single_move),
            ("MoveNow", None, "_Move Now", "<Control>M",
             "Move Now", gv.gshogi.move_now),
            ("SetBoardColours", None, "_Set Board Colours", None,
             "Set Board Colours", self.set_board_colours.show_dialog),
            ("SetPieces", None, "_Set Pieces", None,
             "Set Pieces", self.set_board_colours.show_pieces_dialog),
            ("TimeControl", None, "_Time Control", None,
             "Time Control", gv.tc.time_control),
            # ConfigureEngine1 - this name is used in engine_manager.
            # don't change it.
            ("ConfigureEngine1", None, "_Configure Engine 1", None,
             "Configure Engine 1", gv.engine_manager.configure_engine),
            ("ConfigureEngine2", None, "_Configure Engine 2", None,
             "Configure Engine 2", gv.engine_manager.configure_engine),
            ("Players", None, "_Players", None,
             "Players", gv.gshogi.set_players),
            ("Engines", None, "_Engines", None,
             "Engines", gv.engine_manager.engines),
            ("CommonEngineSettings", None, "_Common Engine Settings", None,
             "Common Engine Settings", gv.engine_manager.common_settings),
            ("MoveList", None, "_Move List", None,
             "Move List", self.move_list.show_movelist_window),
            ("GameList", None, "_Game List", None,
             "Game List", self.gamelist.show_gamelist_window_cb),
            ("EngineOutput", None, "_Engine Output", None,
             "Engine Output", self.engine_output.show_engine_output_window),
            ("EngineDebug", None, "_Engine Debug", None,
             "Engine Debug", self.engine_debug.show_debug_window),
            ("Options", None, "_Options"),
            ("View", None, "_View"),
            ("About", Gtk.STOCK_ABOUT, "_About", None,
             "Show About Box", self.about_box),
            ("Help", None, "_Help"),
            ("CopyPosition", None, "_Copy Position", None,
             "Copy Position", utils.copy_SFEN_to_clipboard),
            ("PastePosition", None, "_Paste Position", None,
             "Paste Position", utils.paste_clipboard_to_SFEN),
            ("CopyGame", None, "_Copy Game", None,
             "Copy Game", utils.copy_game_to_clipboard),
            ("PasteGame", None, "_Paste Game", None,
             "Paste Game", utils.paste_game_from_clipboard),
            ("EditPosition", None, "_Edit Position", None,
             "Edit Position", self.enable_edit_mode),
            ("Preferences", None, "_Preferences", None,
             "Preferences", self.preferences),
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
        eb_1.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#EDECEB"))

        # Create a MenuBar
        menubar = uimanager.get_widget("/MenuBar")
        vbox2.pack_start(menubar, False, True, 0)

        # create a toolbar
        toolbar = Gtk.Toolbar()
        vbox2.pack_start(toolbar, False, True, 0)

        # populate toolbar
        toolitem = Gtk.ToolItem()

        # 2 rows, 4 columns, not homogeneous
        tb = Gtk.Table(2, 5, False)

        # Gtk.ShadowType.NONE, SHADOW_IN, SHADOW_OUT, SHADOW_ETCHED_IN,
        # SHADOW_ETCHED_OUT

        self.side_to_move = [
            Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.ETCHED_IN),
            Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.ETCHED_IN)]
        self.side_to_move[BLACK].set_alignment(0.5, 0.4)
        self.side_to_move[WHITE].set_alignment(0.5, 0.4)

        tb.attach(self.side_to_move[WHITE], 0, 1, 0, 1)
        tb.attach(self.side_to_move[BLACK], 0, 1, 1, 2)

        lw = Gtk.Label(label="White: ")
        lb = Gtk.Label(label="Black: ")
        lw.set_alignment(0, 0.5)
        lb.set_alignment(0, 0.5)
        tb.attach(lw, 1, 2, 0, 1)
        tb.attach(lb, 1, 2, 1, 2)

        self.engines_lblw = Gtk.Label(label="gshogi")
        self.engines_lblw.set_use_markup(True)
        self.engines_lblw.set_alignment(0, 0.5)

        self.engines_lblb = Gtk.Label(label="human")
        self.engines_lblb.set_use_markup(True)
        self.engines_lblb.set_alignment(0, 0.5)

        tb.attach(self.engines_lblw, 2, 3, 0, 1)
        tb.attach(self.engines_lblb, 2, 3, 1, 2)

        # time control
        self.tc_lbl = [
            Gtk.Label(label="00:45:00 00/10"),
            Gtk.Label(label="00:45:00 00/10")]
        self.tc_lbl[BLACK].set_alignment(0, 0.5)
        self.tc_lbl[WHITE].set_alignment(0, 0.5)

        tb.attach(self.tc_lbl[WHITE], 3, 4, 0, 1)
        tb.attach(self.tc_lbl[BLACK], 3, 4, 1, 2)

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

        # set_tooltip_text needs PyGTK 2.12 and above.
        try:
            self.gobutton.set_tooltip_text("go")
            self.stopbutton.set_tooltip_text("stop")
        except AttributeError, ae:
            pass

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

        ###
        main_hbox = self.builder.get_object("main_hbox")
        # main_hbox = Gtk.HBox(False, 0)

        # Create a 7x1 table for pieces captured by the white side
        self.setup_white_komadai(main_hbox)

        # Create a 9x9 table for the main board
        self.table = Gtk.Table(9, 9, True)
        self.table.set_border_width(1)
        eb2 = Gtk.EventBox()

        eb2.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))
        eb2.add(self.table)
        eb = Gtk.EventBox()
        eb.add(eb2)
        eb.show()
        eb.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.board_square_colour))

        aspect_frame = Gtk.AspectFrame(label=None, xalign=0.5, yalign=0.5,
                                       ratio=1.0, obey_child=False)

        aspect_frame.add(eb)
        eb2.set_border_width(20)
        self.grid_eb = eb2
        # self.grid_eb.connect("draw", self.configure_event)
        main_hbox.pack_start(aspect_frame, True, True, 0)
        aspect_frame.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))

        eb.connect_after("draw", self.draw_coords)
        self.border_eb = eb

        # Create a 7x1 table for pieces captured by the black side
        self.setup_black_komadai(main_hbox)

        # status bar
        self.status_bar = self.builder.get_object("status_bar")

        # set status bar bg color
        # Use an event box and set its background colour.
        # This was needed on Fedora 19 to set the statusbar bg colour.
        # Otherwise it uses the window bg colour which is not
        # correct. This was not needed on F17.
        eb_2 = self.builder.get_object("eb_2")
        eb_2.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#EDECEB"))
        # self.status_bar = Gtk.Statusbar()
        # main_vbox.pack_start(self.status_bar, False, False, 0)
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
        mask = Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE
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
        # self.window.set_geometry_hints(self.window, geometry, mask)
        # self.window.set_geometry_hints(
        #   self.window, min_width=378, min_height=378, max_width=-1,
        #   max_height=-1, base_width=-1, base_height=-1, width_inc=-1,
        #   height_inc=-1, min_aspect=-1.0, max_aspect=-1.0)

        self.build_edit_popup()

    def init_board_square(self, image, x, y):
        event_box = Gtk.EventBox()
        event_box.add(image)
        self.table.attach(event_box, x, x+1, y, y+1)
        event_box.show()
        event_box.modify_bg(Gtk.StateType.NORMAL,
                            Gdk.color_parse(self.board_square_colour))
        event_box.set_border_width(1)
        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        data = (x, y)
        event_box.connect("button_press_event", gv.gshogi.square_clicked, data)
        image.show()

        # set up square as a source square for sending out drag data
        # from a drag & drop action
        # self.targets =
        #   [( "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT ) ]

        event_box.connect("drag_data_get", self.drag_and_drop.sendCallback)
        event_box.connect_after(
            "drag_begin", self.drag_and_drop.drag_begin, (x, y))
        # event_box.emit_stop_by_name("drag_begin")
        event_box.connect_after("drag_end", self.drag_and_drop.drag_end)
        # event_box.drag_source_set(
        #   Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        # set up square as a destination square to receive drag data
        # from a drag & drop action

        event_box.connect(
            "drag_data_received", self.drag_and_drop.receiveCallback, (x, y))
        # event_box.drag_dest_set(
        #     Gtk.DestDefaults.MOTION |
        #     Gtk.DestDefaults.HIGHLIGHT |
        #     Gtk.DestDefaults.DROP, self.targets, Gdk.DragAction.COPY)
        self.eb[x][y] = event_box

    def dnd_set_source_square(self, x, y):
        # self.targets = [
        #   ( "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT ) ]
        self.targets = [
            Gtk.TargetEntry.new(
                "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]
        self.eb[x][y].drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

    def dnd_unset_source_square(self, x, y):
        self.eb[x][y].drag_source_unset()

    def dnd_set_dest_square(self, x, y):
        # self.targets =
        #   [( "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT ) ]
        self.targets = [
            Gtk.TargetEntry.new(
                "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]
        self.eb[x][y].drag_dest_set(
            Gtk.DestDefaults.MOTION |
            Gtk.DestDefaults.HIGHLIGHT |
            Gtk.DestDefaults.DROP,
            self.targets, Gdk.DragAction.COPY)

    def dnd_unset_dest_square(self, x, y):
        self.eb[x][y].drag_dest_unset()

    def dnd_unset_source_bcap_square(self, y):
        self.beb[y].drag_source_unset()

    def dnd_unset_source_wcap_square(self, y):
        self.web[y].drag_source_unset()

    def dnd_set_source_bcap_square(self, y):
        # self.targets = [
        #    "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT ) ]
        self.targets = [
            Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP,
                                TARGET_TYPE_TEXT)]
        self.beb[y].drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

    def dnd_set_source_wcap_square(self, y):
        # self.targets = [
        #   ( "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT ) ]
        self.targets = [
            Gtk.TargetEntry.new(
                "text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]
        self.web[y].drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

    # set all squares so they cannot be used for drag and drop
    def unset_all_drag_and_drop_squares(self):
        # main board
        for x in range(0, 9):
            for y in range(0, 9):
                self.dnd_unset_source_square(x, y)
                self.dnd_unset_dest_square(x, y)

        # komadai
        for y in range(0, 7):
            # set default to unset (no square can be dragged)
            self.dnd_unset_source_bcap_square(y)
            self.dnd_unset_source_wcap_square(y)

    #
    # Look at each board square and set it as a valid drag and drop
    # source square or target square if applicable
    #
    def apply_drag_and_drop_settings(self, player, stm):

        if gv.verbose:
            print "in apply_drag_and_drop_settings"

        # If drag and drop not enabled then exit
        # if not self.ta_action_group.get_action("enableDND").get_active():
        if not self.enable_dnd:
            self.unset_all_drag_and_drop_squares
            return

        for x in range(0, 9):
            for y in range(0, 9):
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
                    if gv.verbose:
                        print x, y, "is a valid source sq"
                    self.dnd_set_source_square(x, y)
                    self.dnd_unset_dest_square(x, y)
                else:
                    # valid target square for dnd
                    if gv.verbose:
                        print x, y, "is NOT a valid source sq"
                    self.dnd_unset_source_square(x, y)
                    self.dnd_set_dest_square(x, y)

        wcap = gv.board.get_capturedw()
        bcap = gv.board.get_capturedb()

        # komadai
        for y in range(0, 7):
            # set default to unset (no square can be dragged)
            self.dnd_unset_source_bcap_square(y)
            self.dnd_unset_source_wcap_square(y)
            if player != "Human":
                continue

            # player is human so allow a square to be dragged if it
            # contains a piece for his side
            if gv.board.get_cap_piece(y, stm) != "0":
                if stm == WHITE:
                    self.dnd_set_source_wcap_square(y)
                else:
                    self.dnd_set_source_bcap_square(y)

    #
    # set up the komadai for white. this is a column on the left of the board
    # to hold pieces captured by white
    #
    def setup_white_komadai(self, hbox):
        self.wcaptable = Gtk.Table(7, 1, True)

        eb2 = Gtk.EventBox()
        eb2.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#000000"))

        eb = Gtk.EventBox()
        eb.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.board_komadai_colour))
        eb.add(self.wcaptable)
        eb.show()
        self.komadaiw_eb = eb
        eb.set_border_width(3)
        eb2.add(eb)

        al = Gtk.Alignment.new(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        al.add(eb2)
        hbox.pack_start(al, True, True, 0)
        self.wcaptable.show()

    #
    # set up the komadai for black. this is a column on the right of the board
    # to hold pieces captured by black
    #
    def setup_black_komadai(self, hbox):
        self.bcaptable = Gtk.Table(7, 1, True)

        eb2 = Gtk.EventBox()
        eb2.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#000000"))

        eb = Gtk.EventBox()
        eb.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.board_komadai_colour))
        eb.add(self.bcaptable)
        eb.show()
        self.komadaib_eb = eb
        eb.set_border_width(3)
        eb2.add(eb)

        al = Gtk.Alignment.new(xalign=1.0, yalign=1.0, xscale=0.0, yscale=0.0)
        al.add(eb2)
        hbox.pack_start(al, True, True, 0)
        self.bcaptable.show()

    def init_wcap_square(self, image, y, label):

        hb = Gtk.HBox(False, 0)
        hb.show()

        label.modify_fg(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.board_text_colour))

        fontdesc = Pango.FontDescription("Monospace 15")
        label.modify_font(fontdesc)

        label.show()
        hb.pack_start(label, True, True, 0)
        self.wcap_label[y] = label

        event_box = Gtk.EventBox()
        event_box.add(image)

        hb.pack_start(event_box, True, True, 0)
        x = 0
        self.wcaptable.attach(hb, x, x+1, y, y+1)

        hb.show()

        event_box.show()
        event_box.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.board_komadai_colour))
        event_box.set_border_width(5)

        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        data = (x, y, WHITE)
        event_box.connect(
            "button_press_event", gv.gshogi.cap_square_clicked, data)
        image.show()
        self.web[y] = event_box

        event_box.set_name("wcap_eb")

        self.targets = [
            ("text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]

        event_box.connect("drag_data_get", self.drag_and_drop.sendCallback)
        event_box.connect_after(
            "drag_begin", self.drag_and_drop.drag_begin, (x, y))
        event_box.connect_after("drag_end", self.drag_and_drop.drag_end)

    def init_bcap_square(self, image, y, label):

        hb = Gtk.HBox(False, 0)
        hb.show()

        label.modify_fg(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.board_text_colour))
        fontdesc = Pango.FontDescription("Monospace 15")
        label.modify_font(fontdesc)

        label.show()
        hb.pack_end(label, True, True, 0)
        self.bcap_label[y] = label

        event_box = Gtk.EventBox()
        event_box.add(image)

        hb.pack_end(event_box, True, True, 0)

        x = 0
        self.bcaptable.attach(hb, x, x+1, y, y+1)

        hb.show()

        event_box.show()
        event_box.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.board_komadai_colour))
        event_box.set_border_width(5)

        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        data = (x, y, BLACK)
        event_box.connect(
            "button_press_event", gv.gshogi.cap_square_clicked, data)

        image.show()
        self.beb[y] = event_box

        event_box.set_name("bcap_eb")

        self.targets = [
            ("text/plain", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_TEXT)]

        event_box.connect("drag_data_get", self.drag_and_drop.sendCallback)
        event_box.connect_after(
            "drag_begin", self.drag_and_drop.drag_begin, (x, y))
        event_box.connect_after("drag_end", self.drag_and_drop.drag_end)

    # return the size of a square on the board
    def get_square_size(self, w=None, h=None):

        # work out the board square size from the size of the main window

        # allocation contains:
        #   x, y, width, height
        if w is not None and h is not None:
            window_width = w
            window_height = h
        else:
            window_width = self.window.get_allocation().width
            window_height = self.window.get_allocation().height

        sq_width = window_width / 15
        sq_height = window_height / 15

        # sq_size contains the width of the board square
        # the height will be the same as the width
        if sq_width < sq_height:
            sq_size = sq_width
        else:
            sq_size = sq_height

        # print "new sq wdth=",sq_width
        # print "new sq hght=",sq_height
        # print "new sq sz=",sq_size

        # Now apply an adjustment to the board square size
        if sq_size < 27:
            sq_size = sq_size * 0.8
        elif sq_size < 30:
            sq_size = sq_size * 1.0
        elif sq_size < 35:
            sq_size = sq_size * 1.0
        elif sq_size < 40:
            sq_size = sq_size * 1.1
        elif sq_size < 50:
            sq_size = sq_size * 1.2
        else:
            sq_size = sq_size * 1.3

        # print "new sq sz2=",sq_size
        # print

        return sq_size

    # about box
    def about_box(self, widget):
        about = Gtk.AboutDialog()
        #
        # set_program_name method is available in PyGTK 2.12 and above
        #
        try:
            about.set_program_name(NAME)
        except AttributeError:
            pass
        about.set_version(VERSION)
        about.set_copyright(u"Copyright \u00A9 2010-2012 John Cheetham")
        about.set_comments(
            "gshogi is a program to play shogi (Japanese Chess).")
        about.set_authors(["John Cheetham"])
        about.set_website(
            "http://www.johncheetham.com/projects/gshogi/index.shtml")
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
        self.status_bar.push(self.context_id, msg)

    # ask before promoting
    def promote_mode(self, w):
        if w.get_active():
            gv.gshogi.set_promotion_mode(True)
        else:
            gv.gshogi.set_promotion_mode(False)

    def enable_drag_and_drop(self, w):
        if not w.get_active():
            self.unset_all_drag_and_drop_squares()

    # def get_dnd(self):
    #    return self.ta_action_group.get_action("enableDND").get_active()

    # def set_dnd(self):
    #    self.ta_action_group.get_action("enableDND").set_active(True)

    # user is resizing the window
    # call board.refresh_screen to resize the pieces
    #
    def configure_event(self, widget, event):
        self.resize_pieces(event.width, event.height)

    def resize_pieces(self, w, h):
        gv.board.refresh_screen(w, h)
        return False

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
            "Promotion",
            None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("Yes", Gtk.ResponseType.YES,
             "No", Gtk.ResponseType.NO,
             "Cancel", Gtk.ResponseType.CANCEL))

        dialog.vbox.pack_start(Gtk.Label("\nPromote piece?\n", True, True, 0))

        dialog.show_all()

        response = dialog.run()
        dialog.destroy()

        return response

    def update_toolbar(self, player):
        self.engines_lblw.set_markup("<b>" + player[WHITE] + " </b>")
        self.engines_lblb.set_markup("<b>" + player[BLACK] + " </b>")

    #
    # Update the clocks on the display
    # These countdown the time while the player is thinking
    #
    def set_toolbar_time_control(self, txt, side_to_move):
        if side_to_move is None:
            return
        self.tc_lbl[side_to_move].set_text(txt)

    def info_box(self, msg):
        dialog = Gtk.MessageDialog(
            None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            None)

        # markup = "<b>" + msg + "</b>"
        markup = msg
        dialog.set_markup(markup)
        dialog.set_title("Info")

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
        dialog.set_title("Ok/Cancel")

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
        screen = self.window.get_screen()
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        if screen_width > 918 and screen_height > 724:
            w = 918
            h = 724
        elif screen_width > 658 and screen_height > 523:
            w = 658
            h = 523
        else:
            w = 511
            h = 406

        self.window.resize(w, h)

    def set_colours(self, bg_colour, komadai_colour, square_colour,
                    text_colour, border_colour, grid_colour):
        # stack = inspect.stack()
        # for item in stack:
        #     print item
        # print "stack:",inspect.stack()
        if gv.verbose:
            print "in gui set_colours with these parms:"
            print "  bg_colour=", bg_colour
            print "  komadai_colour=", komadai_colour
            print "  square_colour=", square_colour
            print "  text_colour=", text_colour
            # print "  piece_fill_colour=", piece_fill_colour
            # print "  piece_outline_colour=", piece_outline_colour
            # print "  piece_kanji_colour=", piece_kanji_colour
            print "  border_colour=", border_colour
            print "  grid_colour=", grid_colour

        self.window.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(bg_colour))
        self.komadaiw_eb.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(komadai_colour))
        self.komadaib_eb.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(komadai_colour))

        for i in range(0, 7):
            self.web[i].modify_bg(
                Gtk.StateType.NORMAL, Gdk.color_parse(komadai_colour))
            self.beb[i].modify_bg(
                Gtk.StateType.NORMAL, Gdk.color_parse(komadai_colour))

            self.wcap_label[i].modify_fg(
                Gtk.StateType.NORMAL, Gdk.color_parse(text_colour))
            self.bcap_label[i].modify_fg(
                Gtk.StateType.NORMAL, Gdk.color_parse(text_colour))

        for i in range(0, 9):
            for j in range(0, 9):
                self.eb[i][j].modify_bg(
                    Gtk.StateType.NORMAL, Gdk.color_parse(square_colour))

        # border surrounds the board and contains the co-ordinates
        # self.border_eb.modify_bg(
        #   Gtk.StateType.NORMAL, Gdk.color_parse(square_colour))
        self.border_eb.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(border_colour))

        self.grid_eb.modify_bg(
            Gtk.StateType.NORMAL, Gdk.color_parse(grid_colour))

        # gv.pieces.change_piece_colours2(
        #   piece_fill_colour, piece_outline_colour, piece_kanji_colour)

        gv.board.refresh_screen()

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

    def hilite_squares(self, square_list):

        self.unhilite_squares()

        if not self.highlight_moves:
            return

        square_colour = self.set_board_colours.get_square_colour()

        # get r, g, b of square colour
        r = square_colour[1:3]
        g = square_colour[3:5]
        b = square_colour[5:7]

        # modify it a bit to get r, g, b of hilite colour
        r = self.addhex(r, 30)
        g = self.addhex(g, 30)
        b = self.addhex(b, 30)
        hilite_colour = "#" + r + g + b

        # square_list contains a list of squares to be highlighted
        for sq in square_list:
            # highlight the square
            x, y = sq
            self.eb[x][y].modify_bg(
                Gtk.StateType.NORMAL, Gdk.color_parse(hilite_colour))

            # add to list of highlighted squares
            self.highlighted.append(sq)

    # unhighlight existing highlighted squares
    def unhilite_squares(self):
        square_colour = self.set_board_colours.get_square_colour()
        # unhighlight existing highlighted squares
        for sq in self.highlighted:
            # unhighlight the square
            x, y = sq
            self.eb[x][y].modify_bg(
                Gtk.StateType.NORMAL, Gdk.color_parse(square_colour))
        self.highlighted = []

    def build_edit_popup(self):
        self.edit_mode = False

        popup_items = ["Separator",
                       "Empty",
                       "Pawn",
                       "Bishop",
                       "Rook",
                       "Lance",
                       "Knight",
                       "Silver",
                       "Gold",
                       "King",
                       "Separator",
                       "+Pawn",
                       "+Bishop",
                       "+Rook",
                       "+Lance",
                       "+Knight",
                       "+Silver",
                       "Separator",
                       "Black to Move",
                       "White to Move",
                       "Separator",
                       "Clear Board",
                       "Separator",
                       "Cancel",
                       "End"]

        # set up menu for black
        self.bmenu = Gtk.Menu()
        menuitem = Gtk.MenuItem("Black")
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
        menuitem = Gtk.MenuItem("White")
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
        except AttributeError, ae:
            self.info_box(
                "Unable to edit board - you need a newer version of pygtk"
                "(version 2.16 or above)")
            return

        if piece_name == "Clear Board":
            gv.board.clear_board()
            return

        if piece_name == "Black to Move":
            gv.gshogi.set_side_to_move(BLACK)
            self.set_side_to_move(BLACK)   # update ind in gui
            return

        if piece_name == "White to Move":
            gv.gshogi.set_side_to_move(WHITE)
            self.set_side_to_move(WHITE)   # update ind in gui
            return

        if piece_name == "Cancel":
            self.edit_mode = False
            gv.gshogi.set_side_to_move(self.orig_stm)
            self.set_side_to_move(self.orig_stm)
            gv.board.update()            # restore board to its pre-edit state
            self.enable_menu_items(mode="editmode")
            return

        if piece_name == "End":
            self.end_edit()
            return

        # pieces contains the list of possible pieces in self.board_position
        # pieces = [
        #    " -", " p", " l", " n", " s", " g", " b", " r", " k", "+p", "+l",
        #    "+n", "+s", "+b", "+r", " P", " L", " N", " S", " G", " B", " R",
        #    " K", "+P", "+L", "+N", "+S", "+B", "+R"]

        piece_dict = {
            "Empty": " -", "Pawn": " p", "Lance": " l", "Knight": " n",
            "Silver": " s", "Gold": " g", "Bishop": " b", "Rook": " r",
            "King": " k", "+Pawn": "+p", "+Lance": "+l", "+Knight": "+n",
            "+Silver": "+s", "+Bishop": "+b", "+Rook": "+r"}

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

    # need to connect this routine to the expose event of what the co-ords are
    # drawn on (i.e. the event box).
    def draw_coords(self, widget, context):

        if not self.show_coords:
            return

        cr = widget.get_window().cairo_create()

        # cr.set_source_rgb(0.0, 0.0, 0.0)  # black
        col = self.set_board_colours.get_text_colour()
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

        tb_x = self.table.get_allocation().x
        tb_y = self.table.get_allocation().y
        tb_width = self.table.get_allocation().width
        tb_height = self.table.get_allocation().height

        sq_size = tb_width / 9

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
        xpos = widget.get_allocation().x + (
            widget.get_allocation().width - tb_width) / 2 + sq_size / 2
        xpos = (widget.get_allocation().width - tb_width) / 2 + sq_size / 2
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
        ypos = (widget.get_allocation().height - tb_height) / 2 + sq_size / 2
        let = "abcdefghi"
        for num in range(1, 10):
            cr.move_to(xpos, ypos)
            cr.show_text(let[num - 1])
            ypos = ypos + sq_size

    def preferences(self, action):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.glade_file_preferences)
        self.builder.connect_signals(self)
        dialog = self.builder.get_object("preferences")

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
