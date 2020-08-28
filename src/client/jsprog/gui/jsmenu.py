# Base class for joystick menus

#----------------------------------------------------------------------------

from .common import *
from .common import _

#-----------------------------------------------------------------------------------

class JSProfileMenuBase(object):
    """Base class for joystick profile menus.

    It contains some of the common logic used by the various menus associated
    with a joystick, i.e. status icon menu, the joystick context menu and the
    secondary popover."""
    def __init__(self, joystick):
        super().__init__()

        self._id = joystick.id
        self._gui = joystick.gui

        self._firstProfileWidget = None
        self._profileWidgets = {}

        profileList = joystick.profileList
        profileList.connect("profile-added", self._profileAdded)
        profileList.connect("profile-renamed", self._profileRenamed)
        profileList.connect("profile-removed", self._profileRemoved)

        (profilesEditWidget, editWidget, signal) = self._createEditWidgets()
        profilesEditWidget.connect(signal, self._editProfilesActivated)
        editWidget.connect(signal, self._editActivated)

    # FIXME: very similar logic in all the menus (status icon, popover)
    def _profileAdded(self, profileList, profile, name, position):
        """Add a profile to the menu."""
        (profileWidget, signal) = self._createProfileWidget(name)
        profileWidget.connect(signal, self._profileActivated, profile)

        if self._firstProfileWidget is None:
            self._firstProfileWidget = profileWidget
            self._initiateFirstProfileWidget()
        else:
            profileWidget.join_group(self._firstProfileWidget)

        self._addProfileWidget(profileWidget, position)

        self._profileWidgets[profile] = profileWidget

    def _profileRenamed(self, profileList, profile, name, oldIndex, index):
        """Called when a profile is renamed."""
        profileWidget = self._profileWidgets[profile]
        profileWidget.set_label(name)
        if oldIndex!=index:
            self._moveProfileWidget(profileWidget, oldIndex, index)

    def _profileRemoved(self, profileList, profile, index):
        """Called when a profile is removed."""
        profileWidget = self._profileWidgets[profile]
        self._removeProfileWidget(profileWidget)
        del self._profileWidgets[profile]

        if profileWidget is self._firstProfileWidget:
            self._firstProfileWidget = None
            for i in self._profileWidgets.values():
                self._firstProfileWidget = i
                break

            if self._firstProfileWidget is None:
                self._finalizeLastProfileWidget()

    def setActive(self, profile):
        """Make the profile widget belonging to the given profile active."""
        profileWidget = self._profileWidgets[profile]
        profileWidget.set_active(True)

    def _editProfilesActivated(self, menuitem):
        """Called when the Edit profiles menu item is activated."""
        self._gui.showProfilesEditor(self._id)

    def _editActivated(self, menuitem):
        """Called when the Edit menu item is activated."""
        self._gui.showTypeEditor(self._id)

    def _profileActivated(self, profileWidget, profile):
        """Called when a menu item is activated"""
        if profileWidget.get_active():
            self._gui.activateProfile(self._id, profile)

#-----------------------------------------------------------------------------------

class JSMenu(Gtk.Menu, JSProfileMenuBase):
    """A menu for a joystick."""
    def __init__(self, joystick, profileMenuItemOffset = 0):
        super().__init__()
        JSProfileMenuBase.__init__(self, joystick)

        self._id = joystick.id
        self._gui = joystick.gui

        self._profileMenuItemOffset = profileMenuItemOffset
        self._profileSeparator = None

    def _createEditWidgets(self):
        """Create the menu items for editing."""
        editProfilesMenuItem = Gtk.MenuItem.new_with_mnemonic(_("Edit _profiles"))
        self.append(editProfilesMenuItem)
        editProfilesMenuItem.show()

        separator = Gtk.SeparatorMenuItem()
        self.append(separator)
        separator.show()

        editMenuItem = Gtk.MenuItem.new_with_mnemonic(_("_Edit"))
        self.append(editMenuItem)
        editMenuItem.show()

        return (editProfilesMenuItem, editMenuItem, "activate")

    def _createProfileWidget(self, name):
        """Create a profile menu item for the given name."""
        profileMenuItem = Gtk.RadioMenuItem(name)
        profileMenuItem.show()

        return (profileMenuItem, "activate")

    def _initiateFirstProfileWidget(self):
        """Add the separator for the first profile menu item."""
        separator = self._profileSeparator = Gtk.SeparatorMenuItem()
        separator.show()
        self.insert(separator,
                    0 if self._profileMenuItemOffset==0 else
                    self._profileMenuItemOffset - 1)

    def _addProfileWidget(self, profileMenuItem, position):
        """Add the profile widget at the given position."""
        self.insert(profileMenuItem, position + self._profileMenuItemOffset)

    def _moveProfileWidget(self, profileMenuItem, oldIndex, index):
        """Move the profile menu item to the given new index."""
        if self._profileMenuItemOffset>0 and oldIndex<index:
            index += 1
        self.remove(profileMenuItem)
        self.insert(profileMenuItem, index + self._profileMenuItemOffset)

    def _removeProfileWidget(self, profileMenuItem):
        """Remove the given profile menu item."""
        self.remove(profileMenuItem)

    def _finalizeLastProfileWidget(self):
        """Remove the profile menu item separator."""
        self.remove(self._profileSeparator)
        self._profileSeparator = None
