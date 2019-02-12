
from joystick import InputID, JoystickIdentity, Key, Axis
from action import Action, SimpleAction, RepeatableAction, MouseMoveCommand, MouseMove
from action import AdvancedAction, KeyPressCommand, KeyReleaseCommand, DelayCommand
from util import appendLinesIndented, linesToText

from xml.sax.handler import ContentHandler
from xml.sax import SAXParseException, make_parser

from xml.dom.minidom import getDOMImplementation

import os
import sys

#------------------------------------------------------------------------------

## @package jsprog.profile
#
# The handling of the profiles

#------------------------------------------------------------------------------

def getShiftLevelStateName(index):
    """Get the name of the variable containing the state of a certain shift
    level."""
    return "_jsprog_shiftLevel_%d_state" % (index,)

#------------------------------------------------------------------------------

class ProfileHandler(ContentHandler):
    """XML content handler for a profile file."""
    def __init__(self):
        """Construct the parser."""
        self._locator = None

        self._context = []
        self._characterContext = []

        self._profileName = None
        self._autoLoad = False

        self._profile = None

        self._inputID = None
        self._name = None
        self._phys = None
        self._uniq = None

        self._virtualControl = None
        self._shiftLevel = None
        self._virtualState = None

        self._controlProfile = None
        self._controlHandlerTree = None
        self._shiftContext = []

        self._action = None
        self._leftShift = False
        self._rightShift = False
        self._leftControl = False
        self._rightControl = False
        self._leftAlt = False
        self._rightAlt = False

    @property
    def profile(self):
        """Get the profile parsed."""
        return self._profile

    @property
    def _parent(self):
        """Get the parent context."""
        return self._context[-1]

    def setDocumentLocator(self, locator):
        """Called to set the locator."""
        self._locator = locator

    def startDocument(self):
        """Called at the beginning of the document."""
        self._context = []
        self._characterContext = []
        self._shiftContext = []
        self._virtualControl = None
        self._shiftLevel = None
        self._virtualState = None
        self._profile = None

    def startElement(self, name, attrs):
        """Called for each start tag."""
        if name=="joystickProfile":
            if self._context:
                self._fatal("'joystickProfile' should be the top-level element")
            self._startJoystickProfile(attrs)
        elif name=="identity":
            self._checkParent(name, "joystickProfile")
            self._startIdentity(attrs)
        elif name=="inputID":
            self._checkParent(name, "identity")
            self._startInputID(attrs)
        elif name=="name":
            self._checkParent(name, "identity")
            self._startName(attrs)
        elif name=="phys":
            self._checkParent(name, "identity")
            self._startPhys(attrs)
        elif name=="uniq":
            self._checkParent(name, "identity")
            self._startUniq(attrs)
        elif name=="virtualControls":
            self._checkParent(name, "joystickProfile")
            self._startVirtualControls(attrs)
        elif name=="virtualControl":
            self._checkParent(name, "virtualControls", "virtualState", "controls")
            self._startVirtualControl(attrs)
        elif name=="shiftLevels":
            self._checkParent(name, "joystickProfile")
            self._startShiftLevels(attrs)
        elif name=="shiftLevel":
            self._checkParent(name, "shiftLevels")
            self._startShiftLevel(attrs)
        elif name=="virtualState":
            self._checkParent(name, "virtualControl", "shiftLevel")
            self._startVirtualState(attrs)
        elif name=="controls":
            self._checkParent(name, "joystickProfile")
            self._startControls(attrs)
        elif name=="key":
            self._checkParent(name, "virtualState", "controls")
            self._startKey(attrs)
        elif name=="axis":
            self._checkParent(name, "virtualState")
            self._startAxis(attrs)
        elif name=="shift":
            self._checkParent(name, "key", "shift", "virtualState")
            self._startShift(attrs)
        elif name=="action":
            self._checkParent(name, "key", "shift", "virtualState")
            self._startAction(attrs)
        elif name=="keyCombination":
            self._checkParent(name, "action")
            self._startKeyCombination(attrs)
        elif name=="enter":
            self._checkParent(name, "action")
            self._startEnter(attrs)
        elif name=="repeat":
            self._checkParent(name, "action")
            self._startRepeat(attrs)
        elif name=="leave":
            self._checkParent(name, "action")
            self._startLeave(attrs)
        elif name=="keyPress":
            self._checkParent(name, "enter", "repeat", "leave")
            self._startKeyPress(attrs)
        elif name=="keyRelease":
            self._checkParent(name, "enter", "repeat", "leave")
            self._startKeyRelease(attrs)
        elif name=="delay":
            self._checkParent(name, "enter", "repeat", "leave")
            self._startDelay(attrs)
        else:
            self._fatal("unhandled tag")
        self._context.append(name)
        if len(self._characterContext)<len(self._context):
            self._characterContext.append(None)

    def endElement(self, name):
        """Called for each end tag."""
        del self._context[-1]
        if name=="joystickProfile":
            self._endJoystickProfile()
        elif name=="identity":
            self._endIdentity()
        elif name=="name":
            self._endName()
        elif name=="phys":
            self._endPhys()
        elif name=="uniq":
            self._endUniq()
        elif name=="virtualControl":
            self._endVirtualControl()
        elif name=="shiftLevel":
            self._endShiftLevel()
        elif name=="virtualState":
            self._endVirtualState()
        elif name=="key":
            self._endKey()
        elif name=="shift":
            self._endShift()
        elif name=="action":
            self._endAction()
        elif name=="keyCombination":
            self._endKeyCombination()
        elif name=="enter":
            self._endEnter()
        elif name=="repeat":
            self._endRepeat()
        elif name=="leave":
            self._endLeave()
        elif name=="keyPress":
            self._endKeyPress()
        elif name=="keyRelease":
            self._endKeyRelease()
        elif name=="delay":
            self._endDelay()

    def characters(self, content):
        """Called for character content."""
        if content.strip():
            self._appendCharacters(content)

    def endDocument(self):
        """Called at the end of the document."""

    @property
    def _shiftLevelIndex(self):
        """Determine the shift level index, i.e. the length of the shift
        context."""
        return len(self._shiftContext)

    @property
    def _handlerTree(self):
        """Get the current handler tree."""
        return self._shiftContext[-1] if self._shiftContext else self._controlHandlerTree

    @property
    def _numExpectedShiftStates(self):
        """Determine the number of expected shift states at the
        current level."""
        shiftLevelIndex = self._shiftLevelIndex
        if shiftLevelIndex<self._profile.numShiftLevels:
            return self._profile.getShiftLevel(shiftLevelIndex).numStates
        else:
            return 0

    def _startJoystickProfile(self, attrs):
        """Handle the joystickProfile start tag."""
        if self._profile is not None:
            self._fatal("there should be only one 'joystickProfile' element")

        self._profileName = self._getAttribute(attrs, "name")
        if not self._profileName:
            self._fatal("the profile's name should not be empty")

        self._autoLoad = self._findBoolAttribute(attrs, "autoLoad")

    def _startIdentity(self, attrs):
        """Handle the identity start tag."""
        if self._profile is not None:
            self._fatal("there should be only one identity")

            self._inputID = None
            self._name = None
            self._phys = None
            self._uniq = None

    def _startInputID(self, attrs):
        """Handle the input ID start tag."""
        busName = self._getAttribute(attrs, "busType")
        busType = InputID.findBusTypeFor(busName)
        if busType is None:
            self._fatal("invalid bus type '%s'" % (busName,))

        vendor = self._getHexAttribute(attrs, "vendor")
        product = self._getHexAttribute(attrs, "product")
        version = self._getHexAttribute(attrs, "version")

        self._inputID = InputID(busType, vendor, product, version)

    def _startName(self, attrs):
        """Handle the name start tag."""
        self._startCollectingCharacters()

    def _endName(self):
        """Handle the name end tag."""
        self._name = self._getCollectedCharacters()

    def _startPhys(self, attrs):
        """Handle the phys start tag."""
        self._startCollectingCharacters()

    def _endPhys(self):
        """Handle the phys end tag."""
        self._phys = self._getCollectedCharacters()

    def _startUniq(self, attrs):
        """Handle the uniq start tag."""
        self._startCollectingCharacters()

    def _endUniq(self):
        """Handle the uniq end tag."""
        uniq = self._getCollectedCharacters()
        self._uniq = uniq if uniq else None

    def _endIdentity(self):
        """Handle the identity end tag."""
        if self._inputID is None:
            self._fatal("the input ID is missing from the identity")
        if self._name is None:
            self._fatal("the name is missing from the identity")
        if self._phys is None:
            self._fatal("the physical location is missing from the identity")
        identity = JoystickIdentity(self._inputID, self._name,
                                    self._phys, self._uniq)
        self._profile = Profile(self._profileName, identity,
                                autoLoad = self._autoLoad)

    def _startVirtualControls(self, attrs):
        """Handle the virtualControls start tag."""
        if self._profile is None:
            self._fatal("the virtual controls should be specified after the identity")
        if self._profile.hasVirtualControls:
            self._fatal("the virtual controls are already defined")
        if self._profile.numShiftLevels>0 or self._profile.hasControlProfiles:
            self._fatal("the virtual controls should be specified before any shift levels and control profiles")

    def _startVirtualControl(self, attrs):
        """Handle the virtualControl start tag."""
        if self._parent=="virtualControls":
            name = self._getAttribute(attrs, "name")
            if not VirtualControl.checkName(name):
                self._fatal("the name of a virtual control should start ith a letter and may contain only alphanumeric or underscore characters")
            self._virtualControl = self._profile.addVirtualControl(name)
        elif self._parent=="virtualState":
            virtualControl = self._getVirtualControl(attrs)
            control = Control(Control.TYPE_VIRTUAL, virtualControl.code)
            constraint = self._getFromToValueConstraint(attrs, control,
                                                        minValue = 0,
                                                        maxValue =
                                                        virtualControl.numStates - 1)
            self._virtualState.addConstraint(constraint)
        elif self._parent=="controls":
            virtualControl = self._getVirtualControl(attrs)

            if self._profile.findVirtualControlProfile(virtualControl.code) is not None:
                self._fatal("a profile for the virtual control is already defined")

            self._controlProfile = VirtualControlProfile(virtualControl.code)
            self._controlHandlerTree = None

    def _endVirtualControl(self):
        """Handle the virtualControl end tag."""
        if self._parent=="virtualControls":
            if self._virtualControl.numStates<2:
                self._fatal("a virtual control must have at least 2 states.")
            self._virtualControl = None
        elif self._parent=="controls":
            self._profile.addControlProfile(self._controlProfile)
            self._controlProfile = None

    def _startShiftLevels(self, attrs):
        """Handle the shiftLevels start tag."""
        if self._profile is None:
            self._fatal("the shift controls should be specified after the identity")
        if self._profile.hasControlProfiles:
            self._fatal("the shift controls should be specified before any control profiles")

    def _startShiftLevel(self, attrs):
        """Handle the shiftLevel start tag."""
        self._shiftLevel = ShiftLevel()

    def _endShiftLevel(self):
        """Handle the shiftLevel end tag."""
        if self._shiftLevel.numStates<2:
            self._fatal("a shift level should have at least two states")
        self._profile.addShiftLevel(self._shiftLevel)
        self._shiftLevel = None

    def _startVirtualState(self, attrs):
        """Handle the virtualState start tag."""
        if self._context[-2]=="controls":
            value = self._getIntAttribute(attrs, "value")
            if self._controlProfile.hasHandlerTree(value):
                self._fatal("virtual state %d is already defined" % (value,))
            self._controlHandlerTree = \
              self._controlProfile.getHandlerTree(value)
        else:
            self._virtualState = VirtualState()

    def _endVirtualState(self):
        """Handle the virtualState end tag."""
        if self._context[-2]=="controls":
            if not self._controlHandlerTree.isComplete(self._numExpectedShiftStates):
                self._fatal("the virtual control profile is missing either child shift level states or an action")
            self._controlHandlerTree = None
        else:
            virtualState = self._virtualState

            if not virtualState.isValid:
                self._fatal("the virtual state has conflicting controls")

            if self._parent=="virtualControl":
                if not self._virtualControl.addState(virtualState):
                    self._fatal("the virtual state is not unique for the virtual control")
            else:
                if not self._shiftLevel.addState(virtualState):
                    self._fatal("the virtual state is not unique on the level")

            self._virtualState = None

    def _startControls(self, attrs):
        """Handle the controls start tag."""
        if self._profile is None:
            self._fatal("controls should be specified after the identity")

    def _startKey(self, attrs):
        """Handle the key start tag."""
        code = self._getControlCode(attrs, Key.findCodeFor)

        if self._parent == "virtualState":
            value = self._getIntAttribute(attrs, "value")
            if value<0 or value>1:
                self._fatal("the value should be 0 or 1 for a key")
            constraint = SingleValueConstraint(Control(Control.TYPE_KEY, code),
                                               value)
            self._virtualState.addConstraint(constraint)
        else:
            if self._profile.findKeyProfile(code) is not None:
                self._fatal("a profile for the key is already defined")

            self._controlProfile = KeyProfile(code)
            self._controlHandlerTree = self._controlProfile.handlerTree

    def _startAxis(self, attrs):
        """Handle the axis start tag."""
        code = self._getControlCode(attrs, Axis.findCodeFor)

        control = Control(Control.TYPE_AXIS, code)
        constraint = self._getFromToValueConstraint(attrs, control)
        self._virtualState.addConstraint(constraint)

    def _startShift(self, attrs):
        """Start a shift handler."""
        shiftLevelIndex = self._shiftLevelIndex
        if shiftLevelIndex>=self._profile.numShiftLevels:
            self._fatal("too many shift handler levels")

        fromState = self._getIntAttribute(attrs, "fromState")
        toState = self._getIntAttribute(attrs, "toState")

        if toState<fromState:
            self._fatal("the to-state should not be less than the from-state")

        shiftLevel = self._profile.getShiftLevel(shiftLevelIndex)
        if (self._handlerTree.lastState+1)!=fromState:
            self._fatal("shift handler states are not contiguous")
        if toState>=shiftLevel.numStates:
            self._fatal("the to-state is too large")

        self._shiftContext.append(ShiftHandler(fromState, toState))

    def _startAction(self, attrs):
        if self._shiftLevelIndex!=self._profile.numShiftLevels:
            self._fatal("missing shift handler levels")

        if self._handlerTree.numChildren>0:
            self._fatal("a shift handler or a key profile can have only one action")

        type = Action.findTypeFor(self._getAttribute(attrs, "type"))
        if type is None:
            self._fatal("invalid type")

        if type==Action.TYPE_SIMPLE:
            self._action = SimpleAction(repeatDelay =
                                        self._findIntAttribute(attrs, "repeatDelay"))
        elif type==Action.TYPE_MOUSE_MOVE:
            direction = \
                MouseMoveCommand.findDirectionFor(self._getAttribute(attrs, "direction"))
            if direction is None:
                self._fatal("invalid direction")
            self._action = MouseMove(direction = direction,
                                     a = self._findFloatAttribute(attrs, "a"),
                                     b = self._findFloatAttribute(attrs, "b"),
                                     c = self._findFloatAttribute(attrs, "c"),
                                     adjust =
                                     self._findFloatAttribute(attrs, "adjust"),
                                     repeatDelay =
                                     self._findIntAttribute(attrs, "repeatDelay"))
        elif type==Action.TYPE_ADVANCED:
            self._action = AdvancedAction(repeatDelay =
                                          self._findIntAttribute(attrs, "repeatDelay"))
        else:
            self._fatal("unhandled action type")

    def _startKeyCombination(self, attrs):
        """Handle the keyCombination start tag."""
        if self._action.type!=Action.TYPE_SIMPLE:
            self._fatal("a key combination is valid only for a simple action")

        self._leftShift = self._findBoolAttribute(attrs, "leftShift")
        self._rightShift = self._findBoolAttribute(attrs, "rightShift")
        self._leftControl = self._findBoolAttribute(attrs, "leftControl")
        self._rightControl = self._findBoolAttribute(attrs, "rightControl")
        self._leftAlt = self._findBoolAttribute(attrs, "leftAlt")
        self._rightAlt = self._findBoolAttribute(attrs, "rightAlt")
        self._startCollectingCharacters()

    def _endKeyCombination(self):
        """Handle the keyCombination end tag."""
        keyName = self._getCollectedCharacters()
        code = Key.findCodeFor(keyName)
        if code is None:
            self._fatal("no valid code given for the key combination")

        self._action.addKeyCombination(code,
                                       self._leftShift, self._rightShift,
                                       self._leftControl, self._rightControl,
                                       self._leftAlt, self._rightAlt)

    def _startEnter(self, args):
        """Handle the enter start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("an enter tag is valid only for an advanced action")
        self._action.setSection(AdvancedAction.SECTION_ENTER)

    def _startRepeat(self, args):
        """Handle the repeat start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a repeat tag is valid only for an advanced action")
        self._action.setSection(AdvancedAction.SECTION_REPEAT)

    def _startLeave(self, args):
        """Handle the leave start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a leave tag is valid only for an advanced action")
        self._action.setSection(AdvancedAction.SECTION_LEAVE)

    def _startKeyPress(self, args):
        """Handle the keyPress start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a keypress is valid only for a simple action")
        self._startCollectingCharacters()

    def _endKeyPress(self):
        """Handle the keyPress end tag."""
        keyName = self._getCollectedCharacters()
        code = Key.findCodeFor(keyName)
        if code is None:
            self._fatal("no valid code given for the keypress")
        self._action.appendCommand(KeyPressCommand(code))

    def _startKeyRelease(self, args):
        """Handle the keyRelease start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a key release is valid only for a simple action")
        self._startCollectingCharacters()

    def _endKeyRelease(self):
        """Handle the keyRelase end tag."""
        keyName = self._getCollectedCharacters()
        code = Key.findCodeFor(keyName)
        if code is None:
            self._fatal("no valid code given for the keyrelease")
        self._action.appendCommand(KeyReleaseCommand(code))

    def _startDelay(self, args):
        """Handle the delay start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a delay is valid only for a simple action")
        self._startCollectingCharacters()

    def _endDelay(self):
        """Handle the delay end tag."""
        delayStr = self._getCollectedCharacters()
        try:
            delay = int(delayStr)
            if delay<0:
                self._fatal("a negative delay is not allowed")
            self._action.appendCommand(DelayCommand(delay))
        except:
            self._fatal("invalid delay value")

    def _endLeave(self):
        """Handle the leave end tag."""
        self._action.clearSection()

    def _endRepeat(self):
        """Handle the repeat end tag."""
        self._action.clearSection()

    def _endEnter(self):
        """Handle the enter end tag."""
        self._action.clearSection()

    def _endAction(self):
        """End the current action."""
        if self._action.type == Action.TYPE_SIMPLE:
            if not self._action.valid:
                self._fatal("simple action has no key combinations")
        elif self._action.type == Action.TYPE_ADVANCED:
            if not self._action.valid:
                self._fatal("advanced action has no commands")
        elif self._action.type == Action.TYPE_MOUSE_MOVE:
            pass
        else:
            self._fatal("unhandled action type")

        self._handlerTree.addChild(self._action)

        self._action = None

    def _endShift(self):
        """Handle the shift end tag."""
        shiftHandler = self._shiftContext[-1]

        if not shiftHandler.isComplete(self._numExpectedShiftStates):
            self._fatal("shift handler is missing either child shift level states or an action")

        del self._shiftContext[-1]

        self._handlerTree.addChild(shiftHandler)

    def _endKey(self):
        """Handle the key end tag."""

        if self._parent=="controls":
            if not self._controlHandlerTree.isComplete(self._numExpectedShiftStates):
                self._fatal("the key profile is missing either child shift level states or an action")

            self._profile.addControlProfile(self._controlProfile)
            self._controlProfile = None
            self._controlHandlerTree = None

    def _endJoystickProfile(self):
        """Handle the joystickProfile end tag."""
        if self._profile is None:
            self._fatal("empty 'joystickProfile' element")

    def _startCollectingCharacters(self):
        """Indicate that we can collect characters with the current
        tag."""
        self._characterContext.append("")

    def _getCollectedCharacters(self):
        """Get the collected characters, if any."""
        characters = self._characterContext[-1]
        assert characters is not None

        return characters.strip()

    def _appendCharacters(self, chars):
        """Append the given characters to the collected ones.

        If we are not allowed to callect, raise a fatal exception."""
        if self._characterContext[-1] is None:
            self._fatal("characters are not allowed here")
        self._characterContext[-1] += chars

    def _checkParent(self, element, *args):
        """Check if the last element of the context is the given
        one."""
        for parent in args:
            if self._context[-1]==parent:
                return

        self._fatal("tag '%s' should appear within any of %s" %
                    (element, ",".join(args)))

    def _findAttribute(self, attrs, name, default = None):
        """Find the attribute with the given name.

        If not found, return the given default value."""
        return attrs.get(name, default)

    def _getAttribute(self, attrs, name):
        """Get the attribute with the given name.

        If not found, raise a fatal error."""
        value = self._findAttribute(attrs, name)
        if value is None:
            self._fatal("expected attribute '%s'" % (name,))
        return value

    def _findParsableAttribute(self, attrs, name, parser, default = None):
        """Find the value of the given attribute if it should be
        parsed to produce a meaningful value.

        If the attribute is not found, return the given default
        value."""
        value = self._findAttribute(attrs, name)
        return default if value is None else parser(name, value)

    def _getParsableAttribute(self, attrs, name, parser):
        """Get the value of the given attribute if it should be
        parsed to produce a meaningful value.

        If the attribute is not found, raise a fatal error."""
        return parser(name, self._getAttribute(attrs, name))

    def _parseHexAttribute(self, name, value):
        """Parse the given hexadecimal value being the value of the
        attribute with the given name.

        If the parsing fails, raise a fatal error."""
        try:
            return int(value, 16)
        except:
            self._fatal("value of attribute '%s' should be a hexadecimal number" % (name,))

    def _findHexAttribute(self, attrs, name, default = None):
        """Find the value of the given attribute interpreted as a
        hexadecimal number."""
        return self._findParsableAttribute(attrs, name,
                                           self._parseHexAttribute,
                                           default = default)

    def _getHexAttribute(self, attrs, name):
        """Get the value of the given attribute interpreted as a
        hexadecimal number."""
        return self._getParsableAttribute(attrs, name,
                                          self._parseHexAttribute)

    def _parseIntAttribute(self, name, value):
        """Parse the given hexadecimal value being the value of the
        attribute with the given name.

        If the parsing fails, raise a fatal error."""
        try:
            if value.startswith("0x"):
                return int(value[2:], 16)
            elif value.startswith("0") and len(value)>1:
                return int(value[1:], 8)
            else:
                return int(value)
        except Exception, e:
            self._fatal("value of attribute '%s' should be an integer" % (name,))

    def _findIntAttribute(self, attrs, name, default = None):
        """Find the value of the given attribute interpreted as a
        decimal, octal or hexadecimal integer.

        If the attribute is not found, return the given default value."""
        return self._findParsableAttribute(attrs, name,
                                           self._parseIntAttribute,
                                           default = default)

    def _getIntAttribute(self, attrs, name):
        """Get the value of the given attribute interpreted as a
        decimal, octal or hexadecimal integer."""
        return self._getParsableAttribute(attrs, name, self._parseIntAttribute)

    def _parseBoolAttribute(self, name, value):
        """Parse the given boolean value being the value of the
        attribute with the given name.

        If the parsing fails, raise a fatal error."""
        value = value.lower()
        if value in ["yes", "true"]:
            return True
        elif value in ["no", "false"]:
            return False
        else:
            self._fatal("value of attribute '%s' should be a boolean" % (name,))

    def _findBoolAttribute(self, attrs, name, default = False):
        """Find the value of the given attribute interpreted as a
        boolean.

        If the attribute is not found, return the given default value."""
        return self._findParsableAttribute(attrs, name,
                                           self._parseBoolAttribute,
                                           default = default)

    def _getBoolAttribute(self, attrs, name):
        """Get the value of the given attribute interpreted as a boolean."""
        return self._getParsableAttribute(attrs, name, self._parseBoolAttribute)

    def _parseFloatAttribute(self, name, value):
        """Parse the given double value being the value of the
        attribute with the given name.

        If the parsing fails, raise a fatal error."""
        try:
            return float(value)
        except Exception, e:
            self._fatal("value of attribute '%s' should be a floating-point number" % (name,))

    def _findFloatAttribute(self, attrs, name, default = 0.0):
        """Find the value of the given attribute interpreted as a
        floating-point value.

        If the attribute is not found, return the given default value."""
        return self._findParsableAttribute(attrs, name,
                                           self._parseFloatAttribute,
                                           default = default)

    def _getFloatAttribute(self, attrs, name):
        """Get the value of the given attribute interpreted as a
        floating-point value."""
        return self._getParsableAttribute(attrs, name, self._parseFloatAttribute)

    def _getControlCode(self, attrs, getByNameFun):
        """Get the code of a control using the given attributes.

        It looks for either a 'code' attribure or 'name'. In the latter case
        getByNameFun() is called to retrieve the code for the name. It should
        receive the name and should return the code or None, if it is not found
        by the name."""
        if "code" in attrs:
            code = self._getIntAttribute(attrs, "code")
        elif "name" in attrs:
            code = getByNameFun(attrs["name"])

        if code is None:
            self._fatal("either a valid code or name is expected")

        return code

    def _getVirtualControl(self, attrs):
        """Get the virtual control from the given attributes.

        It should be either a 'code' attribute with a valid code for the
        virtual control, or a 'name' attribute with a valid name.

        Returns the virtual control, if found, otherwise fatal error is
        signalled."""
        code = self._getControlCode(attrs,
                                    self._profile.findVirtualControlCodeByName)

        virtualControl = self._profile.findVirtualControlByCode(code)
        if virtualControl is None:
            self._fatal("invalid code specified for virtual control")

        return virtualControl

    def _getFromToValue(self, attrs, minValue = None, maxValue = None):
        """Get a range of values from the given attributes.

        There should either be a 'value' attribute or a 'fromValue' and a
        'toValue'. They should be integers, and should be between the given
        limits, if any.

        Returns the tuple of the following:
        - the from value,
        - the to value."""

        if "fromValue" in attrs and "toValue" in attrs:
            fromValue = self._getIntAttribute(attrs, "fromValue")
            toValue = self._getIntAttribute(attrs, "toValue")
        elif "value" in attrs:
            fromValue = toValue = self._getIntAttribute(attrs, "value")
        else:
            self._fatal("expected either fromValue and toValue or value")

        if minValue is not None and fromValue<minValue:
            self._fatal("value should be at least %d" % (minValue,))
        if maxValue is not None and fromValue>maxValue:
            self._fatal("value should be at most %d" % (maxValue,))

        if minValue is not None and toValue<minValue:
            self._fatal("value should be at least %d" % (minValue,))
        if maxValue is not None and toValue>maxValue:
            self._fatal("value should be at most %d" % (maxValue,))

        if fromValue>toValue:
            self._fatal("fromValue should not be greater than toValue")

        return (fromValue, toValue)

    def _getFromToValueConstraint(self, attrs, control,
                                  minValue = None, maxValue = None):
        """Get a constraint for the given control based on the given
        attributes."""
        (fromValue, toValue) = self._getFromToValue(attrs,
                                                    minValue = minValue,
                                                    maxValue = maxValue)

        if fromValue==toValue:
            return SingleValueConstraint(control, fromValue)
        else:
            return ValueRangeConstraint(control, fromValue, toValue)

    def _fatal(self, msg, exception = None):
        """Raise a parse exception with the given message and the
        current location."""
        raise SAXParseException(msg, exception, self._locator)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class VirtualState(object):
    """A virtual state for a virtual control or a shift level.

    A virtual state corresponds to a certain set of values of one or more
    controls, such as keys (buttons). For example, a virtual state can be if
    the pinkie button is pressed. These controls and values are expressed using
    ShiftConstraint objects.

    If the state is a shift state, it can be empty shift state, meaning that
    the shift level is in that state if no other state is matched."""
    def __init__(self, value = None):
        """Construct the virtual state for the given numerical value."""
        self._value = value
        self._constraints = []

    @property
    def value(self):
        """Get the value of the state."""
        return self._value

    @value.setter
    def value(self, v):
        """Set the value of the virtual state, if it is not set yet."""
        assert self._value is None
        self._value = v

    @property
    def constraints(self):
        """Get an iterator over the constraints of the state."""
        return iter(self._constraints)

    @property
    def isDefault(self):
        """Determine if this state is a default state.

        A state is a default state, if it has no constraints or all constraints
        denote the default value."""
        for constraint in self._constraints:
            if not constraint.isDefault:
                return False

        return True

    @property
    def numConstraints(self):
        """Get the number of constraints defining the state."""
        return len(self._constraints)

    @property
    def isValid(self):
        """Determine if the state is valid.

        A state is valid if it does not contain constraints that refer to
        the same control but conflicting values."""
        # FIXME: implement doesConflict
        # numConstraints = len(self._constraints)
        # for i in range(0, numConstraints - 1):
        #     constraint = self._constraints[i]
        #     for j in range(i+1, numConstraints):
        #         if constraint.doesConflict(self._constraints[j]):
        #             return False
        return True

    def addConstraint(self, constraint):
        """Add a constraint to the state."""
        self._constraints.append(constraint)
        self._constraints.sort()

    def getXML(self, document):
        """Get an XML element describing this virtual state."""
        element = document.createElement("virtualState")

        for constraint in self._constraints:
            element.appendChild(constraint.getXML(document))

        return element

    def addControls(self, controls):
        """Add the controls involved in this constraint to the given set."""
        for constraint in self._constraints:
            controls.add(constraint.control)

    def getLuaCondition(self, profile):
        """Get the Lua expression to evaluate the condition for this virtual
        state being active."""
        expression = ""
        for constraint in self._constraints:
            if expression: expression += " and "
            expression += constraint.getLuaExpression(profile)
        return expression

    def __cmp__(self, other):
        """Compare this virtual state with the other one.

        If this an empty state, it matches any other state that is also empty
        or contains only constraint that match the default value."""
        if self._constraints:
            if other._constraints:
                x = cmp(len(self._constraints), len(other._constraints))
                if x==0:
                    for index in range(0, len(self._constraints)):
                        x = cmp(self._constraints[index],
                                other._constraints[index])
                        if x!=0: break
                return x
            else:
                return 0 if self.isDefault else 1
        elif other._constraints:
            return 0 if other.isDefault else -1
        else:
            return 0

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class VirtualControlBase(object):
    """The base class for virtual controls.

    A virtual control has a number of states each corresponding to a certain
    discrete, integer value startin from 0. Values of other controls determine
    which state a virtual control is in."""
    def __init__(self, needDefault = True):
        """Construct the object with no states."""
        self._states = []
        self._needDefault = needDefault

    @property
    def states(self):
        """Get an iterator over the states of the control."""
        return iter(self._states)

    @property
    def numStates(self):
        """Get the number of states of the control."""
        return len(self._states)

    @property
    def isValid(self):
        """Determine if the shift level is valid.

        It is valid if it has at least two states and all of the states are
        valid. It should also have exactly one default state"""
        if self.numStates<2:
            return False

        hadDefault = False
        for state in self._states:
            if not state.isValid:
                return False
            if state.isDefault:
                if hadDefault:
                    return False
                hadDefault = True

        return hadDefault or not self._needDefault

    def addState(self, virtualState):
        """Add the given state to the control and return it.

        It first checks if the shift state is different from every other state.
        If not, False is returned. Otherwise the new state is added and True is
        returned."""
        for state in self._states:
            if virtualState==state:
                return False

        virtualState.value = len(self._states)
        self._states.append(virtualState)

        return True

    def getXML(self, document):
        """Get the XML code describing this virtual control."""
        element = self._createXMLElement(document)

        for state in self._states:
            stateElement = state.getXML(document)
            element.appendChild(stateElement)

        return element

    def getControls(self):
        """Get the set of controls that are involved in computing the state
        of this shift level."""
        controls = set()
        for state in self._states:
            state.addControls(controls)
        return controls

    def getValueLuaCode(self, profile, valueVariableName):
        """Get the Lua code to compute the value of this virtual control.

        valueVariableName is the name of the variable that should contain the
        computed value.

        Returns an array of lines."""
        lines = []

        defaultValue = None
        for state in self._states:
            if state.isDefault:
                defaultValue = state.value
            else:
                ifStatement = "elseif" if lines else "if"
                lines.append(ifStatement + " " +
                             state.getLuaCondition(profile) + " then")
                lines.append("  %s = %d" % (valueVariableName, state.value))

        assert defaultValue is not None or not self._needDefault
        if defaultValue is not None:
            lines.append("else")
            lines.append("  %s = %d" % (valueVariableName, defaultValue))
        lines.append("end")

        return lines

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class VirtualControl(VirtualControlBase):
    """A virtual control on the joystick."""
    @staticmethod
    def checkName(name):
        """Check if the given name fulfils the requirements.

        It should start with a letter and the further characters should be
        letters, numbers or underscores."""
        first = True
        for c in name:
            if ord(c)>=128 or not ((first and c.isalpha()) or \
                                   (not first and (c.isalnum() or c=='_'))):
                return False
            first = False
        return True

    def __init__(self, name, code):
        """Construct the virtual control with the given name and code."""
        super(VirtualControl, self).__init__(needDefault = False)
        self._name = name
        self._code = code

    @property
    def name(self):
        """Get the name of the control."""
        return self._name

    @property
    def code(self):
        """Get the code of the control."""
        return self._code

    @property
    def control(self):
        """Get the control representing this virtual control."""
        return Control(Control.TYPE_VIRTUAL, self._code)

    @property
    def stateLuaVariableName(self):
        """Get the name of the variable containing the state of this
        control."""
        return "_jsprog_virtual_%s_state" % (self._name,)

    @property
    def stateLuaFunctionName(self):
        """Get the name of the function updating the state of this control."""
        return "_jsprog_virtual_%s_updateState" % (self._name,)

    def getStateLuaCode(self, profile):
        """Get the code computing the state of this virtual control."""
        stateName = self.stateLuaVariableName
        return super(VirtualControl, self).getValueLuaCode(profile, stateName)

    def _createXMLElement(self, document):
        """Create the XML element corresponding to this virtual control."""
        element = document.createElement("virtualControl")
        element.setAttribute("name", self._name)
        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class Control(object):
    """A representation of a control, i.e. a key (button) or an axis."""
    ## Control type: a key
    TYPE_KEY = 1

    ## Control type: an axis
    TYPE_AXIS = 2

    ## Control type: a virtual control
    TYPE_VIRTUAL = 3

    # The current joystick profile to resolve the names of virtual controls
    _currentProfile = None

    @staticmethod
    def setProfile(profile):
        """Set the current profile to resolve virtual controls."""
        Control._currentProfile = profile

    def __init__(self, type, code):
        """Construct the control of the given type and code."""
        self._type = type
        self._code = code

    @property
    def type(self):
        """Get the type of the control."""
        return self._type

    @property
    def code(self):
        """Get the code of the control."""
        return self._code

    @property
    def defaultValue(self):
        """Get the default value of the control.

        For keys this is 0 (not pressed), for axes it is None, since no default
        value can be defined there."""
        return 0 if self._type==Control.TYPE_KEY else None

    @property
    def isKey(self):
        """Determine if the control object represents a key."""
        return self._type==Control.TYPE_KEY

    @property
    def isAxis(self):
        """Determine if the control object represents an axis."""
        return self._type==Control.TYPE_AXIS

    @property
    def isVirtual(self):
        """Determine if the control object represents a virtual control."""
        return self._type==Control.TYPE_VIRTUAL

    @property
    def name(self):
        """Get the name of this control based on the code and the type."""
        if self.isKey:
            return Key.getNameFor(self._code)
        elif self.isAxis:
            return Axis.getNameFor(self._code)
        elif self.isVirtual:
            if Control._currentProfile is not None:
                virtualControl = \
                  Control._currentProfile.findVirtualControlByCode(self._code)
                if virtualControl is not None:
                    return "virtual_%s" % (virtualControl.name,)
            return "virtual_%d" % (self._code,)
        else:
            return "unknown_%d_%d" % (self._type, self._code)

    @property
    def luaIDName(control):
        """Get the name of the variable containing the ID of the control."""
        return "jsprog_%s" % (control.name,)

    @property
    def luaValueName(control):
        """Get the name of the Lua variable containing the current value of the
        control."""
        # FIXME: perhaps call the value of a virtual control also 'value'
        # instead of 'state'
        return "_jsprog_%s_%s" % (control.name,
                                  "state" if control.isVirtual else "value")

    def getConstraintXML(self, document):
        """Get the XML element for a constraint involving this control."""
        element = document.createElement("key" if self._type==Control.TYPE_KEY
                                         else "axis")
        element.setAttribute("name", self.name)
        return element

    def __hash__(self):
        """Compute a hash value for the control."""
        return hash(self._type) ^ hash(self._code)

    def __cmp__(self, other):
        """Compare the control with the given other one."""
        x = cmp(self._type, other._type)
        if x==0:
            x = cmp(self._code, other._code)
        return x

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ControlConstraint(object):
    """Base class for objects that represent some constraint on the value of a
    certain control."""
    ## Constraint type: single value
    TYPE_SINGLE_VALUE = 1

    ## Constraint type: value range
    TYPE_VALUE_RANGE = 2

    def __init__(self, control):
        """Construct the constraint for the given control."""
        self._control = control

    @property
    def control(self):
        """Get the control the constraint belongs to."""
        return self._control

    def __cmp__(self, other):
        """Compare the constraint with the given other one for ordering.

        This one first compares the controls then the types (classes) of the
        constraints."""
        x = cmp(self._control, other._control)
        if x==0:
            x = cmp(self.__class__, other.__class__)
        return x

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class SingleValueConstraint(ControlConstraint):
    """A constraint that matches a single value of a certain control."""
    def __init__(self, control, value):
        """Construct the constraint for the given value."""
        super(SingleValueConstraint, self).__init__(control)
        self._value = value

    @property
    def type(self):
        """Get the type of this constraint."""
        return ControlConstraint.TYPE_SINGLE_VALUE

    @property
    def value(self):
        """Get the value of the constraint."""
        return self._value

    @property
    def isDefault(self):
        """Determine if the value refers to the default value of the
        constraint."""
        return self._value == self._control.defaultValue

    def getXML(self, document):
        """Get the XML representation of this constraint.

        It queries the control for a suitable XML element and then adds a value
        attribute."""
        element = self._control.getConstraintXML(document)
        element.setAttribute("value", str(self._value))
        return element

    def getLuaExpression(self, profile):
        """Get the Lua expression to evaluate this constraint."""
        return "%s == %d" % (self._control.luaValueName, self._value)

    def __cmp__(self, other):
        """Compare the constraint with the given other one.

        If the base comparison finds equality, this one compares the values."""
        x = super(SingleValueConstraint, self).__cmp__(other)
        if x==0:
            x = cmp(self._value, other._value)
        return x

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ValueRangeConstraint(ControlConstraint):
    """A constraint that matches a contiguous range of values of a certain
    control."""
    def __init__(self, control, fromValue, toValue):
        """Construct the constraint for the given value."""
        super(ValueRangeConstraint, self).__init__(control)
        self._fromValue = fromValue
        self._toValue = toValue

    @property
    def type(self):
        """Get the type of this constraint."""
        return ControlConstraint.TYPE_VALUE_RANGE

    @property
    def fromValue(self):
        """Get the from-value of the constraint."""
        return self._fromValue

    @property
    def toValue(self):
        """Get the to-value of the constraint."""
        return self._toValue

    @property
    def isDefault(self):
        """Determine if the value refers to the default value of the
        constraint."""
        return self._fromValue <= self._control.defaultValue and \
               self._toValue >= self._control.defaultValue

    def getXML(self, document):
        """Get the XML representation of this constraint.

        It queries the control for a suitable XML element and then adds a value
        attribute."""
        element = self._control.getConstraintXML(document)
        element.setAttribute("fromValue", str(self._fromValue))
        element.setAttribute("toValue", str(self._toValue))
        return element

    def getLuaExpression(self, profile):
        """Get the Lua expression to evaluate this constraint."""
        if self._fromValue == self._toValue:
            return "%s == %d" % (self._control.luaValueName, self._fromValue)
        else:
            return "%s >= %d and %s <= %d" % (self._control.luaValueName,
                                              self._fromValue,
                                              self._control.luaValueName,
                                              self._toValue)

    def __cmp__(self, other):
        """Compare the constraint with the given other one.

        If the base comparison finds equality, this one compares the values."""
        x = super(ValueRangeConstraint, self).__cmp__(other)
        if x==0:
            x = cmp(self._fromValue, other._fromValue)
        if x==0:
            x = cmp(self._toValue, other._toValue)
        return x

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftLevel(VirtualControlBase):
    """A level in the shift tree.

    Since the actual value of a shift level is determined by a number of shift
    states, it is basically a virtual control."""
    def __init__(self):
        """Construct the shift level."""
        self._states = []

    def getStateLuaCode(self, profile, levelIndex):
        """Get the Lua code to compute the state of this shift level.

        Returns an array of lines."""
        stateName = getShiftLevelStateName(levelIndex)
        return super(ShiftLevel, self).getValueLuaCode(profile, stateName)

    def _createXMLElement(self, document):
        """Get an XML element describing this shift level."""
        return document.createElement("shiftLevel")


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class HandlerTree(object):
    """The root of a tree of shift handlers and actions."""
    def __init__(self):
        """Construct an empty tree."""
        self._children = []

    @property
    def children(self):
        """Get the list of child handlers of the shift handler."""
        return self._children

    @property
    def numChildren(self):
        """Get the number of children."""
        return len(self._children)

    @property
    def lastState(self):
        """Get the last state handled by the children, if they are
        shift handlers.

        If there are no children, -1 is returned."""
        return self._children[-1]._toState if self._children else -1

    def addChild(self, handler):
        """Add a child handler."""
        assert \
            (isinstance(handler, Action) and not
             self._children) or \
            (isinstance(handler, ShiftHandler) and
             handler._fromState == (self.lastState+1))

        self._children.append(handler)

    def isComplete(self, numStates = 0):
        """Determine if the tree is complete.

        numStates is the number of states expected at the tree's
        level. If the tree contains a clear handler, numStates is 0,
        and the tree is complete if there is one key
        handler. Otherwise the last state should equal to the number
        of states - 1."""
        return len(self._children)==1 if numStates==0 \
            else (self.lastState+1)==numStates

    def foldStates(self, control, numStates, numShiftLevels, fun, acc = None,
                   branchFun = None, branchAcc = None):
        """Fold over the distinct states.

        A distinct state is one for which an action belongs but may cover more
        than one shift states.

        control is the control for which the states are being folded

        numStates is the number of states encountered so far.

        numShiftLevels is the shift levels after the one handled by this tree.

        fun is the function to call. It receives the following arguments:
        - the control,
        - the 1-based index of the state,
        - the child,
        - an arbitray accumulator.
        It is expected to return a new value of the accumulator.

        acc is the value of the accumulator.

        branchFun is an optional function to call for the branches of the
        tree. It is called with the following arguments:
        - the control,
        - the child,
        - a boolean indicating if the call is before or after calling
          foldStates on the child
        - the accumulator.
        It is expected to return a new value of the accumulator.

        This function returns a tuple of:
        - the new number of states,
        - the new value of the accumulator, and
        - if branchFun is given, the new value of branchAcc."""
        if numShiftLevels==0:
            for child in self._children:
                numStates += 1
                acc = fun(control, numStates, child, acc)
        else:
            for child in self._children:
                if branchFun is not None:
                    branchAcc = branchFun(control, child, True, branchAcc)
                    (numStates, acc, branchAcc) = \
                        child.foldStates(control, numStates, numShiftLevels - 1,
                                         fun, acc = acc,
                                         branchFun = branchFun,
                                         branchAcc = branchAcc)
                    branchAcc = branchFun(control, child, False, branchAcc)
                else:
                    (numStates, acc) = \
                        child.foldStates(control, numStates, numShiftLevels - 1,
                                         fun, acc)

        return (numStates, acc) if branchFun is None \
               else (numStates, acc, branchAcc)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftHandler(HandlerTree):
    """Handler for a certain value or set of values for a shift
    level.

    Zero or more shift levels can be specified each having a value
    from 0 to a certain positive value (e.g. 1 in case of a single key
    (i.e. button) - 0=not pressed, 1=pressed). The shift levels are specified
    in a certain order and thus they form a hierarchy.

    Each shift level consists of at least two shift states which are entered by
    setting certain controls to certain values, e.g. by pressing a button or
    two or more buttons at the same time.

    For each key or other control the actual handlers should be
    specified in the context of the shift state. This context is
    defined by a hierarchy of shift handlers corresponding to the
    hierarchy of shift controls.

    Let's assume, that the state of button A determines the first shift level
    and button B determines the second one. Then for each key we have one
    or more shift handlers describing one or more states
    (i.e. released and/or pressed) for button A. Each such shift
    handler contains one or more similar shift handlers for button
    B. The shift handlers for button B contain the actual key
    handlers.

    A shift handler may specify more than one possible states for the
    shift control, and it may specify all states, making the shift
    control irrelevant for the key as only the other shift controls,
    if any, determine what the key does. Thus, by carefully ordering
    the shift controls, it is possible to eliminate repetitions of key
    handlers.

    It should be noted, that in the XML profile, the shift handlers
    for one level should follow each other in the order of the states,
    and all states should be covered at each level. Otherwise the
    profile is rejected by the parser."""
    @staticmethod
    def _addIfStatementFor(control, shiftHandler, before,
                           (profile, lines, level, indentation)):
        """Get the if statement for the given shift handler."""
        shiftLevel = profile.getShiftLevel(level if before else (level-1))
        fromStart = shiftHandler._fromState==0
        toEnd = shiftHandler._toState>=(shiftLevel.numStates-1)
        needIf = not fromStart or not toEnd
        if before:
            if needIf:
                ind = indentation[0]
                if toEnd:
                    lines.append(ind + "else")
                else:
                    shiftStateName = getShiftLevelStateName(level)
                    ifStatement = "if" if fromStart else "elseif"
                    if shiftHandler._fromState==shiftHandler._toState:
                        lines.append(ind + "%s %s==%d then" %
                                     (ifStatement, shiftStateName,
                                      shiftHandler._fromState))
                    else:
                        lines.append(ind + "%s %s>=%d and %s<=%d then" %
                                     (ifStatement, shiftStateName,
                                      shiftHandler._fromState,
                                      shiftStateName, shiftHandler._toState))
                indentation[0] += "  "
            return (profile, lines, level + 1, indentation)
        else:
            if needIf:
                indentation[0] = indentation[0][:-2]
                if toEnd:
                    lines.append(indentation[0] + "end")
            return (profile, lines, level - 1, indentation)

    def __init__(self, fromState, toState):
        """Construct the shift handler to handle the states between
        the given ones (both inclusive)."""
        assert toState >= fromState

        super(ShiftHandler, self).__init__()

        self._fromState = fromState
        self._toState = toState

    @property
    def fromState(self):
        """Get the starting state for the shift handler."""
        return self._fromState

    @property
    def toState(self):
        """Get the ending state for the shift handler."""
        return self._toState


    def getXML(self, document):
        """Get the XML element describing this shift handler."""
        element = document.createElement("shift")
        element.setAttribute("fromState", str(self._fromState))
        element.setAttribute("toState", str(self._toState))

        for child in self._children:
            element.appendChild(child.getXML(document))

        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ControlProfile(object):
    """Base class for the profiles of controls (keys, axes or virtual ones)."""
    @staticmethod
    def getUpdateLuaFunctionName(control):
        """Get the name of the function to update the shifted state of the
        given control."""
        return "_jsprog_%s_update" % (control.name,)

    @staticmethod
    def _getEnterLuaFunctionName(control, stateIndex):
        """Get the name of the function to be called when the given  control
        enters into the state with the given index.

        It returns a tuple of:
        - the name of the function,
        - the name of the array containing the function objects."""
        return ("_jsprog_%s_enter%d" % (control.name, stateIndex),
                "_jsprog_%s_enterFunctions" % (control.name,))

    @staticmethod
    def _getLeaveLuaFunctionName(control, stateIndex):
        """Get the name of the function to be called when the given control
        leaves the state with the given index.

        It returns a tuple of:
        - the name of the function,
        - the name of the array containing the function objects."""
        return ("_jsprog_%s_leave%d" % (control.name, stateIndex),
                "_jsprog_%s_leaveFunctions" % (control.name,))

    @staticmethod
    def _generateActionLuaFunction(control, stateIndex, action,
                                   (codeFun, nameFun, lines, hasCode)):
        """Generate a Lua function for the given action either when entering
        its state or when leaving it.

        control is the control for which code is being generated.

        stateIndex is the 1-based index of the state.

        action is the action to use for code generation.

        codeFun is the function to call to get the code. It has the following
        arguments:
        - the action,
        - the control.
        It returns the list of Lua code lines making up the function. If an
        empty list is returned, no function is generated.

        nameFun is the function to call to get the function's name. It has the
        following arguments:
        - the control,
        - the state index.
        It returns a tuple consisting of:
        - the name of the function,
        - the name of the array containing the function objects.

        lines is the list of lines which will possibly be extended.

        hasCode is a list of booleans indicating if the corresponding state has
        any code, i.e. any function.

        It returns the tuple of:
        - the code generator function,
        - the name generator function,
        - the possibly extended list of code lines,
        - the extended list of booleans indicating the presence of a function
        for the corresponding state."""
        functionLines = codeFun(action, control)

        if functionLines:
            if lines: lines.append("")

            (functionName, _) = nameFun(control, stateIndex)
            lines.append("function %s()" % (functionName,))
            appendLinesIndented(lines, functionLines, "  ")
            lines.append("end")

        hasCode.append(not not functionLines)
        return (codeFun, nameFun, lines, hasCode)

    @staticmethod
    def _getShiftedStateLuaFunctionName(control):
        """Get the name of the function to calculate the shifted state of the
        given control."""
        return "_jsprog_%s_getShiftedState" % (control.name,)

    @staticmethod
    def _appendStateReturnLuaCode(control, stateIndex, action,
                                  (lines, indentation)):
        """Append the Lua code for returning the state index."""
        lines.append(indentation[0] + "return %d" % (stateIndex,))
        return (lines, indentation)

    @staticmethod
    def _getLuaShiftedStateName(control):
        """Get the name of the shifted state of the control in the Lua code."""
        return "_jsprog_%s_shiftedState" % (control.name,)

    def __init__(self, control):
        """Construct the profile for the given control."""
        self._control = control
        self._profile = None

    @property
    def control(self):
        """Get the control of the profile."""
        return self._control

    @property
    def code(self):
        """Get the code of the profile's control."""
        return self._control.code

    @property
    def profile(self):
        """Get the joystick profile this control profile belongs to."""
        return self._profile

    @profile.setter
    def profile(self, profile):
        """Set the joystick profile this control profile belongs to.

        It can be set only once."""
        assert self._profile is None
        self._profile = profile

    def getPrologueLuaCode(self, profile):
        """Get the Lua code to put into the prologue for the control."""
        lines = self._getEnterLuaFunctions(profile)
        leaveLines = self._getLeaveLuaFunctions(profile)
        if leaveLines:
            if lines: lines.append("")
            lines += leaveLines

        if lines: lines.append("")
        lines += self._getShiftedStateLuaFunction(profile)

        if lines: lines.append("")
        lines += self._getUpdateLuaFunction(profile)

        return lines

    def _getEnterLuaFunctions(self, profile):
        """Get the code of the Lua functions for entering the various
        shift states of the control.

        profile is the joystick profile.

        Returns a list of Lua code lines."""
        lines = []
        lines.append("%s = nil" %
                     (RepeatableAction.getRepeatFlagLuaName(self._control),))
        lines.append("%s = { nil }" %
                     (RepeatableAction.getThreadLuaName(self._control),))
        lines.append("")

        lines += self._getActionLuaFunctions(profile,
                                             lambda action, control:
                                             action.getEnterLuaCode(control),
                                             ControlProfile._getEnterLuaFunctionName)

        return lines

    def _getLeaveLuaFunctions(self, profile):
        """Get the code of the Lua functions for leaving the various shift
        states of the control.

        profile is the joystick profile.

        Returns a list of Lua code lines."""
        return self._getActionLuaFunctions(profile,
                                           lambda action, control:
                                           action.getLeaveLuaCode(control),
                                           ControlProfile._getLeaveLuaFunctionName)

    def _getActionLuaFunctions(self, profile, codeFun, nameFun):
        """Get the code for the Lua functions of entering or leaving the
        various states of the virtual control.

        profile is the joystick profile.

        codeFun is the function to call to get the code. It has the following
        arguments:
        - the action,
        - the control.
        It returns the list of Lua code lines making up the function. If an
        empty list is returned, no function is generated.

        nameFun is the function to call to get the function's name. It has the
        following arguments:
        - the control,
        - the shift state index.
        It returns a tuple consisting of:
        - the name of the function,
        - the name of the array containing the function objects.

        It calls the _getActionLuaFunctionCode() function that is to be
        implemented in the various child classes.

        The function returns the Lua code lines consisting of the codes of the
        functions as well as array definitions with the functions."""
        (lines, hasCode) = self._getActionLuaFunctionCode(profile, codeFun,
                                                          nameFun)
        if lines: lines.append("")

        (_, arrayName) = nameFun(self._control, 0)
        lines.append("%s = {" % (arrayName,))

        index = 1
        for hc in hasCode:
            if hc:
                (functionName, _) = nameFun(self._control, index)
                lines.append("  %s," % (functionName,))
            else:
                lines.append("  nil,")
            index += 1

        lines.append("}")

        return lines

    def _getShiftedStateLuaCodeFor(self, handlerTree, profile,
                                   numStates, lines, indentation):
        """Get the code to compute the shifted state according to the given
        handler tree.

        profile is the joystick profile to use.

        numStates is the number of states processed and lines is the
        array of code lines generated so far

        Returns a tuple of:
        - the number if states processed including the previously processed
          ones,
        - the Lua code lines extended with the ones generated here."""
        (numStates, (lines, _), _) = \
            handlerTree.foldStates(self._control, numStates,
                                   profile.numShiftLevels,
                                   ControlProfile._appendStateReturnLuaCode,
                                   acc = (lines, indentation),
                                   branchFun = ShiftHandler._addIfStatementFor,
                                   branchAcc = (profile, lines, 0, indentation))
        return (numStates, lines)

    def _getShiftedStateLuaFunction(self, profile):
        """Get the code of the Lua function to compute the shifted state of the
        key."""
        lines = []

        if not self._control.isVirtual:
            lines.append("%s = 0" % (self._control.luaValueName,))
            lines.append("")

        lines.append("function %s()" %
                     (ControlProfile._getShiftedStateLuaFunctionName(self._control)))

        appendLinesIndented(lines,
                            self._getShiftedStateLuaFunctionBody(profile))

        lines.append("end")

        return lines

    def _getUpdateLuaFunction(self, profile):
        """Get the code of the Lua function to update the state of the control
        and call the functions doing it."""
        lines = []

        stateName =  ControlProfile._getLuaShiftedStateName(self._control)

        lines.append("%s = 0" % (stateName,))
        lines.append("")

        functionName = ControlProfile.getUpdateLuaFunctionName(self._control)
        lines.append("function %s()" % (functionName,))
        lines.append("  local oldState = %s" % (stateName,))
        lines.append("  local newState = %s()" %
                     (ControlProfile._getShiftedStateLuaFunctionName(self._control),))

        (_, enterFunctionsName) = \
          ControlProfile._getEnterLuaFunctionName(self._control, 0)
        (_, leaveFunctionsName) = \
          ControlProfile._getLeaveLuaFunctionName(self._control, 0)

        lines.append("  if newState ~= oldState then")
        lines.append("    %s = newState" % (stateName,))
        lines.append("")
        lines.append("    if newState == 0 then")
        lines.append("      _jsprog_updaters_remove(%s)" % (functionName))
        lines.append("    elseif oldState == 0 then")
        lines.append("      _jsprog_updaters_add(%s)" % (functionName))
        lines.append("    end")
        lines.append("")
        lines.append("    if oldState > 0 then")
        lines.append("      local fn = %s[oldState]" % (leaveFunctionsName,))
        lines.append("      if fn then fn() end")
        lines.append("    end")
        lines.append("    if newState > 0 then")
        lines.append("      local fn = %s[newState]" % (enterFunctionsName,))
        lines.append("      if fn then fn() end")
        lines.append("    end")
        lines.append("  end")

        lines.append("end")

        return lines

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class KeyProfile(ControlProfile):
    """The profile for a key.

    It maintains a tree of handlers the leaves of which are key
    handlers, and the other nodes (if any) are shift handlers each
    level of them corresponding to a shift level."""
    def __init__(self, code):
        """Construct the key profile for the given key code."""
        super(KeyProfile, self).__init__(Control(Control.TYPE_KEY, code))

        self._handlerTree = HandlerTree()

    @property
    def handlerTree(self):
        """Get the handler tree for the key's pressed value."""
        return self._handlerTree

    def getXML(self, document):
        """Get the XML element describing the key profile."""
        element = document.createElement("key")
        element.setAttribute("name", self._control.name)

        for child in self._handlerTree.children:
            element.appendChild(child.getXML(document))

        return element

    def getDaemonXML(self, document, profile):
        """Get the XML element for the XML document to be sent to the
        daemon."""
        element = document.createElement("key")

        element.setAttribute("name", Key.getNameFor(self.code))

        luaCode = self.getLuaCode(profile)
        luaText = "\n" + linesToText(luaCode, indentation = "    ")

        element.appendChild(document.createTextNode(luaText))

        return element

    def getLuaCode(self, profile):
        """Get the Lua code for the key."""
        lines = []
        lines.append("%s = value" % (self._control.luaValueName,))
        lines.append("%s()" %
                     (ControlProfile.getUpdateLuaFunctionName(self._control),))
        return lines

    def _getActionLuaFunctionCode(self, profile, codeFun, nameFun):
        """Get the code for the Lua functions of entering or leaving the
        various states of the virtual control.

        The arguments are the same as for _getActionLuaFunctions().

        It returns a tuple of:
        - the lines of code containing the functions,
        - a boolean array indicating whether there is a function for the state
        corresponding the index into the array + 1."""
        (numStates, (_, _, lines, hasCode)) = \
          self._handlerTree.foldStates(self._control, 0, profile.numShiftLevels,
                                       ControlProfile._generateActionLuaFunction,
                                       (codeFun, nameFun, [], []))

        return (lines, hasCode)

    def _getShiftedStateLuaFunctionBody(self, profile):
        """Get the code of the Lua function to compute the shifted state of the
        key."""
        lines = []

        lines.append("if %s==0 then" % (self._control.luaValueName,))
        lines.append("  return 0")
        lines.append("else")

        indentation = ["  "]
        (numStates, lines) = \
            self._getShiftedStateLuaCodeFor(self._handlerTree, profile,
                                            0, lines, indentation)

        lines.append("end")

        return lines

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class VirtualControlProfile(ControlProfile):
    """The profile for a virtual control.

    It maintains a tree of handlers the leaves of which are actions,
    and the other nodes (if any) are shift handlers each level of them
    corresponding to a shift level."""
    def __init__(self, code):
        """Construct the vitual control profile for the given code."""
        control = Control(Control.TYPE_VIRTUAL, code)
        super(VirtualControlProfile, self).__init__(control)

        self._handlerTrees = {}

    def hasHandlerTree(self, state):
        """Determine if there is a handler tree for the given state."""
        return state in self._handlerTrees

    def getHandlerTree(self, state):
        """Get the handler tree for the given state.

        If it does not exist yet, it will be created."""
        if state not in self._handlerTrees:
            self._handlerTrees[state] = HandlerTree()

        return self._handlerTrees[state]

    def getXML(self, document):
        """Get the XML element describing the key profile."""
        element = document.createElement("virtualControl")
        virtualControl = self._profile.findVirtualControlByCode(self.code)
        element.setAttribute("name", virtualControl.name)

        states = self._handlerTrees.keys()
        states.sort()
        for state in states:
            virtualStateElement = document.createElement("virtualState")
            virtualStateElement.setAttribute("value", str(state))
            for child in self._handlerTrees[state].children:
                virtualStateElement.appendChild(child.getXML(document))
            element.appendChild(virtualStateElement)

        return element

    def getDaemonXML(self, document, profile):
        """Get the XML element for the XML document to be sent to the
        daemon."""
        return None

    def _getActionLuaFunctionCode(self, profile, codeFun, nameFun):
        """Get the code for the Lua functions of entering or leaving the
        various states of the virtual control.

        The arguments are the same as for _getActionLuaFunctions().

        It returns a tuple of:
        - the lines of code containing the functions,
        - a boolean array indicating whether there is a function for the state
        corresponding the index into the array + 1."""
        virtualControl = profile.findVirtualControlByCode(self.code)

        lines = []
        hasCode = []
        numStates = 0

        for controlState in range(0, virtualControl.numStates):
            if controlState in self._handlerTrees:
                handlerTree = self._handlerTrees[controlState]
                (numStates, (_, _, lines, hasCode)) = \
                    handlerTree.foldStates(self._control, numStates,
                                           profile.numShiftLevels,
                                           ControlProfile._generateActionLuaFunction,
                                           (codeFun, nameFun, lines, hasCode))

        return (lines, hasCode)

    def _getShiftedStateLuaFunctionBody(self, profile):
        """Get the code of the Lua function to compute the shifted state of the
        key."""
        lines = []

        virtualControl = profile.findVirtualControlByCode(self.code)

        stateName = virtualControl.stateLuaVariableName

        numStates = 0
        ifStatement = "if"
        indentation = ["  "]
        for controlState in range(0, virtualControl.numStates):
            if controlState in self._handlerTrees:
                lines.append("%s %s==%d then" %
                             (ifStatement, stateName, controlState))
                handlerTree = self._handlerTrees[controlState]
                (numStates, lines) = \
                  self._getShiftedStateLuaCodeFor(handlerTree, profile,
                                                  numStates, lines,
                                                  indentation)

                ifStatement = "elseif"

        lines.append("end")
        lines.append("return 0")

        return lines

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class Profile(object):
    """A joystick profile."""
    @staticmethod
    def loadFrom(directory):
        """Load the profiles in the given directory.

        Returns a list of the loaded profiles."""
        profiles = []

        parser = make_parser()

        handler = ProfileHandler()
        parser.setContentHandler(handler)

        for entry in os.listdir(directory):
            path = os.path.join(directory, entry)
            if entry.endswith(".profile") and os.path.isfile(path):
                try:
                    parser.parse(path)
                    profiles.append(handler.profile)
                except Exception, e:
                    print >> sys.stderr, e

        return profiles

    @staticmethod
    def getTextXML(document, name, text):
        """Create a tag with the given name containing the given
        text."""
        element = document.createElement(name)
        value = document.createTextNode(text)
        element.appendChild(value)
        return element

    @staticmethod
    def getInputIDXML(document, inputID):
        """Get the XML representation of the given input ID."""
        inputIDElement = document.createElement("inputID")

        inputIDElement.setAttribute("busType", inputID.busName)
        inputIDElement.setAttribute("vendor", "%04x" % (inputID.vendor,))
        inputIDElement.setAttribute("product", "%04x" % (inputID.product,))
        inputIDElement.setAttribute("version", "%04x" % (inputID.version,))

        return inputIDElement

    @staticmethod
    def getIdentityXML(document, identity):
        """Get the XML representation of the given identity."""
        identityElement = document.createElement("identity")

        inputIDElement = Profile.getInputIDXML(document, identity.inputID)
        identityElement.appendChild(inputIDElement)

        identityElement.appendChild(Profile.getTextXML(document,
                                                       "name",
                                                       identity.name))

        identityElement.appendChild(Profile.getTextXML(document,
                                                       "phys",
                                                       identity.phys))

        if identity.uniq is not None:
            identityElement.appendChild(Profile.getTextXML(document,
                                                           "uniq",
                                                           identity.uniq))

        return identityElement

    @staticmethod
    def getShiftLevelStateLuaFunctionName(levelIndex):
        """Get the name of the function to update the state of the shift level
        with the given index."""
        return "_jsprog_shiftLevel%d_update" % (levelIndex,)

    def __init__(self, name, identity, autoLoad = False):
        """Construct an empty profile for the joystick with the given
        identity."""
        self.name = name
        self.identity = identity
        self.autoLoad = autoLoad

        self._virtualControls = []

        self._shiftLevels = []

        self._controlProfiles = []
        self._controlProfileMap = {}

    @property
    def hasVirtualControls(self):
        """Determine if we have any virtual controls."""
        return bool(self._virtualControls)

    @property
    def hasControlProfiles(self):
        """Determine if we have control (key or axis) profiles or not."""
        return bool(self._controlProfiles)

    @property
    def numShiftLevels(self):
        """Determine the number of shift levels."""
        return len(self._shiftLevels)

    def match(self, identity):
        """Get the match level for the given joystick identity."""
        return self.identity.match(identity)

    def addVirtualControl(self, name):
        """Add a virtual control to the profile with the given name.

        The new control will be returned."""
        virtualControl = VirtualControl(name, len(self._virtualControls)+1)
        self._virtualControls.append(virtualControl)
        return virtualControl

    def findVirtualControlByName(self, name):
        """Find the virtual control with the given name."""
        for virtualControl in self._virtualControls:
            if virtualControl.name==name:
                return virtualControl

    def findVirtualControlByCode(self, code):
        """Find the virtual control with the given code."""
        code -= 1
        return self._virtualControls[code] if code<len(self._virtualControls) \
          else None

    def findVirtualControlCodeByName(self, name):
        """Find the code of the virtual control with the given name."""
        virtualControl = self.findVirtualControlByName(name)
        return None if virtualControl is None else virtualControl.code

    def addShiftLevel(self, shiftLevel):
        """Add the given shift level to the profile."""
        self._shiftLevels.append(shiftLevel)

    def getShiftLevel(self, index):
        """Get the shift level at the given index."""
        return self._shiftLevels[index]

    def addControlProfile(self, controlProfile):
        """Add the given control profile to the list of control profiles."""
        self._controlProfiles.append(controlProfile)
        self._controlProfileMap[controlProfile.control] = controlProfile
        controlProfile.profile = self

    def findKeyProfile(self, code):
        """Find the key profile for the given code.

        Returns the key profile or None if, not found."""
        return self._controlProfileMap.get(Control(Control.TYPE_KEY, code))

    def findVirtualControlProfile(self, code):
        """Find the virtual control profile for the given code.

        Returns the key profile found, or None."""
        return self._controlProfileMap.get(Control(Control.TYPE_VIRTUAL, code))

    def getXMLDocument(self):
        """Get the XML document describing the profile."""
        Control.setProfile(self)

        document = getDOMImplementation().createDocument(None,
                                                         "joystickProfile",
                                                         None)
        topElement = document.documentElement
        topElement.setAttribute("name", self.name)
        topElement.setAttribute("autoLoad",
                                "yes" if self.autoLoad else "no")

        identityElement = Profile.getIdentityXML(document, self.identity)
        topElement.appendChild(identityElement)

        if self._virtualControls:
            virtualControlsElement = document.createElement("virtualControls")
            for virtualControl in self._virtualControls:
                element = virtualControl.getXML(document)
                virtualControlsElement.appendChild(element)
            topElement.appendChild(virtualControlsElement)

        if self._shiftLevels:
            shiftLevelsElement = document.createElement("shiftLevels")
            for shiftLevel in self._shiftLevels:
                shiftLevelsElement.appendChild(shiftLevel.getXML(document))
            topElement.appendChild(shiftLevelsElement)

        if self._controlProfiles:
            controlsElement = document.createElement("controls")
            for controlProfile in self._controlProfiles:
                controlsElement.appendChild(controlProfile.getXML(document))
            topElement.appendChild(controlsElement)

        return document

    def getDaemonXMLDocument(self):
        """Get the XML document to be downloaded to the daemon."""
        Control.setProfile(self)

        document = getDOMImplementation().createDocument(None,
                                                         "jsprogProfile",
                                                         None)
        topElement = document.documentElement

        (prologueElement,
         virtualControlControls, virtualControls,
         shiftLevelControls, shiftControls) = self._getPrologueXML(document)
        topElement.appendChild(prologueElement)

        for control in (shiftControls | virtualControls):
            if control.isVirtual:
                continue

            element = document.createElement("key" if control.isKey else "axis")
            element.setAttribute("name", control.name)

            lines = []
            lines.append("%s = value" % (control.luaValueName,))
            isShiftControl = False
            if control in virtualControlControls:
                for virtualControl in virtualControlControls[control]:
                    lines.append("%s()" % (virtualControl.stateLuaFunctionName,))

            for (controls, levelIndex) in zip(shiftLevelControls,
                                              range(0, len(shiftLevelControls))):
                if self._isControlIncludedIn(control, controls):
                    lines.append("%s()" %
                                 (Profile.getShiftLevelStateLuaFunctionName(levelIndex),))
                    isShiftControl = True

            if not isShiftControl and control in virtualControlControls:
                for virtualControl in virtualControlControls[control]:
                    updateName = \
                      ControlProfile.getUpdateLuaFunctionName(virtualControl.control)
                    if not isShiftControl:
                        lines.append("%s()" % (updateName,))

            if isShiftControl:
                lines.append("_jsprog_updaters_call()")

            luaText = "\n" + linesToText(lines, indentation = "    ")

            element.appendChild(document.createTextNode(luaText))
            topElement.appendChild(element)

        for controlProfile in self._controlProfiles:
            daemonXML = controlProfile.getDaemonXML(document, self)
            if daemonXML is not None:
                topElement.appendChild(daemonXML)

        epilogueElement = document.createElement("epilogue")
        topElement.appendChild(epilogueElement)

        return document

    def _getPrologueXML(self, document):
        """Get the XML code for the prologue."""

        lines = []
        lines.append("require(\"table\")")
        lines.append("")
        lines.append("_jsprog_updaters = {}")
        lines.append("")
        lines.append("function _jsprog_updaters_add(fn)")
        lines.append("  table.insert(_jsprog_updaters, fn)")
        lines.append("end")
        lines.append("")
        lines.append("function _jsprog_updaters_remove(fn)")
        lines.append("  for i, updater in ipairs(_jsprog_updaters) do")
        lines.append("    if fn == updater then")
        lines.append("      table.remove(_jsprog_updaters, i)")
        lines.append("      break")
        lines.append("    end")
        lines.append("  end")
        lines.append("end")
        lines.append("")
        lines.append("function _jsprog_updaters_call()")
        lines.append("  for i, updater in ipairs(_jsprog_updaters) do")
        lines.append("    updater()")
        lines.append("  end")
        lines.append("end")
        lines.append("")

        virtualControlControls = {}
        virtualControls = set()

        shiftLevelControls = []
        shiftControls = set()

        for virtualControl in self._virtualControls:
            controls = virtualControl.getControls()
            for control in controls:
                if control in virtualControlControls:
                    virtualControlControls[control].append(virtualControl)
                else:
                    virtualControlControls[control] = [virtualControl]

            virtualControls |= controls

        for shiftLevel in self._shiftLevels:
            controls = shiftLevel.getControls()
            shiftLevelControls.append(controls)
            shiftControls |= controls

        allControls = virtualControls | shiftControls

        for control in allControls:
            lines.append("%s = 0" % (control.luaValueName,))
        lines.append("")

        for virtualControl in self._virtualControls:
            stateVariableName = virtualControl.stateLuaVariableName

            lines.append("%s = 0" % (stateVariableName,))
            lines.append("")
            lines.append("function %s()" %
                         (virtualControl.stateLuaFunctionName,))
            appendLinesIndented(lines, virtualControl.getStateLuaCode(self),
                                "  ")
            lines.append("end")
            lines.append("")

        for (shiftLevel, index) in zip(self._shiftLevels,
                                       range(0, len(self._shiftLevels))):
            lines.append("%s = 0" % (getShiftLevelStateName(index),))
            lines.append("")
            lines.append("function %s()" %
                         (Profile.getShiftLevelStateLuaFunctionName(index),))
            appendLinesIndented(lines, shiftLevel.getStateLuaCode(self, index),
                                "  ")
            lines.append("end")
            lines.append("")

        for controlProfile in self._controlProfiles:
            controlLines = controlProfile.getPrologueLuaCode(self)
            if controlLines:
                lines += controlLines
                lines.append("")

        if not lines[-1]: lines = lines[:-1]

        text = "\n" + linesToText(lines, indentation = "    ")

        prologue = document.createTextNode(text)

        element = document.createElement("prologue")
        element.appendChild(prologue)

        return (element,
                virtualControlControls, virtualControls,
                shiftLevelControls, shiftControls)

    def _isControlIncludedIn(self, control, controls):
        """Determine if the given control is included in the given other set of
        controls directly or indirectly."""
        for c in controls:
            if control==c:
                return True
            if c.isVirtual:
                virtualControl = self.findVirtualControlByCode(c.code)
                if self._isControlIncludedIn(control,
                                             virtualControl.getControls()):
                    return True

#------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = make_parser()

    handler = ProfileHandler()
    parser.setContentHandler(handler)

    parser.parse(sys.argv[1])

    profile = handler.profile

    #document = profile.getXMLDocument()
    document = profile.getDaemonXMLDocument()

    with open("profile.xml", "wt") as f:
        document.writexml(f, addindent = "  ", newl = "\n")

#------------------------------------------------------------------------------
