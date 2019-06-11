import gi, logging, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
#from gi_composites import GtkTemplate
import locale

from .bar_trend import BarTrend
from . import AccountColors

from datetime import timedelta

#@GtkTemplate(ui='/org/gnome/saldo/ui/account_tile.ui')
class AccountTile(Gtk.VBox):
#    __gtype_name__ = 'AccountTile'

#    title = GtkTemplate.Child()
#    details = GtkTemplate.Child()
#    date = GtkTemplate.Child()
#    balance = GtkTemplate.Child()
#    trend = GtkTemplate.Child()

    def __init__(self, model, account):
        super().__init__()

        self.model = model
        self.account = account

        #self.init_template()
        self.init_ui()
        self.refresh()

    def init_ui(self):
        self.set_name('account_tile')

        css = Gtk.CssProvider()
        css.load_from_data(b"""
            #account_tile {
                /*border: 1px solid #AAA;*/
                box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.1), 0 3px 10px 0 rgba(0, 0, 0, 0.1);
            }
        """)

        self.get_style_context().add_provider_for_screen(
            Gdk.Screen.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.lbl_title = Gtk.Label(label="Account Name", xalign=0.0, yalign=0.5, xpad=15, ypad=5)
        self.lbl_details = Gtk.Label(label="Bank Name\nIBAN\nBIC",  xalign=0.0, yalign=0, xpad=15, ypad=0)
        self.lbl_date = Gtk.Label(label="Date", xalign=1.0, yalign=0.5, xpad=15, ypad=0)
        self.lbl_balance = Gtk.Label(label="0.00 EUR",  xalign=1.0, yalign=0.5, xpad=15, ypad=2)
        self.bar_trend = BarTrend(xpad=15)

        overlay = Gtk.Overlay()
        overlay.add(self.bar_trend)
        overlay.add_overlay(self.lbl_details)
        overlay.set_overlay_pass_through(self.lbl_details, True)

        self.pack_start(self.lbl_title, expand=False, fill=True, padding=0)
        self.pack_start(overlay, expand=True, fill=True, padding=0)
        self.pack_end(self.lbl_balance, expand=False, fill=True, padding=0)
        self.pack_end(self.lbl_date, expand=False, fill=True, padding=2)

        self.set_size_request(400,250)
        self.set_vexpand(False)
        self.set_vexpand_set(True)
        self.set_hexpand(False)
        self.set_hexpand_set(True)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        self.lbl_balance.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 1))

        self.bar_trend.connect('selection_changed', self.bar_selection_changed)

    def bar_selection_changed(self, widget, selection):
        if self.balances:
            if not selection is None:
                bal = self.balances[selection]
            else:
                bal = self.balances[-1]

            if bal.pre_booked:
                self.lbl_date.set_markup("<span color='white'>(pre-booked) %s</span>" % bal.date.strftime('%A, %x'))
            else:
                self.lbl_date.set_markup("<span color='white'>%s</span>" % bal.date.strftime('%A, %x'))

            if bal.value >= 0:
                self.lbl_balance.set_markup("<span font='bold 20.0' color='#000000'>%s</span>" % (locale.format('%+.2f', bal.value, grouping=True) + " " + bal.currency))
            else:
                self.lbl_balance.set_markup("<span font='bold 20.0' color='#ef2929'>%s</span>" % (locale.format('%+.2f', bal.value, grouping=True) + " " + bal.currency))

    def refresh(self):
        bal = self.model.balances(account=self.account, pre_booked=True)
        bank_name = self.account.account_iban.bic.bank_name
        self.override_background_color(Gtk.StateFlags.NORMAL,
            AccountColors.fromString(self.account.name).value)

        self.lbl_title.set_markup(
            "<span font='bold 18.0' color='white'>%s</span>" % self.account.name)

        self.lbl_details.set_markup(
            "<span color='white'>%s</span>" %   
            (bank_name + "\n" + self.account.account_iban.formatted + "\n" + self.account.account_iban.bic.formatted))

        # gather historic balances
        self.balances = self.model.balances(account=self.account,
                                from_date=(bal.date - timedelta(days=31)),
                                to_date=bal.date)

        self.bar_trend.set_data([b.value for b in self.balances])

        self.bar_selection_changed(None, None)
