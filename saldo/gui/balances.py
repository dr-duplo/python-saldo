import gi, logging, os, math, datetime, collections, locale
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GObject, Pango, PangoCairo

from . import AccountColors

class BalanceData:
    value = None
    color = Gdk.RGBA(0, 0, 0, 1)
    name = None

    def __init__(self, value = None, color = Gdk.RGBA(0, 0, 0, 1), name = None):
        self.value = value
        self.color = color
        self.name = name

class Balances(Gtk.DrawingArea):
    xpad = GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)
    ypad = GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)
    title = GObject.Property(type=str, default="Total", flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **properties):
        super().__init__(**properties)
        self.data = None
        self.data_sum = 0
        self.regions = []

        self.add_events(  Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.ENTER_NOTIFY_MASK
                        | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.mouse_pos = None
        self.selected_region = None

    def do_motion_notify_event(self, event):
        self.mouse_pos = (event.x, event.y)
        self._check_selected_region()

    def do_enter_notify_event(self, event):
        self.mouse_pos = (event.x, event.y)
        self._check_selected_region()

    def do_leave_notify_event(self, event):
        self.mouse_pos = None
        self._check_selected_region()

    def _check_selected_region(self):
        selected_region = None
        if self.regions and self.mouse_pos:
            width = self.get_allocation().width - self.props.xpad * 2.0
            height = self.get_allocation().height - self.props.ypad * 2.0
            ro = min(width, height) / 2.0;
            ri = ro * 0.8

            cx = self.get_allocation().width / 2.0;
            cy = self.get_allocation().height / 2.0;

            mouse_a = math.atan2(self.mouse_pos[1] - cy, self.mouse_pos[0] - cx)
            mouse_r = math.sqrt(math.pow(self.mouse_pos[0] - cx, 2) + math.pow(self.mouse_pos[1] - cy, 2))

            if mouse_a < -math.pi * 0.5:
                mouse_a += 2.0 * math.pi

            if mouse_r >= ri and mouse_r <= ro:
                for idx, r in enumerate(self.regions):
                    if mouse_a >= r['start'] and mouse_a <= r['end']:
                        selected_region = idx

        if self.selected_region != selected_region:
            self.selected_region = selected_region
            self.queue_draw()

    def set_data(self, data):
        self.data = data
        self.data_sum = 0
        self.regions = []

        if self.data:
            for v in self.data:
                self.data_sum += v.value

        a = -math.pi / 2.0
        an = 0
        sn = 0
        if self.data_sum:
            for data in self.data:
                ac = data.value / self.data_sum * math.pi * 2.0

                if ac < 0.040 or data.name is None or data.value / self.data_sum < 0.01:
                    an += ac
                    sn += data.value
                    continue

                color = data.color

                self.regions.append({
                        "data" : data,
                        "start" : a,
                        "end" : a + ac,
                        "color" : data.color,
                        "text" : data.name})
                a += ac

            if an >= 0.020:
                self.regions.append({
                        "data" : None,
                        "start" : a,
                        "end" : a + an,
                        "color" : Gdk.RGBA(0.5, 0.5, 0.5, 1),
                        "text" : "Remains"})
                a += an

    def draw_circle_band(self, context, cx, cy, a_start, a_end, inner_r, outer_r, color=Gdk.RGBA(0,0,0,1), text=None):
        context.set_source_rgba(color.red, color.green, color.blue, color.alpha)
        context.arc(cx, cy, outer_r, a_start, a_end)
        context.line_to(cx + math.cos(a_end) * inner_r, cy + math.sin(a_end) * inner_r)
        context.arc_negative(cx, cy, inner_r, a_end, a_start)
        context.line_to(cx + math.cos(a_start) * outer_r, cy + math.sin(a_start) * outer_r)
        context.fill_preserve()
        context.set_source_rgba(color.red * 0.5, color.green * 0.5, color.blue * 0.5, 1)
        context.stroke()

    def do_draw(self, context):
        context.set_line_width(0.5);

        width = self.get_allocation().width - self.props.xpad * 2.0
        height = self.get_allocation().height - self.props.ypad * 2.0
        ro = min(width, height) / 2.0;
        ri = ro * 0.8

        cx = self.get_allocation().width / 2.0;
        cy = self.get_allocation().height / 2.0;

        context.set_source_rgba(1, 1, 1, 1)
        context.arc(cx, cy, ro * 0.75, 0, 2.0 * math.pi)
        context.fill();

        if self.regions:
            for idx, r in enumerate(self.regions):
                color = r['color']
                ric = ri
                roc = ro
                if self.selected_region is not None:
                    if self.selected_region != idx:
                        color = Gdk.RGBA(0.95, 0.95, 0.95, 1.0)
                    else:
                        ric *= 1.00
                        roc *= 1.05

                self.draw_circle_band(context, cx, cy, r['start'] + 0.010, r['end'] - 0.010, ric, roc, color=color, text=r['text'])

        else:
            self.draw_circle_band(context, cx, cy, -math.pi * 0.5, math.pi * 1.5, ri, ro, color=Gdk.RGBA(0.5, 0.5, 0.5, 1))

        if not self.regions or self.selected_region is None:
            text = "%s\n%s EUR\n" % (self.title, locale.format("%0.2f", self.data_sum, grouping=True))
        else:
            text = "%s\n%s EUR\n%s%%" % \
                (self.regions[self.selected_region]['text'], \
                 locale.format("%0.2f", self.regions[self.selected_region]['data'].value, grouping=True), \
                 locale.format("%0.2f", self.regions[self.selected_region]['data'].value / self.data_sum * 100.0))

        layout = self.create_pango_layout(text);
        font_desc = Pango.FontDescription()
        font_desc.set_weight(Pango.Weight.HEAVY)
        font_desc.set_size(21 * Pango.SCALE)
        layout.set_font_description(font_desc)
        layout.set_alignment(Pango.Alignment.CENTER)
        (text_width, text_height) = layout.get_pixel_size();

        if text_width > ro * 0.75 * 2.0:
            font_desc.set_size(21 * Pango.SCALE * ro * 0.75 * 2.0 / text_width)
            layout.set_font_description(font_desc)
            (text_width, text_height) = layout.get_pixel_size();

        context.move_to(cx - text_width / 2.0, cy - text_height / 2.0);
        context.set_source_rgba(0,0,0,1)
        PangoCairo.show_layout(context, layout)

        return True
