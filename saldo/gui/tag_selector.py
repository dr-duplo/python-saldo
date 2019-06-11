import gi, logging, locale
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from . import AccountColors
from .balances import Balances, BalanceData
import datetime
import collections
from .tag_share_assistant import TagShareAssistent

class TagSelector(Gtk.ButtonBox):
    def __init__(self, model):
        super().__init__()
        self.model = model

        self.tag_model = Gtk.ListStore(int, float, str)
        self.tag_model_sorted = Gtk.TreeModelSort(model=self.tag_model)
        self.tag_model_sorted.set_sort_column_id(1, Gtk.SortType.DESCENDING)

        self.cbx_tag = Gtk.ComboBox.new_with_model_and_entry(self.tag_model_sorted)
        self.cbx_tag.set_size_request(250, -1)
        self.cbx_tag.set_id_column(0)
        self.cbx_tag.set_entry_text_column(2)
        self.cbx_tag.connect('changed', self.on_cbx_tag_changed)
        self.cbx_tag.get_child().connect('activate', self.on_cbx_tag_activate)

        self.init_popover()

        self.btn_tag_share = Gtk.MenuButton(popover=self.tag_share_popover, image=Gtk.Image.new_from_icon_name("view-list-symbolic", Gtk.IconSize.MENU))

        self.btn_remove_tag = Gtk.Button(image=Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
        self.btn_remove_tag.connect("clicked", self.on_btn_remove_tag_clicked)

        self.set_property('layout_style', Gtk.ButtonBoxStyle.EXPAND)
        self.set_homogeneous(False)
        self.pack_start(self.cbx_tag, True, True, 0)
        self.pack_start(self.btn_tag_share, False, True, 0)
        self.pack_start(self.btn_remove_tag, False, True, 0)

    def set_transactions(self, transactions):
        self.transactions = transactions
        self.update()

    def update(self):
        # single transaction
        if self.transactions and len(self.transactions) == 1:
            self.tag_model.clear()

            for tag, likelihood in self.transactions[0].tag_likelihood():
                self.tag_model.append([tag.id, likelihood, tag.name])

            self.cbx_tag.get_child().set_placeholder_text(_("Category"))

            if len(self.transactions[0].tags) == 1:
                self.cbx_tag.get_child().set_text(self.transactions[0].tags[0].tag.name)
                self.btn_remove_tag.set_sensitive(True)
            elif len(self.transactions[0].tags) > 1:
                cbx_text = set()
                for tag in self.transactions[0].tags:
                    cbx_text.add(tag.name)

                self.cbx_tag.get_child().set_placeholder_text(", ".join(cbx_text))
                self.cbx_tag.get_child().set_text("")
                self.btn_remove_tag.set_sensitive(True)
            else:
                self.cbx_tag.get_child().set_text("")
                self.btn_remove_tag.set_sensitive(False)

            self.btn_tag_share.set_sensitive(True)
            self.update_tag_share()

        # multiple transactions
        elif self.transactions and len(self.transactions) > 1:
            # FIXME CURRENCY
            self.tag_model.clear()
            for tag in self.model.tags():
                self.tag_model.append([tag.id, 0, tag.name])

            cbx_text = set()
            for t in self.transactions:
                for tag in t.tags:
                    cbx_text.add(tag.name)

            if len(cbx_text) > 1:
                self.cbx_tag.get_child().set_placeholder_text(", ".join(cbx_text))
                self.cbx_tag.get_child().set_text("")
                self.btn_remove_tag.set_sensitive(True)
            elif len(cbx_text) == 1:
                self.cbx_tag.get_child().set_placeholder_text(_("Category"))
                self.cbx_tag.get_child().set_text(", ".join(cbx_text))
                self.btn_remove_tag.set_sensitive(True)
            else:
                self.cbx_tag.get_child().set_placeholder_text(_("Category"))
                self.cbx_tag.get_child().set_text("")
                self.btn_remove_tag.set_sensitive(False)

            self.btn_tag_share.set_sensitive(False)

        # no transaction
        else:
            self.cbx_tag.get_child().set_placeholder_text(_("Category"))
            self.cbx_tag.get_child().set_text("")
            self.btn_remove_tag.set_sensitive(False)
            self.btn_tag_share.set_sensitive(True)

    def on_btn_remove_tag_clicked(self, widget):
        if not self.transactions:
            return

        # assign tag to transactions
        for t in self.transactions:
            self.model.assign_tag(t, None)

        self.update()

    def on_cbx_tag_activate(self, widget):
        if not self.transactions:
            return

        if self.cbx_tag.get_child().get_text():
            tag = self.model.tags(name=self.cbx_tag.get_child().get_text())
            # new tag
            if tag is None:
                dialog = Gtk.MessageDialog( #parent=self,
                                            flags=Gtk.DialogFlags.MODAL,
                                            type=Gtk.MessageType.WARNING,
                                            buttons=Gtk.ButtonsType.OK_CANCEL,
                                            message_format="Create new category: %s" % self.cbx_tag.get_child().get_text())

                if dialog.run() != Gtk.ResponseType.YES:
                    return

                #tag = self.model.create_tag(self.cbx_tag.get_active_text())
                return

        # assign tag to transactions
        for t in self.transactions:
            self.model.assign_tag(t, tag)


        self.update()

    def on_cbx_tag_changed(self, widget):
        if not self.transactions:
            return

        # existing tag
        if self.cbx_tag.get_active() >= 0:
            tag = self.model.tags(id=self.tag_model_sorted[self.cbx_tag.get_active()][0])
        else:
            # nothing to assign
            return

        # assign tag to transactions
        for t in self.transactions:
            self.model.assign_tag(t, tag)

        self.update()

    def init_popover(self):
        self.tag_share_list = Gtk.ListBox()
        self.tag_share_list.set_selection_mode(Gtk.SelectionMode.NONE)

        self.btn_add_share = Gtk.Button(image=Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU), relief=Gtk.ReliefStyle.NONE);
        self.btn_add_share.connect("clicked", self.btn_add_share_clicked)
        self.tag_share_list.add(self.btn_add_share)
        self.tag_share_list.show_all()

        self.tag_share_popover = Gtk.Popover()
        self.tag_share_popover.add(self.tag_share_list)

    def share_add_row(self, ttag = None):
        row = Gtk.HBox(margin=1)

        cbx = Gtk.ComboBox.new_with_model_and_entry(self.tag_model_sorted)
        cbx.set_size_request(100, -1)
        cbx.set_id_column(0)
        cbx.set_entry_text_column(2)
        cbx.get_child().set_placeholder_text(_("Category"))

        sbtn = Gtk.SpinButton()
        sbtn.set_numeric(True)
        sbtn.set_digits(2)
        sbtn.set_increments(0.1, 1.0)

        if ttag:
            cbx.get_child().set_text(ttag.name)
            if ttag.transaction.value < 0:
                sbtn.set_range(ttag.transaction.value, 0)
            else:
                sbtn.set_range(0, ttag.transaction.value)

            sbtn.set_value(ttag.value)

        row.pack_start(cbx, True, True, 0)
        row.pack_start(sbtn, True, True, 5)
        row.pack_end(Gtk.Button(image=Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU), relief=Gtk.ReliefStyle.NONE), False, False, 0)
        row.show_all()

        self.tag_share_list.insert(row, len(self.tag_share_list) - 1)

    def btn_add_share_clicked(self, widget):
        self.share_add_row(None)

    def update_tag_share(self):
        # clear list
        self.tag_share_list.get_children()[-1].remove(self.btn_add_share)

        for w in self.tag_share_list:
            self.tag_share_list.remove(w)

        if len(self.transactions) == 1:
            for ttag in self.transactions[0].tags:
                self.share_add_row(ttag)

        # "add" button
        self.tag_share_list.add(self.btn_add_share)
