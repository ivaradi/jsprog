
from statusicon import StatusIcon

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

    @property
    def statusIcon(self):
        """Get the status icon of the joystick."""
        return self._statusIcon

    def destroy(self):
        """Destroy the joystick."""
        self._statusIcon.destroy();
