import gi
import logging

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib

# register ui gresource file
from os.path import abspath, join, dirname

scriptdir = dirname(abspath(__file__))
resource = Gio.resource_load(join(scriptdir, 'resources', 'saldo.gresource'))
Gio.Resource._register(resource)

import threading
import locale

locale.setlocale(locale.LC_ALL, '')

from enum import Enum
from hashlib import md5


def RGBAfromString(s):
    rgba = Gdk.RGBA()
    rgba.parse(s)
    return rgba


class AccountColors(Enum):
    #    YELLOW = RGBAfromString("#fce94f")
    #    ORANGE = RGBAfromString("#fcaf3e")
    #    RED = RGBAfromString("#ef2929")
    #    BROWN = RGBAfromString("#e9b96e")
    #    GREEN = RGBAfromString("#8ae234")
    #    BLUE = RGBAfromString("#729fcf")
    #    VIOLET = RGBAfromString("#ad7fa8")

    BUTTER = RGBAfromString("#edd400")
    ORANGE = RGBAfromString("#fcaf3e")
    CHOCOLATE = RGBAfromString("#e9b96e")
    CHAMELEON = RGBAfromString("#8ae234")
    SKY_BLUE = RGBAfromString("#729fcf")
    PLUM = RGBAfromString("#ad7fa8")
    SCARLET_RED = RGBAfromString("#ef2929")

    @staticmethod
    def fromString(s):
        return list(AccountColors)[
            int.from_bytes(
                md5(s.encode('utf-8')).digest()[:4],
                byteorder='little',
                signed=False) % len(list(AccountColors)
                                    )
            ]


from .header_bar import SaldoHeaderBar
from .account_pane import AccountPane
from .transaction_pane import TransactionPane
from .fetch_progress_bar import FetchProgressBar
from .add_account_assistant import AddAccountAssistant
from .analysis_pane import AnalysisPane

logging.getLogger("saldo_ui").setLevel(logging.DEBUG)


class SaldoUi(Gtk.ApplicationWindow):

    def __init__(self, model):
        super().__init__(title="Saldo")

        self.set_default_size(1024, 768)
        self.set_icon_name('saldo')

        self.model = model

        # transaction search with ctr-f
        accel_group = Gtk.AccelGroup()
        accel_group.connect(ord('f'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.LOCKED, self.on_ctrl_f)
        self.add_accel_group(accel_group)

        # init the pane stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE);
        self.stack.set_vexpand(True);

        # set the header bar
        self.set_titlebar(SaldoHeaderBar(self.stack))
        self.get_titlebar().connect('fetch-clicked', self.on_fetch_clicked);
        self.get_titlebar().connect('add-account-clicked', self.on_add_account_clicked);
        self.get_titlebar().connect('search-clicked', self.on_search_clicked);

        # init panes of stack
        self.init_accounts_pane()
        self.init_transactions_pane()
        self.init_budgets_pane()

        # info bar box
        self.info_bar_box = Gtk.VBox()
        self.info_bar_box.pack_end(self.stack, True, True, 0)
        self.add(self.info_bar_box)

        # init fetch progress bar
        self.init_fetch_progress()

        # show the main window
        self.show_all()

    def on_ctrl_f(self, accel_group, window, key, flags):
        if self.stack.get_visible_child_name() == 'transactions':
            self.transaction_pane.set_search_mode(True)

    def init_accounts_pane(self):
        self.account_pane = AccountPane(self.model)
        self.stack.add_titled(self.account_pane, 'accounts', 'Accounts')

    def init_transactions_pane(self):
        self.transaction_pane = TransactionPane(self.model)
        self.stack.add_titled(self.transaction_pane, 'transactions', 'Transactions')

    def init_budgets_pane(self):
        self.stack.add_titled(AnalysisPane(self.model), 'analysis', 'Analysis')

    def init_fetch_progress(self):
        self.fetch_progress_bar = FetchProgressBar()
        self.fetch_progress_bar.connect('response', self.on_cancel_fetch_clicked)
        self.fetch_cancellable = Gio.Cancellable()

    def on_add_account_clicked(self, widget):
        a = AddAccountAssistant(self.model)
        a.set_title("Add Account");
        a.set_can_focus(False)
        a.set_icon(self.get_icon());
        a.set_transient_for(self);
        a.set_position(Gtk.WindowPosition.CENTER_ON_PARENT);
        a.set_modal(True)
        a.show_all();

    def on_search_clicked(self, widget):
        self.transaction_pane.set_search_mode(not self.transaction_pane.get_search_mode())

    def on_fetch_clicked(self, widget):
        logging.debug('Fetch Account Data clicked')
        # show progress bar
        self.show_fetch_progress()
        # start fetch thread
        self.fetch_cancellable.reset()
        threading.Thread(target=self.fetch_thread, daemon=True).start()

    def on_cancel_fetch_clicked(self, widget, response_id):
        logging.debug('Cancel Fetch clicked')
        # disable cancel button
        self.fetch_progress_bar.set_sensitive(False)
        # cancel fetch
        self.fetch_cancellable.cancel()

    def on_fetch_finished(self, new_transaction_ids):
        self.hide_fetch_progress()
        self.model.refresh()
        self.account_pane.update(new_transaction_ids)
        self.transaction_pane.update(new_transaction_ids)

    def show_fetch_progress(self):
        # workaround for info bar revealer bug (https://bugzilla.gnome.org/show_bug.cgi?id=710888)
        self.info_bar_box.pack_start(self.fetch_progress_bar, False, True, 0)
        # show info bar
        self.fetch_progress_bar.set_visible(True)
        self.fetch_progress_bar.set_sensitive(True)
        # disable fetch button
        self.get_titlebar().btn_fetch.set_sensitive(False)

    def hide_fetch_progress(self):
        # enable fetch button
        self.get_titlebar().btn_fetch.set_sensitive(True)
        # hide info bar
        self.fetch_progress_bar.set_visible(False)
        # workaround for info bar revealer bug (https://bugzilla.gnome.org/show_bug.cgi?id=710888)
        Gtk.Container.remove(self.info_bar_box, self.fetch_progress_bar)

    # run in thread
    def fetch_thread_on_progress(self, p):
        # schedule progress bar update
        GLib.idle_add(self.fetch_progress_bar.update, p / 100, "Fetching Account Data")
        # return True if fetch should cancel itself
        return self.fetch_cancellable.is_cancelled()

    # run in thread
    def fetch_thread(self):
        new_transactions = []
        try:
            # do fetch
            logging.debug('Fetch Account Data started')
            new_transactions = self.model.fetch(progress_callback=self.fetch_thread_on_progress)
            logging.debug('Fetch Account Data finished')
        except Exception as e:
            logging.error('Fetch Account Data failed', e)

        # signal fetch finished
        GLib.idle_add(self.on_fetch_finished, [t.id for t in new_transactions])

    def run(self):
        self.connect("delete-event", Gtk.main_quit)
        self.show_all()
        Gtk.main()
