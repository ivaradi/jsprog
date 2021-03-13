
from  .jsmenu import JSMenu

from .common import *
from .common import _

#-------------------------------------------------------------------------------

## @package jsprog.gui.statusicon
#
# The status icon.
#

#-------------------------------------------------------------------------------

class StatusIconMenu(JSMenu):
    """The menu for the status icon."""
    def __init__(self, joystick):
        """Construct the menu for the given joystick."""
        super().__init__(joystick, profileMenuItemOffset = 2)

        name = joystick.identity.name

        nameMenuItem = self._nameMenuItem = Gtk.MenuItem()
        # FIXME: how to make the label bold
        nameMenuItem.set_label(name)
        nameMenuItem.show()
        self.insert(nameMenuItem, 0)

        separator = Gtk.SeparatorMenuItem()
        separator.show()
        self.insert(separator, 1)

        separator = Gtk.SeparatorMenuItem()
        separator.show()
        self.append(separator)

        quitMenuItem = Gtk.MenuItem()
        quitMenuItem.set_label(_("Quit"))
        quitMenuItem.connect("activate", self._quit, joystick.gui)
        quitMenuItem.show()
        self.append(quitMenuItem)

    def _getModifiedProfileNameMarkup(self, name):
        """Convert the given name into a markup representing that the
        corresponding profile has been modified since downloaded.

        This implementation puts an asterisk in front of the name."""
        return "* " + name

    def _quit(self, mi, gui):
        """Called when the Quit menu item is activated."""
        gui.quit()

#-------------------------------------------------------------------------------

class StatusIcon(object):
    """The class handling the status icon."""
    def __init__(self, id, joystick, gui):
        """Construct the status icon."""
        self._gui = gui
        self._id = id

        menu = self._menu = StatusIconMenu(joystick)
        menu.show()

        joystickType = joystick.type
        joystickType.connect("indicator-icon-changed", self._iconChanged)
        iconPath = joystickType.indicatorIconPath

        if appIndicator:
            # FIXME: do we need a unique name here?
            indicator = AppIndicator3.Indicator.new ("jsprog-%d" % (id,), iconPath,
                                                     AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            indicator.set_status (AppIndicator3.IndicatorStatus.ACTIVE)

            indicator.set_menu(menu)
            self._indicator = indicator
        else:
            def popup_menu(status, button, time):
                menu.popup(None, None, Gtk.status_icon_position_menu,
                           button, time, status)

            statusIcon = Gtk.StatusIcon()
            statusIcon.set_from_file(iconPath)
            statusIcon.set_visible(True)
            statusIcon.connect('popup-menu', popup_menu)
            self._statusIcon = statusIcon

    def setName(self, name):
        """Set the label of the name menu item to the given value."""
        self._nameMenuItem.set_label(name)

    def setActive(self, profile):
        """Make the menu item belonging to the given profile
        active."""
        self._menu.setActive(profile)

    def destroy(self):
        """Hide and destroy the status icon."""
        if appIndicator:
            self._indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        else:
            self._statusIcon.set_visible(False)

    def _iconChanged(self, joystickType, iconName):
        """Called when the indicator icon of the joystick type has changed."""
        if appIndicator:
            self._indicator.set_icon(joystickType.indicatorIconPath)
        else:
            self._statusIcon.set_from_file(joystickType.indicatorIconPath)

#-------------------------------------------------------------------------------
