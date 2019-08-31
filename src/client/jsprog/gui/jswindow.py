#-------------------------------------------------------------------------------

from .common import *
from .common import _

#-------------------------------------------------------------------------------

## @package jsprog.gui.jswindow
#
# The window containing the detected joysticks.
#

#-------------------------------------------------------------------------------

class JSWindow(Gtk.ApplicationWindow):
    """The window with the icons of the detected joysticks and some menus."""

    # The only instance of this window
    _instance = None

    @staticmethod
    def get():
        """Get the only instance of the window."""
        return JSWindow._instance

    def __init__(self, *args, **kwargs):
        """Construct the window."""
        super().__init__(*args, **kwargs)

        # It may be deprecated, but it causes the app menu to have a
        # normal title
        self.set_wmclass("jsprog", "JSProg")
        self.set_role("JSProg")

        self.set_title(WINDOW_TITLE_BASE + " - " + _("Joysticks"))
        self.set_border_width(10)
        self.set_default_size(600, 450)

        headerBar = Gtk.HeaderBar()
        headerBar.set_show_close_button(True)
        headerBar.props.title = WINDOW_TITLE_BASE + " - " + _("Joysticks")
        self.set_titlebar(headerBar)


        self.show_all()

        JSWindow._instance = self


#-------------------------------------------------------------------------------
