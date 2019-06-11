import gi, logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

import re
import datetime

from .transaction_search_popover import TransactionSearchPopover

def calendar_date_to_date(gtk_calendar):
    year, month, day = gtk_calendar.get_date()
    return datetime.date(year, month + 1, day)

class TransactionSearchBar(Gtk.SearchBar):

    __gsignals__ = {
        'search-filter-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, model):
        super().__init__()

        self.model = model
        self.filter_set = None
        self.set_show_close_button(True)
        self.entry = Gtk.SearchEntry()
        self.entry.set_size_request(350, -1)
        self.connect_entry(self.entry)
        self.entry.connect('search-changed', lambda w: self.on_search_changed())
        #self.init_search_prop_popover()
        self.search_prop_popover = TransactionSearchPopover(self.model)

        btn_box = Gtk.ButtonBox(layout_style=Gtk.ButtonBoxStyle.EXPAND)
        btn_box.set_homogeneous(False)
        btn_box.pack_start(self.entry, True, True, 0)
        btn_box.pack_start(Gtk.MenuButton(popover=self.search_prop_popover), False, True, 0)

        self.add(btn_box)

        self.connect('notify::search-mode-enabled', self.on_search_mode_changed)

    def init_search_prop_popover(self):
        self.search_prop_popover = Gtk.Popover()

        self.date_switch = Gtk.Switch(hexpand=False, hexpand_set=True, margin=5)
        self.date_switch.connect("notify::active", lambda w, p: self.on_search_changed())

        self.date_from = Gtk.Calendar(margin=5, sensitive=False)
        self.date_to = Gtk.Calendar(margin=5, sensitive=False)
        for cal in [self.date_from, self.date_to]:
            cal.connect('day-selected', lambda w: self.on_search_changed())
            cal.set_display_options(
                    Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES
                |   Gtk.CalendarDisplayOptions.SHOW_HEADING
                |   Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS)
            cal.set_property('width-request', 240)

        popover_box = Gtk.Grid()
        popover_box.attach(Gtk.Separator(), 0, 0, 2, 1)
        popover_box.attach(self.date_switch, 0, 1, 2, 1)
        popover_box.attach(Gtk.Label(label="From", margin=5, xalign=0), 0, 2, 1, 1)
        popover_box.attach(Gtk.Label(label="To", margin=5, xalign=0), 1, 2, 1, 1)
        popover_box.attach(self.date_from, 0, 3, 1, 1)
        popover_box.attach(self.date_to, 1, 3, 1, 1)
        popover_box.show_all()

        self.search_prop_popover.add(popover_box)

    def on_search_changed(self):
        # remember old filter set
        old_filter_set = self.filter_set

        if self.get_search_mode():
            # generate date range
            # FIXME self.date_from.set_sensitive(self.date_switch.get_state())
            # FIXME self.date_to.set_sensitive(self.date_switch.get_state())
            date_from = None # FIXME calendar_date_to_date(self.date_from) if self.date_switch.get_state() else None
            date_to = None # FIXME calendar_date_to_date(self.date_to) if self.date_switch.get_state() else None

            # generate token list
            matches = re.findall(r"((\"[^\"]{2,}\")|\S{2,})+", self.entry.get_text())
            search_token = [m[0].strip('""') for m in matches] if matches else None

            # search transactions if any search constraints
            if search_token or (date_from and date_to):
                # search for transactions
                result = self.model.transactions(from_date=date_from, to_date=date_to, search=search_token, cols=['id', 'date'])
                # create filtersets
                self.filter_set = (set([t.id for t in result]), set([t.timestamp for t in result]))
            # no tokens -> all visible
            else:
                self.filter_set = None
        else:
            self.filter_set = None

        if old_filter_set != self.filter_set:
            self.emit("search-filter-changed")

    def get_filter_set(self):
        return self.filter_set if self.get_search_mode() else None

    def on_search_mode_changed(self, widget, param):
        if not self.get_search_mode():
            self.date_switch.set_state(False)

        self.emit("search-filter-changed")
