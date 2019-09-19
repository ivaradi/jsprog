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

        self.set_border_width(4)
        self.set_default_size(600, 450)

        self.set_default_icon_name(PROGRAM_ICON_NAME)

        headerBar = Gtk.HeaderBar()
        headerBar.set_show_close_button(True)
        headerBar.props.title = _("Joysticks")

        primaryMenuButton = Gtk.MenuButton()
        primaryMenuButton.set_direction(Gtk.ArrowType.NONE)

        menu = Gio.Menu.new()
        menu.append(_("_About"), "app.about")
        popover = Gtk.Popover.new_from_model(primaryMenuButton, menu)
        primaryMenuButton.set_popover(popover)

        headerBar.pack_end(primaryMenuButton)

        self._secondaryMenuButton = secondaryMenuButton = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name = "view-more-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        secondaryMenuButton.add(image)
        headerBar.pack_end(secondaryMenuButton)

        self.set_titlebar(headerBar)

        scrolledWindow = Gtk.ScrolledWindow()
        scrolledWindow.set_policy(Gtk.PolicyType.NEVER,
                                  Gtk.PolicyType.AUTOMATIC)

        self._joystickIcons = Gtk.ListStore(GdkPixbuf.Pixbuf, str, object)

        iconView = self._iconView = Gtk.IconView.new()
        iconView.set_model(self._joystickIcons)
        iconView.set_pixbuf_column(0)
        iconView.set_text_column(1)
        iconView.set_selection_mode(Gtk.SelectionMode.SINGLE)
        iconView.connect("selection-changed", self._iconSelectionChanged)
        iconView.connect("button-press-event", self._buttonPressed)

        scrolledWindow.add(iconView)

        self.add(scrolledWindow)
        self.show_all()

        JSWindow._instance = self

    @property
    def secondaryMenuButton(self):
        """Get the secondary menu button."""
        return self._secondaryMenuButton

    def addJoystick(self, joystick, icon, name):
        """Add the given joystick widget.

        A reference (actually, an iterator) is returned which can be used to
        call removeJoystick."""
        return self._joystickIcons.append([icon, name, joystick])

    def setJoystickName(self, ref, name):
        """Set the name of the joystick with the given reference."""
        self._joystickIcons.set(ref, [1], [name])

    def removeJoystick(self, ref):
        """Remove the given joystick with the given reference."""
        self._joystickIcons.remove(ref)

    def _iconSelectionChanged(self, iconView):
        """Called when the icon selection has changed."""
        items = iconView.get_selected_items()
        if items:
            ref = self._joystickIcons.get_iter(items[0])
            joystick = self._joystickIcons.get(ref, 2)[0]
            self._secondaryMenuButton.set_popover(joystick.popover)
        else:
            self._secondaryMenuButton.set_popover(None)

    def _buttonPressed(self, iconView, event):
        """Called when the mouse button has been pressed in the icon view."""
        if event.type==Gdk.EventType.BUTTON_PRESS and event.button==3:
            item = iconView.get_item_at_pos(event.x, event.y)
            if item is not None:
                iter = self._joystickIcons.get_iter(item[0])
                joystick = self._joystickIcons.get_value(iter, 2)
                contextMenu = joystick.contextMenu
                if contextMenu is not None:
                    contextMenu.show_all()
                    contextMenu.popup_at_pointer(event)


#-------------------------------------------------------------------------------
