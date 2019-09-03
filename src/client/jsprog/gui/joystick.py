
from .statusicon import StatusIcon
from .jswindow import JSWindow
from .common import *

import jsprog.joystick
from jsprog.device import JoystickType

#------------------------------------------------------------------------------

## @package jsprog.gui.joystick
#
# The GUI-specific representation of joysticks

#-----------------------------------------------------------------------------

class Joystick(jsprog.joystick.Joystick):
    """A joystick on the GUI."""
    def __init__(self, id, identity, keys, axes, gui):
        """Construct the joystick with the given attributes."""
        super(Joystick, self).__init__(id, identity, keys, axes)

        self._type = JoystickType(identity)

        self._statusIcon = StatusIcon(id, self, gui)

        iconTheme = Gtk.IconTheme.get_default()
        icon = iconTheme.load_icon("gtk-preferences", 64, 0)
        self._iconRef = JSWindow.get().addJoystick(self, icon, identity.name)

        self._profiles = []
        self._autoLoadProfile = None

    @property
    def type(self):
        """Get the type descriptor for this joystick."""
        return self._type

    @property
    def statusIcon(self):
        """Get the status icon of the joystick."""
        return self._statusIcon

    @property
    def profiles(self):
        """Get an iterator over the profiles of the joystick."""
        return iter(self._profiles)

    @property
    def autoLoadProfile(self):
        """Get the profile to load automatically."""
        return self._autoLoadProfile

    def selectProfiles(self, gui):
        """Traverse the list of profiles of the given GUI object and select the
        ones that match this joystick.

        The status icon menu items will also be setup."""
        self._profiles = []
        self._autoLoadProfile = None
        autoLoadCandidateScore = 0
        for profile in gui.profiles:
            score = profile.match(self.identity)
            if score>0:
                self._profiles.append(profile)
                self._statusIcon.addProfile(profile)
                if profile.autoLoad and score>autoLoadCandidateScore:
                    self._autoLoadProfile = profile
                    autoLoadCandidateScore = score

    def setActiveProfile(self, profile):
        """Make the given profile active."""
        self._statusIcon.setActive(profile)

    def destroy(self):
        """Destroy the joystick."""
        self._statusIcon.destroy()
        JSWindow.get().removeJoystick(self._iconRef)
