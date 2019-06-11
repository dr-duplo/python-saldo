import gi, logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GObject, GLib

from .account_tile import AccountTile

class AccountPane(Gtk.ScrolledWindow):
    def __init__(self, model):
        super().__init__()

        self.model = model

        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.flow_box.set_margin_top(25)
        self.flow_box.set_margin_right(25)
        self.flow_box.set_margin_bottom(25)
        self.flow_box.set_margin_left(25)
        self.flow_box.set_vexpand(False)
        self.flow_box.set_vexpand_set(False)
        self.flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow_box.set_column_spacing(25)
        self.flow_box.set_row_spacing(25)
        self.flow_box.set_homogeneous(True)

        self.add(self.flow_box)

        self.update()

    def update(self, new_transaction_ids=None):

        for c in self.flow_box.get_children():
            c.destroy()

        for account in self.model.accounts():
            self.flow_box.add(AccountTile(self.model, account))

        self.flow_box.show_all()
