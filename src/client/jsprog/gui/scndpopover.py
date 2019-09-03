# The popover for the secondary menu for a joystick

#------------------------------------------------------------------------------

from .common import *
from .common import _

#------------------------------------------------------------------------------

class JSSecondaryPopover(Gtk.Popover):
    """The popover for the secondary menu of a joystick."""
    def __init__(self, joystick):
        """Construct the popover for the given joystick."""
        super().__init__()

        self.set_relative_to(joystick.gui.joysticksWindow.secondaryMenuButton)

        self._id = joystick.id
        self._gui = joystick.gui

        vbox = self._vbox = Gtk.VBox()
        vbox.set_margin_top(4)
        vbox.set_margin_bottom(4)
        vbox.set_margin_left(6)
        vbox.set_margin_right(6)
        self.add(vbox)

        title = Gtk.Label()
        title.set_markup("<b>" + joystick.identity.name + "</b>")
        vbox.pack_start(title, False, False, 0)

        alignment = Gtk.Alignment()
        alignment.set_margin_top(12)
        vbox.pack_start(alignment, True, True, 0)

        profilesFrame = Gtk.Frame()
        profilesFrame.set_label(_("Profiles"))

        self._profilesBox = Gtk.VBox()
        self._profilesBox.set_margin_top(4)
        self._profilesBox.set_margin_bottom(2)
        self._profilesBox.set_margin_left(6)
        self._profilesBox.set_margin_right(6)
        profilesFrame.add(self._profilesBox)

        vbox.pack_start(profilesFrame, False, False, 0)

        self._firstProfileButton = None
        self._profileButtons = {}

    def addProfile(self, profile):
        """Add the given profile to the poporver."""
        if self._firstProfileButton is None:
            profileButton = \
                Gtk.RadioButton.new_with_label(None, profile.name)
            self._firstProfileButton = profileButton
        else:
            profileButton = \
                Gtk.RadioButton.new_with_label_from_widget(self._firstProfileButton,
                                                           profile.name)

        profileButton.connect("toggled", self._profileActivated, profile)
        self._profileButtons[profile] = profileButton
        self._profilesBox.pack_start(profileButton, False, False, 2)

        self._vbox.show_all()

    def setActive(self, profile):
        """Set the given profile active."""
        print("setActive0")
        profileButton = self._profileButtons[profile]
        profileButton.set_active(True)

    def _profileActivated(self, profileButton, profile):
        """Called when the activation state of a profile button is changed."""
        if profileButton.get_active():
            self._gui.activateProfile(self._id, profile)

#------------------------------------------------------------------------------
