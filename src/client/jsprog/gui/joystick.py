
from .statusicon import StatusIcon
from .jswindow import JSWindow
from .scndpopover import JSSecondaryPopover
from .jsctxtmenu import JSContextMenu
from .common import *
from .common import _

import jsprog.joystick
import jsprog.device
import jsprog.parser
from jsprog.profile import Profile

import pathlib

#------------------------------------------------------------------------------

## @package jsprog.gui.joystick
#
# The GUI-specific representation of joysticks

#-----------------------------------------------------------------------------

class JoystickType(jsprog.device.JoystickType, GObject.Object):
    """A joystick type descriptor.

    This class maintains a registry for joystick types based on their input
    IDs. It also contains the profiles defined for that certain joystick
    type."""
    # The name of the joystick type descriptor file
    _typeDescriptorName = "type.xml"

    # A mapping of input IDs to joystick type instances
    _instances = {}

    @staticmethod
    def get(gui, identity, keys, axes):
        """Get the joystick type for the given identity."""
        inputID = identity.inputID
        if inputID not in JoystickType._instances:
            print("Creating a new joystick type for %s" % (identity,))
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
                for key in keys:
                    joystickType.addKey(key.code)
                for axis in axes:
                    joystickType.addAxis(axis.code, axis.minimum, axis.maximum)

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
    def getDeviceDirectoryFor(parentDirectory, identity):
        """Get the device directory for the given parent directory."""
        return os.path.join(parentDirectory, "devices",
                            JoystickType.getDeviceSubdirectoryName(identity))

    @staticmethod
    def getDeviceDirectories(gui, identity):
        """Get an iterator over the directories potentially containing files
        related to a device with the given identity.

        Each item is a tuple of:
        - the path of the directory
        - the type of the directory as a string (see GUI.dataDirectories)
        """
        for (path, directoryType) in gui.dataDirectories:
            yield (JoystickType.getDeviceDirectoryFor(path, identity),
                   directoryType)

    @staticmethod
    def getUserDeviceDirectory(gui, identity):
        """Get the user's device directory for the joystick type with the given
        identity."""
        return JoystickType.getDeviceDirectoryFor(gui.userDataDirectory,
                                                  identity)

    def __init__(self, identity, gui):
        """Construct a joystick type for the given identity."""
        super().__init__(identity)
        GObject.Object.__init__(self)

        self._gui = gui

        self.userDefined = False

        self._profiles = []
        self._changed = False

    @property
    def profiles(self):
        """Get an iterator over the profiles in this joystick type."""
        return iter(self._profiles.values())

    @property
    def userDeviceDirectory(self):
        """Get the user's device directory for this joystick type."""
        return JoystickType.getUserDeviceDirectory(self._gui, self.identity)

    @property
    def deviceDirectories(self):
        """Get an iterator of the device directories for this joystick type."""
        for data in JoystickType.getDeviceDirectories(self._gui,
                                                      self.identity):
            yield data

    @property
    def changed(self):
        """Indicate if the joystick type has changed."""
        return self._changed

    @property
    def profiles(self):
        """Get an iterator over the profiles."""
        return iter(self._profiles)

    def isDeviceDirectory(self, directory):
        """Determine if the given diretctory is a device directory for this
        joystick type."""
        for (deviceDirectory, _type) in self.deviceDirectories:
            if directory==deviceDirectory:
                return True

        return False

    def setKeyDisplayName(self, code, displayName):
        """Set the display name of the key with the given code.

        A key-display-name-changed signal will also be emitted, if the key
        indeed exists and the display name is different."""
        key = self.findKey(code)
        if key is not None and key.displayName!=displayName:
            key.displayName = displayName
            self._changed = True
            self.emit("key-display-name-changed", code, displayName)
            self.save()

    def setAxisDisplayName(self, code, displayName):
        """Set the display name of the axis with the given code.

        An axis-display-name-changed signal will also be emitted, if the axis
        indeed exists and the display name is different."""
        axis = self.findAxis(code)
        if axis is not None and axis.displayName!=displayName:
            axis.displayName = displayName
            self._changed = True
            self.emit("axis-display-name-changed", code, displayName)
            self.save()

    def newView(self, viewName, imageFileName):
        """Add a view to the joystick type with the given name and image file
        name.

        A view-added signal will also be emitted."""

        if self.findView(viewName) is None:
            view = jsprog.device.View(viewName, imageFileName)
            super().addView(view)
            self.emit("view-added", viewName)
            self._changed = True
            self.save()
            return view

    def changeViewName(self, origViewName, newViewName):
        """Change the name of the view with the given name to the given new
        name, if no other view with the same name exists.

        A view-name-changed signal will also be emitted."""
        if origViewName==newViewName:
            return False

        view = self.findView(origViewName)
        if view is None:
            return False

        if self.findView(newViewName) is not None:
            return False

        view.name = newViewName
        self.emit("view-name-changed", origViewName, newViewName)
        self._changed = True
        self.save()
        return True

    def getHotspotLabel(self, hotspot):
        """Get the label for the given hotspot, i.e. the name of the
        corresponding control."""
        if hotspot.controlType==jsprog.device.Hotspot.CONTROL_TYPE_KEY:
            return self.findKey(hotspot.controlCode).displayName
        elif hotspot.controlType==jsprog.device.Hotspot.CONTROL_TYPE_AXIS:
            return self.findAxis(hotspot.controlCode).displayName

    def addViewHotspot(self, view, hotspot):
        """Add the given hotspot to the given view.

        A hotspot-added signal will be emitted."""
        view.addHotspot(hotspot)
        self._changed = True
        self.emit("hotspot-added", view, hotspot)
        self.save()

    def modifyViewHotspot(self, view, origHotspot, newHotspot):
        """Modify the given original hotspot of the view by replacing it with
        the new hotspot.

        A hotspot-modified signal will be emitted."""
        view.modifyHotspot(origHotspot, newHotspot)
        self._changed = True
        self.emit("hotspot-modified", view, origHotspot, newHotspot)
        self.save()

    def removeViewHotspot(self, view, hotspot):
        """Delete the given hotspot from the given view.

        A hotspot-removed signal will be emitted."""
        view.removeHotspot(hotspot)
        self._changed = True
        self.emit("hotspot-removed", view, hotspot)
        self.save()

    def updateViewHotspotCoordinates(self, hotspot, x, y):
        """Update the coordinates of the hotspot from the given image-related
        ones.

        A hotspot-moved signal will be emitted."""
        hotspot.x = round(x)
        hotspot.y = round(y)
        self._changed = True
        self.emit("hotspot-moved", hotspot)
        self.save()

    def updateViewHotspotDotCoordinates(self, hotspot, x, y):
        """Update the coordinates of the hotspot's dot from the given
        image-related ones.

        A hotspot-moved signal will be emitted."""
        hotspot.dot.x = round(x)
        hotspot.dot.y = round(y)
        self._changed = True
        self.emit("hotspot-moved", hotspot)
        self.save()

    def deleteView(self, viewName):
        """Delete the view with the given name.

        A view-removed signal will also be emitted."""
        view = self.findView(viewName)
        if view is not None:
            super().removeView(view)
            self._changed = True
            self.save()
            self.emit("view-removed", viewName)

    def newVirtualControl(self, name, displayName,
                          baseControlType, baseControlCode):
        """Add a virtual control with the given name and display name.

        If the addition is successful, the virtualControl-added signal is
        emitted."""
        virtualControl = self.addVirtualControl(name, displayName)
        if virtualControl is not None:
            class StateNameSource(object):
                def __init__(self):
                    self._nextValue = 1

                def __call__(self):
                    value = self._nextValue
                    self._nextValue += 1
                    return jsprog.device.DisplayVirtualState("State %d" % (value,))

            virtualControl.addStatesFromControl(baseControlType,
                                                baseControlCode,
                                                StateNameSource(),
                                                self)

            self._changed = True
            self.save()
            self.emit("virtualControl-added", virtualControl)

        return virtualControl

    def setVirtualControlName(self, virtualControl, newName):
        """Try to set the name of the given virtual control.

        It is checked if the name is correct, and if not, False is returned.
        It is then checked if another virtual control has the given name. If so,
        False is returned. Otherwise the change is performed and the
        virtualControl-name-changed signal is emitted."""
        if not jsprog.parser.VirtualControl.checkName(newName):
            return False

        vc = self.findVirtualControl(newName)
        if vc is None:
            virtualControl.name = newName
            self._changed = True
            self.save()
            self.emit("virtualControl-name-changed", virtualControl, newName)
            return True
        else:
            return vc is virtualControl

    def setVirtualControlDisplayName(self, virtualControl, newName):
        """Try to set the name of the given virtual control.

        It is checked if another virtual control has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualControl-display-name-changed signal is emitted."""
        if not newName:
            return False

        vc = self.findVirtualControlByDisplayName(newName)
        if vc is None:
            virtualControl.displayName = newName
            self._changed = True
            self.save()
            self.emit("virtualControl-display-name-changed",
                      virtualControl, newName)
            return True
        else:
            return vc is virtualControl

    def deleteVirtualControl(self, virtualControl):
        """Remove the given virtual control.

        The virtualControl-removed signal is emitted."""
        self.removeVirtualControl(virtualControl)
        self._changed = True
        self.save()
        self.emit("virtualControl-removed",
                  virtualControl.name)

    def getControlDisplayName(self, control, profile = None):
        """Get the display name of the given control."""
        if control.isKey:
            key = self.findKey(control.code)
            if key is not None:
                return key.name if key.displayName is None else key.displayName
        elif control.isAxis:
            axis =  self.findAxis(control.code)
            if axis is not None:
                return axis.name if axis.displayName is None else axis.displayName
        elif control.isVirtual:
            vc = self.findVirtualControlByCode(control.code) if profile is None \
                else profile.findVirtualControlByCode(control.code)
            if vc is not None:
                return vc.name if vc.displayName is None else vc.displayName

        return control.name

    def newVirtualState(self, virtualControl, virtualState):
        """Add the given virtual state to the given virtual control.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualState-added signal is emitted."""
        if virtualControl.findStateByDisplayName(virtualState.displayName) is not None:
            return False

        if not virtualControl.addState(virtualState):
            return False

        self._changed = True
        self.save()

        self.emit("virtualState-added", virtualControl, virtualState)

        return True

    def setVirtualStateDisplayName(self, virtualControl, virtualState, newName):
        """Set the display name of the given virtual state of the given virtual
        control.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualState-display-name-changed signal is emitted."""
        if not newName:
            return False

        state = virtualControl.findStateByDisplayName(newName)
        if state is None:
            virtualState.displayName = newName
            self._changed = True
            self.save()
            self.emit("virtualState-display-name-changed",
                      virtualControl, virtualState, newName)
            return True
        else:
            return state is virtualState

    def setVirtualStateConstraints(self, virtualControl, virtualState,
                                   newConstraints):
        """Set the constraints of the given virtual state of the given virtual
        control.

        The virtualState-constraints-changed signal is emitted."""
        # FIXME: implement a check for equivalence
        virtualState.clearConstraints()
        for constraint in newConstraints:
            virtualState.addConstraint(constraint)

        self._changed = True
        self.save()
        self.emit("virtualState-constraints-changed",
                  virtualControl, virtualState)

    def deleteVirtualState(self, virtualControl, virtualState):
        """Remove the given virtual state of the vien virtual control.

        The virtualState-removed signal is emitted."""
        virtualControl.removeState(virtualState)

        self._changed = True
        self.save()
        self.emit("virtualState-removed",
                  virtualControl, virtualState.displayName)

    def save(self):
        """Save the joystick type into the user's directory."""
        directoryPath = JoystickType.getUserDeviceDirectory(self._gui,
                                                            self._identity)


        pathlib.Path(directoryPath).mkdir(parents = True, exist_ok = True)

        try:
            self.saveInto(os.path.join(directoryPath, self._typeDescriptorName))
            self._changed = False
        except Exception as e:
            self.emit("save-failed", e)

    def getNextControl(self, lastControlType, lastControlCode):
        """Get the control coming after the given type and code pair.

        If either of them is None, the first control is returned."""
        controlType = None
        controlCode = None
        if lastControlType is not None and lastControlCode is not None:
            afterPrevious = False
            if lastControlType == jsprog.parser.Control.TYPE_KEY:
                for key in self.iterKeys:
                    if afterPrevious:
                        controlType = jsprog.parser.Control.TYPE_KEY
                        controlCode = key.code
                        afterPrevious = False
                        break
                    elif key.code==lastControlCode:
                        afterPrevious = True

            if controlType is None:
                for axis in self.iterAxes:
                    if afterPrevious:
                        controlType = jsprog.parser.Control.TYPE_AXIS
                        controlCode = axis.code
                        afterPrevious = False
                        break
                    elif axis.code==lastControlCode:
                        afterPrevious = True

        if controlType is None:
            firstKey = self.firstKey
            if firstKey is None:
                controlType = jsprog.parser.Control.TYPE_AXIS
                controlCode = self.firstAxis.code
            else:
                controlType = jsprog.parser.Control.TYPE_KEY
                controlCode = firstKey.code

        return (controlType, controlCode)

    def _loadProfiles(self):
        """Load the profiles for this joystick type."""
        self._profiles = []

        for (path, directoryType) in self.getDeviceDirectories(self._gui,
                                                               self.identity):
            if os.path.isdir(path):
                for profile in Profile.loadFrom(self, path):
                    score = profile.match(self.identity)
                    if score>0:
                        profile.directoryType = directoryType
                        self._profiles.append(profile)

    def findProfiles(self, name, excludeProfile = None, directoryType = None):
        """Find the profiles with the given name."""
        return [profile for profile in self._profiles
                if profile.name==name and profile is not excludeProfile and
                (directoryType is None or profile.directoryType==directoryType)]

    def hasUserProfileFileName(self, fileName, excludeProfile = None):
        """Determine if there is a user profile with the given file name."""
        for profile in self._profiles:
            if profile.userDefined and profile.fileName == fileName and \
               profile is not excludeProfile:
                return True
        return False

    def addProfile(self, name, fileName, identity, cloneFrom = None):
        """Add a new, user-defined profile with the given name and file name.

        If there is already a user profile with the given file name, nothing is
        done, and None is returned.

        On success, the profile is saved, the profile-added signal is emitted
        and the profile returned."""

        if self.hasUserProfileFileName(fileName):
            return None

        if cloneFrom:
            profile = cloneFrom.clone()
            profile.name = name
            profile.autoLoad = False
        else:
            profile = Profile(self, name, identity)

        profile.directoryType = "user"
        profile.fileName = fileName

        self._saveProfile(profile)

        self._profiles.append(profile)

        self.emit("profile-added", profile)

        return profile

    def updateProfileNames(self, profile, newName, newFileName):
        """Update the name and file name of the given profile.

        It should be a user-defined profile. It can be renamed if
        there is no other user-defined profile with the same file name.

        On success, the profile is saved, the profile-renamed signal is emitted
        and True is returned. Otherwise False is returned."""
        assert profile.userDefined

        oldName = profile.name
        if oldName==newName and profile.fileName==newFileName:
            return True

        if self.hasUserProfileFileName(newFileName, excludeProfile = profile):
            return False

        profile.name = newName

        oldFilePath = self._getUserProfilePath(profile)

        profile.fileName = newFileName
        newFilePath = self._getUserProfilePath(profile)
        self._saveProfile(profile)

        if newFilePath!=oldFilePath:
            os.unlink(oldFilePath)

        if oldName!=newName:
            self.emit("profile-renamed", profile, oldName)

        return True

    def updateProfileIdentity(self, profile):
        """Called when the identity of the given profile was updated.

        Only the version, the physical location or the unique ID might have
        changed when this function is called.

        The profile is saved."""
        self._saveProfile(profile)

    def deleteProfile(self, profile):
        """Delete the given profile.

        If it is not user-defined, False is returned.

        Otherwise the profile is removed from our list and a profile-removed
        signal is emitted, and True is returned."""
        if not profile.userDefined:
            return False

        self._profiles.remove(profile)
        filePath = self._getUserProfilePath(profile)
        os.unlink(filePath)

        self.emit("profile-removed", profile)

        return True

    def _getUserProfilePath(self, profile):
        """Get the path of the given user profile."""
        return os.path.join(JoystickType.getUserDeviceDirectory(self._gui,
                                                                self._identity),
                            profile.fileName + ".profile")

    def _saveProfile(self, profile):
        """Save the given (user-defined) profile."""
        path = self._getUserProfilePath(profile)
        newPath = path + ".new"
        document = profile.getXMLDocument()
        with open(newPath, "wt") as f:
            document.writexml(f, addindent = "  ", newl = "\n")
        os.rename(newPath, path)

#-----------------------------------------------------------------------------

GObject.signal_new("key-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (int, str))

GObject.signal_new("axis-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (int, str))

GObject.signal_new("view-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

GObject.signal_new("view-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str, str))

GObject.signal_new("hotspot-moved", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("hotspot-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("hotspot-modified", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, object))

GObject.signal_new("hotspot-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("view-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

GObject.signal_new("virtualControl-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("virtualControl-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str))

GObject.signal_new("virtualControl-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str))

GObject.signal_new("virtualControl-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

GObject.signal_new("virtualState-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object,))

GObject.signal_new("virtualState-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, str))

GObject.signal_new("virtualState-constraints-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("virtualState-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str,))

GObject.signal_new("save-failed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("profile-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("profile-renamed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str))

GObject.signal_new("profile-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

#-----------------------------------------------------------------------------

class ProfileList(GObject.Object):
    """The list of profiles belonging to a joystick or joystick type.

    It contains all profiles from a joystick type that match a certain
    identity, i.e. that of a joystick or the joystick type itself. It handles
    signals from a joystick type about profiles being created, modified,
    deleted, renamed, etc, and updates the set accordingly.

    It also provides unique 'virtual' names for the profiles. If two or more
    profiles have the same name, the directory type and possibly the file name
    are put after the name in parentheses so that they can be distinguished."""
    def __init__(self, joystickType, identity):
        """Construct the profile set for the given joystick type and
        identity."""
        GObject.Object.__init__(self)

        self._joystickType = joystickType
        self._identity = identity

        self._profilesByName = {}
        self._profiles = []

        joystickType.connect("profile-added", self._profileAdded)
        joystickType.connect("profile-renamed", self._profileRenamed)
        joystickType.connect("profile-removed", self._profileRemoved)

    def setup(self):
        """Setup the profiles from the joystick type.

        Returns the best matching auto-load profile."""
        autoLoadProfile = None
        autoLoadCandidateScore = 0

        for profile in self._joystickType.profiles:
            score = profile.match(self._identity)
            if score>0:
                self._addProfile(profile)
                if profile.autoLoad and score>autoLoadCandidateScore:
                    autoLoadProfile = profile
                    autoLoadCandidateScore = score

        return autoLoadProfile

    def _addProfile(self, profile):
        """Add the given profile to the list."""
        if profile.match(self._identity)<=0:
            return

        name = profile.name
        if name in self._profilesByName:
            self._profilesByName[name].append(profile)
        else:
            self._profilesByName[name] = [profile]

        self._recalculateProfiles(name)

    def _profileAdded(self, joystickType, profile):
        """Called when a profile is added to the joystick type."""
        self._addProfile(profile)

    def _profileRenamed(self, joystickType, profile, oldName):
        """Called when a profile is renamed."""
        oldName = self._findProfileName(profile)
        if oldName is None:
            return

        self._profilesByName[oldName] = \
            [p for p in self._profilesByName[oldName] if p is not profile]

        self._addProfile(profile)
        self._recalculateProfiles(oldName)

    def _profileRemoved(self, joystickType, profile):
        """Called when a profile is removed."""
        index = self._findProfileIndex(profile)
        if index<0:
            return

        name = profile.name

        self._profilesByName[name] = \
            [p for p in self._profilesByName[name] if p is not profile]
        del self._profiles[index]

        self.emit("profile-removed", profile, index)

        self._recalculateProfiles(name)

    def _recalculateProfiles(self, name):
        """Recalculate the names and positions of the profiles with the given
        name."""
        profileNames = self._calculateProfileNames(name)
        for (profile, name) in profileNames.items():
            oldName = self._findProfileName(profile)
            if oldName is None:
                index = self._findIndexForProfile(profile, name)
                self._insertProfile(index, profile, name)
            elif name!=oldName:
                oldIndex = self._findProfileIndex(profile)
                index = self._findIndexForProfile(profile, name)
                self._moveProfile(oldIndex, index, name)

    def _calculateProfileNames(self, name):
        """Calculate the unique names of the profiles with the given name."""
        profileNames = {}

        profiles = self._profilesByName[name]
        if len(profiles)<1:
            del self._profilesByName[name]
        elif len(profiles)<2:
            profileNames[profiles[0]] = name
        else:
            profilesByDirectoryType = {}
            for profile in profiles:
                directoryType = profile.directoryType
                if directoryType in profilesByDirectoryType:
                    profilesByDirectoryType[directoryType].append(profile)
                else:
                    profilesByDirectoryType[directoryType] = [profile]
            for (directoryType, profiles) in profilesByDirectoryType.items():
                if len(profiles)<2:
                    profile = profiles[0]
                    profileNames[profile] = profile.name + " (" + \
                        _(directoryType) + ")"
                else:
                    for profile in profiles:
                        profileNames[profile] = profile.name + " (" + \
                            _(directoryType) + ", " + profile.fileName + ")"
        return profileNames

    def _findProfileIndex(self, profile):
        """Find the index of the given profile."""
        for (index, (_name, p)) in enumerate(self._profiles):
            if p is profile:
                return index
        return -1

    def _findIndexForProfile(self, profile, name):
        """Find the index for the given name."""
        for (index, (n, p)) in enumerate(self._profiles):
            if p.userDefined != profile.userDefined:
                if profile.userDefined:
                    return index
            elif p.name>profile.name or \
                 (p.name==profile.name and p.fileName>profile.fileName):
                return index
        return len(self._profiles)

    def _findProfileName(self, profile):
        """Find the name of the given profile, if it is in the list already.

        If it is not found in the list, None is returned."""
        index = self._findProfileIndex(profile)
        return None if index<0 else self._getNameAt(index)

    def _moveProfile(self, oldIndex, index, name):
        """Move the profile from the given old index to the given new index
        with the given new name.

        If oldIndex is less than index, 1 is subtracted from index assuming
        that it was determined with the profile being at its old index.

        It is assumed that the profile's new display name is already in
        self._profileNames.

        The function emits a profile-renamed signal."""
        profile = self._getProfileAt(oldIndex)

        if oldIndex<index:
            index -= 1

        if oldIndex==index:
            self._profiles[index] = (name, profile)
        else:
            del self._profiles[oldIndex]
            self._profiles.insert(index, (name, profile))


        self.emit("profile-renamed", profile, name, oldIndex, index)

    def _insertProfile(self, index, profile, name):
        """Insert the profile at the given index with the given name.

        It is assumed that the profile's display name is already in
        self._profileNames.

        The function emits a profile-added signal.
        """
        self._profiles.insert(index, (name, profile))
        self.emit("profile-added", profile, name, index)

    def _getNameAt(self, index):
        """Get the name at the given index."""
        return self._profiles[index][0]

    def _getProfileAt(self, index):
        """Get the profile at the given index."""
        return self._profiles[index][1]

GObject.signal_new("profile-added", ProfileList,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str, int))

GObject.signal_new("profile-renamed", ProfileList,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str, int, int))

GObject.signal_new("profile-removed", ProfileList,
                   GObject.SignalFlags.RUN_FIRST, None, (object, int))

#-----------------------------------------------------------------------------

class Joystick(object):
    """A joystick on the GUI."""
    def __init__(self, id, identity, type, gui):
        """Construct the joystick with the given attributes."""
        self._id = id
        self._identity = identity
        self._type = type
        self._gui = gui

        self._profileList = ProfileList(type, identity)

        self._statusIcon = StatusIcon(id, self, gui)

        iconTheme = Gtk.IconTheme.get_default()
        icon = iconTheme.load_icon("gtk-preferences", 64, 0)
        self._iconRef = JSWindow.get().addJoystick(self, icon, identity.name)

        self._profiles = []
        self._autoLoadProfile = None

        self._popover = JSSecondaryPopover(self)

        self._contextMenu = JSContextMenu(self)

        self._setupProfiles()

        if self._autoLoadProfile is None:
            notifyMessage = None
        else:
            notifyMessage = _("Profile: '{0}'").\
                format(self._autoLoadProfile.name)

        self._notifySend(_("Added"), notifyMessage)

    @property
    def id(self):
        """Get the identifier of this joystick."""
        return self._id

    @property
    def identity(self):
        """Get the identity of this joystick."""
        return self._identity

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
    def profileList(self):
        """Get the ProfileList object associated with this joystick."""
        return self._profileList

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
        self._autoLoadProfile = self._profileList.setup()

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
