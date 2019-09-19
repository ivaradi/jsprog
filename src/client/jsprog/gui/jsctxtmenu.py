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

        editMenuItem = Gtk.MenuItem.new_with_mnemonic(_("_Edit"))
        editMenuItem.connect("activate", self._editActivated)

        self.append(editMenuItem)

    def addProfile(self, profile):
        """Add a profile to the menu."""
        if self._firstProfileMenuItem is None:
            profileMenuItem = Gtk.RadioMenuItem()
            profileMenuItem.set_label(profile.name)
            self._firstProfileMenuItem = profileMenuItem
        else:
            profileMenuItem = \
                Gtk.RadioMenuItem.new_with_label_from_widget(self._firstProfileMenuItem,
                                                             profile.name)

        profileMenuItem.connect("activate", self._profileActivated, profile)
        profileMenuItem.show()

        if len(self._profileMenuItems)==0:
            separator = Gtk.SeparatorMenuItem()
            separator.show()
            self.insert(separator, 0)

        self.insert(profileMenuItem, len(self._profileMenuItems))

        self._profileMenuItems[profile] = profileMenuItem

    def setActive(self, profile):
        """Make the menu item belonging to the given profile active."""
        profileMenuItem = self._profileMenuItems[profile]
        profileMenuItem.set_active(True)

    def _editActivated(self, menuitem):
        """Called when the Edit menu item is activated."""
        self._gui.showTypeEditor(self._id)

    def _profileActivated(self, menuItem, profile):
        """Called when a menu item is activated"""
        if menuItem.get_active():
            self._gui.activateProfile(self._id, profile)

#----------------------------------------------------------------------------
