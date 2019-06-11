import gi, logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib

from schwifty import IBAN
import fints_url
from urllib.parse import urlparse
import threading

class AddAccountAssistant(Gtk.Assistant):
    def __init__(self, model):
        super().__init__(use_header_bar=True)

        self.model = model
        self.init_page_1()
        self.init_page_2()

        self.on_entry_changed(self.entry_iban)
        self.on_entry_changed(self.entry_name)
        self.on_entry_changed(self.entry_owner)
        self.on_entry_changed(self.entry_url)
        self.on_entry_changed(self.entry_login)
        self.on_entry_changed(self.entry_pass)

        self.show_all()

    def do_cancel(self):
        self.hide()

    def do_apply(self):
        self.hide() # FIXME

    def do_prepare(self, page):
        pass

    def set_entry_status(self, entry, valid, hint):
        entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "emblem-ok-symbolic" if valid else "emblem-important-symbolic");
        # FIXME entry.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, hint);
        entry.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, False);
        entry.set_icon_sensitive(Gtk.EntryIconPosition.SECONDARY, True);

    def on_entry_changed(self, entry):
        if entry is self.entry_name:
            if not len(entry.get_text()):
                self.set_entry_status(entry, False, "Please enter an account name.")
                self.page_1_name = False
            else:
                self.set_entry_status(entry, True, None)
                self.page_1_name = True
        elif entry is self.entry_owner:
            if not len(entry.get_text()):
                self.set_entry_status(entry, False, "Please enter an account owner.")
                self.page_1_owner = False
            else:
                self.set_entry_status(entry, True, None)
                self.page_1_owner = True
        elif entry is self.entry_iban:
            iban = None
            try:
                iban = IBAN(entry.get_text())
                self.set_entry_status(entry, True, None)
                self.page_1_iban = True
            except:
                self.set_entry_status(entry, False, "Please enter an account owner.")
                self.page_1_iban = False

            if iban:
                threading.Thread(target=self.async_fints_url_finder, args=(iban,), daemon=True).start()
        elif entry is self.entry_url:
            try:
                url = urlparse(entry.get_text() if entry.get_text() else entry.get_placeholder_text())
                self.set_entry_status(entry, True, None)
            except:
                self.set_entry_status(entry, False, "Please enter the banks FinTS URL.")
        elif entry is self.entry_login:
            if not entry.get_text():
                self.set_entry_status(entry, False, "Please enter FinTS login name.")
            else:
                self.set_entry_status(entry, True, None)
        elif entry is self.entry_pass:
            if not entry.get_text():
                self.set_entry_status(entry, False, "Please enter FinTS password.")
            else:
                self.set_entry_status(entry, True, None)

        self.set_page_complete(self.get_nth_page(0), self.page_1_name and self.page_1_owner and self.page_1_iban)
        self.set_page_complete(self.get_nth_page(1), False) #Fixme

    def async_fints_url_finder(self, iban):
        try:
            url = fints_url.find(iban=iban)
            GLib.idle_add(self.entry_url.set_placeholder_text, url)
            if not self.entry_url.get_text():
                GLib.idle_add(self.entry_url.set_text, url)
                GLib.idle_add(self.entry_url.select_region, -1, 0)
            Glib.idle_add(self.on_entry_changed, self.entry_url)
        except:
            pass

    def init_page_1(self):
        self.page_1_name = False;
        self.page_1_owner = False;
        self.page_1_iban = False;

        grid = Gtk.Grid(row_spacing=10, column_spacing=10)

        self.entry_name = Gtk.Entry(input_purpose=Gtk.InputPurpose.NAME, hexpand=True)
        self.entry_name.connect('changed', self.on_entry_changed)

        self.entry_owner = Gtk.Entry(input_purpose=Gtk.InputPurpose.NAME, hexpand=True)
        self.entry_owner.connect('changed', self.on_entry_changed)

        self.entry_iban = Gtk.Entry(input_purpose=Gtk.InputPurpose.FREE_FORM, hexpand=True)
        self.entry_iban.connect('changed', self.on_entry_changed)

        grid.attach(Gtk.Label(label='''
            To create an account please fill in the account details.
            Account name and owner name can be arbitarly choosen by you.
        ''', xalign=0, hexpand=True), 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Account Name", xalign=1.0), 0, 1, 1, 1)
        grid.attach(self.entry_name, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Owner Name", xalign=1.0), 0, 2, 1, 1)
        grid.attach(self.entry_owner, 1, 2, 1, 1)

        grid.attach(Gtk.Label(label='''
            Account name and owner name can be arbitarly choosen by you.
            Saldo automatically determines the bank from the accounts IBAN.
        ''', xalign=0, hexpand=True), 1, 3, 1, 1)

        grid.attach(Gtk.Label(label="IBAN", xalign=1.0), 0, 4, 1, 1)
        grid.attach(self.entry_iban, 1, 4, 1, 1)

        self.append_page(grid)

    def init_page_2(self):
        grid = Gtk.Grid(row_spacing=10, column_spacing=10)

        self.entry_url = Gtk.Entry(input_purpose=Gtk.InputPurpose.URL, hexpand=True)
        self.entry_url.connect('changed', self.on_entry_changed)

        self.entry_login = Gtk.Entry(input_purpose=Gtk.InputPurpose.FREE_FORM, hexpand=True)
        self.entry_login.connect('changed', self.on_entry_changed)

        self.entry_pass = Gtk.Entry(input_purpose=Gtk.InputPurpose.PASSWORD, hexpand=True)
        self.entry_pass.connect('changed', self.on_entry_changed)

        grid.attach(Gtk.Label(label="Please fill in the banks connection details.", xalign=0), 0, 0, 2, 1)

        grid.attach(Gtk.Label(label="FinTS URL", xalign=1.0), 0, 1, 1, 1)
        grid.attach(self.entry_url, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Login", xalign=1.0), 0, 2, 1, 1)
        grid.attach(self.entry_login, 1, 2, 1, 1)
        grid.attach(Gtk.Label(label="Password", xalign=1.0), 0, 3, 1, 1)
        grid.attach(self.entry_pass, 1, 3, 1, 1)

        self.append_page(grid)
