# The popover for the secondary menu for a joystick

#------------------------------------------------------------------------------

from .jsmenu import JSProfileMenuBase

from .common import *
from .common import _

#------------------------------------------------------------------------------

class JSSecondaryPopover(Gtk.Popover, JSProfileMenuBase):
    """The popover for the secondary menu of a joystick."""
    def __init__(self, joystick):
        """Construct the popover for the given joystick."""
        super().__init__()

        self.set_relative_to(joystick.gui.joysticksWindow.secondaryMenuButton)

        vbox = self._vbox = Gtk.VBox()
        vbox.set_margin_top(4)
        vbox.set_margin_bottom(4)
        vbox.set_margin_left(6)
        vbox.set_margin_right(6)
        self.add(vbox)

        title = self._title = Gtk.Label()
        title.set_markup("<b>" + joystick.identity.name + "</b>")
        vbox.pack_start(title, False, False, 0)

        alignment = Gtk.Alignment()
        alignment.set_margin_top(12)
        vbox.pack_start(alignment, True, True, 0)

        profilesFrame = self._profilesFrame = Gtk.Frame()
        profilesFrame.set_label(_("Profiles"))

        self._profilesBox = Gtk.VBox()
        self._profilesBox.set_margin_top(4)
        self._profilesBox.set_margin_bottom(2)
        self._profilesBox.set_margin_left(6)
        self._profilesBox.set_margin_right(6)
        profilesFrame.add(self._profilesBox)

        buttonBox = self._buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        buttonBox.set_layout(Gtk.ButtonBoxStyle.EXPAND)

        identityButtonBox = self._identityButtonBox = \
            Gtk.ButtonBox.new(Gtk.Orientation.VERTICAL)
        identityButtonBox.set_layout(Gtk.ButtonBoxStyle.EXPAND)

        JSProfileMenuBase.__init__(self, joystick)

        vbox.pack_end(identityButtonBox, False, False, 4)
        vbox.pack_end(buttonBox, False, False, 4)

        vbox.show_all()

    def setTitle(self, title):
        """Set the title of the popover."""
        self._title.set_markup("<b>" + title + "</b>")

    def _createEditWidgets(self):
        """Create the profiles and type edit buttons."""
        profilesEditButton = Gtk.Button.new_with_mnemonic(_("Edit _profiles"))
        profilesEditButton.set_tooltip_text(
            _("Edit the profiles belonging to a joystick."))

        self._buttonBox.pack_start(profilesEditButton, True, True, 0)

        editButton = Gtk.Button.new_with_mnemonic(_("_Edit"))
        editButton.set_tooltip_text(
            _("Edit the joystick type information."))

        self._buttonBox.pack_start(editButton, True, True, 0)

        return (profilesEditButton, editButton, "clicked")

    def _createIdentityCopyWidgets(self, version, phys, uniq):
        """Create the menu items to copy the various elements of the identity
        to the profile editor."""
        copyVersionButton = \
            Gtk.Button.new_with_mnemonic(_("_Version: %04x") % (version,))
        copyVersionButton.get_child().set_xalign(0.0)
        copyVersionButton.set_tooltip_text(_("Copy the version to the currently edited profile."))
        self._identityButtonBox.pack_start(copyVersionButton, True, True, 0)

        copyPhysButton = \
            Gtk.Button.new_with_mnemonic(_("Ph_ysical location: %s") % (phys,))
        copyPhysButton.get_child().set_xalign(0.0)
        copyPhysButton.set_tooltip_text(_("Copy the physical location to the currently edited profile."))
        self._identityButtonBox.pack_start(copyPhysButton, True, True, 0)

        copyUniqButton = None
        if uniq:
            copyUniqButton = \
                Gtk.Button.new_with_mnemonic(_("_Unique ID: %s") % (uniq,))
            copyUniqButton.get_child().set_xalign(0.0)
            copyUniqButton.set_tooltip_text(_("Copy the unique identifier to the currently edited profile."))
            self._identityButtonBox.pack_start(copyUniqButton, True, True, 0)

        return (copyVersionButton, copyPhysButton, copyUniqButton, "clicked")

    def _createProfileWidget(self, name):
        """Create a radio button for the given name."""
        profileButton = Gtk.RadioButton.new_with_label(None, name)
        profileButton.show()

        return (profileButton, "toggled")

    def _initiateFirstProfileWidget(self):
        """Pack the profile frame into the vbox."""
        self._vbox.pack_end(self._profilesFrame, False, False, 0)

    def _addProfileWidget(self, profileButton, position):
        """Add the given profile button at the given position."""
        self._profilesBox.pack_start(profileButton, False, False, 2)
        self._profilesBox.reorder_child(profileButton, position)

        self._vbox.show_all()

    def _moveProfileWidget(self, profileButton, oldIndex, index):
        """Move the profile button to the given new index."""
        self._profilesBox.remove(profileButton)
        self._profilesBox.pack_start(profileButton, False, False, 2)
        self._profilesBox.reorder_child(profileButton, index)

    def _removeProfileWidget(self, profileButton):
        """Remove the given profile button."""
        self._profilesBox.remove(profileButton)

    def _finalizeLastProfileWidget(self):
        """Remove the profiles frame from the vbox."""
        self._vbox.remove(self._profilesFrame)

#------------------------------------------------------------------------------
