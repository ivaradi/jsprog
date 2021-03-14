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

        self._joystick = joystick
        self._joystickType = joystickType = joystick.type
        self._id = joystick.id
        self._gui = joystick.gui

        self._firstProfileWidget = None
        self._profileWidgets = {}
        self._activeProfile = None
        self._activeProfileModified = False

        self._gui.connect("editing-profile", self._editingProfile)

        profileList = joystick.profileList
        profileList.connect("profile-added", self._profileAdded)
        profileList.connect("profile-renamed", self._profileRenamed)
        profileList.connect("profile-removed", self._profileRemoved)

        joystickType.connect("profile-modified", self._profileModified)

        (profilesEditWidget, editWidget, signal) = self._createEditWidgets()
        profilesEditWidget.connect(signal, self._editProfilesActivated)
        editWidget.connect(signal, self._editActivated)

        identity = joystick.identity
        version = identity.inputID.version
        phys = identity.phys
        uniq = identity.uniq

        (versionCopyWidget, physCopyWidget, uniqCopyWidget, signal) = \
            self._createIdentityCopyWidgets(version, phys, uniq)
        self._versionCopyWidget = versionCopyWidget
        self._physCopyWidget = physCopyWidget
        self._uniqCopyWidget = uniqCopyWidget

        editingProfile = self._gui.getEditedProfile(joystick.type) is not None

        versionCopyWidget.connect(signal, self._versionCopyActivated)
        versionCopyWidget.set_sensitive(editingProfile)

        physCopyWidget.connect(signal, self._physCopyActivated)
        physCopyWidget.set_sensitive(editingProfile)

        if uniqCopyWidget is not None:
            uniqCopyWidget.connect(signal, self._uniqCopyActivated)
            uniqCopyWidget.set_sensitive(editingProfile)

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

        self._profileWidgets[profile] = (profileWidget, name)
        self._updateProfileNameDisplay(profile)

    def _profileRenamed(self, profileList, profile, name, oldIndex, index):
        """Called when a profile is renamed."""
        (profileWidget, _oldName) = self._profileWidgets[profile]
        self._profileWidgets[profile] = (profileWidget, name)
        self._updateProfileNameDisplay(profile)

        if oldIndex!=index:
            self._moveProfileWidget(profileWidget, oldIndex, index)

    def _profileModified(self, joystickType, profile):
        """Called when the given profile is modified.

        If it is the active profile, and it is not yet marked as modified, it
        will be so."""
        if profile is self._activeProfile and not self._activeProfileModified:
            self._activeProfileModified = True
            self._updateProfileNameDisplay(profile)

    def _profileRemoved(self, profileList, profile, index):
        """Called when a profile is removed."""
        if self._activeProfile is profile:
            self._activeProfile = None
            self._activeProfileModified = False

        (profileWidget, _name) = self._profileWidgets[profile]
        self._removeProfileWidget(profileWidget)
        del self._profileWidgets[profile]

        if profileWidget is self._firstProfileWidget:
            self._firstProfileWidget = None
            for (i, _name) in self._profileWidgets.values():
                self._firstProfileWidget = i
                break

            if self._firstProfileWidget is None:
                self._finalizeLastProfileWidget()

    def setActive(self, profile):
        """Make the profile widget belonging to the given profile active."""
        oldActiveProfile = self._activeProfile

        (profileWidget, _name) = self._profileWidgets[profile]
        profileWidget.set_active(True)

        self._activeProfile = profile
        self._activeProfileModified = False

        if profile is not oldActiveProfile:
            self._updateProfileNameDisplay(oldActiveProfile)
        self._updateProfileNameDisplay(profile)

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

    def _versionCopyActivated(self, menuitem):
        """Called when the version copy widget is activated."""
        self._gui.copyVersion(self._joystickType,
                              self._joystick.identity.inputID.version)

    def _physCopyActivated(self, menuitem):
        """Called when the widget to copy the joystick's physical location is
        activated."""
        self._gui.copyPhys(self._joystickType,
                           self._joystick.identity.phys)

    def _uniqCopyActivated(self, menuitem):
        """Called when the widget to copy the joystick's unique identifier is
        activated."""
        self._gui.copyUniq(self._joystickType,
                           self._joystick.identity.uniq)

    def _editingProfile(self, gui, joystickType, profile):
        """Called when the profile being edited has changed."""
        if joystickType is self._joystickType:
            editingProfile = profile is not None
            self._versionCopyWidget.set_sensitive(editingProfile)
            self._physCopyWidget.set_sensitive(editingProfile)
            if self._uniqCopyWidget is not None:
                self._uniqCopyWidget.set_sensitive(editingProfile)

    def _updateProfileNameDisplay(self, profile):
        """Update the display of the name of the given profile."""
        if profile is not None:
            (profileWidget, name) = self._profileWidgets[profile]
            if profile is self._activeProfile and self._activeProfileModified:
                markup = self._getModifiedProfileNameMarkup(name)
                profileWidget.get_child().set_markup(markup)
                profileWidget.set_tooltip_text(
                    _("This is the currently downloaded profile, "
                      "but it has been modified since it was downloaded. "
                      "Download it again to make the changes effective."))
            else:
                profileWidget.get_child().set_markup(name)
                if profile is self._activeProfile:
                    profileWidget.set_tooltip_text(
                        _("This is the currently downloaded profile."))
                else:
                    profileWidget.set_tooltip_text(
                        _("Select the profile to download it to the joystick."))

    def _getModifiedProfileNameMarkup(self, name):
        """Convert the given name into a markup representing that the
        corresponding profile has been modified since downloaded.

        This default implementation puts the name between <i> tags."""
        return "<i>" + name + "</i>"

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
        editProfilesMenuItem.set_tooltip_text(
            _("Edit the profiles belonging to a joystick."))
        self.append(editProfilesMenuItem)
        editProfilesMenuItem.show()

        separator = Gtk.SeparatorMenuItem()
        self.append(separator)
        separator.show()

        editMenuItem = Gtk.MenuItem.new_with_mnemonic(_("_Edit"))
        editMenuItem.set_tooltip_text(
            _("Edit the joystick type information."))
        self.append(editMenuItem)
        editMenuItem.show()

        return (editProfilesMenuItem, editMenuItem, "activate")

    def _createIdentityCopyWidgets(self, version, phys, uniq):
        """Create the menu items to copy the various elements of the identity
        to the profile editor."""
        separator = Gtk.SeparatorMenuItem()
        self.append(separator)
        separator.show()

        copyVersionMenuItem = \
            Gtk.MenuItem.new_with_mnemonic(_("_Version: %04x") % (version,))
        copyVersionMenuItem.set_tooltip_text(_("Copy the version to the currently edited profile."))
        self.append(copyVersionMenuItem)
        copyVersionMenuItem.show()

        copyPhysMenuItem = \
            Gtk.MenuItem.new_with_mnemonic(_("_Physical location: %s") % (phys,))
        copyPhysMenuItem.set_tooltip_text(_("Copy the physical location to the currently edited profile."))
        self.append(copyPhysMenuItem)
        copyPhysMenuItem.show()

        copyUniqMenuItem = None
        if uniq:
            copyUniqMenuItem = \
                Gtk.MenuItem.new_with_mnemonic(_("_Unique ID: %s") % (uniq,))
            copyUniqMenuItem.set_tooltip_text(_("Copy the unique identifier to the currently edited profile."))
            self.append(copyUniqMenuItem)
            copyUniqMenuItem.show()

        return (copyVersionMenuItem, copyPhysMenuItem, copyUniqMenuItem, "activate")

    def _createProfileWidget(self, name):
        """Create a profile menu item for the given name."""
        profileMenuItem = Gtk.RadioMenuItem.new_with_label(None, name)
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
