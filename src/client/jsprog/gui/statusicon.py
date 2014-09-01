
from common import *

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

        menu = self._menu = gtk.Menu()

        nameMenuItem = gtk.MenuItem()
        # FIXME: how to make the label bold
        nameMenuItem.set_label(name)
        nameMenuItem.show()
        menu.append(nameMenuItem)

        menu.show()

        # FIXME: find out the icon name properly
        #iconFile = os.path.join(iconDirectory, "logo.ico")
        iconFile = "/home/vi/munka/jsprog/src/client/logo.ico"

        if appIndicator:
            if pygobject:
                # FIXME: do we need a unique name here?
                indicator = appindicator.Indicator.new ("jsprog-%d" % (id,), iconFile,
                                                        appindicator.IndicatorCategory.APPLICATION_STATUS)
                indicator.set_status (appindicator.IndicatorStatus.ACTIVE)
            else:
                indicator = appindicator.Indicator ("jsprog-%d" % (id,), iconFile,
                                                    appindicator.CATEGORY_APPLICATION_STATUS)
                indicator.set_status (appindicator.STATUS_ACTIVE)

            indicator.set_menu(menu)
            self._indicator = indicator
        else:
            def popup_menu(status, button, time):
                menu.popup(None, None, gtk.status_icon_position_menu,
                           button, time, status)

            statusIcon = gtk.StatusIcon()
            statusIcon.set_from_file(iconFile)
            statusIcon.set_visible(True)
            statusIcon.connect('popup-menu', popup_menu)
            self._statusIcon = statusIcon

    def addProfile(self, gui, profile):
        """Add a menu item and action for the given profile"""
        if pygobject:
            if self._firstProfileMenuItem is None:
                profileMenuItem = gtk.RadioMenuItem()
                profileMenuItem.set_label(profile.name)
            else:
                profileMenuItem = \
                    gtk.RadioMenuItem.new_with_label_from_widget(self._firstProfileMenuItem,
                                                                 profile.name)
        else:
            profileMenuItem = \
                gtk.RadioMenuItem(self._firstProfileMenuItem, profile.name)
        profileMenuItem.connect("activate", self._profileActivated, profile)
        profileMenuItem.show()

        if self._firstProfileMenuItem is None:
            self._firstProfileMenuItem = profileMenuItem

            separator = gtk.SeparatorMenuItem()
            separator.show()
            self._menu.append(separator)

        self._menu.append(profileMenuItem)

        self._profileMenuItems[profile] = profileMenuItem

    def finalize(self, gui):
        """Finalize the menu."""

        separator = gtk.SeparatorMenuItem()
        separator.show()
        self._menu.append(separator)

        quitMenuItem = gtk.MenuItem()
        quitMenuItem.set_label("Quit")
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
            if pygobject:
                self._indicator.set_status(appindicator.IndicatorStatus.PASSIVE)
            else:
                self._indicator.set_status(appindicator.STATUS_PASSIVE)
        else:
            self._statusIcon.set_visible(False)

    def _profileActivated(self, menuItem, profile):
        """Called when a menu item is activated"""
        if menuItem.get_active():
            self.gui.loadProfile(self._id, profile)

#-------------------------------------------------------------------------------
