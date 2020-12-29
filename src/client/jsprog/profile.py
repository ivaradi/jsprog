
from .joystick import InputID, JoystickIdentity, Key, Axis
from .action import Action, SimpleAction, RepeatableAction, MouseMoveCommand, MouseMove
from .action import AdvancedAction, KeyPressCommand, KeyReleaseCommand, DelayCommand
from .action import ScriptAction, NOPAction
from .util import appendLinesIndented, linesToText
from .parser import SingleValueConstraint, ValueRangeConstraint
from .parser import BaseHandler, checkVirtualControlName, Control
from .parser import VirtualControlBase, VirtualState
from .device import DisplayVirtualControl, DisplayVirtualState
from .common import _

from xml.sax import make_parser
from xml.dom.minidom import getDOMImplementation

import os
import sys
import copy

from functools import total_ordering

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

class ProfileHandler(BaseHandler):
    """XML content handler for a profile file."""
    def __init__(self, joystickType):
        """Construct the parser."""
        super(ProfileHandler, self).__init__(deviceVersionNeeded = False)

        self._joystickType = joystickType

        self._profileName = None
        self._autoLoad = False

        self._profile = None

        self._shiftLevel = None

        self._controlProfile = None
        self._controlHandlerTree = None
        self._shiftContext = []
        self._valueRangeHandler = None

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

    def startDocument(self):
        """Called at the beginning of the document."""
        super(ProfileHandler, self).startDocument()
        self._shiftContext = []
        self._valueRangeHandler = None
        self._shiftLevel = None
        self._profile = None

    def doStartElement(self, name, attrs):
        """Called for each start tag."""
        if name=="shiftLevels":
            self._checkParent(name, "joystickProfile")
            self._startShiftLevels(attrs)
        elif name=="shiftLevel":
            self._checkParent(name, "shiftLevels")
            self._startShiftLevel(attrs)
        elif name=="shift":
            self._checkParent(name, "key", "axis", "shift", "virtualState")
            self._startShift(attrs)
        elif name=="valueRange":
            self._checkParent(name, "axis", "shift")
            self._startValueRange(attrs)
        elif name=="action":
            self._checkParent(name, "key", "axis", "shift", "virtualState",
                              "valueRange")
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
        elif name=="mouseMove":
            self._checkParent(name, "enter", "repeat", "leave")
            self._startMouseMove(attrs)
        elif name=="line":
            self._checkParent(name, "enter", "leave")
            self._startLine(attrs)
        else:
            super(ProfileHandler, self).\
                doStartElement(name, attrs, "joystickProfile",
                               virtualControlParents = ["virtualState", "controls"],
                               virtualStateParents = ["shiftLevel"])

    def doEndElement(self, name):
        """Called for each end tag."""
        if name=="shiftLevel":
            self._endShiftLevel()
        elif name=="shift":
            self._endShift()
        elif name=="valueRange":
            self._endValueRange()
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
        elif name=="line":
            self._endLine()
        else:
            super(ProfileHandler, self).\
                doEndElement(name, "joystickProfile")

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
        return self._valueRangeHandler if self._valueRangeHandler \
            else self._shiftContext[-1] if self._shiftContext else \
            self._controlHandlerTree

    @property
    def _numExpectedShiftStates(self):
        """Determine the number of expected shift states at the
        current level."""
        shiftLevelIndex = self._shiftLevelIndex
        if shiftLevelIndex<self._profile.numShiftLevels:
            return self._profile.getShiftLevel(shiftLevelIndex).numStates
        else:
            return 0

    def _startTopLevelElement(self, attrs):
        """Handle the joystickProfile start tag."""
        if self._profile is not None:
            self._fatal("there should be only one 'joystickProfile' element")

        self._profileName = self._getAttribute(attrs, "name")
        if not self._profileName:
            self._fatal("the profile's name should not be empty")

        self._autoLoad = self._findBoolAttribute(attrs, "autoLoad")

    def _endIdentity(self):
        """Handle the identity end tag."""
        super(ProfileHandler, self)._endIdentity()
        self._profile = Profile(self._joystickType,
                                self._profileName, self._identity,
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
            super(ProfileHandler, self)._startVirtualControl(attrs)
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

            shiftActive = "shiftActive" in attrs and \
                attrs["shiftActive"] in ["yes", "true"]

            self._controlProfile = VirtualControlProfile(virtualControl.code,
                                                         shiftActive = shiftActive)
            self._controlHandlerTree = None

    def _addVirtualControl(self, name, attrs):
        """Add the virtual control with the given name to the profile."""
        return self._profile.addVirtualControl(name, attrs)

    def _endVirtualControl(self):
        """Handle the virtualControl end tag."""
        if self._parent=="virtualControls":
            super(ProfileHandler, self)._endVirtualControl()
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
        elif self._context[-2]=="virtualControls":
            if "displayName" not in attrs:
                self._fatal("a virtual state must have a display name")
            self._virtualState = DisplayVirtualState(attrs["displayName"])
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

    def _handleStartKey(self, code, attrs):
        """Handle the start of key start tag."""
        if self._profile.findKeyProfile(code) is not None:
            self._fatal("a profile for the key is already defined")

        shiftActive = "shiftActive" in attrs and \
            attrs["shiftActive"] in ["yes", "true"]

        self._controlProfile = KeyProfile(code, shiftActive = shiftActive)
        self._controlHandlerTree = self._controlProfile.handlerTree

    def _handleStartAxis(self, code, attrs):
        """Handle the axis start tag."""
        if self._profile.findAxisProfile(code) is not None:
            self._fatal("a profile for the axis is already defined")

        shiftActive = "shiftActive" in attrs and \
            attrs["shiftActive"] in ["yes", "true"]

        self._controlProfile = AxisProfile(code, shiftActive = shiftActive)
        self._controlHandlerTree = self._controlProfile.handlerTree

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

    def _startValueRange(self, attrs):
        """Start a value range handler."""
        if self._shiftLevelIndex!=self._profile.numShiftLevels:
            self._fatal("missing shift handler levels")
        if self._valueRangeHandler is not None:
            self._fatal("a value range handler is already present")

        fromValue = self._getIntAttribute(attrs, "fromValue")
        toValue = self._getIntAttribute(attrs, "toValue")

        if toValue<fromValue:
            self._fatal("the to-value should not be less than the from-value")

        self._valueRangeHandler = ValueRangeHandler(fromValue, toValue)

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
        elif type==Action.TYPE_SCRIPT:
            self._action = ScriptAction()
        elif type==Action.TYPE_NOP:
            self._action = NOPAction()
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

    def _startEnter(self, attrs):
        """Handle the enter start tag."""
        if self._action.type!=Action.TYPE_ADVANCED and \
           self._action.type!=Action.TYPE_SCRIPT:
            self._fatal("an enter tag is valid only for an advanced or script action")

        if self._action.type==Action.TYPE_ADVANCED:
            self._action.setSection(AdvancedAction.SECTION_ENTER)
        else:
            self._action.setSection(ScriptAction.SECTION_ENTER)

    def _startRepeat(self, attrs):
        """Handle the repeat start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a repeat tag is valid only for an advanced action")
        self._action.setSection(AdvancedAction.SECTION_REPEAT)

    def _startLeave(self, attrs):
        """Handle the leave start tag."""
        if self._action.type!=Action.TYPE_ADVANCED and \
           self._action.type!=Action.TYPE_SCRIPT:
            self._fatal("a leave tag is valid only for an advanced or script action")
        if self._action.type==Action.TYPE_ADVANCED:
            self._action.setSection(AdvancedAction.SECTION_LEAVE)
        else:
            self._action.setSection(ScriptAction.SECTION_LEAVE)

    def _startKeyPress(self, attrs):
        """Handle the keyPress start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a keypress is valid only for an advanced action")
        self._startCollectingCharacters()

    def _endKeyPress(self):
        """Handle the keyPress end tag."""
        keyName = self._getCollectedCharacters()
        code = Key.findCodeFor(keyName)
        if code is None:
            self._fatal("no valid code given for the keypress")
        self._action.appendCommand(KeyPressCommand(code))

    def _startKeyRelease(self, attrs):
        """Handle the keyRelease start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a key release is valid only for an advanced action")
        self._startCollectingCharacters()

    def _endKeyRelease(self):
        """Handle the keyRelase end tag."""
        keyName = self._getCollectedCharacters()
        code = Key.findCodeFor(keyName)
        if code is None:
            self._fatal("no valid code given for the keyrelease")
        self._action.appendCommand(KeyReleaseCommand(code))

    def _startDelay(self, attrs):
        """Handle the delay start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a delay is valid only for an advanced action")
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

    def _startMouseMove(self, attrs):
        """Handle the mouseMove start tag."""
        if self._action.type!=Action.TYPE_ADVANCED:
            self._fatal("a mouse move is valid only for a simple action")
        direction = \
            MouseMoveCommand.findDirectionFor(self._getAttribute(attrs,
                                                                 "direction"))
        if direction is None:
            self._fatal("invalid direction")
        command = MouseMoveCommand(direction = direction,
                                   a = self._findFloatAttribute(attrs, "a"),
                                   b = self._findFloatAttribute(attrs, "b"),
                                   c = self._findFloatAttribute(attrs, "c"),
                                   adjust =
                                   self._findFloatAttribute(attrs, "adjust"))
        self._action.appendCommand(command)

    def _startLine(self, attrs):
        """Handle the line start tag."""
        if self._action.type!=Action.TYPE_SCRIPT:
            self._fatal("a line element is valid only for a script action")

        self._startCollectingCharacters(keepFormatting = True)

    def _endLine(self):
        """Handle the line end tag."""
        self._action.appendLine(self._getCollectedCharacters())

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
        elif self._action.type == Action.TYPE_SCRIPT:
            if not self._action.valid:
                self._fatal("script action has no scripts")
        elif self._action.type == Action.TYPE_NOP:
            pass
        else:
            self._fatal("unhandled action type")

        self._handlerTree.addChild(self._action)

        self._action = None

    def _endValueRange(self):
        """Handle the value ranger end tag."""
        valueRangeHandler = self._valueRangeHandler

        if not valueRangeHandler.isComplete():
            self._fatal("value range handler is missing an action")

        self._valueRangeHandler = None

        self._handlerTree.addChild(valueRangeHandler)

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

    def _endAxis(self):
        """Handle the axis end tag."""

        if self._parent=="controls":
            if not self._controlHandlerTree.isComplete(self._numExpectedShiftStates):
                self._fatal("the axis profile is missing either child shift level states or an action")

            self._profile.addControlProfile(self._controlProfile)
            self._controlProfile = None
            self._controlHandlerTree = None

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

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftLevel(VirtualControlBase):
    """A level in the shift tree.

    Since the actual value of a shift level is determined by a number of shift
    states, it is basically a virtual control."""
    def __init__(self):
        """Construct the shift level."""
        super().__init__()
        self._states = []

    def clone(self):
        """Make a clone of this shift level."""
        sl = ShiftLevel()
        sl._states = [s.clone() for s in self._states]
        return sl

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
        self._parent = None

    @property
    def children(self):
        """Get the list of child handlers of the shift handler."""
        return self._children

    @property
    def numChildren(self):
        """Get the number of children."""
        return len(self._children)

    @property
    def parent(self):
        """Get the parent of this handler."""
        return self._parent

    @property
    def isLastChild(self):
        """Determine if this is the last child of its parent."""
        return self._parent is not None and self._parent._children[-1] is self

    @property
    def lastState(self):
        """Get the last state handled by the children, if they are
        shift handlers.

        If there are no children, -1 is returned."""
        return self._children[-1]._toState if self._children else -1

    def copyFrom(self, source):
        """Copy the parent and the children into this tree from the given
        source."""
        self._parent = source._parent
        self._children = [c.clone() for c in source._children]

    def addChild(self, handler):
        """Add a child handler."""
        assert \
            (isinstance(handler, Action) and not
             self._children) or \
            (isinstance(handler, ShiftHandler) and
             handler._fromState == (self.lastState+1)) or \
             isinstance(handler, ValueRangeHandler)

        self._children.append(handler)
        handler._parent = self

    def findChild(self, state):
        """Find the child for the given state."""
        for handler in self._children:
            if handler._fromState<=state and state<=handler._toState:
                return handler

    def isComplete(self, numStates = 0):
        """Determine if the tree is complete.

        numStates is the number of states expected at the tree's
        level. If the tree contains a clear handler, numStates is 0,
        and the tree is complete if there is one key
        handler. Otherwise the last state should equal to the number
        of states - 1."""
        if numStates==0:
            numChildren = len(self._children)
            return numChildren>0 and \
                (numChildren==1 if isinstance(self._children[0], Action) else
                 True)
        else:
            return (self.lastState+1)==numStates

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
        if numShiftLevels<=0 and isinstance(self._children[0], Action):
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

    def insertShiftHandler(self, beforeIndex, fromState, toState):
        """Insert a shift handler before the given index having the given state
        range.

        The index is 0-based and starts at this tree handler level.

        If the index is 0, it returns the new shift handler, otherwise it
        returns itself."""
        if beforeIndex==0:
            shiftHandler = ShiftHandler(fromState, toState)
            for child in self._children:
                shiftHandler.addChild(child)
            self._children = [shiftHandler]
        else:
            self._children = [child.insertShiftHandler(beforeIndex - 1,
                                                       fromState, toState)
                              for child in self._children]
        return self

    def modifyShiftHandler(self, index, stateMap):
        """Modify the shift handler with the given index according to the given
        state map."""
        if index==0:
            newChildren = []
            for child in self._children:
                fromState = child.fromState
                toState = child.toState

                newFromState = -1
                newToState = -1

                while fromState<=toState:
                    if stateMap[fromState][0]>=0:
                        if newFromState<0:
                            newFromState = stateMap[fromState][0]
                        else:
                            newFromState = min(newFromState, stateMap[fromState][0])
                        if newToState<0:
                            newToState = stateMap[fromState][1]
                        else:
                            newToState = max(newToState, stateMap[fromState][1])

                    fromState +=1

                if newFromState>=0 and newToState>=0:
                    if newFromState>newToState:
                        s = newFromState
                        newFromState = newToState
                        newToState = s

                    child._fromState = newFromState
                    child._toState = newToState
                    newChildren.append(child)

            newChildren.sort(key = lambda c: c.fromState)
            self._children = newChildren
        else:
            for child in self._children:
                child.modifyShiftHandler(index - 1, stateMap)

    def removeShiftHandler(self, index, keepStateIndex):
        """Remove the shift handler at the given index."""
        if index==0:
            keepHandler = None
            for child in self._children:
                if child.fromState<=keepStateIndex and \
                   keepStateIndex<=child.toState:
                    keepHandler = child
                    break

            assert(isinstance(keepHandler, ShiftHandler))

            self._children = []
            for child in keepHandler._children:
                self.addChild(child)
        else:
            for child in self._children:
                child.removeShiftHandler(index - 1, keepStateIndex)

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
    def _addIfStatementFor(control, shiftHandler, before, context):
        """Get the if statement for the given shift (or value range) handler."""
        (profile, lines, level, indentation) = context
        if isinstance(shiftHandler, ValueRangeHandler):
            if before:
                constraint = ValueRangeConstraint(control,
                                                  shiftHandler.fromValue,
                                                  shiftHandler.toValue)
                lines.append(indentation[0] +
                             ("if %s then" %
                              (constraint.getLuaExpression(profile),)))
                indentation[0] += "  "
                return (profile, lines, level + 1, indentation)
            else:
                indentation[0] = indentation[0][:-2]
                lines.append(indentation[0] + "end")
                if shiftHandler.isLastChild:
                    lines.append(indentation[0] + "return 0")
                return (profile, lines, level - 1, indentation)
        else:
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

    def clone(self):
        """Clone this shift handler into a new one."""
        return self.cloneWithRange(self._fromState, self._toState)

    def cloneWithRange(self, fromState, toState):
        """Clone this shift handler into a new one with the given state
        range."""
        shiftHandler = ShiftHandler(fromState, toState)
        shiftHandler.copyFrom(self)

        return shiftHandler

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

class ValueRangeHandler(HandlerTree):
    """A handler for a value range of a certain axis."""
    def __init__(self, fromValue, toValue):
        """Construct the value range handler to handle the values between
        the given ones (both inclusive)."""
        assert toValue >= fromValue

        super(ValueRangeHandler, self).__init__()

        self._fromValue = fromValue
        self._toValue = toValue

    @property
    def fromValue(self):
        """Get the starting value of the range."""
        return self._fromValue

    @property
    def toValue(self):
        """Get the ending value of the range."""
        return self._toValue

    @property
    def action(self):
        """Get the action (i.e. the only child) of the value range handler."""
        return self._children[0]

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
    def _generateActionLuaFunction(control, stateIndex, action, context):
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
        (codeFun, nameFun, lines, hasCode) = context
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
    def _appendStateReturnLuaCode(control, stateIndex, action, acc):
        """Append the Lua code for returning the state index."""
        (lines, indentation) = acc
        lines.append(indentation[0] + "return %d" % (stateIndex,))
        return (lines, indentation)

    @staticmethod
    def _getLuaShiftedStateName(control):
        """Get the name of the shifted state of the control in the Lua code."""
        return "_jsprog_%s_shiftedState" % (control.name,)

    def __init__(self, control, shiftActive = False):
        """Construct the profile for the given control."""
        self._control = control
        self._profile = None
        self._shiftActive = shiftActive

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

    @property
    def shiftActive(self):
        """Determine if a change in the shift state causes the reevaluation of
        the control."""
        return self._shiftActive

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

    def insertShiftLevel(self, beforeIndex, fromState, toState):
        """Insert a new shift level before the given index spanning the given
        states.

        This function should be implemented by the children."""
        raise NotImplementedError()

    def modifyShiftLevel(self, index, stateMap):
        """Modify the shift level with the given index according to the given
        state map.

        This function should be implemented by the children."""
        raise NotImplementedError()

    def removeShiftLevel(self, index, keepStateIndex):
        """Remove the shift level at the given index.

        This function should be implemented by the children."""
        raise NotImplementedError()

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
        if self.shiftActive:
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
    def __init__(self, code, shiftActive = False):
        """Construct the key profile for the given key code."""
        super(KeyProfile, self).__init__(Control(Control.TYPE_KEY, code),
                                         shiftActive = shiftActive)

        self._handlerTree = HandlerTree()

    @property
    def handlerTree(self):
        """Get the handler tree for the key's pressed value."""
        return self._handlerTree

    def getXML(self, document):
        """Get the XML element describing the key profile."""
        element = document.createElement("key")
        element.setAttribute("name", self._control.name)
        if self.shiftActive:
            element.setAttribute("shiftActive", "yes")

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

    def insertShiftLevel(self, beforeIndex, fromState, toState):
        """Insert a new shift level before the given index spanning the given
        states."""
        self._handlerTree = self._handlerTree.insertShiftHandler(beforeIndex,
                                                                 fromState,
                                                                 toState)
    def modifyShiftLevel(self, index, stateMap):
        """Modify the shift level with the given index according to the given
        state map."""
        self._handlerTree.modifyShiftHandler(index, stateMap)

    def removeShiftLevel(self, index, keepStateIndex):
        """Remove the shift level at the given index."""
        self._handlerTree.removeShiftHandler(index, keepStateIndex)

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
    def __init__(self, code, shiftActive = False):
        """Construct the vitual control profile for the given code."""
        control = Control(Control.TYPE_VIRTUAL, code)
        super(VirtualControlProfile, self).__init__(control,
                                                    shiftActive = shiftActive)

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
        if self.shiftActive:
            element.setAttribute("shiftActive", "yes")

        states = list(self._handlerTrees.keys())
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

    def insertShiftLevel(self, beforeIndex, fromState, toState):
        """Insert a new shift level before the given index spanning the given
        states."""
        newHandlerTrees = {}
        for (state, handlerTree) in self._handlerTrees.items():
            newHandlerTrees[state] = handlerTree.insertShiftHandler(beforeIndex,
                                                                    fromState,
                                                                    toState)
        self._handlerTrees = newHandlerTrees

    def modifyShiftLevel(self, index, stateMap):
        """Modify the shift level with the given index according to the given
        state map."""
        for handlerTree in self._handlerTrees.values():
            handlerTree.modifyShiftHandler(index, stateMap)

    def removeShiftLevel(self, index, keepStateIndex):
        """Remove the shift level at the given index."""
        for handlerTree in self._handlerTrees.values():
            handlerTree.removeShiftHandler(index, keepStateIndex)

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

class AxisProfile(ControlProfile):
    """Control profile for an axis."""
    def __init__(self, code, shiftActive = False):
        """Construct the profile for the given axis control."""
        super(AxisProfile, self).__init__(Control(Control.TYPE_AXIS, code),
                                          shiftActive = shiftActive)

        self._handlerTree = HandlerTree()

    @property
    def handlerTree(self):
        """Get the handler tree for the key's pressed value."""
        return self._handlerTree

    def getXML(self, document):
        """Get the XML element describing the key profile."""
        element = document.createElement("axis")
        element.setAttribute("name", self._control.name)
        if self.shiftActive:
            element.setAttribute("shiftActive", "yes")

        for child in self._handlerTree.children:
            element.appendChild(child.getXML(document))

        return element

    def getDaemonXML(self, document, profile):
        """Get the XML element for the XML document to be sent to the
        daemon."""
        element = document.createElement("axis")

        element.setAttribute("name", Axis.getNameFor(self.code))

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

    def insertShiftLevel(self, beforeIndex, fromState, toState):
        """Insert a new shift level before the given index spanning the given
        states."""
        self._handlerTree = self._handlerTree.insertShiftHandler(beforeIndex,
                                                                 fromState,
                                                                 toState)

    def modifyShiftLevel(self, index, stateMap):
        """Modify the shift level with the given index according to the given
        state map."""
        self._handlerTree.modifyShiftHandler(index, stateMap)

    def removeShiftLevel(self, index, keepStateIndex):
        """Remove the shift level at the given index."""
        self._handlerTree.removeShiftHandler(index, keepStateIndex)

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

        (numStates, lines) = \
            self._getShiftedStateLuaCodeFor(self._handlerTree, profile,
                                            0, lines, [""])

        return lines

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class Profile(object):
    """A joystick profile."""
    @staticmethod
    def loadFrom(joystickType, directory):
        """Load the profiles in the given directory for the given joystick type.

        Returns an iterator over the loaded profiles."""
        parser = make_parser()

        handler = ProfileHandler(joystickType)
        parser.setContentHandler(handler)

        for entry in os.listdir(directory):
            path = os.path.join(directory, entry)
            if entry.endswith(".profile") and os.path.isfile(path):
                try:
                    parser.parse(path)
                    profile = handler.profile
                    profile.fileName = entry[:-8]

                    yield profile
                except Exception as e:
                    print(e, file=sys.stderr)

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
        if inputID.version is not None:
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

    def __init__(self, joystickType, name, identity, autoLoad = False):
        """Construct an empty profile for the joystick with the given
        identity."""
        self.joystickType = joystickType
        self.name = name
        self.identity = identity
        self.autoLoad = autoLoad
        self.directoryType = None
        self.fileName = None

        self._joystickVirtualControls = []
        for vc in joystickType.virtualControls:
            self._joystickVirtualControls.append(vc)

        self._virtualControls = []

        self._shiftLevels = []

        self._controlProfiles = []
        self._controlProfileMap = {}

    @property
    def userDefined(self):
        """Determine if this profile is user-defined."""
        return self.directoryType == "user"

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

    @property
    def virtualControls(self):
        """Get an iterator over the virtual controls."""
        return iter(self._virtualControls)

    @property
    def allVirtualControls(self):
        """Get an iterator over all virtual controls this profile can use.

        Those virtual controls from the joystick type are returned for which
        there is not virtual control in the profile with the same name.

        Then the virtual controls defined by the profile are returned. """
        for vc in self._joystickVirtualControls:
            yield vc

        for vc in self._virtualControls:
            yield vc

    def clone(self):
        """Clone this profile by making a deep copy of itself."""
        return copy.deepcopy(self)

    def match(self, identity):
        """Get the match level for the given joystick identity."""
        return self.identity.match(identity)

    def addVirtualControl(self, name, attrs):
        """Add a virtual control to the profile with the given name.

        The new control will be returned."""
        virtualControl = DisplayVirtualControl(name,
                                               self.joystickType.MAX_NUM_VIRTUAL_CONTROLS +
                                               len(self._virtualControls) + 1,
                                               displayName = attrs["displayName"])
        self._virtualControls.append(virtualControl)

        newJSVirtualControls = []
        for vc in self._joystickVirtualControls:
            if vc.name!=name:
                newJSVirtualControls.append(vc)
        self._joystickVirtualControls = newJSVirtualControls

        return virtualControl

    def findVirtualControlByName(self, name):
        """Find the virtual control with the given name."""
        for virtualControl in self._virtualControls:
            if virtualControl.name==name:
                return virtualControl
        for virtualControl in self.joystickType.virtualControls:
            if virtualControl.name==name:
                return virtualControl

    def findVirtualControlByCode(self, code):
        """Find the virtual control with the given code."""
        vc = self.joystickType.findVirtualControlByCode(code)
        if vc is not None:
            return vc

        for vc in self._virtualControls:
            if vc.code==code:
                return vc

    def findVirtualControlCodeByName(self, name):
        """Find the code of the virtual control with the given name."""
        virtualControl = self.findVirtualControlByName(name)
        return None if virtualControl is None else virtualControl.code

    def addShiftLevel(self, shiftLevel):
        """Add the given shift level to the profile."""
        self._shiftLevels.append(shiftLevel)

    def insertShiftLevel(self, beforeIndex, shiftLevel):
        """Insert a shift level before the given index.

        The control profiles will also be extended."""
        self._shiftLevels.insert(beforeIndex, shiftLevel)
        for controlProfile in self._controlProfiles:
            controlProfile.insertShiftLevel(beforeIndex, 0,
                                            shiftLevel.numStates - 1)
        return True

    def modifyShiftLevel(self, index, modifiedShiftLevel,
                         removedStates, addedStates,
                         existingStates):
        """Modify the shift level at the given index to be equal to the given
        one."""
        shiftLevel = self._shiftLevels[index]
        stateMap = {}
        # print(removedStates, addedStates, existingStates)
        numStates = shiftLevel.numStates
        for i in range(0, numStates):
            stateMap[i] = (i, i)

        for (f, t) in existingStates.items():
            stateMap[f] = (t, t)

        for s in removedStates:
            if s not in addedStates:
                stateMap[s] = (-1, -1)

        maxState = numStates - 1
        for s in addedStates:
            if s>stateMap[maxState][1]:
                stateMap[maxState] = (stateMap[maxState][0], s)
            elif s<stateMap[0][0]:
                stateMap[0] = (s, stateMap[0][1])

        # print(stateMap)
        reverseMap = {}
        modifiedNumStates = modifiedShiftLevel.numStates

        for i in range(0, modifiedNumStates):
            reverseMap[i] = -1

        for (f, (t0, t1)) in stateMap.items():
            while t0>=0 and t0<=t1:
                reverseMap[t0] = f
                t0 += 1

        # print(reverseMap)

        newReverseMap = {}
        for (t, f) in reverseMap.items():
            if f==-1:
                candidateF = -1
                for (f1, (t0, t1)) in stateMap.items():
                    if t0>=0:
                        if t1<t:
                            if candidateF==-1 or stateMap[candidateF][1]<t1:
                                candidateF = f1
                        elif t0<=t and t<=t1:
                            candidateF = f1
                            break

                assert(candidateF>=0)
                newReverseMap[t] = candidateF
                if stateMap[candidateF][0]>t:
                    stateMap[candidateF] = (t, stateMap[candidateF][1])
                elif stateMap[candidateF][1]<t:
                    stateMap[candidateF] = (stateMap[candidateF][0], t)
            else:
                newReverseMap[t] = f

        reverseMap = newReverseMap
        # print(reverseMap)

        # print(stateMap)

        for controlProfile in self._controlProfiles:
            controlProfile.modifyShiftLevel(index, stateMap)
        self._shiftLevels[index] = modifiedShiftLevel

        return True

    def removeShiftLevel(self, index, keepStateIndex):
        """Remove the shift level at the given index.

        keepStateIndex denotes the index of the state whose actions should be kept."""
        for controlProfile in self._controlProfiles:
            controlProfile.removeShiftLevel(index, keepStateIndex)
        del self._shiftLevels[index]

        return True

    def getShiftLevel(self, index):
        """Get the shift level at the given index."""
        return self._shiftLevels[index]

    def addControlProfile(self, controlProfile):
        """Add the given control profile to the list of control profiles."""
        self._controlProfiles.append(controlProfile)
        self._controlProfileMap[controlProfile.control] = controlProfile
        controlProfile.profile = self

    def findControlProfile(self, control):
        """Find the control profile for the given control."""
        return self._controlProfileMap.get(control)

    def findKeyProfile(self, code):
        """Find the key profile for the given code.

        Returns the key profile or None if, not found."""
        return self._controlProfileMap.get(Control(Control.TYPE_KEY, code))

    def findVirtualControlProfile(self, code):
        """Find the virtual control profile for the given code.

        Returns the key profile found, or None."""
        return self._controlProfileMap.get(Control(Control.TYPE_VIRTUAL, code))

    def findAxisProfile(self, code):
        """Find the axis profile for the given code.

        Returns the axis profile or None if, not found."""
        return self._controlProfileMap.get(Control(Control.TYPE_AXIS, code))

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
                                              list(range(0, len(shiftLevelControls)))):
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

    def _findVirtualControlByName(self, name):
        """Find the virtual control among the profile's virtual controls that
        has the given name, if any."""
        for vc in self._virtualControls:
            if vc.name==name:
                return vc

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
                                       list(range(0, len(self._shiftLevels)))):
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
