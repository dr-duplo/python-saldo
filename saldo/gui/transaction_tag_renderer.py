import gi, logging, math
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GObject, Pango, PangoCairo

from . import RGBAfromString, AccountColors

class TransactionTagRenderer(Gtk.CellRenderer):
    background = GObject.Property(type=str, default=None)
    background_set = GObject.Property(type=bool, default=False)
    tag_name = GObject.Property(type=str, default=None)

    def __init__(self, **kwargs):
        super().__init__(*kwargs)

    def do_render(self, cr, widget, background_area, cell_area, flags):
        if self.background_set and self.background and not (flags & Gtk.CellRendererState.SELECTED):
            color = RGBAfromString(self.background)

            cr.rectangle(background_area.x, background_area.y,
                          background_area.width, background_area.height)

            cr.set_source_rgba( color.red,
                                color.green,
                                color.blue,
                                color.alpha);
            cr.fill()

        if self.tag_name:
            # draw the circle
            radius = min(cell_area.width - self.get_property('xpad') * 2, cell_area.height - self.get_property('ypad') * 2) / 2
            color = Gdk.RGBA(1,1,1,1) if (flags & Gtk.CellRendererState.SELECTED) else AccountColors.fromString(self.tag_name).value
            x = cell_area.x + cell_area.width / 2.0
            y = cell_area.y + cell_area.height / 2.0

            cr.arc(x, y, radius, 0.0, 2.0 * math.pi)
            cr.set_source_rgba( color.red,
                                color.green,
                                color.blue,
                                color.alpha);
            cr.stroke()

            # draw the first character of the tag name
            layout = widget.create_pango_layout(self.tag_name[0].upper());
            font_desc = Pango.FontDescription()
            font_desc.set_weight(Pango.Weight.HEAVY)
            layout.set_font_description(font_desc)

            (text_width, text_height) = layout.get_pixel_size();
            cr.move_to(x - text_width / 2.0, y - text_height / 2.0);

            PangoCairo.show_layout(cr, layout)

    def do_get_size(self, widget, cell_area):
        return (0, 0, 32, 32)
