from .joystick import Key
from .util import appendLinesIndented

#------------------------------------------------------------------------------

## @package jsprog.action
#
# The various actions assigned to input controls

#------------------------------------------------------------------------------

class Action(object):
    """Base class for the various actions.

    An action describes what is to be done when an input control is
    actuated, such as when a key is pressed (and then released)."""

    ## Action type: simple (one or more key combinations with an
    ## optional repeat delay)
    TYPE_SIMPLE = 1

    ## Action type: advanced (explicit key presses, releases with
    ## optional delays, separately for the key press, the repeat and
    ## the release).
    TYPE_ADVANCED = 2

    ## Action type: mouse move (the mouse is moved either horizontally
    ## or vertically by an amount proportional to the value)
    TYPE_MOUSE_MOVE = 3

    ## Action type: script (a Lua script)
    TYPE_SCRIPT = 10

    ## Action type: value range
    TYPE_VALUE_RANGE = 20

    ## Action type: NOP (no action)
    TYPE_NOP = -1

    ## The mapping of types to strings
    _typeNames = {
        TYPE_SIMPLE : "simple",
        TYPE_ADVANCED : "advanced",
        TYPE_MOUSE_MOVE : "mouseMove",
        TYPE_SCRIPT: "script",
        TYPE_VALUE_RANGE: "valueRange",
        TYPE_NOP: "nop"
        }

    @staticmethod
    def getTypeNameFor(type):
        """Get the type name for the given type."""
        return Action._typeNames[type]

    @staticmethod
    def findTypeFor(typeName):
        """Get the type for the given type name."""
        for (type, name) in Action._typeNames.items():
            if name==typeName:
                return type
        return None

    @property
    def typeName(self):
        """Get the type name of the action."""
        return Action._typeNames[self.type]

    def __init__(self, displayName = None):
        """Construct the action with the given display name."""
        self.displayName = displayName

    def getXML(self, document):
        """Get the element for the key action."""
        element = document.createElement("action")

        element.setAttribute("type", self.typeName)
        if self.displayName:
            element.setAttribute("displayName", self.displayName)

        self._extendXML(document, element)

        return element

#------------------------------------------------------------------------------

class RepeatableAction(Action):
    """Base class for actions that may be repeated while the control
    event persists."""
    @staticmethod
    def getRepeatFlagLuaName(control):
        """Get the name of the variable containing a boolean indicating if the
        repeatable action should be executed."""
        return "_jsprog_%s_repeat" % (control.name,)

    @staticmethod
    def getThreadLuaName(control):
        """Get the name of the variable containing thread performing the
        action (if a thread is required)."""
        return "_jsprog_%s_thread" % (control.name,)

    def __init__(self, displayName = None, repeatDelay = None):
        """Construct the action with the given repeat delay."""
        super().__init__(displayName = displayName)
        self.repeatDelay = repeatDelay

    @property
    def isRepeatDifferent(self):
        """Indicate if the repeat command sequence is different from the
        entering one."""
        return False

    @property
    def enterCodeNeedsThread(self):
        """Indicate if the enter code needs to be run in a thread (e.g. because
        it contains one or more delays)."""
        return False

    @property
    def leaveCodeNeedsThread(self):
        """Indicate if the leave code needs to be run in a thread (e.g. because
        it contains one or more delays)."""
        return False

    @property
    def useThread(self):
        """Indicate if a thread must be used to execute the action."""
        return self.repeatDelay is not None or self.enterCodeNeedsThread or \
            self.leaveCodeNeedsThread

    def getEnterLuaCode(self, control):
        """Get the Lua code that starts the action.

        If the enter or the leave code requires a thread or there is repeat
        delay, the global repeat flag variable is initialized from a new,
        single element array containing a value of true and a new thread is
        started. If there is no repeat delay or theenter and repeat codes are
        different, the enter code is executed in this thread. Then the repeat
        loop is started. If there is a repeat delay it executes
        If there is a repeay delay, this function generates the
        infinite loop with the delay. Calls the child's _getLuaCode()
        function to get the code of the real action.

        Returns an array of lines."""
        lines = []

        indentation = ""

        if self.useThread:
            repeatFlagName = RepeatableAction.getRepeatFlagLuaName(control)
            threadName = RepeatableAction.getThreadLuaName(control)

            lines.append("local repeatFlag = { true }")
            lines.append("%s = repeatFlag" % (repeatFlagName,))

            lines.append("local lastThread = %s[1]" % (threadName,))

            lines.append("local thread = jsprog_startthread(function ()")
            lines.append("  if lastThread then")
            lines.append("    jsprog_jointhread(lastThread)")
            lines.append("  end")

            if self.repeatDelay is None:
                appendLinesIndented(lines, self._getEnterLuaCode(control), "  ")

            if self.isRepeatDifferent:
                lines.append("  local repeating = false")
                lines.append("  while repeatFlag[1] or not repeating do")
            else:
                lines.append("  while repeatFlag[1] do")

            if self.repeatDelay is None:
                lines.append("    jsprog_delay(10000, true)")
            else:
                if self.isRepeatDifferent:
                    lines.append("    if repeating then")
                    appendLinesIndented(lines,
                                        self._getRepeatLuaCode(control),
                                        "      ")
                    lines.append("    else")
                    indentation = "      "
                else:
                    indentation = "    "

                appendLinesIndented(lines, self._getEnterLuaCode(control),
                                    indentation)

                if self.isRepeatDifferent:
                    lines.append("    end")
                    lines.append("    repeating = true")

                lines.append("    if repeatFlag[1] then")
                lines.append("      jsprog_delay(%d, true)" %
                             (self.repeatDelay,))
                lines.append("    end")
            lines.append("  end")

            appendLinesIndented(lines, self._getLeaveLuaCode(control), "  ")

            lines.append("  if %s[1] == coroutine.running() then" % (threadName,))
            lines.append("    %s = { nil }" % (threadName,))
            lines.append("  end")

            lines.append("end)")

            lines.append("%s = { thread }" % (threadName,))
        else:
            appendLinesIndented(lines, self._getEnterLuaCode(control), "")

        return lines

    def getLeaveLuaCode(self, control):
        """Get the Lua code that finishes the action.

        If there is a repeat delay, this function generates a call to cancel
        the previous operation. Otherwise no code is generated.

        Returns an array of lines."""
        lines = []

        if self.useThread:
            repeatFlagName = RepeatableAction.getRepeatFlagLuaName(control)
            threadName = RepeatableAction.getThreadLuaName(control)

            lines.append("%s[1] = false" % (repeatFlagName,))
            lines.append("jsprog_canceldelay(%s[1])" % (threadName,))
        else:
            appendLinesIndented(lines, self._getLeaveLuaCode(control), "")

        return lines

    def reprRepeatDelay(self, separator = ", "):
        """Get the string representation of the repeat delay."""
        return "" if self.repeatDelay is None \
            else (separator + "repeatDelay=%d" % (self.repeatDelay,))

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        if self.repeatDelay is not None:
            element.setAttribute("repeatDelay", str(self.repeatDelay))

#------------------------------------------------------------------------------

class KeyCommand(object):
    """A key press or release command"""
    def __init__(self, code):
        self.code = code

    def getLuaCode(self, press = True):
        """Get a line array with the Lua code for the key being pressed or released."""
        keyName = Key.getNameFor(self.code)
        if press:
            return ["jsprog_presskey(jsprog_%s)" % (keyName,)]
        else:
            return ["jsprog_releasekey(jsprog_%s)" % (keyName,)]

    def getXMLFor(self, document, elementName):
        """Get the XML element describing this command for the given element
        name."""
        element = document.createElement(elementName)
        keyElement = document.createTextNode(Key.getNameFor(self.code))
        element.appendChild(keyElement)

        return element

#------------------------------------------------------------------------------

class KeyPressCommand(KeyCommand):
    """A command representing the pressing of a key."""
    def __init__(self, code):
        super(KeyPressCommand, self).__init__(code)

    def clone(self):
        """Clone this key command."""
        return KeyPressCommand(self.code)

    def getLuaCode(self, control):
        """Get the Lua code for the key press."""
        return KeyCommand.getLuaCode(self, press = True)

    def getXML(self, document):
        """Get an XML element describing this command."""
        return self.getXMLFor(document, "keyPress")

    def __eq__(self, other):
        """Determine if this command is equal to the other one"""
        return isinstance(other, KeyPressCommand) and \
            self.code==other.code

    def __repr__(self):
        """Get a string representation of this command."""
        return "KeyPressCommand<" + Key.getNameFor(self.code) + ">"

#------------------------------------------------------------------------------

class KeyReleaseCommand(KeyCommand):
    """A command representing the releasing of a key."""
    def __init__(self, code):
        super(KeyReleaseCommand, self).__init__(code)

    def clone(self):
        """Clone this key command."""
        return KeyReleaseCommand(self.code)

    def getLuaCode(self, control):
        """Get the Lua code for the key press."""
        return KeyCommand.getLuaCode(self, press = False)

    def getXML(self, document):
        """Get an XML element describing this command."""
        return self.getXMLFor(document, "keyRelease")

    def __eq__(self, other):
        """Determine if this command is equal to the other one"""
        return isinstance(other, KeyReleaseCommand) and \
            self.code==other.code

    def __repr__(self):
        """Get a string representation of this command."""
        return "KeyReleaseCommand<" + Key.getNameFor(self.code) + ">"

#------------------------------------------------------------------------------

class MouseMoveCommand(object):
    """A mouse move command."""
    ## Direction constant: horizontal
    DIRECTION_HORIZONTAL = 1

    ## Direction constant: vertical
    DIRECTION_VERTICAL = 2

    ## Direction constant: wheel
    DIRECTION_WHEEL = 3

    @staticmethod
    def getDirectionNameFor(direction):
        """Get the direction name for the given direction."""
        return "horizontal" if  direction==MouseMoveCommand.DIRECTION_HORIZONTAL \
            else "vertical" if direction==MouseMoveCommand.DIRECTION_VERTICAL \
            else "wheel"

    @staticmethod
    def findDirectionFor(directionName):
        """Get the direction for the given directioon name."""
        if directionName=="horizontal":
            return MouseMoveCommand.DIRECTION_HORIZONTAL
        elif directionName=="vertical":
            return MouseMoveCommand.DIRECTION_VERTICAL
        elif directionName=="wheel":
            return MouseMoveCommand.DIRECTION_WHEEL
        else:
            return None

    def __init__(self, direction, a = 0.0, b = 0.0, c = 0.0,
                 adjust = 0.0):
        """Construct the mouse move command."""
        self.direction = direction
        self.a = a
        self.b = b
        self.c = c
        self.adjust = adjust

    @property
    def directionName(self):
        """Get the name of the action's direction."""
        return MouseMoveCommand.getDirectionNameFor(self.direction)

    def clone(self):
        """Clone this mouse move command."""
        return MouseMoveCommand(self.direction, a = self.a, b = self.b,
                                c = self.c, adjust = self.adjust)

    def getLuaCode(self, control):
        """Get a line vector with the Lua code to produce the mouse
        movement."""
        lines = []

        lines.append("local avalue = _jsprog_%s_value - (%.f)" %
                     (control.name, self.adjust))
        lines.append("local dist = %.f + %.f * avalue + %.f * avalue * avalue" %
                     (self.a, self.b, self.c))
        lines.append("jsprog_moverel(jsprog_REL_%s, dist)" %
                     ("X" if self.direction==MouseMoveCommand.DIRECTION_HORIZONTAL
                      else "Y" if self.direction==MouseMoveCommand.DIRECTION_VERTICAL
                      else "WHEEL"))

        return lines

    def extendXML(self, document, element):
        """Extend the given element with specific data."""
        element.setAttribute("direction", self.directionName)
        if self.a!=0.0:
            element.setAttribute("a", str(self.a))
        if self.b!=0.0:
            element.setAttribute("b", str(self.b))
        if self.c!=0.0:
            element.setAttribute("c", str(self.c))
        if self.adjust!=0.0:
            element.setAttribute("adjust", str(self.adjust))

    def getXML(self, document):
        """Get an XML element describing this command."""
        element = document.createElement("mouseMove")
        self.extendXML(document, element)

        return element

    def reprInternal(self):
        """Get the internal part of the representation."""
        return ("horizontal"
                if self.direction==MouseMoveCommand.DIRECTION_HORIZONTAL
                else "vertical"
                if self.direction==MouseMoveCommand.DIRECTION_VERTICAL
                else "wheel") + \
               (", a=%f, b=%f, c=%f, adjust=%f" %
                (self.a, self.b, self.c, self.adjust))

    def __eq__(self, other):
        """Determine if this command is equal to the other one"""
        return isinstance(other, MouseMoveCommand) and \
            self.direction==other.direction and \
            self.a==other.a and \
            self.b==other.b and \
            self.c==other.c and \
            self.adjust==other.adjust

    def __repr__(self):
        """Get a string representation of this command."""
        return "MouseMoveCommand<" + self.reprInternal() + ">"

#------------------------------------------------------------------------------

class DelayCommand(object):
    """A command representing the delay of a certain milliseconds."""
    def __init__(self, length):
        """Construct the delay command."""
        self.length = length

    def clone(self):
        """Clone this delay command."""
        return DelayCommand(self.length)

    def getLuaCode(self, control):
        """Get a line vector with the Lua code to produce the delay."""
        return ["jsprog_delay(%d, false)" % (self.length,)]

    def getXML(self, document):
        """Get an XML element describing this command."""
        element = document.createElement("delay")
        lengthElement = document.createTextNode(str(self.length))
        element.appendChild(lengthElement)

        return element

    def __eq__(self, other):
        """Determine if this command is equal to the other one"""
        return isinstance(other, DelayCommand) and \
            self.length==other.length

    def __repr__(self):
        """Get a string representation of this command."""
        return "DelayCommand<%d>" % (self.length,)

#------------------------------------------------------------------------------

class SimpleAction(RepeatableAction):
    """A simple action.

    It emits one or more key combinations when a control event
    happens, and as long as the event is valid, it may repeat the event."""
    class KeyCombination(KeyCommand):
        """A key combination to be issued for the joystick key."""
        def __init__(self, code,
                     leftShift=False, rightShift=False,
                     leftControl = False, rightControl = False,
                     leftAlt = False, rightAlt = False,
                     leftSuper = False, rightSuper = False):
            """Construct the key combination with the given values."""
            super(SimpleAction.KeyCombination, self).__init__(code)

            self.leftShift = leftShift
            self.rightShift = rightShift

            self.leftControl = leftControl
            self.rightControl = rightControl

            self.leftAlt = leftAlt
            self.rightAlt = rightAlt

            self.leftSuper = leftSuper
            self.rightSuper = rightSuper

        def reset(self):
            """Reset the key combination to be empty."""
            self.code = 0

            self.leftShift = False
            self.rightShift = False

            self.leftControl = False
            self.rightControl = False

            self.leftAlt = False
            self.rightAlt = False

            self.leftSuper = False
            self.rightSuper = False

        def clone(self):
            """Make a clone of this key combination."""
            return SimpleAction.KeyCombination(self.code,
                                               leftShift = self.leftShift,
                                               rightShift = self.rightShift,
                                               leftControl = self.leftControl,
                                               rightControl = self.rightControl,
                                               leftAlt = self.leftAlt,
                                               rightAlt = self.rightAlt,
                                               leftSuper = self.leftSuper,
                                               rightSuper = self.rightSuper)

        def getXML(self, document):
            """Get the XML element for this key combination."""
            element = document.createElement("keyCombination")

            if self.leftShift: element.setAttribute("leftShift", "yes")
            if self.rightShift: element.setAttribute("rightShift", "yes")
            if self.leftControl: element.setAttribute("leftControl", "yes")
            if self.rightControl: element.setAttribute("rightControl", "yes")
            if self.leftAlt: element.setAttribute("leftAlt", "yes")
            if self.rightAlt: element.setAttribute("rightAlt", "yes")
            if self.leftSuper: element.setAttribute("leftSuper", "yes")
            if self.rightSuper: element.setAttribute("rightSuper", "yes")

            keyNameElement = document.createTextNode(Key.getNameFor(self.code))
            element.appendChild(keyNameElement)

            return element

        def getLuaCode(self):
            """Get the Lua code to invoke this key combination.

            Return an array of lines."""
            lines = []

            if self.leftShift: lines.append("jsprog_presskey(jsprog_KEY_LEFTSHIFT)")
            if self.rightShift: lines.append("jsprog_presskey(jsprog_KEY_RIGHTSHIFT)")
            if self.leftControl: lines.append("jsprog_presskey(jsprog_KEY_LEFTCTRL)")
            if self.rightControl: lines.append("jsprog_presskey(jsprog_KEY_RIGHTCTRL)")
            if self.leftAlt: lines.append("jsprog_presskey(jsprog_KEY_LEFTALT)")
            if self.rightAlt: lines.append("jsprog_presskey(jsprog_KEY_RIGHTALT)")
            if self.leftSuper: lines.append("jsprog_presskey(jsprog_KEY_LEFTMETA)")
            if self.rightSuper: lines.append("jsprog_presskey(jsprog_KEY_RIGHTMETA)")

            lines += KeyCommand.getLuaCode(self, press = True)
            lines += KeyCommand.getLuaCode(self, press = False)

            if self.rightSuper: lines.append("jsprog_releasekey(jsprog_KEY_RIGHTMETA)")
            if self.leftSuper: lines.append("jsprog_releasekey(jsprog_KEY_LEFTMETA)")
            if self.rightAlt: lines.append("jsprog_releasekey(jsprog_KEY_RIGHTALT)")
            if self.leftAlt: lines.append("jsprog_releasekey(jsprog_KEY_LEFTALT)")
            if self.rightControl: lines.append("jsprog_releasekey(jsprog_KEY_RIGHTCTRL)")
            if self.leftControl: lines.append("jsprog_releasekey(jsprog_KEY_LEFTCTRL)")
            if self.rightShift: lines.append("jsprog_releasekey(jsprog_KEY_RIGHTSHIFT)")
            if self.leftShift: lines.append("jsprog_releasekey(jsprog_KEY_LEFTSHIFT)")

            return lines

        def __eq__(self, other):
            """Determine if this key combination is equal to the given other
            one."""
            return self.code==other.code and \
                self.leftShift==other.leftShift and \
                self.rightShift==other.rightShift and \
                self.leftControl==other.leftControl and \
                self.rightControl==other.rightControl and \
                self.leftAlt==other.leftAlt and \
                self.rightAlt==other.rightAlt and \
                self.leftSuper==other.leftSuper and \
                self.rightSuper==other.rightSuper

        def __repr__(self):
            """Get a string representation of this key combination."""
            s = ""
            if self.leftShift:
                s += "LS+"
            if self.rightShift:
                s += "RS+"
            if self.leftControl:
                s += "LC+"
            if self.rightControl:
                s += "RC+"
            if self.leftAlt:
                s += "LA+"
            if self.rightAlt:
                s += "RA+"
            if self.leftSuper:
                s += "LSu+"
            if self.rightSuper:
                s += "RSu+"
            s += Key.getNameFor(self.code)
            return "KeyCombination<" + s + ">"

    def __init__(self, displayName = None, repeatDelay = None):
        """Construct the simple action with the given repeat delay."""
        super(SimpleAction, self).__init__(displayName = displayName,
                                           repeatDelay = repeatDelay)
        self._keyCombinations = []

    @property
    def type(self):
        """Get the type of the action."""
        return Action.TYPE_SIMPLE

    @property
    def valid(self):
        """Determine if the action is valid, i.e. if it has any key
        combinations."""
        return bool(self._keyCombinations)

    @property
    def keyCombinations(self):
        """Get an iterator over the key combinations."""
        return iter(self._keyCombinations)

    def clone(self):
        """Make a clone of this action."""
        action = SimpleAction(self.repeatDelay)

        action._keyCombinations = [k.clone() for k in self._keyCombinations]

        return action

    def addKeyCombination(self, code,
                          leftShift=False, rightShift=False,
                          leftControl = False, rightControl = False,
                          leftAlt = False, rightAlt = False,
                          leftSuper = False, rightSuper = False):
        """Add the key combination with the given data."""
        keyCombination = \
            SimpleAction.KeyCombination(code,
                                        leftShift = leftShift,
                                        rightShift = rightShift,
                                        leftControl = leftControl,
                                        rightControl = rightControl,
                                        leftAlt = leftAlt,
                                        rightAlt = rightAlt,
                                        leftSuper = leftSuper,
                                        rightSuper = rightSuper)
        self.appendKeyCombination(keyCombination)

    def appendKeyCombination(self, keyCombination):
        """Append a key combination to the action."""
        self._keyCombinations.append(keyCombination)

    def _getEnterLuaCode(self, control):
        """Get the Lua code to be executed when the action is entered into.

        Returns an array of lines."""
        lines = []

        for keyCombination in self._keyCombinations:
            lines += keyCombination.getLuaCode()

        return lines

    def _getLeaveLuaCode(self, control):
        """Get the Lua code to be executed when the action is left.

        Returns an empty array."""
        return []

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        super(SimpleAction, self)._extendXML(document, element)

        for keyCombination in self._keyCombinations:
            element.appendChild(keyCombination.getXML(document))

    def __eq__(self, other):
        """Determine if this and other other actions are equal."""
        if not isinstance(other, SimpleAction):
            return False

        return self.repeatDelay==other.repeatDelay and \
            self._keyCombinations==other._keyCombinations

    def __repr__(self):
        """Get a string representation of this action."""
        return "SimpleAction<" + repr(self._keyCombinations) + \
            self.reprRepeatDelay() + ">"

#------------------------------------------------------------------------------

class MouseMove(RepeatableAction):
    def __init__(self, direction, a = 0.0, b = 0.0, c = 0.0,
                 adjust = 0.0, displayName = None, repeatDelay = None):
        """Construct the mouse move action with the given repeat delay."""
        super(MouseMove, self).__init__(displayName = None,
                                        repeatDelay = repeatDelay)
        self.command = MouseMoveCommand(direction, a, b, c, adjust)

    @property
    def type(self):
        """Get the type of the action."""
        return Action.TYPE_MOUSE_MOVE

    @property
    def valid(self):
        """Determine if the action is valid, which it is once
        parsed."""
        return True

    @property
    def directionName(self):
        """Get the name of the action's direction."""
        return self.command.directionName

    def clone(self):
        """Clone this action."""
        return MouseMove(self.command.direction, a = self.command.a,
                         b = self.command.b, c = self.command.c,
                         adjust = self.command.adjust,
                         repeatDelay = self.repeatDelay)

    def _getEnterLuaCode(self, control):
        """Get the Lua code to produce the mouse movement.

        Returns an array of lines."""
        return self.command.getLuaCode(control)

    def _getLeaveLuaCode(self, control):
        """Get the Lua code to be executed when the action is left.

        Returns an empty array."""
        return []

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        super(MouseMove, self)._extendXML(document, element)

        self.command.extendXML(document, element)

    def __eq__(self, other):
        """Determine if this and other other actions are equal."""
        if not isinstance(other, MouseMove):
            return False

        return self.repeatDelay==other.repeatDelay and \
            self.command==other.command

    def __repr__(self):
        """Get a string representation of this action."""
        return "MouseMove<" + self.command.reprInternal() + \
            self.reprRepeatDelay() + ">"

#------------------------------------------------------------------------------

class AdvancedAction(RepeatableAction):
    """An action that contains direct key press and release events with
    possible delays. There are separate sequences for the entry, the repeated
    and the leaving events.
    """
    SECTION_NONE = 0

    SECTION_ENTER = 1

    SECTION_REPEAT = 2

    SECTION_LEAVE = 3

    def __init__(self, displayName = None, repeatDelay = None):
        super(AdvancedAction, self).__init__(displayName = displayName,
                                             repeatDelay = repeatDelay)
        self._enterCommands = []
        self._repeatCommands = None
        self._leaveCommands = []
        self._section = AdvancedAction.SECTION_NONE

    @property
    def type(self):
        """Get the type of the action."""
        return Action.TYPE_ADVANCED

    @property
    def isRepeatDifferent(self):
        """Determine if a different sequence of commands should be executed
        when repeating the control."""
        return self._repeatCommands is not None

    @property
    def enterCodeNeedsThread(self):
        """Indicate if the enter code needs to be run in a thread (e.g. because
        it contains one or more delays)."""
        if self._repeatCommands:
            return True

        for command in self._enterCommands:
            if isinstance(command, DelayCommand):
                return True

        return False

    @property
    def leaveCodeNeedsThread(self):
        """Indicate if the leave code needs to be run in a thread (e.g. because
        it contains one or more delays)."""
        for command in self._leaveCommands:
            if isinstance(command, DelayCommand):
                return True

        return False

    @property
    def valid(self):
        """Determine if the action is valid, i.e. if it has at least one
        command."""
        hasRepeatCommands = \
            self._repeatCommands is not None and len(self._repeatCommands)>0
        repeatDelay = self.repeatDelay

        return (repeatDelay is None and
                (len(self._enterCommands)>0 or len(self._leaveCommands)>0) and
                not hasRepeatCommands) or \
                (repeatDelay is not None and
                 (len(self._enterCommands)>0 or hasRepeatCommands))

        if repeatDelay is None:
            return (len(self._enterCommands)>0 or \
                    len(self._leaveCommands)>0)  and \
                    not hasRepeatCommands
        else:
            return len(self._enterCommands)>0 or hasRepeatCommands

    @property
    def enterCommands(self):
        """Get an iterator over the enter commands."""
        return iter(self._enterCommands)

    @property
    def hasRepeatCommands(self):
        """Indicate if the action has any repeat commands."""
        return self._repeatCommands is not None and len(self._repeatCommands)>0

    @property
    def repeatCommands(self):
        """Get an iterator over the repeat commands."""
        if self._repeatCommands is not None:
            for command in self._repeatCommands:
                yield command

    @property
    def leaveCommands(self):
        """Get an iterator over the leave commands."""
        return iter(self._leaveCommands)

    def clone(self):
        """Clone this action."""
        action = AdvancedAction(self.repeatDelay)

        action._enterCommands = \
            [c.clone() for c in self._enterCommands]
        action._repeatCommands = \
            None if self._repeatCommands is None else \
            [c.clone() for c in self._repeatCommands]
        action._leaveCommands = \
            [c.clone() for c in self._leaveCommands]
        action._section = self._section

        return action

    def setSection(self, section):
        """Set the section to be used for the succeeding appendCommand
        calls."""
        self._section = section

    def clearSection(self):
        """Clear the section."""
        self._section = AdvancedAction.SECTION_NONE

    def appendCommand(self, command):
        """Append the given command to the current section."""
        if self._section==AdvancedAction.SECTION_ENTER:
            self._enterCommands.append(command)
        elif self._section==AdvancedAction.SECTION_REPEAT:
            if self._repeatCommands is None:
                self._repeatCommands = [command]
            else:
                self._repeatCommands.append(command)
        elif self._section==AdvancedAction.SECTION_LEAVE:
            self._leaveCommands.append(command)
        else:
            assert False, "No section specified"

    def _getEnterLuaCode(self, control):
        """Get the Lua code to be executed when the control is actuated."""
        lines = []
        for command in self._enterCommands:
            lines += command.getLuaCode(control)
        return lines

    def _getRepeatLuaCode(self, control):
        """Get the Lua code to be executed when the control is to be repeated."""
        lines = []
        if self._repeatCommands is not None:
            for command in self._repeatCommands:
                lines += command.getLuaCode(control)
        return lines

    def _getLeaveLuaCode(self, control):
        """Get the Lua code to be executed when the control is released."""
        lines = []
        for command in self._leaveCommands:
            lines += command.getLuaCode(control)
        return lines

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        super(AdvancedAction, self)._extendXML(document, element)

        self._extendXMLWithCommands(document, element, "enter",
                                    self._enterCommands)
        self._extendXMLWithCommands(document, element, "repeat",
                                    self._repeatCommands)
        self._extendXMLWithCommands(document, element, "leave",
                                    self._leaveCommands)

    def _extendXMLWithCommands(self, document, element, childElementName,
                               commands):
        """Extend the given XML document with commands under the given element
        name."""
        if not commands:
            return

        childElement = document.createElement(childElementName)

        for command in commands:
            childElement.appendChild(command.getXML(document))

        element.appendChild(childElement)

    def __eq__(self, other):
        """Determine if this and other other actions are equal."""
        if not isinstance(other, AdvancedAction):
            return False

        return self.repeatDelay==other.repeatDelay and \
            self._enterCommands==other._enterCommands and \
            self._repeatCommands==other._repeatCommands and \
            self._leaveCommands==other._leaveCommands

    def __repr__(self):
        """Get a string representation of this action."""
        return "AdvancedAction<enter=" + repr(self._enterCommands) + \
            ("" if self._repeatCommands is None else
             (", repeat=" + repr(self._repeatCommands))) + \
            ", leave=" + repr(self._leaveCommands) + \
            self.reprRepeatDelay() + ">"

#------------------------------------------------------------------------------

class ScriptAction(Action):
    """An action where both the enter and the leave codes are Lua script
    fragments.
    """
    SECTION_NONE = 0

    SECTION_ENTER = 1

    SECTION_LEAVE = 2

    def __init__(self, displayName = None):
        """Construct the action."""
        super(ScriptAction, self).__init__(displayName = displayName)
        self._enterLines = []
        self._leaveLines = []
        self._section = ScriptAction.SECTION_NONE

    @property
    def type(self):
        """Get the type of the action."""
        return Action.TYPE_SCRIPT

    @property
    def valid(self):
        """Determine if the action is valid, i.e. if it has any key
        combinations."""
        return bool(self._enterLines) or bool(self._leaveLines)

    @property
    def enterLines(self):
        """Get an iterator over the lines of code to be executed when the
        control is activated."""
        return iter(self._enterLines)

    @property
    def leaveLines(self):
        """Get an iterator over the lines of code to be executed when the
        control is deactivated."""
        return iter(self._leaveLines)

    def clone(self):
        """Clone this action."""
        action = ScriptAction()

        action._enterLines = self._enterLines[:]
        action._leaveLines = self._leaveLines[:]
        action._section = self._section

        return action

    def setSection(self, section):
        """Set the section to be used for the succeeding appendCommand
        calls."""
        self._section = section

    def clearSection(self):
        """Clear the section."""
        self._section = ScriptAction.SECTION_NONE

    def getEnterLuaCode(self, control):
        """Get the Lua code to be executed when the control is activated."""
        return self._enterLines

    def getLeaveLuaCode(self, control):
        """Get the Lua code to be executed when the control is released."""
        return self._leaveLines

    def appendLine(self, line):
        """Append the given line to the current section."""
        assert self._section in [ScriptAction.SECTION_ENTER,
                                 ScriptAction.SECTION_LEAVE]
        (self._enterLines if self._section==ScriptAction.SECTION_ENTER
         else self._leaveLines).append(line)

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        self._extendXMLWith(document, element, "enter", self._enterLines)
        self._extendXMLWith(document, element, "leave", self._leaveLines)

    def _extendXMLWith(self, document, element, childElementName, lines):
        """Extend the given XML element with a child tag containing the given
        lines."""
        if not lines:
            return

        childElement = document.createElement(childElementName)

        for line in lines:
            lineElement = document.createElement("line")
            lineContentsElement = document.createTextNode(line)
            lineElement.appendChild(lineContentsElement)
            childElement.appendChild(lineElement)

        element.appendChild(childElement)

    def __eq__(self, other):
        """Determine if this and other other actions are equal."""
        if not isinstance(other, ScriptAction):
            return False

        return self._enterLines==other._enterLines and \
            self._leaveLines==other._leaveLines

    def __repr__(self):
        """Get a string representation of this action."""
        return "ScriptAction<enter=" + repr(self._enterLines) + \
            ", leave=" + repr(self._leaveLines) + \
            self.reprRepeatDelay() + ">"

#------------------------------------------------------------------------------

class ValueRangeAction(Action):
    """An action that is made up of one or more actions assigned to ranges of
    values of a control."""
    def __init__(self):
        """Construct the action."""
        super().__init__()
        self._actions = []

    @property
    def type(self):
        """Get the type of the action."""
        return Action.TYPE_VALUE_RANGE

    @property
    def actions(self):
        """Get an iterator over the actions."""
        return iter(self._actions)

    @property
    def numActions(self):
        """Get the number of actions."""
        return len(self._actions)

    @property
    def valid(self):
        """Determine if the action is valid."""
        previousToValue = None
        for (fromValue, toValue, action) in self._actions:
            if fromValue>toValue or \
               previousToValue is not None and fromValue<=previousToValue or \
               not action.valid:
                return False

            previousToValue = toValue

        return True

    def addAction(self, fromValue, toValue, action):
        """Add the given action."""
        item = (fromValue, toValue, action)

        if len(self._actions)==0:
            self._actions = [item]
        else:
            index = len(self._actions) - 1

            while index>=0:
                if fromValue>self._actions[index][0]:
                    self._actions.insert(index + 1, item)
                    break
                index -= 1

            if index<0:
                self._actions.insert(0, item)

        assert(self.valid)

    def setAction(self, fromValue, toValue, action):
        """Set the action with the given range.

        A range exactly matching an existing one must be given."""
        for i in range(0, len(self._actions)):
            (f, t, a) = self._actions[i]
            if fromValue==f and toValue==t:
                self._actions[i] = (f, t, action)
                return
        assert(False)

    def findAction(self, fromValue, toValue):
        """Find the action that has the given value range."""
        for (f, t, action) in self._actions:
            if fromValue==f and toValue==t:
                return action

    def changeRange(self, origFromValue, origToValue,
                    newFromValue, newToValue):
        """Change the limits of the range with the given original values."""
        self._actions = [(newFromValue, newToValue, action) if
                         f==origFromValue and t==origToValue else
                         (f, t, action) for (f, t, action) in self._actions]

    def removeAction(self, fromValue, toValue):
        """Remove the action corresponding to the given range."""
        self._actions = [(f, t, action) for (f, t, action) in self._actions
                         if f!=fromValue or t!=toValue]

#------------------------------------------------------------------------------

class NOPAction(Action):
    """An action that does nothing."""
    @property
    def type(self):
        """Get the type of the action."""
        return Action.TYPE_NOP

    @property
    def valid(self):
        """Determine if the action is valid, which it always is."""
        return True

    def clone(self):
        """Clone this action."""
        return NOPAction()

    def getEnterLuaCode(self, control):
        """Get the Lua code that starts the action."""
        return []

    def getLeaveLuaCode(self, control):
        """Get the Lua code that ends the action."""
        return []

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        pass

    def __eq__(self, other):
        """Determine if this and other other actions are equal."""
        return isinstance(other, NOPAction)

    def __repr__(self):
        """Get a string representation of this action."""
        return "NOPAction"
