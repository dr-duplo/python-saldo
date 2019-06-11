import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from . import AccountColors
from .balances import Balances, BalanceData
import datetime
import collections


class AnalysisPane(Gtk.HBox):
    def __init__(self, model):
        super().__init__()
        self.model = model

        self.income_pie = Balances(title=_("Income"), xpad=30, ypad=30)
        self.expenses_pie = Balances(title=_("Expenditures"), xpad=30, ypad=30)

        self.pack_start(self.income_pie, True, True, 0)
        self.pack_end(self.expenses_pie, True, True, 0)

        self.update()

    def update(self):
        last_month_to = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        last_month_from = last_month_to.replace(day=1)

        transactions = self.model.transactions(
            account=self.model.accounts(id=2),
            from_date=last_month_from,
            to_date=last_month_to,
            transfer=False
        )

        hist_p = {}
        hist_n = {}
        for t in transactions:
            tag = t.tags[0].tag if t.tags else None

            if t.value and t.value < 0:
                if not tag in hist_n:
                    hist_n[tag] = {"c": 0.0, "s": 0.0}

                hist_n[tag]["s"] += abs(t.value)
                hist_n[tag]["c"] += 1

            elif t.value and t.value > 0:
                if not tag in hist_p:
                    hist_p[tag] = {"c": 0.0, "s": 0.0}

                hist_p[tag]["s"] += abs(t.value)
                hist_p[tag]["c"] += 1

        hist_p = collections.OrderedDict(sorted(hist_p.items(), key=lambda i: (i[1]["s"]), reverse=True))
        hist_n = collections.OrderedDict(sorted(hist_n.items(), key=lambda i: (i[1]["s"]), reverse=True))

        print(hist_p)
        print(hist_n)

        self.income_pie.set_data(
            [BalanceData(v['s'],
                         AccountColors.fromString(k.name).value if k else Gdk.RGBA(0.5, 0.5, 0.5, 1),
                         k.name if k else None) for k, v in hist_p.items()])
        self.expenses_pie.set_data(
            [BalanceData(v['s'],
                         AccountColors.fromString(k.name).value if k else Gdk.RGBA(0.5, 0.5, 0.5, 1),
                         k.name if k else None) for k, v in hist_n.items()])
