appIndicator = False

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import cairo
from gi.repository import Pango
gi.require_version('PangoCairo', '1.0')
from gi.repository import PangoCairo

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
    appIndicator = True
except:
    print("Failed to import AppIndicator3")
