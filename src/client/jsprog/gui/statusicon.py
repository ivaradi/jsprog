
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
    def __init__(self, id, joystick, gui):
        """Construct the status icon."""
        self._gui = gui
        self._id = id
        self._profileMenuItems = {}
        self._firstProfileMenuItem = None
        self._profileSeparator = None

        profileList = joystick.profileList
        profileList.connect("profile-added", self._profileAdded)
        profileList.connect("profile-renamed", self._profileRenamed)
        profileList.connect("profile-removed", self._profileRemoved)

        name = joystick.identity.name

        menu = self._menu = Gtk.Menu()

        nameMenuItem = self._nameMenuItem = Gtk.MenuItem()
        # FIXME: how to make the label bold
        nameMenuItem.set_label(name)
        nameMenuItem.show()
        menu.append(nameMenuItem)

        separator = Gtk.SeparatorMenuItem()
        separator.show()
        self._menu.append(separator)

        editProfilesMenuItem = Gtk.MenuItem()
        editProfilesMenuItem.set_label(_("Edit profiles"))
        editProfilesMenuItem.connect("activate", self._editProfiles, gui)
        editProfilesMenuItem.show()
        self._menu.append(editProfilesMenuItem)

        editMenuItem = Gtk.MenuItem()
        editMenuItem.set_label(_("Edit"))
        editMenuItem.connect("activate", self._edit, gui)
        editMenuItem.show()
        self._menu.append(editMenuItem)

        separator = Gtk.SeparatorMenuItem()
        separator.show()
        self._menu.append(separator)

        quitMenuItem = Gtk.MenuItem()
        quitMenuItem.set_label(_("Quit"))
        quitMenuItem.connect("activate", self._quit, gui)
        quitMenuItem.show()
        self._menu.append(quitMenuItem)

        menu.show()

        # FIXME: find out the icon name properly
        #iconFile = os.path.join(iconDirectory, "logo.ico")
        iconFile = joystick.type.indicatorIconName
        for path in [os.path.join(pkgdatadir, "icons",
                                  joystick.type.indicatorIconName),
                     os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
                                                  "misc",
                                                  joystick.type.indicatorIconName))]:
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

    def setName(self, name):
        """Set the label of the name menu item to the given value."""
        self._nameMenuItem.set_label(name)

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

    def _profileAdded(self, profileList, profile, name, position):
        """Called when a profile is added that is valid to the joystick."""
        profileMenuItem = Gtk.RadioMenuItem(name)
        profileMenuItem.connect("activate", self._profileActivated, profile)
        profileMenuItem.show()

        if self._firstProfileMenuItem is None:
            self._firstProfileMenuItem = profileMenuItem
            separator = self._profileSeparator = Gtk.SeparatorMenuItem()
            separator.show()
            self._menu.insert(separator, 1)
        else:
            profileMenuItem.join_group(self._firstProfileMenuItem)

        self._menu.insert(profileMenuItem, 2+position)

        self._profileMenuItems[profile] = profileMenuItem

    def _profileRenamed(self, profileList, profile, name, oldIndex, index):
        """Called when a profile is renamed."""
        profileMenuItem = self._profileMenuItems[profile]
        profileMenuItem.set_label(name)
        if oldIndex!=index:
            # FIXME: why this is needed here and not in the joystick popup menu?
            if oldIndex<index:
                index += 1
            self._menu.remove(profileMenuItem)
            self._menu.insert(profileMenuItem, 2+index)

    def _profileRemoved(self, profileList, profile, index):
        """Called when a profile is removed."""
        profileMenuItem = self._profileMenuItems[profile]
        self._menu.remove(profileMenuItem)
        del self._profileMenuItems[profile]

        if profileMenuItem is self._firstProfileMenuItem:
            self._firstProfileMenuItem = None
            for i in self._profileMenuItems.values():
                self._firstProfileMenuItem = i
                break

            if self._firstProfileMenuItem is None:
                self._menu.remove(self._profileSeparator)
                self._profileSeparator = None

    def _profileActivated(self, menuItem, profile):
        """Called when a menu item is activated"""
        if menuItem.get_active():
            self._gui.activateProfile(self._id, profile)

    def _editProfiles(self, mi, gui):
        """Called when the Edit profiles menu item is activated."""
        gui.showProfilesEditor(self._id)

    def _edit(self, mi, gui):
        """Called when the Edit menu item is activated."""
        gui.showTypeEditor(self._id)

    def _quit(self, mi, gui):
        """Called when the Quit menu item is activated."""
        gui.quit()

#-------------------------------------------------------------------------------
