import gi, logging, locale
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

from datetime import date

from .tag_selector import TagSelector

class TransactionActionBar(Gtk.ActionBar):
    def __init__(self, tree_view, model):
        super().__init__()

        self.tree_view = tree_view
        self.model = model
        self.transactions = []
        self.tree_view.get_selection().connect('changed', self.on_selection_changed)

        self.lbl_sum = Gtk.Label()
        self.lbl_sum.set_selectable(True)

        self.lbl_detail = Gtk.Label()

        self.tag_selector = TagSelector(self.model)

        self.pack_start(self.tag_selector)
        self.set_center_widget(self.lbl_detail)
        self.pack_end(self.lbl_sum)

    def on_selection_changed(self, selection):
        if selection.count_selected_rows():
            model = selection.get_tree_view().get_model()
            tsum = 0
            cnt = 0
            self.transactions = []
            for path in selection.get_selected_rows()[1]:
                obj = model.get_value(model.get_iter(path), 2).obj
                if not isinstance(obj, date):
                    tsum += obj.value if obj.value else 0.0
                    cnt += 1
                    self.transactions.append(obj)

            self.set_visible(cnt > 0)

            if cnt > 1:
                if tsum >= 0:
                    self.lbl_sum.set_markup("<span color='#000000'>%s</span>" % (locale.format('%+.2f', tsum, grouping=True) + " EUR"))
                else:
                    self.lbl_sum.set_markup("<span color='#ef2929'>%s</span>" % (locale.format('%+.2f', tsum, grouping=True) + " EUR"))

                self.lbl_detail.set_markup("%u Transactions selected" % cnt)
            elif cnt == 1:
                self.lbl_detail.set_markup("Transaction details\nIBAN: %s\nPurpose: %s" % (str(self.transactions[0].r_account_iban), str(self.transactions[0].purpose)))
                self.lbl_sum.set_markup("")

            self.tag_selector.set_transactions(self.transactions)
        else:
            self.set_visible(False)
            self.tag_selector.set_transactions(None)
