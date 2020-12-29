
from .joystick import InputID, JoystickIdentity, Key, Axis

from xml.sax.handler import ContentHandler
from xml.sax import SAXParseException

from functools import total_ordering

#------------------------------------------------------------------------------

## @package jsprog.parser
#
# Various utilities for parsing the device and profile files

#------------------------------------------------------------------------------

def checkVirtualControlName(name):
    """Check if the given name fulfils the requirements for a name of a virtual
    control.

    It should start with a letter and the further characters should be
    letters, numbers or underscores."""
    first = True
    for c in name:
        if ord(c)>=128 or not ((first and c.isalpha()) or \
                               (not first and (c.isalnum() or c=='_'))):
            return False
        first = False
    return True

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
        returned.

        If the new state is a default state, it is added as the first one."""
        for state in self._states:
            if virtualState==state:
                return False

        if virtualState.isDefault:
            for state in self._states:
                state.incValue()
            self._states.insert(0, virtualState)
            virtualState.value = 0
        else:
            virtualState.value = len(self._states)
            self._states.append(virtualState)

        return True

    def addStatesFromControl(self, controlType, controlCode, stateFactory,
                             axisOwner, virtualControlOwner = None):
        """Add states corresponding to the states of the given control.

        axisOwner is an object (typically a joystick type) from which axes can
        be queried. virtualControlOwner is an object (typically a profile) that
        can be used to query virtual controls.

        The state objects are created by calling stateFactory."""
        control = Control(controlType, controlCode)
        if controlType==Control.TYPE_KEY:
            state = stateFactory()
            state.addConstraint(SingleValueConstraint(control, 0))
            self.addState(state)

            state = stateFactory()
            state.addConstraint(SingleValueConstraint(control, 1))
            self.addState(state)
        elif controlType==Control.TYPE_AXIS:
            axis = axisOwner.findAxis(controlCode)
            middle = (axis.minimum + axis.maximum) // 2

            state = stateFactory()
            state.addConstraint(
                ValueRangeConstraint(control, axis.minimum, middle) if
                axis.minimum<middle else
                SingleValueConstraint(control, axis.minimum))
            self.addState(state)

            middle += 1
            state = stateFactory()
            state.addConstraint(
                ValueRangeConstraint(control, middle, axis.maximum) if
                middle<axis.maximum else
                SingleValueConstraint(control, axis.maximum))
            self.addState(state)
        elif controlType==Control.TYPE_VIRTUAL:
            vc = virtualControlOwner.findVirtualControlByCode(controlCode)
            for vcState in vc.states:
                state = stateFactory()
                state.addConstraint(SingleValueConstraint(control, vcState.value))
                self.addState(state)
        else:
            assert False


    def getState(self, value):
        """Get the state corresponding to the given value."""
        return self._states[value]

    def removeState(self, virtualState):
        """Remove the given virtual state."""
        after = False
        for state in self._states:
            if after:
                state.decValue()
            if state is virtualState:
                after = True
        self._states.remove(virtualState)

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

    def getDifferenceFrom(self, other):
        """Get the difference from the given other virtual control

        Returns a tuple of:
        - the list of indexes of states that are present in the other virtual control
          but not here
        - the list of indexes of states in this virtual control not present in the
          other one
        - the dictionary of state indexes where the key is the index in the
          other virtual control and the value is the index in this one."""
        removedStates = []
        addedStates = []
        existingStates = {}

        hasDifference = False

        for (otherIndex, otherState) in enumerate(other._states):
            index = self._findStateIndex(otherState)
            if index<0:
                hasDifference = True
                removedStates.append(otherIndex)
            else:
                if index!=otherIndex:
                    hasDifference = True
                existingStates[otherIndex] = index

        for (index, state) in enumerate(self._states):
            if other._findStateIndex(state)<0:
                hasDifference = True
                addedStates.append(index)

        return (hasDifference, removedStates, addedStates, existingStates)

    def _findStateIndex(self, state):
        """Find the index of the state that is equal to the given one."""
        for (index, s) in enumerate(self._states):
            if s==state:
                return index
        return -1

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class VirtualControl(VirtualControlBase):
    """A virtual control on the joystick."""
    @staticmethod
    def checkName(name):
        """Check if the given name fulfils the requirements.

        It should start with a letter and the further characters should be
        letters, numbers or underscores."""
        return checkVirtualControlName(name)

    def __init__(self, name, code):
        """Construct the virtual control with the given name and code."""
        super(VirtualControl, self).__init__(needDefault = False)
        self._name = name
        self._code = code

    @property
    def name(self):
        """Get the name of the control."""
        return self._name

    @name.setter
    def name(self, name):
        """Set the name of the control."""
        self._name = name

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

@total_ordering
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

    @property
    def isDisplay(self):
        """Indiciate if this is a virtual state with a display name, which it
        is not."""
        return False

    def clone(self):
        """Clone this virtual state."""
        vs = VirtualState(self._value)
        vs._constraints = [c.clone() for c in self._constraints]
        return vs

    def incValue(self):
        """Increment the value."""
        self._value += 1

    def decValue(self):
        """Decrement the value."""
        self._value -= 1

    def addConstraint(self, constraint):
        """Add a constraint to the state."""
        self._constraints.append(constraint)
        self._constraints.sort()

    def clearConstraints(self):
        """Clear the constraints in this virtual state."""
        self._constraints.clear()

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
                x = len(self._constraints) - len(other._constraints)
                if x==0:
                    for index in range(0, len(self._constraints)):
                        x = self._constraints[index].__cmp__(
                            other._constraints[index])
                        if x!=0: break
                return x
            else:
                return 0 if self.isDefault else 1
        elif other._constraints:
            return 0 if other.isDefault else -1
        else:
            return 0

    def __eq__(self, other):
        """Equality comparison."""
        return self.__cmp__(other)==0

    def __lt__(self, other):
        """Less-than comparison."""
        return self.__cmp__(other)<0

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

@total_ordering
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
    def fromJoystickControl(jscontrol):
        if isinstance(jscontrol, Key):
            return Control(Control.TYPE_KEY, jscontrol.code)
        elif isinstance(jscontrol, Axis):
            return Control(Control.TYPE_AXIS, jscontrol.code)
        elif isinstance(jscontrol, VirtualControlBase):
            return Control(Control.TYPE_VIRTUAL, jscontrol.code)

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
    def xmlName(self):
        """Get the name of this control based on the code and the type for XML
        documents."""
        if self.isVirtual:
            if Control._currentProfile is not None:
                virtualControl = \
                  Control._currentProfile.findVirtualControlByCode(self._code)
                if virtualControl is not None:
                    return virtualControl.name
        else:
            return self.name

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
                                         else "axis"
                                         if self._type==Control.TYPE_AXIS
                                         else "virtualControl")
        element.setAttribute("name", self.xmlName)
        return element

    def __hash__(self):
        """Compute a hash value for the control."""
        return hash(self._type) ^ hash(self._code)

    def __cmp__(self, other):
        """Compare the control with the given other one."""
        x = self._type - other._type
        if x==0:
            x = self._code - other._code
        return x

    def __eq__(self, other):
        """Equality comparison."""
        return self.__cmp__(other)==0

    def __lt__(self, other):
        """Less-than comparison."""
        return self.__cmp__(other)<0

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

@total_ordering
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
        x = self._control.__cmp__(other._control)
        if x==0:
            x = hash(self.__class__) - hash(other.__class__)
        return x

    def __eq__(self, other):
        """Equality comparison."""
        return self.__cmp__(other)==0

    def __lt__(self, other):
        """Less-than comparison."""
        return self.__cmp__(other)<0

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

@total_ordering
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

    def clone(self):
        """Clone this constraint."""
        return SingleValueConstraint(self._control, self._value)

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
            x = self._value - other._value
        return x

    def __eq__(self, other):
        """Equality comparison."""
        return self.__cmp__(other)==0

    def __lt__(self, other):
        """Less-than comparison."""
        return self.__cmp__(other)<0

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

@total_ordering
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

    def clone(self):
        """Clone this constraint."""
        return ValueRangeConstraint(self._control, self._fromValue, self._toValue)

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
            x = self._fromValue - other._fromValue
        if x==0:
            x = self._toValue - other._toValue
        return x

    def __eq__(self, other):
        """Equality comparison."""
        return self.__cmp__(other)==0

    def __lt__(self, other):
        """Less-than comparison."""
        return self.__cmp__(other)<0

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class BaseHandler(ContentHandler):
    """Base XML content handler with some utility functions."""
    def __init__(self, deviceVersionNeeded = True):
        """Construct the parser."""
        self._deviceVersionNeeded = deviceVersionNeeded

        self._locator = None

        self._context = []
        self._characterContext = []
        self._keepContentsFormatting = []

        self._identity = None
        self._inputID = None
        self._name = None
        self._phys = None
        self._uniq = None

        self._virtualControl = None
        self._virtualState = None

    @property
    def identity(self):
        """Get the identity parsed."""
        return self._identity

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
        self._keepContentsFormatting = []
        self._identity = None
        self._virtualControl = None
        self._virtualState = None

    def startElement(self, name, attrs):
        """Called for each start tag."""
        self.doStartElement(name, attrs)

        self._context.append(name)
        if len(self._characterContext)<len(self._context):
            self._characterContext.append(None)
            self._keepContentsFormatting.append(None)

    def doStartElement(self, name, attrs, topLevelElement,
                       virtualControlParents = [], virtualStateParents = []):
        """Called for each start tag."""
        if name==topLevelElement:
            if self._context:
                self._fatal("'%s' should be the top-level element" % (topLevelElement,))
            self._startTopLevelElement(attrs)
        elif name=="identity":
            self._checkParent(name, topLevelElement)
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
            self._checkParent(name, topLevelElement)
            self._startVirtualControls(attrs)
        elif name=="virtualControl":
            self._checkParent(name, "virtualControls", *virtualControlParents)
            self._startVirtualControl(attrs)
        elif name=="virtualState":
            self._checkParent(name, "virtualControl", *virtualStateParents)
            self._startVirtualState(attrs)
        elif name=="controls":
            self._checkParent(name, topLevelElement)
            self._startControls(attrs)
        elif name=="key":
            self._checkParent(name, "virtualState", "controls")
            self._startKey(attrs)
        elif name=="axis":
            self._checkParent(name, "virtualState", "controls")
            self._startAxis(attrs)
        else:
            self._fatal("unhandled tag")

    def endElement(self, name):
        """Called for each end tag."""
        del self._context[-1]

        self.doEndElement(name)

        del self._characterContext[-1]
        del self._keepContentsFormatting[-1]

    def doEndElement(self, name, topLevelElement):
        if name==topLevelElement:
            self._endTopLevelElement(topLevelElement)
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
        elif name=="virtualState":
            self._endVirtualState()
        elif name=="key":
            self._endKey()
        elif name=="axis":
            self._endAxis()

    def characters(self, content):
        """Called for character content."""
        if content.strip():
            self._appendCharacters(content)

    def _startTopLevelElement(self, attrs):
        """Handle the joystickProfile start tag."""
        raise NotImplementedError()

    def _startIdentity(self, attrs):
        """Handle the identity start tag."""
        if self._identity is not None:
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
        if self._deviceVersionNeeded:
            version = self._getHexAttribute(attrs, "version")
        else:
            version = self._findHexAttribute(attrs, "version", None)

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
        self._identity = JoystickIdentity(self._inputID, self._name,
                                          self._phys, self._uniq)

    def _startVirtualControls(self, attrs):
        """Handle the virtualControls start tag."""
        raise NotImplementedError()

    def _startVirtualControl(self, attrs):
        """Handle the virtualControl start tag.

        This implementation handles only the case when the parent is
        'virtualControls', and even in that case, it calls _addVirtualControl()
        with the control's name. """
        if self._parent=="virtualControls":
            name = self._getAttribute(attrs, "name")
            if not checkVirtualControlName(name):
                self._fatal("the name of a virtual control should start with a letter and may contain only alphanumeric or underscore characters")
            self._virtualControl = self._addVirtualControl(name, attrs)

    def _endVirtualControl(self):
        """Handle the virtualControl end tag.

        This implementation handles only the case when the parent is
        'virtualControls'. """
        if self._parent=="virtualControls":
            if self._virtualControl.numStates<2:
                self._fatal("a virtual control must have at least 2 states.")
            self._virtualControl = None

    def _startVirtualState(self, attrs):
        """Handle the virtualState start tag."""
        self._virtualState = VirtualState()

    def _endVirtualState(self):
        """Handle the virtualState end tag."""
        raise NotImplementedError()

    def _startControls(self, attrs):
        """Handle the controls start tag."""
        if self._identity is None:
            self._fatal("controls should be specified after the identity")

    def _startKey(self, attrs):
        """Handle the key start tag.

        It is handled by this function for the case when ther parent element is
        'virtualState'. For other parents _handleStartKey() is called with the
        key's code."""
        code = self._getControlCode(attrs, Key.findCodeFor)

        if self._parent == "virtualState":
            value = self._getIntAttribute(attrs, "value")
            if value<0 or value>1:
                self._fatal("the value should be 0 or 1 for a key")
            constraint = SingleValueConstraint(Control(Control.TYPE_KEY, code),
                                               value)
            self._virtualState.addConstraint(constraint)
        else:
            self._handleStartKey(code, attrs)

    def _startAxis(self, attrs):
        """Handle the axis start tag.

        It is handled by this function for the case when ther parent element is
        'virtualState'. For other parents _handleStartAxis() is called with the
        key's code."""
        code = self._getControlCode(attrs, Axis.findCodeFor)

        if self._parent == "virtualState":
            control = Control(Control.TYPE_AXIS, code)
            constraint = self._getFromToValueConstraint(attrs, control)
            self._virtualState.addConstraint(constraint)
        else:
            self._handleStartAxis(code, attrs)

    def _endKey(self):
        """Handle the key end tag."""
        raise NotImplementedError()

    def _endAxis(self):
        """Handle the axis end tag."""
        raise NotImplementedError()

    def _endTopLevelElement(self, topLevelElement):
        """Handle the top-level element end tag."""
        if self._identity is None:
            self._fatal("empty '%s' element" % (topLevelElement,))

    def _startCollectingCharacters(self, keepFormatting = False):
        """Indicate that we can collect characters with the current
        tag."""
        self._characterContext.append("")
        self._keepContentsFormatting.append(keepFormatting)

    def _getCollectedCharacters(self):
        """Get the collected characters, if any."""
        characters = self._characterContext[-1]
        assert characters is not None

        keepFormatting = self._keepContentsFormatting[-1]

        return characters if keepFormatting else characters.strip()

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
        except Exception as e:
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
        except Exception as e:
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
