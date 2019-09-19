
from .statusicon import StatusIcon
from .jswindow import JSWindow
from .scndpopover import JSSecondaryPopover
from .jsctxtmenu import JSContextMenu
from .common import *
from .common import _

import jsprog.joystick
import jsprog.device
from jsprog.profile import Profile

#------------------------------------------------------------------------------

## @package jsprog.gui.joystick
#
# The GUI-specific representation of joysticks

#-----------------------------------------------------------------------------

class JoystickType(jsprog.device.JoystickType):
    """A joystick type descriptor.

    This class maintains a registry for joystick types based on their input
    IDs. It also contains the profiles defined for that certain joystick
    type."""
    # The name of the joystick type descriptor file
    _typeDescriptorName = "type.xml"

    # A mapping of input IDs to joystick type instances
    _instances = {}

    @staticmethod
    def get(gui, identity):
        """Get the joystick type for the given identity."""
        inputID = identity.inputID
        if inputID not in JoystickType._instances:
            print("Creating new joystick type for %s" % (identity,))
            joystickType = None
            for (path, directoryType) in JoystickType.getDeviceDirectories(gui,
                                                                           identity):
                typeDescriptorPath = os.path.join(path,
                                                  JoystickType._typeDescriptorName)
                if os.path.isfile(typeDescriptorPath):
                    joystickType = JoystickType.fromFile(typeDescriptorPath,
                                                         gui)
                    if joystickType is not None:
                        print("Loaded joystick type from", typeDescriptorPath)
                        joystickType.userDefined = directoryType=="user"
                        break

            if joystickType is None:
                joystickType = JoystickType(identity, gui)

            joystickType._loadProfiles()

            JoystickType._instances[inputID] = joystickType
        else:
            print("Using existing joystick type for %s" % (identity,))

        return JoystickType._instances[inputID]

    @staticmethod
    def getDeviceSubdirectoryName(identity):
        """Get the name of device-specific subdirectory for a joystick with the
        given identity."""
        inputID = identity.inputID
        return "%sV%04xP%04x" % (inputID.busName, inputID.vendor,
                                 inputID.product)

    @staticmethod
    def getDeviceDirectories(gui, identity):
        """Get an iterator over the directories potentially containing files
        related to a device with the given identity.

        Each item is a tuple of:
        - the path of the directory
        - the type of the directory as a string (see GUI.dataDirectories)
        """
        subdirectoryName = JoystickType.getDeviceSubdirectoryName(identity)
        for (path, directoryType) in gui.dataDirectories:
            yield (os.path.join(path, "devices", subdirectoryName),
                   directoryType)

    def __init__(self, identity, gui):
        """Construct a joystick type for the given identity."""
        super().__init__(identity)

        self._gui = gui

        self.userDefined = False

        self._profiles = {}

    @property
    def profiles(self):
        """Get an iterator over the profiles in this joystick type."""
        return iter(self._profiles.values())

    def _loadProfiles(self):
        """Load the profiles for this joystick type."""
        self._profiles = {}

        for (path, directoryType) in self.getDeviceDirectories(self._gui,
                                                               self.identity):
            if os.path.isdir(path):
                for profile in Profile.loadFrom(path):
                    score = profile.match(self.identity)
                    if score>0:
                        name = profile.name
                        if name in self._profiles:
                            print("A profile with name '%s' already exists, ignoring the one from directory %s" % (name, path), file = sys.stderr)
                            continue

                        self._profiles[name] = profile
                        profile.userDefined = directoryType=="user"

#-----------------------------------------------------------------------------

class Joystick(jsprog.joystick.Joystick):
    """A joystick on the GUI."""
    def __init__(self, id, identity, keys, axes, gui):
        """Construct the joystick with the given attributes."""
        super(Joystick, self).__init__(id, identity, keys, axes)

        self._gui = gui

        self._type = JoystickType.get(gui, identity)

        self._statusIcon = StatusIcon(id, self, gui)

        iconTheme = Gtk.IconTheme.get_default()
        icon = iconTheme.load_icon("gtk-preferences", 64, 0)
        self._iconRef = JSWindow.get().addJoystick(self, icon, identity.name)

        self._profiles = []
        self._autoLoadProfile = None

        self._popover = None

        self._contextMenu = None

        self._setupProfiles()

        if self._autoLoadProfile is None:
            notifyMessage = None
        else:
            notifyMessage = _("Profile: '{0}'").\
                format(self._autoLoadProfile.name)

        self._notifySend(_("Added"), notifyMessage)

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

    def extendDisplayedNames(self):
        """Extend the displayed names so that they are unique."""
        identity = self.identity

        self._setDisplayedNames(identity.name + " (" + identity.phys + ")")

    def simplifyDisplayedNames(self):
        """Simpify the displayed names so that they are unique."""
        self._setDisplayedNames(self.identity.name)

    def setActiveProfile(self, profile, notify = True):
        """Make the given profile active."""
        if notify:
            # FIXME: use the joystick's icon, if any
            self._notifySend(_("Downloaded profile"),
                             _("Profile: '{0}'").format(profile.name))

        self._statusIcon.setActive(profile)
        self._popover.setActive(profile)
        self._contextMenu.setActive(profile)

    def profileDownloadFailed(self, profile, exc):
        """Called when downloading the profile has failed with the given
        exception."""
        self._notifySend(_("Profile download failed"),
                         _("{0}").format(str(exc)))

    def destroy(self, notify = True):
        """Destroy the joystick."""
        if notify:
            self._notifySend(_("Removed"))

        self._statusIcon.destroy()
        JSWindow.get().removeJoystick(self._iconRef)

    def _setupProfiles(self):
        """Select the profiles matching this joystick and add them to the
        various menus."""
        self._autoLoadProfile = None
        autoLoadCandidateScore = 0

        for profile in self._type.profiles:
            score = profile.match(self.identity)
            if score>0:
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

    def _setDisplayedNames(self, name):
        """Set the displayed names to the given one."""
        self._statusIcon.setName(name)
        JSWindow.get().setJoystickName(self._iconRef, name)
        self._popover.setTitle(name)

    def _notifySend(self, summary, body = None):
        """Send (update) the notification associated with this joystick with
        the given summary and body"""
        identity = self.identity
        summary = "%s: %s (%s)" % (summary, identity.name, identity.phys)
        self._gui.sendNotify(summary, body)
