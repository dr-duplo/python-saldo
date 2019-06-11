import gi, logging, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

class BarTrend(Gtk.DrawingArea):
    __gsignals__ = {
        'selection_changed': (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    xpad = GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **properties):
        super().__init__(**properties)

        self.connect("draw", self.on_draw)
        self.data = None

        self.add_events(  Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.ENTER_NOTIFY_MASK
                        | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.mouse_pos = None
        self.selected_bar = None

    def do_motion_notify_event(self, event):
        self.mouse_pos = (event.x, event.y)
        self.queue_draw()
        self._check_selected_bar()

    def do_enter_notify_event(self, event):
        self.mouse_pos = (event.x, event.y)
        self.queue_draw()
        self._check_selected_bar()

    def do_leave_notify_event(self, event):
        self.mouse_pos = None
        self.queue_draw()
        self._check_selected_bar()

    def _check_selected_bar(self):
        if self.mouse_pos:
            new_selected = self._pos_to_idx(self.mouse_pos[0])

        else:
            new_selected = None

        if self.selected_bar != new_selected:
            self.selected_bar = new_selected
            self.emit('selection_changed', self.selected_bar if not self.selected_bar is None else -1)

    def set_data(self, data):
        self.data = data
        self.queue_draw()

    def _pos_to_idx(self, x):
        width = self.get_allocation().width - self.props.xpad * 2
        height = self.get_allocation().height
        spacing = 1

        bar_width = (width - (len(self.data) - 1) * spacing) / len(self.data);

        idx = (x - self.props.xpad) / (bar_width + spacing)

        if idx >= len(self.data) or idx < 0:
            idx = None
        else:
            idx = int(idx)

        return idx

    def _bar_rect(self, idx):
        width = self.get_allocation().width - self.props.xpad * 2
        height = self.get_allocation().height
        spacing = 1

        bar_width = (width - (len(self.data) - 1) * spacing) / len(self.data);

        value_min = min(min(self.data), 0);
        value_max = max(max(self.data), 0);
        value_scale = height / (value_max - value_min);
        value_offset = height + value_scale * value_min;

        bar_x = idx * (bar_width + spacing) + self.props.xpad;
        bar_y = value_offset;
        bar_height = -self.data[idx] * value_scale;
        if abs(bar_height) < 1:
            bar_height = 1 if bar_height > 0 else -1;

        return (bar_x, bar_y, bar_width, bar_height)

    def on_draw(self, widget, context):
        context.set_line_width(0.5);

        for i, value in enumerate(self.data):
            rect = self._bar_rect(i)

            context.rectangle(rect[0], rect[1], rect[2], rect[3]);

            if self.selected_bar == i: # or (i == len(self.data) - 1 and self.selected_bar == None):
                context.set_source_rgba(1, 1, 1, 0.50);
            else:
                context.set_source_rgba(1, 1, 1, 0.25);

            context.fill();

        return True
