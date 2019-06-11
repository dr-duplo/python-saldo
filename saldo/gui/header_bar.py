import gi, logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

class SaldoHeaderBar(Gtk.HeaderBar):

    __gsignals__ = {
        'fetch-clicked':        (GObject.SignalFlags.RUN_FIRST, None, ()),
        'add-account-clicked':  (GObject.SignalFlags.RUN_FIRST, None, ()),
        'search-clicked':       (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, stack):
        super().__init__()

        # refresh button
        self.btn_fetch = Gtk.Button(image=Gtk.Image.new_from_icon_name("emblem-synchronizing-symbolic" , Gtk.IconSize.MENU))
        self.btn_fetch.set_tooltip_text("Fetch Account Data");
        self.btn_fetch.connect("clicked", lambda w: self.emit("fetch-clicked"))

        # add account button
        self.btn_add_account = Gtk.Button(image=Gtk.Image.new_from_icon_name("list-add-symbolic" , Gtk.IconSize.MENU))
        self.btn_add_account.set_tooltip_text("Add Account");
        self.btn_add_account.connect("clicked", lambda w: self.emit("add-account-clicked"))

        # add search button
        self.btn_search = Gtk.Button(image=Gtk.Image.new_from_icon_name("preferences-system-search-symbolic" , Gtk.IconSize.MENU))
        self.btn_search.set_tooltip_text("Find Transactions");
        self.btn_search.connect("clicked", lambda w: self.emit("search-clicked"))

        # set up
        self.set_title('Saldo')

        self.stack_switcher = Gtk.StackSwitcher(stack=stack)
        self.stack_switcher.set_margin_right(18);
        self.set_custom_title(self.stack_switcher)
        self.stack_switcher.get_stack().connect("notify::visible-child", self.on_stack_changed)

        self.set_show_close_button(True)

        # pane dependent action buttons
        self.btn_stack = Gtk.Stack()
        self.btn_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE);
        self.btn_stack.set_vexpand(True);
        self.btn_stack.add_named(self.btn_add_account, 'accounts')
        self.btn_stack.add_named(self.btn_search, 'transactions')

        self.pack_start(self.btn_stack)
        self.pack_end(self.btn_fetch)

    def on_stack_changed(self, widget, param):
        vcn = self.stack_switcher.get_stack().get_visible_child_name()
        self.btn_stack.set_visible_child_name(vcn)
