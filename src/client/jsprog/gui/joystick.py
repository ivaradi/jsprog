
from .statusicon import StatusIcon
from .jswindow import JSWindow
from .common import *

import jsprog.joystick

#------------------------------------------------------------------------------

## @package jsprog.gui.joystick
#
# The GUI-specific representation of joysticks

#-----------------------------------------------------------------------------

class Joystick(jsprog.joystick.Joystick):
    """A joystick on the GUI."""
    def __init__(self, id, identity, keys, axes):
        """Construct the joystick with the given attributes."""
        super(Joystick, self).__init__(id, identity, keys, axes)
        self._statusIcon = StatusIcon(id, identity.name)

        iconTheme = Gtk.IconTheme.get_default()
        icon = iconTheme.load_icon("gtk-preferences", 64, 0)
        self._iconRef = JSWindow.get().addJoystick(icon, identity.name)

    @property
    def statusIcon(self):
        """Get the status icon of the joystick."""
        return self._statusIcon

    def destroy(self):
        """Destroy the joystick."""
        self._statusIcon.destroy();
        JSWindow.get().removeJoystick(self._iconRef)
