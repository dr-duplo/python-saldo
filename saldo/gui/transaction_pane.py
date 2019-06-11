import gi, logging, locale
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .transaction_search_bar import TransactionSearchBar
from .transaction_view import TransactionView
from .transaction_action_bar import TransactionActionBar

class TransactionPane(Gtk.VBox):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.tree_view = TransactionView(model)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.tree_view)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # search bar
        self.search_bar = TransactionSearchBar(self.model)
        self.search_bar.connect('search-filter-changed', self.on_search_filter_changed)

        # disable tree search and use search bar instead
        self.tree_view.set_search_column(-1);
        self.tree_view.set_enable_search(False);
        self.tree_view.connect("key-press-event", lambda w, e: self.search_bar.handle_event(e))

        self.action_bar = TransactionActionBar(self.tree_view, self.model)
        self.action_bar.set_visible(False)

        # put all together
        self.pack_start(self.search_bar, False, False, 0)
        self.pack_start(scrolled_window, True, True, 0)
        self.pack_end(self.action_bar, False, False, 0)

    def on_search_filter_changed(self, widget):
        self.tree_view.set_filter_set(self.search_bar.get_filter_set())

    def get_search_mode(self):
        return self.search_bar.get_search_mode()

    def set_search_mode(self, mode):
        self.search_bar.set_search_mode(mode)

    def update(self, new_transaction_ids=None):
        self.tree_view.update(new_transaction_ids)
