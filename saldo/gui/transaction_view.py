import gi, logging, locale
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GObject, GLib, Pango

from datetime import date
from . import AccountColors

from .transaction_tag_renderer import TransactionTagRenderer

class TreeModelObject(GObject.GObject):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj

class TransactionView(Gtk.TreeView):
    def __init__(self, model):
        super().__init__()

        self.model = model

        # the base tree model
        self.tree_store = Gtk.TreeStore(int, int, TreeModelObject)

        # the row filter model
        self.filter_set = None
        self.filter = Gtk.TreeModelFilter(child_model=self.tree_store, virtual_root=None)
        self.filter.set_visible_func(self.__is_row_visible)

        # the row sorter model
        self.sort = Gtk.TreeModelSort(model=self.filter)
        self.sort.set_sort_column_id(1, Gtk.SortType.DESCENDING)

        # set tree model to view
        self.set_model(self.sort)

        self.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        # columns

        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn('', cell)
        col.set_cell_data_func(cell, self.__load_cell_data, 0)
        col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col.set_fixed_width(10)

        self.append_column(col)

        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn('Date/Name', cell)
        col.set_cell_data_func(cell, self.__load_cell_data, 1)
        col.set_expand(True)
        col.set_resizable(True)

        self.append_column(col)
        self.set_expander_column(col)

        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn('Purpose', cell)
        col.set_cell_data_func(cell, self.__load_cell_data, 2)
        col.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        col.set_expand(True)
        col.set_resizable(True)

        self.append_column(col)

        cell = TransactionTagRenderer()
        col = Gtk.TreeViewColumn('Category', cell)
        col.set_cell_data_func(cell, self.__load_cell_data, 3)
        col.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        col.set_expand(False)
        col.set_resizable(True)

        self.append_column(col)

        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn('Amount', cell)
        col.set_cell_data_func(cell, self.__load_cell_data, 4)
        col.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        col.set_expand(False)
        col.set_resizable(False)

        self.append_column(col)

        # initial populate list
        row_date = None
        row_iter = None
        for t in self.model.transactions():#cols=['id', 'date']):
            # every new date gets a new top row
            if row_iter is None or row_date != t.date:
                row_date = t.date
                row_iter = self.tree_store.append(None, [None, t.timestamp, TreeModelObject(row_date)])

            # every transaction is a child of a date row
            self.tree_store.append(row_iter, [t.id, t.timestamp, TreeModelObject(t)])

        self.expand_all()

    def set_filter_set(self, filter_set):
        self.filter_set = filter_set
        self.update()

    def __is_row_visible(self, tree_model, i, data):
        tid, ts = tree_model.get(i, 0, 1)

        # check if row fits to filter set
        if tid and self.filter_set is not None:
            return tid in self.filter_set[0]
        elif not tid and self.filter_set is not None:
            return ts in self.filter_set[1]
        else:
            return True

    def __load_cell_data(self, col, cell, tree_model, iter, data):
        obj = tree_model.get_value(iter, 2).obj

        # common cell attributes
        cell.set_property('xalign', 0);
        cell.set_property('xpad', 5);
        cell.set_property('ypad', 5);
        if data != 3:
            cell.set_property('single_paragraph_mode', True)

        # date row
        if isinstance(obj, date):
            cell.set_property('background', '#EEEEEE');
            cell.set_property('background_set', True);

            if data == 1:
                cell.set_property('text', obj.strftime('%A, %x'))
            else:
                if data != 3:
                    cell.set_property('text', None)
                else:
                    cell.set_property('tag_name', None)

        # transaction row
        else:
            if data == 0:
                cell.set_property('text', str(obj.account.id))
                cell.set_property('cell_background_gdk', AccountColors.fromString(obj.account.name).value.to_color())
            elif data == 1:
                cell.set_property('text', " ".join(str(obj.r_name).split()))
                cell.set_property('ellipsize', Pango.EllipsizeMode.END)
            elif data == 2:
                cell.set_property('text', " ".join(str(obj.purpose).split()))
                cell.set_property('ellipsize', Pango.EllipsizeMode.END)
            elif data == 3:
                if obj.tags:
                    cell.set_property('tag_name', obj.tags[0].name)
                else:
                    cell.set_property('tag_name', None)
            elif data == 4:
                cell.set_property('xalign', 1);
                cell.set_property('text', ('%s %s' % (locale.format('%+.2f', obj.value, grouping=True), obj.value_currency)) if obj.value else None)
                if obj.pre_booked:
                    cell.set_property('foreground', '#cccccc')
                elif obj.value and obj.value < 0:
                    cell.set_property('foreground', '#ef2929')
                else:
                    cell.set_property('foreground', '#000000')

            cell.set_property('background_set', False);

    def _find_date_row(self, date_to_find):
        for row in self.tree_store:
            obj = row[2].obj
            if isinstance(obj, date) and obj == date_to_find:
                # found
                return row.iter

        # not found
        return None

    def update(self, new_transaction_ids=[]):
        self.get_selection().unselect_all()
        # populate list
        row_date = None
        row_iter = None
        for id_ in new_transaction_ids:
            t = self.model.transactions(id=id_)

            # try find existing top row
            if row_date != t.date or not row_iter:
                row_iter = self._find_date_row(t.date)
                row_date = t.date

            # every new date gets a new top row
            if not row_iter:
                row_date = t.date
                row_iter = self.tree_store.append(None, [None, t.timestamp, TreeModelObject(row_date)])

            # every transaction is a child of a date row
            self.tree_store.append(row_iter, [t.id, t.timestamp, TreeModelObject(t)])

        # refilter model
        self.filter.refilter()
        self.expand_all()
