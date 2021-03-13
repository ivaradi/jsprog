
from .statusicon import StatusIcon
from .jswindow import JSWindow
from .scndpopover import JSSecondaryPopover
from .jsctxtmenu import JSContextMenu
from .common import *
from .common import _

import jsprog.joystick
from jsprog.joystick import Key, Axis
import jsprog.device
import jsprog.parser
from jsprog.parser import Control, VirtualControl
from jsprog.profile import Profile

import pathlib

#------------------------------------------------------------------------------

## @package jsprog.gui.joystick
#
# The GUI-specific representation of joysticks

#-----------------------------------------------------------------------------

class StateNameGenerator(object):
    """A generator of state names."""
    def __init__(self):
        """Construct the generator."""
        self._nextValue = 1

    def __call__(self):
        """Generate the next state name."""
        value = self._nextValue
        self._nextValue += 1
        return jsprog.device.DisplayVirtualState("State %d" % (value,))

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

        self._icon = None
        self._indicatorIconPath = None
        self._indicatorIcon = None

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

    @property
    def iconDirectories(self):
        """Get an iterator over the icon directories.

        First the device directories are returned, then the
        icons/hicolor/scalable/devices subdirectory of the data directory and
        finally the misc directory three levels above the module's
        directory.
        """
        for (directory, type) in self.deviceDirectories:
            yield directory

        yield os.path.join(datadir, "icons", "hicolor",
                           "scalable", "devices")
        yield os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(__file__))))),
            "misc"))

    @property
    def icon(self):
        """Get the icon of the joystick type"""
        if self._icon is None:
            self._icon = self._getIcon(self._iconName, "jsprog-default-joystick")

        return self._icon

    @property
    def indicatorIconPath(self):
        """Get the path of the indicator icon of the joystick type"""
        if self._indicatorIconPath is None:
            self._indicatorIconPath = \
                self._getIconPath(self._indicatorIconName, "jsprog-default-indicator")

        return self._indicatorIconPath

    @property
    def indicatorIcon(self):
        """Get the the indicator icon of the joystick type"""
        if self._indicatorIcon is None:
            indicatorIconPath = self.indicatorIconPath
            if indicatorIconPath:
                try:
                    self._indicatorIcon = \
                        GdkPixbuf.Pixbuf.new_from_file_at_size(indicatorIconPath,
                                                               64, 64)
                except:
                    pass

        return self._indicatorIcon

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
        indeed exists and the display name is different.

        If displayName is empty, the key's name will be used.

        Returns the real display name set."""
        key = self.findKey(code)
        if key is not None and key.displayName!=displayName:
            if not displayName:
                displayName = Key.getNameFor(code)
            key.displayName = displayName
            self._changed = True
            self.emit("key-display-name-changed", code, displayName)
            self.save()

        return displayName

    def setAxisDisplayName(self, code, displayName):
        """Set the display name of the axis with the given code.

        An axis-display-name-changed signal will also be emitted, if the axis
        indeed exists and the display name is different.

        If displayName is empty, the axis' name will be used.

        Returns the real display name set."""
        axis = self.findAxis(code)
        if axis is not None and axis.displayName!=displayName:
            if not displayName:
                displayName = Axis.getNameFor(code)
            axis.displayName = displayName
            self._changed = True
            self.emit("axis-display-name-changed", code, displayName)
            self.save()

        return displayName

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

    def updateViewHotspotCoordinates(self, view, hotspot, x, y):
        """Update the coordinates of the hotspot from the given image-related
        ones.

        A hotspot-moved signal will be emitted."""
        hotspot.x = round(x)
        hotspot.y = round(y)
        self._changed = True
        self.emit("hotspot-moved", view, hotspot)
        self.save()

    def updateViewHotspotDotCoordinates(self, view, hotspot, x, y):
        """Update the coordinates of the hotspot's dot from the given
        image-related ones.

        A hotspot-moved signal will be emitted."""
        hotspot.dot.x = round(x)
        hotspot.dot.y = round(y)
        self._changed = True
        self.emit("hotspot-moved", view, hotspot)
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

    def newVirtualControl(self, displayName,
                          baseControlType, baseControlCode):
        """Add a virtual control with the given name and display name.

        If the addition is successful, the virtualControl-added signal is
        emitted."""
        virtualControl = self.addVirtualControl(displayName)
        if virtualControl is not None:
            virtualControl.addStatesFromControl(baseControlType,
                                                baseControlCode,
                                                StateNameGenerator(),
                                                self)

            self._changed = True
            self.save()
            self.emit("virtualControl-added", virtualControl)

        return virtualControl

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

    def removeVirtualControl(self, virtualControl):
        """Remove the given virtual control.

        It will be removed from the profiles as well."""
        super().removeVirtualControl(virtualControl)

        for profile in self._profiles:
            if profile.joystickVirtualControlRemoved(virtualControl):
                yield profile

    def deleteVirtualControl(self, virtualControl):
        """Remove the given virtual control.

        The virtualControl-removed signal is emitted."""
        for profile in self.removeVirtualControl(virtualControl):
            self._saveProfile(profile)

        self._changed = True
        self.save()

        self.emit("virtualControl-removed", virtualControl.name)

    def getControlDisplayName(self, control, profile = None):
        """Get the display name of the given control.

        If it is a virtual control and is defined in the joystick type and the
        profile (if given) has a control with the same display name, the
        display name will be appended '(joystick)'."""
        if control is None:
            return None
        elif isinstance(control, Control):
            if control.isKey:
                return self.getControlDisplayName(self.findKey(control.code),
                                                  profile = profile)
            elif control.isAxis:
                return self.getControlDisplayName(self.findAxis(control.code),
                                                  profile = profile)
            elif control.isVirtual:
                vc = self.findVirtualControlByCode(control.code) \
                    if  profile is None else \
                    profile.findVirtualControlByCode(control.code)

                return self.getControlDisplayName(vc, profile = profile)
            else:
                return control.name
        elif isinstance(control, Key) or isinstance(control, Axis):
            return control.name if control.displayName is None else control.displayName
        elif isinstance(control, VirtualControl):
            return self.getVirtualControlDisplayName(control,
                                                     profile =  profile)
        else:
            return None

    def getVirtualControlDisplayName(self, virtualControl, profile = None):
        """Get the name of the given virtual control.

        If it is  defined in the joystick type and the profile (if given) has a
        control with the same display name, the display name will be
        appended '(joystick)'."""
        displayName = virtualControl.name \
            if virtualControl.displayName is None \
            else virtualControl.displayName

        if virtualControl.owner is self and profile is not None and \
           profile.findVirtualControlByDisplayName(displayName) is not None:
            displayName += _(" (joystick)")

        return displayName

    def newVirtualState(self, virtualControl, virtualState):
        """Add the given virtual state to the given virtual control.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualState-added signal is emitted."""
        if self._newVirtualState(virtualControl, virtualState):
            for profile in self._profiles:
                if profile.virtualStateAdded(virtualControl, virtualState):
                    self._saveProfile(profile)

            self._changed = True
            self.save()

            self.emit("virtualState-added", virtualControl, virtualState)

            return True
        else:
            return False

    def setVirtualStateDisplayName(self, virtualControl, virtualState, newName):
        """Set the display name of the given virtual state of the given virtual
        control.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualState-display-name-changed signal is emitted."""
        result = self._setVirtualStateDisplayName(virtualControl, virtualState,
                                                  newName)

        if result:
            self._changed = True
            self.save()
            self.emit("virtualState-display-name-changed",
                      virtualControl, virtualState, newName)
            return True
        else:
            return result is None

    def setVirtualStateConstraints(self, virtualControl, virtualState,
                                   newConstraints):
        """Set the constraints of the given virtual state of the given virtual
        control.

        The virtualState-constraints-changed signal is emitted."""
        if self._setVirtualStateConstraints(virtualControl, virtualState, newConstraints):
            self._changed = True
            self.save()
            self.emit("virtualState-constraints-changed",
                      virtualControl, virtualState)

    def moveVirtualStateForward(self, virtualControl, virtualState):
        """Move the given virtual state of the given virtual control
        forward.

        The virtualState-moved-forward signal will be emitted and any modified
        profiles will be saved."""
        if virtualControl.moveStateForward(virtualState):
            for profile in self._profiles:
                if profile.virtualStateMovedForward(virtualControl, virtualState):
                    self._saveProfile(profile)

            self._changed = True
            self.save()
            self.emit("virtualState-moved-forward",
                      virtualControl, virtualState)
            return True
        else:
            return False

    def moveVirtualStateBackward(self, virtualControl, virtualState):
        """Move the given virtual state of the given virtual control
        backward.

        The virtualState-moved-backward signal will be emitted and any modified
        profiles will be saved."""
        if virtualControl.moveStateBackward(virtualState):
            for profile in self._profiles:
                if profile.virtualStateMovedBackward(virtualControl, virtualState):
                    self._saveProfile(profile)

            self._changed = True
            self.save()
            self.emit("virtualState-moved-backward",
                      virtualControl, virtualState)
            return True
        else:
            return False

    def deleteVirtualState(self, virtualControl, virtualState):
        """Remove the given virtual state of the vien virtual control.

        The virtualState-removed signal is emitted."""
        virtualControl.removeState(virtualState)
        for profile in self._profiles:
            if profile.virtualStateRemoved(virtualControl, virtualState):
                self._saveProfile(profile)

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

    def hasHardVirtualControlReference(self, control):
        """Determine if this joystick profile has a hard reference to a certain
        virtual control.

        The profiles are checked for any hard references."""
        for profile in self._profiles:
            if profile.hasHardVirtualControlReference(control):
                return True

        return False

    def hasHardVirtualStateReference(self, control, virtualStateValue):
        """Determine if this joystick profile has a hard reference to a certain
        state of a virtual control.

        The profiles are checked for any hard references."""
        for profile in self._profiles:
            if profile.hasHardVirtualStateReference(control, virtualStateValue):
                return True

        return False

    def hasSoftControlReference(self, control):
        """Determine if this joystick profile has a soft reference to a certain
        virtual control.

        The profiles are checked for any soft references."""
        for profile in self._profiles:
            if profile.hasSoftControlReference(control):
                return True

        return False

    def hasSoftVirtualStateReference(self, control, virtualStateValue):
        """Determine if this joystick type has a soft reference to a certain
        virtual state of a virtual control.

        The profiles are checked for any soft references."""
        for profile in self._profiles:
            if profile.hasSoftVirtualStateReference(control, virtualStateValue):
                return True

        return False

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

    def newProfileVirtualControl(self, profile, displayName,
                                 baseControlType, baseControlCode):
        """Called when a new virtual control is added to the given profile.

        If the addition is successful, the profile-virtualControl-added signal
        is emitted."""
        virtualControl = profile.addVirtualControl(displayName)
        if virtualControl is not None:
            virtualControl.addStatesFromControl(baseControlType,
                                                baseControlCode,
                                                StateNameGenerator(),
                                                profile)

            self._saveProfile(profile)
            self.emit("profile-virtualControl-added", profile, virtualControl)

        return virtualControl

    def setProfileVirtualControlDisplayName(self, profile, virtualControl, newName):
        """Try to set the display name of the given virtual control of the
        given profile.

        It is checked if another virtual control has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        profile-virtualControl-display-name-changed signal is emitted."""
        if not newName:
            return False

        vc = profile.findVirtualControlByDisplayName(newName)
        if vc is None:
            virtualControl.displayName = newName
            self._saveProfile(profile)
            self.emit("profile-virtualControl-display-name-changed",
                      profile, virtualControl, newName)
            return True
        else:
            return vc is virtualControl

    def newProfileVirtualState(self, profile, virtualControl, virtualState):
        """Add the given virtual state to the given virtual control defined in
        the given profile.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        profile-virtualState-added signal is emitted."""
        if self._newVirtualState(virtualControl, virtualState):
            profile.virtualStateAdded(virtualControl, virtualState)
            self._saveProfile(profile)

            self.emit("profile-virtualState-added",
                      profile, virtualControl, virtualState)

            return True
        else:
            return False

    def setProfileVirtualStateDisplayName(self, profile, virtualControl,
                                          virtualState, newName):
        """Set the display name of the given virtual state of the given virtual
        control defined in the given profile.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and the
        virtualState-display-name-changed signal is emitted."""
        result = self._setVirtualStateDisplayName(virtualControl, virtualState,
                                                  newName)

        if result:
            self._saveProfile(profile)
            self.emit("profile-virtualState-display-name-changed",
                      profile, virtualControl, virtualState, newName)
            return True
        else:
            return result is None

    def setProfileVirtualStateConstraints(self, profile, virtualControl,
                                          virtualState, newConstraints):
        """Set the constraints of the given virtual state of the given virtual
        control defined in the given profile.

        The profile-virtualState-constraints-changed signal is emitted."""
        if self._setVirtualStateConstraints(virtualControl, virtualState, newConstraints):
            self._saveProfile(profile)
            self.emit("profile-virtualState-constraints-changed",
                      profile, virtualControl, virtualState)

    def moveProfileVirtualStateForward(self, profile, virtualControl, virtualState):
        """Move the given virtual state of the given virtual control
        forward in the given profile.

        The profile-virtualState-moved-forward signal will be emitted."""
        if virtualControl.moveStateForward(virtualState):
            if profile.virtualStateMovedForward(virtualControl, virtualState):
                self._saveProfile(profile)

            self.emit("profile-virtualState-moved-forward",
                      profile, virtualControl, virtualState)

            return True
        else:
            return False

    def moveProfileVirtualStateBackward(self, profile, virtualControl, virtualState):
        """Move the given virtual state of the given virtual control
        backward in the given profile.

        The profile-virtualState-moved-backward signal will be emitted."""
        if virtualControl.moveStateBackward(virtualState):
            if profile.virtualStateMovedBackward(virtualControl, virtualState):
                self._saveProfile(profile)

            self.emit("profile-virtualState-moved-backward",
                      profile, virtualControl, virtualState)

            return True
        else:
            return False

    def deleteProfileVirtualState(self, profile, virtualControl, virtualState):
        """Remove the given virtual state of the virtual control defined in
        the give profile.

        The profile-virtualState-removed signal is emitted."""
        virtualControl.removeState(virtualState)
        profile.virtualStateRemoved(virtualControl, virtualState)

        self._saveProfile(profile)
        self.emit("profile-virtualState-removed",
                  profile, virtualControl, virtualState.displayName)

    def deleteProfileVirtualControl(self, profile, virtualControl):
        """Remove the given virtual control of the given profile.

        The profile-virtualControl-removed signal is emitted."""
        profile.removeVirtualControl(virtualControl)
        self._saveProfile(profile)
        self.emit("profile-virtualControl-removed",
                  profile, virtualControl.name)

    def insertShiftLevel(self, profile, beforeIndex, shiftLevel):
        """Called when the given shift level should be inserted into the given
        profile before the given index.

        The shift-level-inserted signal is emitted and the profile is saved, if
        the insertion is successful."""
        if profile.insertShiftLevel(beforeIndex, shiftLevel):
            self._saveProfile(profile)

            self.emit("shift-level-inserted", profile, beforeIndex, shiftLevel)

            return True
        else:
            return False

    def modifyShiftLevel(self, profile, index, modifiedShiftLevel,
                         removedStates, addedStates, existingStates):
        """Called when the shift level with the given index of the given
        profile should be modified.

        removedStates, addStates and existingStates are from the output of
        the VirtualControl.getDifferenceFrom function.

        The shift-level-modified signal is emitted and the profile is saved, if
        the modification is successful."""
        if profile.modifyShiftLevel(index, modifiedShiftLevel,
                                    removedStates, addedStates,
                                    existingStates):
            self._saveProfile(profile)

            self.emit("shift-level-modified", profile, index, modifiedShiftLevel,
                      (removedStates, addedStates, existingStates))

            return True
        else:
            return False

    def removeShiftLevel(self, profile, index, keepStateIndex):
        """Called when the shift level with the given index should be removed
        from the given profile keeping the actions for the state with the given
        index.

        The shift-level-removed signals is emitted and the profile is saved, if
        the removal is successful."""
        if profile.removeShiftLevel(index, keepStateIndex):
            self._saveProfile(profile)

            self.emit("shift-level-removed", profile, index)

            return True
        else:
            return False

    def setAction(self, profile, control, state, shiftStateSequence, action):
        """Set the action belonging to the given shift state sequence and the
        given control in the given profile.

        If successful, an action-set signal is emitted and the profile is
        saved."""
        if profile.setAction(control, state, shiftStateSequence, action):
            self._saveProfile(profile)

            self.emit("action-set", profile, control, state,
                      shiftStateSequence, action)

            return True
        else:
            return False

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

    def setIconName(self, iconName):
        """Set the given file name as the new icon.

        The type will be saved and the icon-changed signal will be emitted."""
        if iconName!=self._iconName:
            self._iconName = iconName
            self._icon = None

            self._changed = True
            self.save()

            self.emit("icon-changed", iconName)

            return True
        else:
            return False

    def resetIcon(self):
        """Reset the name of the icon.

        The type will be saved and the icon-changed signal will be emitted."""
        return self.setIconName(None)

    def setIndicatorIconName(self, iconName):
        """Set the given file name as the new indicator icon.

        The type will be saved and the indicator-icon-changed signal will be emitted."""
        if iconName!=self._indicatorIconName:
            self._indicatorIconName = iconName
            self._indicatorIconPath = None
            self._indicatorIcon = None

            self._changed = True
            self.save()

            self.emit("indicator-icon-changed", iconName)

            return True
        else:
            return False

    def resetIndicatorIcon(self):
        """Reset the name of the indicator icon.

        The type will be saved and the indicator icon-changed signal will be emitted."""
        return self.setIndicatorIconName(None)

    def _getUserProfilePath(self, profile):
        """Get the path of the given user profile."""
        return os.path.join(JoystickType.getUserDeviceDirectory(self._gui,
                                                                self._identity),
                            profile.fileName + ".profile")

    def _saveProfile(self, profile):
        """Save the given (user-defined) profile.

        The signal profile-modified is emitted."""
        path = self._getUserProfilePath(profile)
        newPath = path + ".new"
        document = profile.getXMLDocument()
        with open(newPath, "wt") as f:
            document.writexml(f, addindent = "  ", newl = "\n")
        os.rename(newPath, path)
        self.emit("profile-modified", profile)

    def _newVirtualState(self, virtualControl, virtualState):
        """Add the given virtual state to the given virtual control.

        It is checked if another virtual state has the given display name. If
        so, False is returned. Otherwise the change is performed and True is
        returned.

        This function can be used for a virtual control of a joystick type or
        a profile."""
        if virtualControl.findStateByDisplayName(virtualState.displayName) is not None:
            return False

        if not virtualControl.addState(virtualState):
            return False

        return True

    def _setVirtualStateDisplayName(self, virtualControl,
                                    virtualState, newName):
        """Set the display name of the given virtual state of the given virtual
        control defined in the given profile.

        It is checked if another virtual state has the given display name. If
        so, False is returned if a different virtual state has the same display
        name, None if it is the same virtual state.
        Otherwise the change is performed True is returned.

        This function can be used for a virtual control defined in the joystick
        typr or a profile."""
        if not newName:
            return False

        state = virtualControl.findStateByDisplayName(newName)
        if state is None:
            virtualState.displayName = newName
            return True
        else:
            return None if state is virtualState else False

    def _setVirtualStateConstraints(self, virtualControl,
                                    virtualState, newConstraints):
        """Set the constraints of the given virtual state of the given virtual
        control."""
        if virtualControl.areConstraintsUnique(newConstraints,
                                               excludeState = virtualState):
            virtualState.clearConstraints()
            for constraint in newConstraints:
                virtualState.addConstraint(constraint)

            return True
        else:
            return False

    def _getIcon(self, iconName, defaultName):
        """Get the icon for the given icon and default icon names.

        The icons are searched for in the icon directories. If not found,
        the default theme is searched.

        If iconName is not None, first it is searched. If it fails, or iconName
        is None, the default name is searched. If an icon name has no suffix,
        .svg is assumed"""

        if iconName is None:
            iconName = defaultName
        while True:
            iconPath = self._getIconPath(iconName)

            try:
                if iconPath is None:
                    iconTheme = Gtk.IconTheme.get_default()
                    return iconTheme.load_icon(iconName, 64, 0)
                else:
                    return GdkPixbuf.Pixbuf.new_from_file_at_size(iconPath, 64, 64)
            except:
                pass

            if iconName==defaultName:
                return None

            iconName = defaultName

    def _getIconPath(self, iconName, defaultName = None):
        """Get the path of the icon for the given icon and default icon names.

        The icons are searched for in the icon directories.

        If iconName is not None, first it is searched. If it fails, or iconName
        is None, the default name is searched. If an icon name has no suffix,
        .svg is assumed"""
        if iconName is None:
            iconName = defaultName
        while True:
            iconPath = None
            if iconName[0]==os.path.sep:
                iconPath = iconName
            else:
                hasSuffix = iconName.find(".")>0

                for directory in self.iconDirectories:
                    path = os.path.join(directory,
                                        iconName + ("" if hasSuffix else ".svg"))
                    if os.path.exists(path):
                        iconPath = path
                        break

            if os.path.exists(iconPath):
                return iconPath
            elif iconName==defaultName or defaultName is None:
                return None

            iconName = defaultName

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
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

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

GObject.signal_new("virtualState-moved-forward", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("virtualState-moved-backward", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("virtualState-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str,))

GObject.signal_new("save-failed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("profile-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("profile-renamed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str))

GObject.signal_new("profile-virtualControl-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))

GObject.signal_new("profile-virtualControl-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, str))

GObject.signal_new("profile-virtualState-added", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, object,))

GObject.signal_new("profile-virtualState-display-name-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, object, str))

GObject.signal_new("profile-virtualState-constraints-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, object))

GObject.signal_new("profile-virtualState-moved-forward", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, object))

GObject.signal_new("profile-virtualState-moved-backward", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, object))

GObject.signal_new("profile-virtualState-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object, str,))

GObject.signal_new("profile-virtualControl-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, str))

GObject.signal_new("profile-modified", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("profile-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

GObject.signal_new("shift-level-inserted", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, int, object))

GObject.signal_new("shift-level-modified", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, int, object, object))

GObject.signal_new("shift-level-removed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, int))

GObject.signal_new("action-set", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object,
                                                         object, object, object))

GObject.signal_new("icon-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

GObject.signal_new("indicator-icon-changed", JoystickType,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

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

        icon = type.icon

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


#------------------------------------------------------------------------------

_gdkKey2Code = {
    Gdk.KEY_Escape: Key.findCodeFor("KEY_ESC"),
    Gdk.KEY_1: Key.findCodeFor("KEY_1"),
    Gdk.KEY_2: Key.findCodeFor("KEY_2"),
    Gdk.KEY_3: Key.findCodeFor("KEY_3"),
    Gdk.KEY_4: Key.findCodeFor("KEY_4"),
    Gdk.KEY_5: Key.findCodeFor("KEY_5"),
    Gdk.KEY_6: Key.findCodeFor("KEY_6"),
    Gdk.KEY_7: Key.findCodeFor("KEY_7"),
    Gdk.KEY_8: Key.findCodeFor("KEY_8"),
    Gdk.KEY_9: Key.findCodeFor("KEY_9"),
    Gdk.KEY_0: Key.findCodeFor("KEY_0"),
    Gdk.KEY_minus: Key.findCodeFor("KEY_MINUS"),
    Gdk.KEY_equal: Key.findCodeFor("KEY_EQUAL"),
    Gdk.KEY_BackSpace: Key.findCodeFor("KEY_BACKSPACE"),
    Gdk.KEY_Tab: Key.findCodeFor("KEY_TAB"),
    Gdk.KEY_q: Key.findCodeFor("KEY_Q"),
    Gdk.KEY_w: Key.findCodeFor("KEY_W"),
    Gdk.KEY_e: Key.findCodeFor("KEY_E"),
    Gdk.KEY_r: Key.findCodeFor("KEY_R"),
    Gdk.KEY_t: Key.findCodeFor("KEY_T"),
    Gdk.KEY_y: Key.findCodeFor("KEY_Y"),
    Gdk.KEY_u: Key.findCodeFor("KEY_U"),
    Gdk.KEY_i: Key.findCodeFor("KEY_I"),
    Gdk.KEY_o: Key.findCodeFor("KEY_O"),
    Gdk.KEY_p: Key.findCodeFor("KEY_P"),
    Gdk.KEY_bracketleft: Key.findCodeFor("KEY_LEFTBRACE"),
    Gdk.KEY_bracketright: Key.findCodeFor("KEY_RIGHTBRACE"),
    Gdk.KEY_Control_L: Key.findCodeFor("KEY_LEFTCTRL"),
    Gdk.KEY_a: Key.findCodeFor("KEY_A"),
    Gdk.KEY_s: Key.findCodeFor("KEY_S"),
    Gdk.KEY_d: Key.findCodeFor("KEY_D"),
    Gdk.KEY_f: Key.findCodeFor("KEY_F"),
    Gdk.KEY_g: Key.findCodeFor("KEY_G"),
    Gdk.KEY_h: Key.findCodeFor("KEY_H"),
    Gdk.KEY_j: Key.findCodeFor("KEY_J"),
    Gdk.KEY_k: Key.findCodeFor("KEY_K"),
    Gdk.KEY_l: Key.findCodeFor("KEY_L"),
    Gdk.KEY_semicolon: Key.findCodeFor("KEY_SEMICOLON"),
    Gdk.KEY_apostrophe: Key.findCodeFor("KEY_APOSTROPHE"),
    Gdk.KEY_grave: Key.findCodeFor("KEY_GRAVE"),
    Gdk.KEY_Shift_L: Key.findCodeFor("KEY_LEFTSHIFT"),
    Gdk.KEY_backslash: Key.findCodeFor("KEY_BACKSLASH"),
    Gdk.KEY_z: Key.findCodeFor("KEY_Z"),
    Gdk.KEY_x: Key.findCodeFor("KEY_X"),
    Gdk.KEY_c: Key.findCodeFor("KEY_C"),
    Gdk.KEY_v: Key.findCodeFor("KEY_V"),
    Gdk.KEY_b: Key.findCodeFor("KEY_B"),
    Gdk.KEY_n: Key.findCodeFor("KEY_N"),
    Gdk.KEY_m: Key.findCodeFor("KEY_M"),
    Gdk.KEY_comma: Key.findCodeFor("KEY_COMMA"),
    Gdk.KEY_period: Key.findCodeFor("KEY_DOT"),
    Gdk.KEY_slash: Key.findCodeFor("KEY_SLASH"),
    Gdk.KEY_Shift_R: Key.findCodeFor("KEY_RIGHTSHIFT"),
    Gdk.KEY_KP_Multiply: Key.findCodeFor("KEY_KPASTERISK"),
    Gdk.KEY_Alt_L: Key.findCodeFor("KEY_LEFTALT"),
    Gdk.KEY_space: Key.findCodeFor("KEY_SPACE"),
    Gdk.KEY_Caps_Lock: Key.findCodeFor("KEY_CAPSLOCK"),
    Gdk.KEY_F1: Key.findCodeFor("KEY_F1"),
    Gdk.KEY_F2: Key.findCodeFor("KEY_F2"),
    Gdk.KEY_F3: Key.findCodeFor("KEY_F3"),
    Gdk.KEY_F4: Key.findCodeFor("KEY_F4"),
    Gdk.KEY_F5: Key.findCodeFor("KEY_F5"),
    Gdk.KEY_F6: Key.findCodeFor("KEY_F6"),
    Gdk.KEY_F7: Key.findCodeFor("KEY_F7"),
    Gdk.KEY_F8: Key.findCodeFor("KEY_F8"),
    Gdk.KEY_F9: Key.findCodeFor("KEY_F9"),
    Gdk.KEY_F10: Key.findCodeFor("KEY_F10"),
    Gdk.KEY_Num_Lock: Key.findCodeFor("KEY_NUMLOCK"),
    Gdk.KEY_Scroll_Lock: Key.findCodeFor("KEY_SCROLLLOCK"),
    Gdk.KEY_KP_Home: Key.findCodeFor("KEY_KP7"),
    Gdk.KEY_KP_Up: Key.findCodeFor("KEY_KP8"),
    Gdk.KEY_KP_Page_Up: Key.findCodeFor("KEY_KP9"),
    Gdk.KEY_KP_Subtract: Key.findCodeFor("KEY_KPMINUS"),
    Gdk.KEY_KP_Left: Key.findCodeFor("KEY_KP4"),
    Gdk.KEY_KP_Begin: Key.findCodeFor("KEY_KP5"),
    Gdk.KEY_KP_Right: Key.findCodeFor("KEY_KP6"),
    Gdk.KEY_KP_Add: Key.findCodeFor("KEY_KPPLUS"),
    Gdk.KEY_KP_End: Key.findCodeFor("KEY_KP1"),
    Gdk.KEY_KP_Down: Key.findCodeFor("KEY_KP2"),
    Gdk.KEY_KP_Page_Down: Key.findCodeFor("KEY_KP3"),
    Gdk.KEY_KP_Insert: Key.findCodeFor("KEY_KP0"),
    Gdk.KEY_KP_Delete: Key.findCodeFor("KEY_KPDOT"),
    Gdk.KEY_Zenkaku_Hankaku: Key.findCodeFor("KEY_ZENKAKUHANKAKU"),
    Gdk.KEY_F11: Key.findCodeFor("KEY_F11"),
    Gdk.KEY_F12: Key.findCodeFor("KEY_F12"),
    Gdk.KEY_Romaji: Key.findCodeFor("KEY_RO"),
    Gdk.KEY_Katakana: Key.findCodeFor("KEY_KATAKANA"),
    Gdk.KEY_Hiragana: Key.findCodeFor("KEY_HIRAGANA"),
    Gdk.KEY_Henkan: Key.findCodeFor("KEY_HENKAN"),
    Gdk.KEY_Hiragana_Katakana: Key.findCodeFor("KEY_KATAKANAHIRAGANA"),
    Gdk.KEY_Muhenkan: Key.findCodeFor("KEY_MUHENKAN"),
    Gdk.KEY_KP_Enter: Key.findCodeFor("KEY_KPENTER"),
    Gdk.KEY_Control_R: Key.findCodeFor("KEY_RIGHTCTRL"),
    Gdk.KEY_KP_Divide: Key.findCodeFor("KEY_KPSLASH"),
    Gdk.KEY_Sys_Req: Key.findCodeFor("KEY_SYSRQ"),
    Gdk.KEY_Alt_R: Key.findCodeFor("KEY_RIGHTALT"),
    Gdk.KEY_Linefeed: Key.findCodeFor("KEY_LINEFEED"),
    Gdk.KEY_Home: Key.findCodeFor("KEY_HOME"),
    Gdk.KEY_Up: Key.findCodeFor("KEY_UP"),
    Gdk.KEY_Page_Up: Key.findCodeFor("KEY_PAGEUP"),
    Gdk.KEY_Left: Key.findCodeFor("KEY_LEFT"),
    Gdk.KEY_Right: Key.findCodeFor("KEY_RIGHT"),
    Gdk.KEY_End: Key.findCodeFor("KEY_END"),
    Gdk.KEY_Down: Key.findCodeFor("KEY_DOWN"),
    Gdk.KEY_Page_Down: Key.findCodeFor("KEY_PAGEDOWN"),
    Gdk.KEY_Insert: Key.findCodeFor("KEY_INSERT"),
    Gdk.KEY_Delete: Key.findCodeFor("KEY_DELETE"),
    Gdk.KEY_AudioMute: Key.findCodeFor("KEY_MUTE"),
    Gdk.KEY_AudioLowerVolume: Key.findCodeFor("KEY_VOLUMEDOWN"),
    Gdk.KEY_AudioRaiseVolume: Key.findCodeFor("KEY_VOLUMEUP"),
    Gdk.KEY_PowerOff: Key.findCodeFor("KEY_POWER"),
    Gdk.KEY_KP_Equal: Key.findCodeFor("KEY_KPEQUAL"),
    Gdk.KEY_Pause: Key.findCodeFor("KEY_PAUSE"),
    Gdk.KEY_Hangul: Key.findCodeFor("KEY_HANGEUL"),
    Gdk.KEY_Hangul_Hanja: Key.findCodeFor("KEY_HANJA"),
    Gdk.KEY_yen: Key.findCodeFor("KEY_YEN"),
    #Gdk.KEY_Meta_L: Key.findCodeFor("KEY_LEFTMETA"),
    #Gdk.KEY_Meta_R: Key.findCodeFor("KEY_RIGHTMETA"),
    Gdk.KEY_Undo: Key.findCodeFor("KEY_UNDO"),
    Gdk.KEY_Copy: Key.findCodeFor("KEY_COPY"),
    Gdk.KEY_Open: Key.findCodeFor("KEY_OPEN"),
    Gdk.KEY_Paste: Key.findCodeFor("KEY_PASTE"),
    Gdk.KEY_Find: Key.findCodeFor("KEY_FIND"),
    Gdk.KEY_Cut: Key.findCodeFor("KEY_CUT"),
    Gdk.KEY_Help: Key.findCodeFor("KEY_HELP"),
    Gdk.KEY_Menu: Key.findCodeFor("KEY_MENU"),
    Gdk.KEY_Calculator: Key.findCodeFor("KEY_CALC"),
    Gdk.KEY_3270_Setup: Key.findCodeFor("KEY_SETUP"),
    Gdk.KEY_Sleep: Key.findCodeFor("KEY_SLEEP"),
    Gdk.KEY_WakeUp: Key.findCodeFor("KEY_WAKEUP"),
    Gdk.KEY_Xfer: Key.findCodeFor("KEY_XFER"),
    Gdk.KEY_WWW: Key.findCodeFor("KEY_WWW"),
    Gdk.KEY_DOS: Key.findCodeFor("KEY_MSDOS"),
    Gdk.KEY_Mail: Key.findCodeFor("KEY_MAIL"),
    Gdk.KEY_MyComputer: Key.findCodeFor("KEY_COMPUTER"),
    Gdk.KEY_Back: Key.findCodeFor("KEY_BACK"),
    Gdk.KEY_Forward: Key.findCodeFor("KEY_FORWARD"),
    Gdk.KEY_Eject: Key.findCodeFor("KEY_EJECTCD"),
    Gdk.KEY_AudioNext: Key.findCodeFor("KEY_NEXT"),
    Gdk.KEY_AudioPrev: Key.findCodeFor("KEY_PREVIOUS"),
    Gdk.KEY_AudioStop: Key.findCodeFor("KEY_STOP"),
    Gdk.KEY_AudioRecord: Key.findCodeFor("KEY_RECORD"),
    Gdk.KEY_AudioRewind: Key.findCodeFor("KEY_REWIND"),
    Gdk.KEY_Phone: Key.findCodeFor("KEY_PHONE"),
    Gdk.KEY_HomePage: Key.findCodeFor("KEY_HOMEPAGE"),
    Gdk.KEY_Refresh: Key.findCodeFor("KEY_REFRESH"),
    Gdk.KEY_ScrollUp: Key.findCodeFor("KEY_SCROLLUP"),
    Gdk.KEY_ScrollDown: Key.findCodeFor("KEY_SCROLLDOWN"),
    Gdk.KEY_New: Key.findCodeFor("KEY_NEW"),
    Gdk.KEY_Redo: Key.findCodeFor("KEY_REDO"),
    Gdk.KEY_F13: Key.findCodeFor("KEY_F13"),
    Gdk.KEY_F14: Key.findCodeFor("KEY_F14"),
    Gdk.KEY_F15: Key.findCodeFor("KEY_F15"),
    Gdk.KEY_F16: Key.findCodeFor("KEY_F16"),
    Gdk.KEY_F17: Key.findCodeFor("KEY_F17"),
    Gdk.KEY_F18: Key.findCodeFor("KEY_F18"),
    Gdk.KEY_F19: Key.findCodeFor("KEY_F19"),
    Gdk.KEY_F20: Key.findCodeFor("KEY_F20"),
    Gdk.KEY_F21: Key.findCodeFor("KEY_F21"),
    Gdk.KEY_F22: Key.findCodeFor("KEY_F22"),
    Gdk.KEY_F23: Key.findCodeFor("KEY_F23"),
    Gdk.KEY_F24: Key.findCodeFor("KEY_F24"),
    Gdk.KEY_AudioPlay: Key.findCodeFor("KEY_PLAY"),
    Gdk.KEY_AudioForward: Key.findCodeFor("KEY_FASTFORWARD"),
    Gdk.KEY_Print: Key.findCodeFor("KEY_PRINT"),
    Gdk.KEY_question: Key.findCodeFor("KEY_QUESTION"),
    Gdk.KEY_Search: Key.findCodeFor("KEY_SEARCH"),
    Gdk.KEY_Finance: Key.findCodeFor("KEY_FINANCE"),
    Gdk.KEY_Shop: Key.findCodeFor("KEY_SHOP"),
    Gdk.KEY_Cancel: Key.findCodeFor("KEY_CANCEL"),
    Gdk.KEY_MonBrightnessDown: Key.findCodeFor("KEY_BRIGHTNESSDOWN"),
    Gdk.KEY_MonBrightnessUp: Key.findCodeFor("KEY_BRIGHTNESSUP"),
    Gdk.KEY_AudioMedia: Key.findCodeFor("KEY_MEDIA"),
    Gdk.KEY_Mode_switch: Key.findCodeFor("KEY_SWITCHVIDEOMODE"),
    Gdk.KEY_KbdBrightnessDown: Key.findCodeFor("KEY_KBDILLUMDOWN"),
    Gdk.KEY_KbdBrightnessUp: Key.findCodeFor("KEY_KBDILLUMUP"),
    Gdk.KEY_Send: Key.findCodeFor("KEY_SEND"),
    Gdk.KEY_Reply: Key.findCodeFor("KEY_REPLY"),
    Gdk.KEY_Save: Key.findCodeFor("KEY_SAVE"),
    Gdk.KEY_Documents: Key.findCodeFor("KEY_DOCUMENTS"),
    Gdk.KEY_Battery: Key.findCodeFor("KEY_BATTERY"),
    Gdk.KEY_Bluetooth: Key.findCodeFor("KEY_BLUETOOTH"),
    Gdk.KEY_WLAN: Key.findCodeFor("KEY_WLAN"),
    Gdk.KEY_UWB: Key.findCodeFor("KEY_UWB"),
    Gdk.KEY_Next_VMode: Key.findCodeFor("KEY_VIDEO_NEXT"),
    Gdk.KEY_Prev_VMode: Key.findCodeFor("KEY_VIDEO_PREV"),
    Gdk.KEY_AudioMicMute: Key.findCodeFor("KEY_MICMUTE"),
    Gdk.KEY_Select: Key.findCodeFor("KEY_SELECT"),
    Gdk.KEY_Clear: Key.findCodeFor("KEY_CLEAR"),
    Gdk.KEY_PowerDown: Key.findCodeFor("KEY_POWER2"),
    Gdk.KEY_Option: Key.findCodeFor("KEY_OPTION"),
    Gdk.KEY_Time: Key.findCodeFor("KEY_TIME"),
    Gdk.KEY_Favorites: Key.findCodeFor("KEY_FAVORITES"),
    Gdk.KEY_Subtitle: Key.findCodeFor("KEY_SUBTITLE"),
    Gdk.KEY_CycleAngle: Key.findCodeFor("KEY_ANGLE"),
    Gdk.KEY_CD: Key.findCodeFor("KEY_CD"),
    Gdk.KEY_Video: Key.findCodeFor("KEY_VIDEO"),
    Gdk.KEY_Memo: Key.findCodeFor("KEY_MEMO"),
    Gdk.KEY_Calendar: Key.findCodeFor("KEY_CALENDAR"),
    Gdk.KEY_Red: Key.findCodeFor("KEY_RED"),
    Gdk.KEY_Green: Key.findCodeFor("KEY_GREEN"),
    Gdk.KEY_Yellow: Key.findCodeFor("KEY_YELLOW"),
    Gdk.KEY_Blue: Key.findCodeFor("KEY_BLUE"),
    #Gdk.KEY_Next: Key.findCodeFor("KEY_NEXT"),
    Gdk.KEY_Break: Key.findCodeFor("KEY_BREAK"),
    Gdk.KEY_Game: Key.findCodeFor("KEY_GAMES"),
    Gdk.KEY_ZoomIn: Key.findCodeFor("KEY_ZOOMIN"),
    Gdk.KEY_ZoomOut: Key.findCodeFor("KEY_ZOOMOUT"),
    Gdk.KEY_News: Key.findCodeFor("KEY_NEWS"),
    Gdk.KEY_Messenger: Key.findCodeFor("KEY_MESSENGER"),
    Gdk.KEY_Spell: Key.findCodeFor("KEY_SPELLCHECK"),
    Gdk.KEY_LogOff: Key.findCodeFor("KEY_LOGOFF"),
    Gdk.KEY_dollar: Key.findCodeFor("KEY_DOLLAR"),
    Gdk.KEY_EuroSign: Key.findCodeFor("KEY_EURO"),
    Gdk.KEY_FrameBack: Key.findCodeFor("KEY_FRAMEBACK"),
    Gdk.KEY_FrameForward: Key.findCodeFor("KEY_FRAMEFORWARD"),
    Gdk.KEY_AudioRepeat: Key.findCodeFor("KEY_MEDIA_REPEAT"),
    Gdk.KEY_TouchpadToggle: Key.findCodeFor("KEY_TOUCHPAD_TOGGLE"),
    Gdk.KEY_TouchpadOn: Key.findCodeFor("KEY_TOUCHPAD_ON"),
    Gdk.KEY_TouchpadOff: Key.findCodeFor("KEY_TOUCHPAD_OFF"),
    Gdk.KEY_Super_L: Key.findCodeFor("KEY_LEFTMETA"),
    Gdk.KEY_Super_R: Key.findCodeFor("KEY_RIGHTMETA"),
}

_codes = set()
for (key, code) in _gdkKey2Code.items():
    if code is None:
        print("No code for", key)
        assert False
    if code in _codes:
        print("Code for", key, "is used several times")
        assert False
    _codes.add(code)

def findCodeForGdkKey(keyval):
    """Find the code for the given Gdk key value."""
    return _gdkKey2Code.get(keyval)
