import gi, logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

import re
import datetime

class TransactionSearchPopover(Gtk.Popover):

    #__gsignals__ = {
#        'search-settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    #}

    def __init__(self, model):
        super().__init__()

        self.model = model
        self.filter_set = None

        self.date_selector_from = Gtk.Calendar()
        self.date_selector_to = Gtk.Calendar()

        for cal in [self.date_selector_from, self.date_selector_to]:
            cal.connect('day-selected', lambda w: self.on_search_changed())
            cal.set_display_options(
                    Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES
                |   Gtk.CalendarDisplayOptions.SHOW_HEADING
                |   Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS)
            cal.set_property('width-request', 240)

        self.select_date_stack = Gtk.Stack()
        self.select_date_button = Gtk.Button(label='Select Dates...', tooltip_text=_('Select a date'), hexpand=True)
        self.select_date_button.connect('clicked', self.select_date_clicked)
        self.select_date_entry = Gtk.Entry(secondary_icon_name='x-office-calendar-symbolic',
                                           secondary_icon_tooltip_text=_('Show a calendar to select the date'))
        self.clear_date_button = Gtk.Button(image=Gtk.Image.new_from_icon_name("edit-clear-symbolic" , Gtk.IconSize.MENU))
        self.clear_date_button.connect('clicked', self.clear_date_clicked)

        btn_box = Gtk.ButtonBox(layout_style=Gtk.ButtonBoxStyle.EXPAND)
        btn_box.set_homogeneous(False)
        btn_box.pack_start(self.select_date_button, True, True, 0)
        btn_box.pack_start(self.clear_date_button, False, True, 0)

        self.select_date_stack.add_named(btn_box, 'date-select')
        self.select_date_stack.add_named(self.select_date_entry, 'date-entry')

        self.select_date_revealer = Gtk.Revealer(transition_type=Gtk.StackTransitionType.SLIDE_DOWN)
        revealer_box = Gtk.Grid(row_spacing=9, column_spacing=18)
        revealer_box.attach(Gtk.Label(label="Since...", xalign=0), 0, 0, 1, 1)
        revealer_box.attach(self.date_selector_from, 0, 1, 1, 1)
        revealer_box.attach(Gtk.Label(label="Until...", xalign=0), 0, 2, 1, 1)
        revealer_box.attach(self.date_selector_to, 0, 3, 1, 1)
        self.select_date_revealer.add(revealer_box)

        grid = Gtk.Grid(row_spacing=9, column_spacing=18, margin=18)
        grid.attach(Gtk.CheckButton(label='Girokonto'), 0, 0, 1, 1)
        grid.attach(Gtk.CheckButton(label='Gemeinschaftkonto'), 0, 1, 1, 1)
        grid.attach(Gtk.CheckButton(label='Sparkonto'), 0, 2, 1, 1)
        grid.attach(Gtk.Separator(), 0, 3, 1, 1)
        grid.attach(Gtk.Label(label="When", xalign=0), 0, 4, 1, 1)
        grid.attach(self.select_date_stack, 0, 5, 1, 1)
        grid.attach(self.select_date_revealer, 0, 6, 1, 1)
        grid.show_all()

        self.add(grid)

    def select_date_clicked(self, widget):
        self.select_date_stack.set_visible_child_name('date-entry')
        self.select_date_revealer.set_reveal_child(True)

    def clear_date_clicked(self, widget):
        self.select_date_stack.set_visible_child_name('date-select')
        self.clear_date_button.set_visible(False)
