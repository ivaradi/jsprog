# Context menu for a joystick

#----------------------------------------------------------------------------

from .common import *
from .common import _

#----------------------------------------------------------------------------

class JSContextMenu(Gtk.Menu):
    """Context menu for a joystick."""
    def __init__(self, joystick):
        """Construct the menu."""
        super().__init__()

        self._id = joystick.id
        self._gui = joystick.gui

        self._firstProfileMenuItem = None
        self._profileMenuItems = {}
        self._profileSeparator = None

        profileList = joystick.profileList
        profileList.connect("profile-added", self._profileAdded)
        profileList.connect("profile-renamed", self._profileRenamed)
        profileList.connect("profile-removed", self._profileRemoved)

        editProfilesMenuItem = Gtk.MenuItem.new_with_mnemonic(_("Edit _profiles"))
        editProfilesMenuItem.connect("activate", self._editProfilesActivated)
        self.append(editProfilesMenuItem)

        separator = Gtk.SeparatorMenuItem()
        separator.show()
        self.append(separator)

        editMenuItem = Gtk.MenuItem.new_with_mnemonic(_("_Edit"))
        editMenuItem.connect("activate", self._editActivated)
        self.append(editMenuItem)

    # FIXME: very similar logic in all the menus (status icon, popover)
    def _profileAdded(self, profileList, profile, name, position):
        """Add a profile to the menu."""
        profileMenuItem = Gtk.RadioMenuItem(name)
        profileMenuItem.connect("activate", self._profileActivated, profile)
        profileMenuItem.show()

        if self._firstProfileMenuItem is None:
            self._firstProfileMenuItem = profileMenuItem
            separator = self._profileSeparator = Gtk.SeparatorMenuItem()
            separator.show()
            self.insert(separator, 0)
        else:
            profileMenuItem.join_group(self._firstProfileMenuItem)

        self.insert(profileMenuItem, position)

        self._profileMenuItems[profile] = profileMenuItem

    def _profileRenamed(self, profileList, profile, name, oldIndex, index):
        """Called when a profile is renamed."""
        profileMenuItem = self._profileMenuItems[profile]
        profileMenuItem.set_label(name)
        if oldIndex!=index:
            self.remove(profileMenuItem)
            self.insert(profileMenuItem, index)

    def _profileRemoved(self, profileList, profile, index):
        """Called when a profile is removed."""
        profileMenuItem = self._profileMenuItems[profile]
        self.remove(profileMenuItem)
        del self._profileMenuItems[profile]

        if profileMenuItem is self._firstProfileMenuItem:
            self._firstProfileMenuItem = None
            for i in self._profileMenuItems.values():
                self._firstProfileMenuItem = i
                break

            if self._firstProfileMenuItem is None:
                self.remove(self._profileSeparator)
                self._profileSeparator = None

    def setActive(self, profile):
        """Make the menu item belonging to the given profile active."""
        profileMenuItem = self._profileMenuItems[profile]
        profileMenuItem.set_active(True)

    def _editProfilesActivated(self, menuitem):
        """Called when the Edit profiles menu item is activated."""
        self._gui.showProfilesEditor(self._id)

    def _editActivated(self, menuitem):
        """Called when the Edit menu item is activated."""
        self._gui.showTypeEditor(self._id)

    def _profileActivated(self, menuItem, profile):
        """Called when a menu item is activated"""
        if menuItem.get_active():
            self._gui.activateProfile(self._id, profile)

#----------------------------------------------------------------------------
