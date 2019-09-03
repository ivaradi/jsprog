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
        self.set_wmclass("jsprog", PROGRAM_TITLE)
        self.set_role(PROGRAM_NAME)

        self.set_title(PROGRAM_TITLE)
        self.set_border_width(4)
        self.set_default_size(600, 450)

        self.set_default_icon_name(PROGRAM_ICON_NAME)

        headerBar = Gtk.HeaderBar()
        headerBar.set_show_close_button(True)
        headerBar.props.title = PROGRAM_TITLE
        headerBar.set_subtitle(_("Joysticks"))

        primaryMenuButton = Gtk.MenuButton()
        primaryMenuButton.set_direction(Gtk.ArrowType.NONE)

        menu = Gio.Menu.new()
        menu.append(_("_About"), "app.about")
        popover = Gtk.Popover.new_from_model(primaryMenuButton, menu)
        primaryMenuButton.set_popover(popover)

        headerBar.pack_end(primaryMenuButton)

        self.set_titlebar(headerBar)

        scrolledWindow = Gtk.ScrolledWindow()
        scrolledWindow.set_policy(Gtk.PolicyType.NEVER,
                                  Gtk.PolicyType.AUTOMATIC)

        self._joystickIcons = Gtk.ListStore(GdkPixbuf.Pixbuf, str, object)

        iconView = Gtk.IconView.new()
        iconView.set_model(self._joystickIcons)
        iconView.set_pixbuf_column(0)
        iconView.set_text_column(1)

        scrolledWindow.add(iconView)

        self.add(scrolledWindow)
        self.show_all()

        JSWindow._instance = self

    def addJoystick(self, joystick, icon, name):
        """Add the given joystick widget.

        A reference (actually, an iterator) is returned which can be used to
        call removeJoystick."""
        return self._joystickIcons.append([icon, name, joystick])

    def removeJoystick(self, ref):
        """Remove the given joystick with the given reference."""
        self._joystickIcons.remove(ref)

#-------------------------------------------------------------------------------
