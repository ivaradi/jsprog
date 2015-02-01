
from joystick import InputID, JoystickIdentity, Key, Axis
from action import Action, SimpleAction, RepeatableAction, MouseMove
from util import appendLinesIndented

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

        self._shiftLevel = None
        self._shiftState = None

        self._keyProfile = None
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
        self._virtualControlState = None
        self._shiftState = None
        self._shiftLevel = None
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
            self._checkParent(name, "virtualControls")
            self._startVirtualControl(attrs)
        elif name=="controlState":
            self._checkParent(name, "virtualControl")
            self._startControlState(attrs)
        elif name=="shiftLevels":
            self._checkParent(name, "joystickProfile")
            self._startShiftLevels(attrs)
        elif name=="shiftLevel":
            self._checkParent(name, "shiftLevels")
            self._startShiftLevel(attrs)
        elif name=="shiftState":
            self._checkParent(name, "shiftLevel")
            self._startShiftState(attrs)
        elif name=="keys":
            self._checkParent(name, "joystickProfile")
            self._startKeys(attrs)
        elif name=="key":
            self._checkParent(name, "controlState", "shiftState", "keys")
            self._startKey(attrs)
        elif name=="axis":
            self._checkParent(name, "controlState")
            self._startAxis(attrs)
        elif name=="shift":
            self._checkParent(name, "key", "shift")
            self._startShift(attrs)
        elif name=="action":
            self._checkParent(name, "key", "shift")
            self._startAction(attrs)
        elif name=="keyCombination":
            self._checkParent(name, "action")
            self._startKeyCombination(attrs)
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
        elif name=="controlState":
            self._endControlState()
        elif name=="shiftLevel":
            self._endShiftLevel()
        elif name=="shiftState":
            self._endShiftState()
        elif name=="key":
            self._endKey()
        elif name=="shift":
            self._endShift()
        elif name=="action":
            self._endAction()
        elif name=="keyCombination":
            self._endKeyCombination()

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
        return self._shiftContext[-1] if self._shiftContext else self._keyProfile

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
        name = self._getAttribute(attrs, "name")
        if not VirtualControl.checkName(name):
            self._fatal("the name of a virtual control should start ith a letter and may contain only alphanumeric or underscore characters")
        self._virtualControl = self._profile.addVirtualControl(name)

    def _startControlState(self, attrs):
        """Handle the controlState start tag."""
        self._virtualControlState = self._virtualControl.addState()

    def _endControlState(self):
        """Handle the controlState end tag."""
        if self._virtualControlState.numConstraints<1:
            self._fatal("a state of a virtual control must have at least 1 constraint.")

        self._virtualControlState = None

    def _endVirtualControl(self):
        """Handle the virtualControl end tag."""
        if self._virtualControl.numStates<2:
            self._fatal("a virtual control must have at least 2 states.")
        self._virtualControl = None

    def _startShiftLevels(self, attrs):
        """Handle the shiftLevels start tag."""
        if self._profile is None:
            self._fatal("the shift controls should be specified after the identity")
        if self._profile.hasControlProfiles:
            self._fatal("the shift controls should be specified before any control profiles")

    def _startShiftLevel(self, attrs):
        """Handle the shiftLevel start tag."""
        self._shiftLevel = ShiftLevel()

    def _startShiftState(self, attrs):
        """Handle the shiftState start tag."""
        self._shiftState = ShiftState()

    def _endShiftState(self):
        """Handle the shiftState end tag."""
        shiftState = self._shiftState
        if not shiftState.isValid:
            self._fatal("the shift state has conflicting controls")
        if not self._shiftLevel.addState(self._shiftState):
            self._fatal("the shift state is not unique on the level")
        self._shiftState = None

    def _endShiftLevel(self):
        """Handle the shiftLevel end tag."""
        if self._shiftLevel.numStates<2:
            self._fatal("a shift level should have at least two states")
        self._profile.addShiftLevel(self._shiftLevel)
        self._shiftLevel = None

    def _startKeys(self, attrs):
        """Handle the keys start tag."""
        if self._profile is None:
            self._fatal("keys should be specified after the identity")

    def _startKey(self, attrs):
        """Handle the key start tag."""
        code = None
        if "code" in attrs:
            code = self._getIntAttribute(attrs, "code")
        elif "name" in attrs:
            code = Key.findCodeFor(attrs["name"])

        if code is None:
            self._fatal("either a valid code or name is expected")

        if self._parent == "controlState" or self._parent == "shiftState":
            value = self._getIntAttribute(attrs, "value")
            if value<0 or value>1:
                self._fatal("the value should be 0 or 1 for a key")
            constraint = SingleValueConstraint(Control(Control.TYPE_KEY, code),
                                               value)
            if self._parent == "controlState":
                self._virtualControlState.addConstraint(constraint)
            else:
                self._shiftState.addConstraint(constraint)
        else:
            if self._profile.findKeyProfile(code) is not None:
                self._fatal("a profile for the key is already defined")

            self._keyProfile = KeyProfile(code)

    def _startAxis(self, attrs):
        """Handle the axis start tag."""
        code = None
        if "code" in attrs:
            code = self._getIntAttribute(attrs, "code")
        elif "name" in attrs:
            code = Axis.findCodeFor(attrs["name"])

        if code is None:
            self._fatal("either a valid code or name is expected")

        fromValue = self._getIntAttribute(attrs, "fromValue")
        toValue = self._getIntAttribute(attrs, "toValue")
        if fromValue>toValue:
            self._fatal("fromValue should not be greater than toValue")

        constraint = ValueRangeConstraint(Control(Control.TYPE_AXIS, code),
                                          fromValue, toValue)
        self._virtualControlState.addConstraint(constraint)

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
                MouseMove.findDirectionFor(self._getAttribute(attrs,
                                                              "direction"))
            if direction is None:
                self._fatal("invalid direction")
            self._action = MouseMove(direction = direction,
                                     a = self._findFloatAttribute(attrs, "a"),
                                     b = self._findFloatAttribute(attrs, "b"),
                                     c = self._findFloatAttribute(attrs, "c"),
                                     repeatDelay =
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

    def _endAction(self):
        """End the current action."""
        if self._action.type == Action.TYPE_SIMPLE:
            if not self._action.valid:
                self._fatal("simple action has no key combinations")
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

        if self._parent=="keys":
            if not self._keyProfile.isComplete(self._numExpectedShiftStates):
                self._fatal("the key profile is missing either child shift level states or an action")

            self._profile.addKeyProfile(self._keyProfile)
            self._keyProfile = None

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

    def _fatal(self, msg, exception = None):
        """Raise a parse exception with the given message and the
        current location."""
        raise SAXParseException(msg, exception, self._locator)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class VirtualControl(object):
    """A virtual control on the joystick.

    It has a fixed number of discrete values, where each value is determined by
    the value(s) of one or more other controls."""
    class State(object):
        """The state of a virtual control.

        This contains a list of constraints all of which must be fulfilled to
        produce this state."""
        def __init__(self, value):
            """Construct the state for the given value."""
            self._value = value
            self._constraints = []

        @property
        def value(self):
            """Get the value of the state."""
            return self._value

        @property
        def constraints(self):
            """Get an iterator over the constraints of the state."""
            return iter(self._constraints)

        @property
        def numConstraints(self):
            """Get the number of constraints defining the state."""
            return len(self._constraints)

        def addConstraint(self, constraint):
            """Add a constraint to the state."""
            self._constraints.append(constraint)

        def getXML(self, document):
            """Get the XML code describing this virtual control state."""
            element = document.createElement("controlState")

            for constraint in self._constraints:
                constraintElement = constraint.getXML(document)
                element.appendChild(constraintElement)

            return element

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
        self._name = name
        self._code = code
        self._states = []

    @property
    def name(self):
        """Get the name of the control."""
        return self._name

    @property
    def code(self):
        """Get the code of the control."""
        return self._code

    @property
    def states(self):
        """Get an iterator over the states of the control."""
        return iter(self._states)

    @property
    def numStates(self):
        """Get the number of states of the control."""
        return len(self._states)

    def addState(self):
        """Add a new state to the control and return it."""
        state = VirtualControl.State(len(self._states))
        self._states.append(state)
        return state

    def getXML(self, document):
        """Get the XML code describing this virtual control."""
        element = document.createElement("virtualControl")
        element.setAttribute("name", self._name)

        for state in self._states:
            stateElement = state.getXML(document)
            element.appendChild(stateElement)

        return element


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class Control(object):
    """A representation of a control, i.e. a key (button) or an axis."""
    ## Control type: a key
    TYPE_KEY = 1

    ## Control type: an axis
    TYPE_AXIS = 2

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
    def name(self):
        """Get the name of this control based on the code and the type."""
        if self.isKey:
            return Key.getNameFor(self._code)
        else:
            return Axis.getNameFor(self._code)

    @property
    def luaIDName(control):
        """Get the name of the variable containing the ID of the control."""
        return "jsprog_%s" % (control.name,)

    @property
    def luaValueName(control):
        """Get the name of the Lua variable containing the current value of the
        control."""
        return "_jsprog_%s_value" % (control.name,)

    def getConstraintXML(self, document):
        """Get the XML element for a constraint involving this control."""
        element = document.createElement("key" if self._type==Control.TYPE_KEY
                                         else "axis")
        element.setAttribute("name", self.name)
        return element

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
            return "%s == %d " % (self._control.luaValueName, self._fromValue)
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

class ShiftState(object):
    """A shift state.

    A shift state corresponds to a certain set of values of one or more
    controls, such as keys (buttons). For example, a shift state can be if the
    pinkie button is pressed. These controls and values are expressed using
    ShiftConstraint objects.

    There can be an empty shift state, meaning that the shift level is in that
    state if no other state is matched."""
    def __init__(self):
        """Construct the shift state."""
        self._constraints = []

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
    def isValid(self):
        """Determine if the state is valid.

        A state is valid if it does not contain constraints that refer to
        the same control but conflicting values."""
        numConstraints = len(self._constraints)
        for i in range(0, numConstraints - 1):
            constraint = self._constraints[i]
            for j in range(i+1, numConstraints):
                if constraint.doesConflict(self._constraints[j]):
                    return False
        return True

    def addConstraint(self, shiftConstraint):
        """Add a shift constraint to the state."""
        self._constraints.append(shiftConstraint)
        self._constraints.sort()

    def getXML(self, document):
        """Get an XML element describing this shift state."""
        element = document.createElement("shiftState")

        for constraint in self._constraints:
            element.appendChild(constraint.getXML(document))

        return element

    def addControls(self, controls):
        """Add the controls involved in this constraint to the given set."""
        for constraint in self._constraints:
            controls.add(constraint.control)

    def getLuaCondition(self, profile):
        """Get the Lua expression to evaluate the condition for this shift
        state being active."""
        expression = ""
        for constraint in self._constraints:
            if expression: expression += " and "
            expression += constraint.getLuaExpression(profile)
        return expression

    def __cmp__(self, other):
        """Compare this shift state with the other one.

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

class ShiftLevel(object):
    """A level in the shift tree.

    A shift level consists of a number of shift states corresponding to certain
    states of certain controls on the joystick."""
    def __init__(self):
        """Construct the shift level."""
        self._states = []

    @property
    def numStates(self):
        """Get the number of states."""
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

        return hadDefault

    def addState(self, shiftState):
        """Try to add a shift state to the level.

        It first checks if the shift state is different from every other state.
        If not, False is returned. Otherwise the new state is added and True is
        returned."""
        for state in self._states:
            if shiftState==state:
                return False

        self._states.append(shiftState)
        return True

    def getXML(self, document):
        """Get an XML element describing this shift level."""
        element = document.createElement("shiftLevel")

        for state in self._states:
            element.appendChild(state.getXML(document))

        return element

    def getControls(self):
        """Get the set of controls that are involved in computing the state
        of this shift level."""
        controls = set()
        for state in self._states:
            state.addControls(controls)
        return controls

    def getStateLuaCode(self, profile, levelIndex):
        """Get the Lua code to compute the state of this shift level.

        Returns an array of lines."""
        lines = []

        stateName = getShiftLevelStateName(levelIndex)
        defaultStateIndex = None
        for (state, index) in zip(self._states, range(0, self.numStates)):
            if state.isDefault:
                defaultStateIndex = index
            else:
                ifStatement = "elseif" if lines else "if"
                lines.append(ifStatement + " " + state.getLuaCondition(profile) +
                             " then")
                lines.append("  %s = %d" % (stateName, index))

        assert defaultStateIndex is not None
        lines.append("else")
        lines.append("  %s = %d" % (stateName, defaultStateIndex))
        lines.append("end")

        return lines

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

class KeyProfile(HandlerTree):
    """The profile for a key.

    It maintains a tree of handlers the leaves of which are key
    handlers, and the other nodes (if any) are shift handlers each
    level of them corresponding to a shift level."""
    @staticmethod
    def _getEnterLuaFunctionName(control, stateIndex):
        """Get the name of the function to be called when the given key
        enters into the state with the given index.

        It returns a tuple of:
        - the name of the function,
        - the name of the array containing the function objects."""
        return ("_jsprog_%s_enter%d" % (control.name, stateIndex),
                "_jsprog_%s_enterFunctions" % (control.name,))

    @staticmethod
    def _getLeaveLuaFunctionName(control, stateIndex):
        """Get the name of the function to be called when the given key
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
    def _getStateLuaFunctionName(control):
        """Get the name of the function to calculate the state of the given
        control."""
        return "_jsprog_%s_getState" % (control.name,)

    @staticmethod
    def _appendStateReturnLuaCode(control, stateIndex, action,
                                  (lines, indentation)):
        """Append the Lua code for returning the state index."""
        lines.append(indentation[0] + "return %d" % (stateIndex,))
        return (lines, indentation)

    @staticmethod
    def _getLuaStateName(control):
        """Get the name of the state of the key in the Lua code."""
        return "_jsprog_%s_state" % (control.name,)

    @staticmethod
    def _getUpdateLuaFunctionName(control):
        """Get the name of the function to update the state of the given
        control."""
        return "_jsprog_%s_update" % (control.name,)

    def __init__(self, code):
        """Construct the key profile for the given key code."""
        super(KeyProfile, self).__init__()

        self._control = Control(Control.TYPE_KEY, code)

    @property
    def control(self):
        """Get the control of the key."""
        return self._control

    @property
    def code(self):
        """Get the code of the key."""
        return self._control.code

    def getXML(self, document):
        """Get the XML element describing the key profile."""
        element = document.createElement("key")
        element.setAttribute("name", self._control.name)

        for child in self._children:
            element.appendChild(child.getXML(document))

        return element

    def getPrologueLuaCode(self, profile):
        """Get the Lua code to put into the prologue for the key."""
        lines = self._getEnterLuaFunctions(profile)
        leaveLines = self._getLeaveLuaFunctions(profile)
        if leaveLines:
            if lines: lines.append("")
            lines += leaveLines

        if lines: lines.append("")
        lines += self._getStateLuaFunction(profile)

        if lines: lines.append("")
        lines += self._getUpdateLuaFunction(profile)

        return lines

    def getDaemonXML(self, document, profile):
        """Get the XML element for the XML document to be sent to the
        daemon."""
        element = document.createElement("key")

        element.setAttribute("name", Key.getNameFor(self.code))

        luaCode = appendLinesIndented([], self.getLuaCode(profile),
                                      indentation = "    ")
        luaText = "\n" + "\n".join(luaCode) + "\n"

        element.appendChild(document.createTextNode(luaText))

        return element

    def getLuaCode(self, profile):
        """Get the Lua code for the key."""
        lines = []
        lines.append("%s = value" % (self._control.luaValueName,))
        lines.append("%s()" %
                     (KeyProfile._getUpdateLuaFunctionName(self._control),))
        return lines

    def _getEnterLuaFunctions(self, profile):
        """Get the code of the Lua functions for entering the various
        states of the key.

        profile is the joystick profile.

        Returns a list of Lua code lines."""
        lines = []
        lines.append("%s = false" %
                     (RepeatableAction.getFlagLuaName(self._control),))
        lines.append("")

        lines += self._getActionLuaFunctions(profile,
                                            lambda action, control:
                                            action.getEnterLuaCode(control),
                                            KeyProfile._getEnterLuaFunctionName)

        return lines

    def _getLeaveLuaFunctions(self, profile):
        """Get the code of the Lua functions for leaving the various states of
        the key.

        profile is the joystick profile.

        Returns a list of Lua code lines."""
        return self._getActionLuaFunctions(profile,
                                           lambda action, control:
                                           action.getLeaveLuaCode(control),
                                           KeyProfile._getLeaveLuaFunctionName)

    def _getActionLuaFunctions(self, profile, codeFun, nameFun):
        """Get the code for the Lua functions of entering or leaving the
        various states of the key.

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
        - the state index.
        It returns a tuple consisting of:
        - the name of the function,
        - the name of the array containing the function objects.

        The function returns the Lua code lines consisting of the codes of the
        functions as well as array definitions with the functions."""
        (numStates, (_, _, lines, hasCode)) = \
          self.foldStates(self._control, 0, profile.numShiftLevels,
                          KeyProfile._generateActionLuaFunction,
                          (codeFun, nameFun, [], []))

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

    def _getStateLuaFunction(self, profile):
        """Get the code of the Lua function to compute the state of the key."""
        lines = []

        lines.append("%s = 0" % (self._control.luaValueName,))
        lines.append("")

        lines.append("function %s()" %
                     (KeyProfile._getStateLuaFunctionName(self._control)))

        lines.append("  if %s==0 then" % (self._control.luaValueName,))
        lines.append("    return 0")
        lines.append("  else")

        indentation = ["    "]
        (numStates, (lines, _), branchAcc) = \
            self.foldStates(self._control, 0, profile.numShiftLevels,
                            KeyProfile._appendStateReturnLuaCode,
                            acc = (lines, indentation),
                            branchFun = ShiftHandler._addIfStatementFor,
                            branchAcc = (profile, lines, 0, indentation))

        lines.append("  end")

        lines.append("end")

        return lines

    def _getUpdateLuaFunction(self, profile):
        """Get the code of the Lua function to update the state of the key and
        call the functions doing it."""
        lines = []

        stateName =  KeyProfile._getLuaStateName(self._control)

        lines.append("%s = 0" % (stateName,))
        lines.append("")

        functionName = KeyProfile._getUpdateLuaFunctionName(self._control)
        lines.append("function %s()" % (functionName,))
        lines.append("  local oldState = %s" % (stateName,))
        lines.append("  local newState = %s()" %
                     (KeyProfile._getStateLuaFunctionName(self._control),))

        (_, enterFunctionsName) = \
          KeyProfile._getEnterLuaFunctionName(self._control, 0)
        (_, leaveFunctionsName) = \
          KeyProfile._getLeaveLuaFunctionName(self._control, 0)

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

        self._keyProfiles = []
        self._keyProfileMap = {}

    @property
    def hasVirtualControls(self):
        """Determine if we have any virtual controls."""
        return bool(self._virtualControls)

    @property
    def hasControlProfiles(self):
        """Determine if we have control (key or axis) profiles or not."""
        return bool(self._keyProfiles)

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

    def addShiftLevel(self, shiftLevel):
        """Add the given shift level to the profile."""
        self._shiftLevels.append(shiftLevel)

    def getShiftLevel(self, index):
        """Get the shift level at the given index."""
        return self._shiftLevels[index]

    def addKeyProfile(self, keyProfile):
        """Add the given key profile to the list of key profiles."""
        self._keyProfiles.append(keyProfile)
        self._keyProfileMap[keyProfile.code] = keyProfile

    def findKeyProfile(self, code):
        """Find the key profile for the given code.

        Returns the key profile or None if, not found."""
        return self._keyProfileMap.get(code)

    def getXMLDocument(self):
        """Get the XML document describing the profile."""
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

        if self._keyProfiles:
            keysElement = document.createElement("keys")
            for keyProfile in self._keyProfiles:
                keysElement.appendChild(keyProfile.getXML(document))
            topElement.appendChild(keysElement)

        return document

    def getDaemonXMLDocument(self):
        """Get the XML document to be downloaded to the daemon."""
        document = getDOMImplementation().createDocument(None,
                                                         "jsprogProfile",
                                                         None)
        topElement = document.documentElement

        (prologueElement, shiftLevelControls, allShiftControls) = \
          self._getPrologueXML(document)
        topElement.appendChild(prologueElement)

        for control in allShiftControls:
            element = document.createElement("key" if control.isKey else "axis")
            element.setAttribute("name", control.name)

            lines = []
            lines.append("%s = value" % (control.luaValueName,))
            for (controls, levelIndex) in zip(shiftLevelControls,
                                              range(0, len(shiftLevelControls))):
                if control in controls:
                    lines.append("%s()" %
                                 (Profile.getShiftLevelStateLuaFunctionName(levelIndex),))
            lines.append("_jsprog_updaters_call()")

            # FIXME: this is very similar to the code in getDaemonXML()
            luaCode = appendLinesIndented([], lines, indentation = "    ")
            luaText = "\n" + "\n".join(luaCode) + "\n"

            element.appendChild(document.createTextNode(luaText))
            topElement.appendChild(element)

        for keyProfile in self._keyProfiles:
            topElement.appendChild(keyProfile.getDaemonXML(document, self))

        epilogueElement = document.createElement("epilogue")
        topElement.appendChild(epilogueElement)

        return document

    def _getPrologueXML(self, document):
        """Get the XML code for the prologue."""

        shiftLevelControls = []
        allControls = set()
        for shiftLevel in self._shiftLevels:
            controls = shiftLevel.getControls()
            shiftLevelControls.append(controls)
            allControls |= controls

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

        for control in allControls:
            lines.append("%s = 0" % (control.luaValueName,))
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

        for keyProfile in self._keyProfiles:
            keyLines = keyProfile.getPrologueLuaCode(self)
            if keyLines:
                lines += keyLines
                lines.append("")

        if not lines[-1]: lines = lines[:-1]

        text = "\n"
        for line in lines:
            text += "    " + line + "\n"

        prologue = document.createTextNode(text)

        element = document.createElement("prologue")
        element.appendChild(prologue)

        return (element, shiftLevelControls, allControls)

#------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = make_parser()

    handler = ProfileHandler()
    parser.setContentHandler(handler)

    parser.parse(sys.argv[1])

    profile = handler.profile

    document = profile.getXMLDocument()
    #document = profile.getDaemonXMLDocument()

    with open("profile.xml", "wt") as f:
        document.writexml(f, addindent = "  ", newl = "\n")

#------------------------------------------------------------------------------
