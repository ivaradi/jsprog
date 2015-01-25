from joystick import Key
from util import appendLinesIndented

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

    ## The mapping of types to strings
    _typeNames = {
        TYPE_SIMPLE : "simple",
        TYPE_ADVANCED : "advanced",
        TYPE_MOUSE_MOVE : "mouseMove",
        TYPE_SCRIPT: "script"
        }

    @staticmethod
    def getTypeNameFor(type):
        """Get the type name for the given type."""
        return Action._typeNames[type]

    @staticmethod
    def findTypeFor(typeName):
        """Get the type for the given type name."""
        for (type, name) in Action._typeNames.iteritems():
            if name==typeName:
                return type
        return None

    @property
    def typeName(self):
        """Get the type name of the action."""
        return Action._typeNames[self.type]

    def getXML(self, document):
        """Get the element for the key action."""
        element = document.createElement("action")

        element.setAttribute("type", self.typeName)

        self._extendXML(document, element)

        return element

#------------------------------------------------------------------------------

class RepeatableAction(Action):
    """Base class for actions that may be repeated while the control
    event persists."""
    def __init__(self, repeatDelay = None):
        """Construct the action with the given repeat delay."""
        self.repeatDelay = repeatDelay

    def getEnterLuaCode(self, control):
        """Get the Lua code that starts the action.

        If there is a repeay delay, this function generates the
        infinite loop with the delay. Calls the child's _getLuaCode()
        function to get the code of the real action.

        Returns an array of lines."""
        lines = []

        indentation = ""
        if self.repeatDelay is not None:
            lines.append("while true do")
            indentation = "  "

        appendLinesIndented(lines, self._getEnterLuaCode(control), indentation)

        if self.repeatDelay is not None:
            lines.append("  jsprog_delay(%d)" % (self.repeatDelay,))
            lines.append("end")

        return lines

    def getLeaveLuaCode(self, control):
        """Get the Lua code that finishes the action.

        If there is a repeat delay, this function generates a call to cancel
        the previous operation. Otherwise no code is generated.

        Returns an array of lines."""
        lines = []
        if self.repeatDelay is not None:
            lines.append("jsprog_cancelpreviousof%s(%s)" %
                         ("key" if control.isKey else "axis", control.name))
        return lines

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        if self.repeatDelay is not None:
            element.setAttribute("repeatDelay", str(self.repeatDelay))

#------------------------------------------------------------------------------

class SimpleAction(RepeatableAction):
    """A simple action.

    It emits one or more key combinations when a control event
    happens, and as long as the event is valid, it may repeat the event."""
    class KeyCombination(object):
        """A key combination to be issued for the joystick key."""
        def __init__(self, code,
                     leftShift=False, rightShift=False,
                     leftControl = False, rightControl = False,
                     leftAlt = False, rightAlt = False):
            """Construct the key combination with the given values."""
            self.code = code

            self.leftShift = leftShift
            self.rightShift = rightShift

            self.leftControl = leftControl
            self.rightControl = rightControl

            self.leftAlt = leftAlt
            self.rightAlt = rightAlt

        def getXML(self, document):
            """Get the XML element for this key combination."""
            element = document.createElement("keyCombination")

            if self.leftShift: element.setAttribute("leftShift", "yes")
            if self.rightShift: element.setAttribute("rightShift", "yes")
            if self.leftControl: element.setAttribute("leftControl", "yes")
            if self.rightControl: element.setAttribute("rightControl", "yes")
            if self.leftAlt: element.setAttribute("leftAlt", "yes")
            if self.rightAlt: element.setAttribute("rightAlt", "yes")

            keyNameElement = document.createTextNode(Key.getNameFor(self.code))
            element.appendChild(keyNameElement)

            return element

        def getLuaCode(self):
            """Get the Lua code to invoke this key combination.

            Return an array of lines."""
            lines = []

            if self.leftShift: lines.append("jsprog_presskey(jsprog_KEY_LEFTSHIFT)")
            if self.rightShift: lines.append("jsprog_presskey(jsprog_KEY_RIGHTSHIFT)")
            if self.leftControl: lines.append("jsprog_presskey(jsprog_KEY_LEFTTCONTROL)")
            if self.rightControl: lines.append("jsprog_presskey(jsprog_KEY_RIGHTCONTROL)")
            if self.leftAlt: lines.append("jsprog_presskey(jsprog_KEY_LEFTALT)")
            if self.rightAlt: lines.append("jsprog_presskey(jsprog_KEY_RIGHTALT)")

            keyName = Key.getNameFor(self.code)
            lines.append("jsprog_presskey(jsprog_%s)" % (keyName,))
            lines.append("jsprog_releasekey(jsprog_%s)" % (keyName,))

            if self.rightAlt: lines.append("jsprog_releasekey(jsprog_KEY_RIGHTALT)")
            if self.leftAlt: lines.append("jsprog_releasekey(jsprog_KEY_LEFTALT)")
            if self.rightControl: lines.append("jsprog_releasekey(jsprog_KEY_RIGHTCONTROL)")
            if self.leftShift: lines.append("jsprog_releasekey(jsprog_KEY_LEFTSHIFT)")
            if self.rightShift: lines.append("jsprog_releasekey(jsprog_KEY_RIGHTSHIFT)")
            if self.rightShift: lines.append("jsprog_releasekey(jsprog_KEY_RIGHTSHIFT)")
            if self.leftShift: lines.append("jsprog_releasekey(jsprog_KEY_LEFTSHIFT)")

            return lines

    def __init__(self, repeatDelay = None):
        """Construct the simple action with the given repeat delay."""
        super(SimpleAction, self).__init__(repeatDelay = repeatDelay)
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

    def addKeyCombination(self, code,
                          leftShift=False, rightShift=False,
                          leftControl = False, rightControl = False,
                          leftAlt = False, rightAlt = False):
        """Add the key combination with the given data."""
        keyCombination = \
            SimpleAction.KeyCombination(code,
                                        leftShift = leftShift,
                                        rightShift = rightShift,
                                        leftControl = leftControl,
                                        rightControl = rightControl,
                                        leftAlt = leftAlt,
                                        rightAlt = rightAlt)
        self._keyCombinations.append(keyCombination)

    def _getEnterLuaCode(self, control):
        """Get the Lua code to be executed when the action is entered into.

        Returns an array of lines."""
        lines = []

        for keyCombination in self._keyCombinations:
            lines += keyCombination.getLuaCode()

        return lines

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        super(SimpleAction, self)._extendXML(document, element)

        for keyCombination in self._keyCombinations:
            element.appendChild(keyCombination.getXML(document))

#------------------------------------------------------------------------------

class MouseMove(RepeatableAction):
    ## Direction constant: horizontal
    DIRECTION_HORIZONTAL = 1

    ## Direction constant: vertical
    DIRECTION_VERTICAL = 2

    @staticmethod
    def getDirectionNameFor(direction):
        """Get the direction name for the given direction."""
        return "horizontal" if  direction==MouseMove.DIRECTION_HORIZONTAL \
            else "vertical"

    @staticmethod
    def findDirectionFor(directionName):
        """Get the directioon for the given directioon name."""
        if directionName=="horizontal":
            return MouseMove.DIRECTION_HORIZONTAL
        elif directionName=="vertical":
            return MouseMove.DIRECTION_VERTICAL
        else:
            return None

    def __init__(self, direction, a = 0.0, b = 0.0, c = 0.0,
                 adjust = 0.0, repeatDelay = None):
        """Construct the mouse move action with the given repeat delay."""
        super(MouseMove, self).__init__(repeatDelay = repeatDelay)
        self.direction = direction
        self.a = a
        self.b = b
        self.c = c
        self.adjust = adjust

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
        return MouseMove.getDirectionNameFor(self.direction)

    def _getEnterLuaCode(self, control):
        """Get the Lua code to produce the mouse movement.

        Returns an array of lines."""
        lines = []

        lines.append("local avalue = value - %.f" % (self.adjust,))
        lines.append("local dist = %.f + %.f * avalue + %.f * avalue * avalue" %
                     (self.a, self.b, self.c))
        lines.append("jsprog_moverel(jsprog_REL_%s, dist)" %
                     ("X" if self.direction==MouseMove.DIRECTION_HORIZONTAL
                      else "Y"))

        return lines

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        super(MouseMove, self)._extendXML(document, element)

        element.setAttribute("direction", self.directionName)
        if self.a!=0.0:
            element.setAttribute("a", str(self.a))
        if self.b!=0.0:
            element.setAttribute("b", str(self.b))
        if self.c!=0.0:
            element.setAttribute("c", str(self.c))
        if self.adjust!=0.0:
            element.setAttribute("adjust", str(self.adjust))
