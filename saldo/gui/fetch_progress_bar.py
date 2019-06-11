import gi, logging, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class FetchProgressBar(Gtk.InfoBar):
    def __init__(self):
        super().__init__()

        # progress bar
        self.progress_bar = Gtk.ProgressBar()

        # info bar
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_message_type(Gtk.MessageType.OTHER)
        self.get_content_area().pack_start(self.progress_bar, True, True, 0)
        self.add_button('Cancel', 0)
        self.show_all()

    def update(self, fraction, info):
        if info:
            self.progress_bar.set_text(info)
            self.progress_bar.set_show_text(True)
        else:
            self.progress_bar.set_show_text(False)

        self.progress_bar.set_fraction(fraction)
