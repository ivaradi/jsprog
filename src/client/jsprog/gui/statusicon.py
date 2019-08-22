
from .common import *
from .common import _

#-------------------------------------------------------------------------------

## @package jsprog.gui.statusicon
#
# The status icon.
#

#-------------------------------------------------------------------------------

class StatusIcon(object):
    """The class handling the status icon."""
    def __init__(self, id, name):
        """Construct the status icon."""
        self.gui = None
        self._id = id
        self._profileMenuItems = {}
        self._firstProfileMenuItem = None

        menu = self._menu = Gtk.Menu()

        nameMenuItem = Gtk.MenuItem()
        # FIXME: how to make the label bold
        nameMenuItem.set_label(name)
        nameMenuItem.show()
        menu.append(nameMenuItem)

        menu.show()

        # FIXME: find out the icon name properly
        #iconFile = os.path.join(iconDirectory, "logo.ico")
        iconFile = None
        for path in [os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  "joystick.png"))]:
            if os.path.exists(path):
                iconFile = path
                break

        if appIndicator:
            # FIXME: do we need a unique name here?
            indicator = AppIndicator3.Indicator.new ("jsprog-%d" % (id,), iconFile,
                                                     AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            indicator.set_status (AppIndicator3.IndicatorStatus.ACTIVE)

            indicator.set_menu(menu)
            self._indicator = indicator
        else:
            def popup_menu(status, button, time):
                menu.popup(None, None, Gtk.status_icon_position_menu,
                           button, time, status)

            statusIcon = Gtk.StatusIcon()
            statusIcon.set_from_file(iconFile)
            statusIcon.set_visible(True)
            statusIcon.connect('popup-menu', popup_menu)
            self._statusIcon = statusIcon

    def addProfile(self, gui, profile):
        """Add a menu item and action for the given profile"""
        if self._firstProfileMenuItem is None:
            profileMenuItem = Gtk.RadioMenuItem()
            profileMenuItem.set_label(profile.name)
        else:
            profileMenuItem = \
                Gtk.RadioMenuItem.new_with_label_from_widget(self._firstProfileMenuItem,
                                                             profile.name)
        profileMenuItem.connect("activate", self._profileActivated, profile)
        profileMenuItem.show()

        if self._firstProfileMenuItem is None:
            self._firstProfileMenuItem = profileMenuItem

            separator = Gtk.SeparatorMenuItem()
            separator.show()
            self._menu.append(separator)

        self._menu.append(profileMenuItem)

        self._profileMenuItems[profile] = profileMenuItem

    def finalize(self, gui):
        """Finalize the menu."""

        separator = Gtk.SeparatorMenuItem()
        separator.show()
        self._menu.append(separator)

        quitMenuItem = Gtk.MenuItem()
        quitMenuItem.set_label(_("Quit"))
        quitMenuItem.connect("activate", lambda mi: gui.quit())
        quitMenuItem.show()
        self._menu.append(quitMenuItem)

    def setActive(self, profile):
        """Make the menu item belonging to the given profile
        active."""
        profileMenuItem = self._profileMenuItems[profile]
        profileMenuItem.set_active(True)

    def destroy(self):
        """Hide and destroy the status icon."""
        if appIndicator:
            self._indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        else:
            self._statusIcon.set_visible(False)

    def _profileActivated(self, menuItem, profile):
        """Called when a menu item is activated"""
        if menuItem.get_active():
            self.gui.loadProfile(self._id, profile)

#-------------------------------------------------------------------------------
