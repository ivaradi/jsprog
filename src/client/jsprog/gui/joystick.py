
from .statusicon import StatusIcon
from .jswindow import JSWindow
from .scndpopover import JSSecondaryPopover
from .jsctxtmenu import JSContextMenu
from .common import *

import jsprog.joystick
from jsprog.device import JoystickType
from jsprog.profile import Profile

#------------------------------------------------------------------------------

## @package jsprog.gui.joystick
#
# The GUI-specific representation of joysticks

#-----------------------------------------------------------------------------

class Joystick(jsprog.joystick.Joystick):
    """A joystick on the GUI."""
    # The name of the joystick type descriptor file
    typeDescriptorName = "type.xml"

    def __init__(self, id, identity, keys, axes, gui):
        """Construct the joystick with the given attributes."""
        super(Joystick, self).__init__(id, identity, keys, axes)

        self._gui = gui

        self._type = JoystickType(identity)

        self._statusIcon = StatusIcon(id, self, gui)

        iconTheme = Gtk.IconTheme.get_default()
        icon = iconTheme.load_icon("gtk-preferences", 64, 0)
        self._iconRef = JSWindow.get().addJoystick(self, icon, identity.name)

        self._profiles = {}
        self._autoLoadProfile = None

        self._popover = None

        self._contextMenu = None

    @property
    def type(self):
        """Get the type descriptor for this joystick."""
        return self._type

    @property
    def statusIcon(self):
        """Get the status icon of the joystick."""
        return self._statusIcon

    @property
    def autoLoadProfile(self):
        """Get the profile to load automatically."""
        return self._autoLoadProfile

    @property
    def popover(self):
        """Get the popover for the secondary menu."""
        return self._popover

    @property
    def contextMenu(self):
        """Get the context menu for the joystick."""
        return self._contextMenu

    @property
    def gui(self):
        """Get the GUI object the joystick belongs to."""
        return self._gui

    @property
    def deviceSubdirectoryName(self):
        """Get the name of device-specific subdirectory for this joystick."""
        inputID = self._identity.inputID
        return "%sV%04xP%04x" % (inputID.busName, inputID.vendor,
                                 inputID.product)

    @property
    def deviceDirectories(self):
        """Get an iterator over the directories potentially containing files
        related to this device.

        Each item is a tuple of:
        - the path of the directory
        - the type of the directory as a string (see GUI.dataDirectories)
        """
        subdirectoryName = self.deviceSubdirectoryName
        for (path, directoryType) in self._gui.dataDirectories:
            yield (os.path.join(path, "devices", subdirectoryName),
                   directoryType)

    def load(self):
        """Load the various files related to this joystick."""
        self.loadType()
        self.loadProfiles()

    def loadType(self):
        """Load the type descriptor for this joystick."""
        for (path, directoryType) in self.deviceDirectories:
            typeDescriptorPath = os.path.join(path, self.typeDescriptorName)
            if os.path.isfile(typeDescriptorPath):
                type = JoystickType.fromFile(typeDescriptorPath)
                if type is not None:
                    print("Loaded joystick type from", typeDescriptorPath)
                    type.userDefined = directoryType=="user"
                    self._type = type
                    break

    def loadProfiles(self):
        """Load the profiles for this joystick."""
        self._profiles = {}

        self._autoLoadProfile = None
        autoLoadCandidateScore = 0

        for (path, directoryType) in self.deviceDirectories:
            if os.path.isdir(path):
                for profile in Profile.loadFrom(path):
                    score = profile.match(self._identity)
                    if score>0:
                        name = profile.name
                        if name in self._profiles:
                            print("A profile with name '%s' already exists, ignoring the one from directory %s" % (name, path), file = sys.stderr)
                            continue

                        self._profiles[name] = profile
                        profile.userDefined = directoryType=="user"

                        self._statusIcon.addProfile(profile)

                        if self._popover is None:
                            self._popover = JSSecondaryPopover(self)
                        self._popover.addProfile(profile)

                        if self._contextMenu is None:
                            self._contextMenu = JSContextMenu(self)
                        self._contextMenu.addProfile(profile)

                        if profile.autoLoad and score>autoLoadCandidateScore:
                            self._autoLoadProfile = profile
                            autoLoadCandidateScore = score


    def setActiveProfile(self, profile):
        """Make the given profile active."""
        self._statusIcon.setActive(profile)
        self._popover.setActive(profile)
        self._contextMenu.setActive(profile)

    def destroy(self):
        """Destroy the joystick."""
        self._statusIcon.destroy()
        JSWindow.get().removeJoystick(self._iconRef)
