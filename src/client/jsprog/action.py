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

    ## Action type: script (a Lua script)
    TYPE_SCRIPT = 3

    ## The mapping of types to strings
    _typeNames = {
        TYPE_SIMPLE : "simple",
        TYPE_ADVANCED : "advanced",
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

class SimpleAction(Action):
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
        self.repeatDelay = repeatDelay
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
    def needCancelThreadOnRelease(self):
        """Determine if the thread running this action needs to be
        cancelled when the control event ceases (e.g. the button is
        released)."""
        return self.repeatDelay is not None

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

    def getLuaCode(self):
        """Get the Lua code handling the key.

        Returns an array of lines."""
        lines = []

        indentation = ""
        if self.repeatDelay is not None:
            lines.append("while true do")
            indentation = "  "

        for keyCombination in self._keyCombinations:
            appendLinesIndented(lines, keyCombination.getLuaCode(), indentation)

        if self.repeatDelay is not None:
            lines.append("  jsprog_delay(%d)" % (self.repeatDelay,))
            lines.append("end")

        return lines

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        if self.repeatDelay is not None:
            element.setAttribute("repeatDelay", str(self.repeatDelay))

        for keyCombination in self._keyCombinations:
            element.appendChild(keyCombination.getXML(document))
