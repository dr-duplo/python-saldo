import gi, logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib

from schwifty import IBAN
#import fints_url
from urllib.parse import urlparse
import threading

class TagShareAssistent(Gtk.ListBox):
    def __init__(self, transaction, tags):
        super().__init__()

        self.model = model
        self.transaction = transaction

        self.set_selection_mode(Gtk.SelectionMode.NONE)

        self.btn_add_share = Gtk.Button(image=Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU), relief=Gtk.ReliefStyle.NONE);
        self.btn_add_share.connect("clicked", self.add_row)
        self.add(self.btn_add_share)

    def add_row(self, w=None):
        row = Gtk.HBox(margin=1)
        cbx = Gtk.ComboBox.new_with_entry()
        cbx.set_size_request(100, -1)
        sbtn = Gtk.SpinButton()
        row.pack_start(cbx, True, True, 0)
        row.pack_start(sbtn, True, True, 5)
        row.pack_end(Gtk.Button(image=Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU), relief=Gtk.ReliefStyle.NONE), False, False, 0)

        row.show_all()

        self.insert(row, len(self) - 1)
