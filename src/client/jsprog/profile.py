
from joystick import InputID, JoystickIdentity, Key

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

def appendLinesIndented(dest, lines, indentation = "  "):
    """Append the given lines with the given indentation to dest."""
    dest += map(lambda l: indentation + l, lines)
    return dest

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

        self._keyProfile = None
        self._shiftContext = []

        self._keyHandler = None
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
        elif name=="shiftControls":
            self._checkParent(name, "joystickProfile")
            self._startShiftControls(attrs)
        elif name=="keys":
            self._checkParent(name, "joystickProfile")
            self._startKeys(attrs)
        elif name=="key":
            self._checkParent(name, "keys", "shiftControls")
            self._startKey(attrs)
        elif name=="shift":
            self._checkParent(name, "key", "shift")
            self._startShift(attrs)
        elif name=="keyHandler":
            self._checkParent(name, "key", "shift")
            self._startKeyHandler(attrs)
        elif name=="keyCombination":
            self._checkParent(name, "keyHandler")
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
        elif name=="key":
            self._endKey()
        elif name=="shift":
            self._endShift()
        elif name=="keyHandler":
            self._endKeyHandler()
        elif name=="keyCombination":
            self._endKeyCombination()

    def characters(self, content):
        """Called for character content."""
        if content.strip():
            self._appendCharacters(content)

    def endDocument(self):
        """Called at the end of the document."""

    @property
    def _shiftLevel(self):
        """Determine the shift level, i.e. the length of the shift
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
        shiftLevel = self._shiftLevel
        if shiftLevel<self._profile.numShiftControls:
            return self._profile.getShiftControl(shiftLevel).numStates
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

    def _startShiftControls(self, attrs):
        """Handle the shiftControls start tag."""
        if self._profile is None:
            self._fatal("the shift controls should be specified after the identity")
        if self._profile.hasControlProfiles:
            self._fatal("the shift controls should be specified before any control profiles")

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

        if self._parent == "shiftControls":
            if not self._profile.addShiftControl(KeyShiftControl(code)):
                self._fatal("a shift control involving the key is already defined")
        else:
            if self._profile.findKeyProfile(code) is not None:
                self._fatal("a profile for the key is already defined")

            self._keyProfile = KeyProfile(code)

    def _startShift(self, attrs):
        """Start a shift handler."""
        shiftLevel = self._shiftLevel
        if shiftLevel>=self._profile.numShiftControls:
            self._fatal("too many shift handler levels")

        fromState = self._getIntAttribute(attrs, "fromState")
        toState = self._getIntAttribute(attrs, "toState")

        if toState<fromState:
            self._fatal("the to-state should not be less than the from-state")

        shiftControl = self._profile.getShiftControl(shiftLevel)
        if (self._handlerTree.lastState+1)!=fromState:
            self._fatal("shift handler states are not contiguous")
        if toState>=shiftControl.numStates:
            self._fatal("the to-state is too large")

        self._shiftContext.append(ShiftHandler(fromState, toState))

    def _startKeyHandler(self, attrs):
        if self._shiftLevel!=self._profile.numShiftControls:
            self._fatal("missing shift handler levels")

        if self._handlerTree.numChildren>0:
            self._fatal("a shift handler or a key profile can have only one key handler")

        type = KeyHandler.findTypeFor(self._getAttribute(attrs, "type"))
        if type is None:
            self._fatal("invalid type")

        if type==KeyHandler.TYPE_SIMPLE:
            self._keyHandler = SimpleKeyHandler(repeatDelay =
                                                self._findIntAttribute(attrs, "repeatDelay"))
        else:
            self._fatal("unhandled key handler type")

    def _startKeyCombination(self, attrs):
        """Handle the keyCombination start tag."""
        if self._keyHandler.type!=KeyHandler.TYPE_SIMPLE:
            self._fatal("a key combination is valid only for a simple key handler")

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

        self._keyHandler.addKeyCombination(code,
                                           self._leftShift, self._rightShift,
                                           self._leftControl, self._rightControl,
                                           self._leftAlt, self._rightAlt)

    def _endKeyHandler(self):
        """End the current key handler."""
        if self._keyHandler.type == KeyHandler.TYPE_SIMPLE:
            if not self._keyHandler.valid:
                self._fatal("key handler has no key combinations")
        else:
            self._fatal("unhandled key handler type")

        self._handlerTree.addChild(self._keyHandler)

        self._keyHandler = None

    def _endShift(self):
        """Handle the shift end tag."""
        shiftHandler = self._shiftContext[-1]

        if not shiftHandler.isComplete(self._numExpectedShiftStates):
            self._fatal("shift handler is missing either child shift level states or a key handler")

        del self._shiftContext[-1]

        self._handlerTree.addChild(shiftHandler)

    def _endKey(self):
        """Handle the key end tag."""

        if self._parent=="keys":
            if not self._keyProfile.isComplete(self._numExpectedShiftStates):
                self._fatal("the key profile is missing either child shift level states or a key handler")

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

    def _fatal(self, msg, exception = None):
        """Raise a parse exception with the given message and the
        current location."""
        raise SAXParseException(msg, exception, self._locator)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftControl(object):
    """Base class for the shift controls."""
    ## Shift control type: a simple key
    TYPE_KEY = 1

    def __init__(self, type):
        """Construct the shift control with the given type."""
        self._type = type

#------------------------------------------------------------------------------

class KeyShiftControl(ShiftControl):
    """A shift control which is a simple key."""

    def __init__(self, code):
        """Construct the key shift control for the key with the given
        code."""
        self._code = code

    @property
    def type(self):
        """Get the type of the control."""
        return ShiftControl.TYPE_KEY

    @property
    def numStates(self):
        """Get the number of states, which is 2 in case of a key (not
        pressed or pressed)."""
        return 2

    @property
    def code(self):
        """Get the code of the key this shift control represents."""
        return self._code

    def overlaps(self, other):
        """Check if this shift control overlaps the given other
        one."""
        if other.type==ShiftControl.TYPE_KEY:
            return self._code == other._code
        else:
            assert False

    def getXML(self, document):
        """Get an XML element describing this control."""
        element = document.createElement("key")
        element.setAttribute("name", Key.getNameFor(self._code))
        return element

    def getStateLuaCode(self, variableName):
        """Get the Lua code acquiring the shift state into a local
        variable with the given name.

        Retuns the lines of code."""
        lines = []
        lines.append("local %s" % (variableName,))
        lines.append("local %s_pressed = jsprog_iskeypressed(%d)" %
                     (variableName, self._code))
        lines.append("if %s_pressed then %s=1 else %s=0 end" %
                     (variableName, variableName, variableName))
        return lines

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class KeyHandler(object):
    """Base class for the various key handlers."""

    ## Key handler type: simple (one or more key combinations with an
    ## optional repeat delay)
    TYPE_SIMPLE = 1

    ## Key handler type: advanced (explicit key presses, releases with
    ## optional delays, separately for the key press, the repeat and
    ## the release).
    TYPE_ADVANCED = 2

    ## Key handler type: script (a Lua script)
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
        return KeyHandler._typeNames[type]

    @staticmethod
    def findTypeFor(typeName):
        """Get the type for the given type name."""
        for (type, name) in KeyHandler._typeNames.iteritems():
            if name==typeName:
                return type
        return None

    @property
    def typeName(self):
        """Get the type name of the key handler."""
        return KeyHandler._typeNames[self.type]

    def getXML(self, document):
        """Get the element for the key handler."""
        element = document.createElement("keyHandler")

        element.setAttribute("type", self.typeName)

        self._extendXML(document, element)

        return element

#------------------------------------------------------------------------------

class SimpleKeyHandler(KeyHandler):
    """A simple key handler."""
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
        """Construct the simple key handler with the given repeat
        delay."""
        self.repeatDelay = repeatDelay
        self._keyCombinations = []

    @property
    def type(self):
        """Get the type of the key handler."""
        return KeyHandler.TYPE_SIMPLE

    @property
    def valid(self):
        """Determine if the key handler is valid, i.e. if it has any
        key combinations."""
        return bool(self._keyCombinations)

    @property
    def needCancelThreadOnRelease(self):
        """Determine if the thread running this key handler needs to
        be cancelled when the key is released."""
        return self.repeatDelay is not None

    def addKeyCombination(self, code,
                          leftShift=False, rightShift=False,
                          leftControl = False, rightControl = False,
                          leftAlt = False, rightAlt = False):
        """Add the key combination with the given data."""
        keyCombination = \
            SimpleKeyHandler.KeyCombination(code,
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

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class HandlerTree(object):
    """The root of a tree of shift and key handlers."""
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

    @property
    def needCancelThreadOnRelease(self):
        """Determine if a thread created when a control was activated
        needs to be cancelled when releasing the control."""
        for child in self._children:
            if child.needCancelThreadOnRelease:
                return True

        return False

    def addChild(self, handler):
        """Add a child handler."""
        assert \
            (isinstance(handler, KeyHandler) and not
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

    def getLuaCode(self, profile, shiftLevel = 0):
        """Get the Lua code for this handler tree.

        profile is the joystick profile and shiftLevel is the level in
        the shift tree.

        Return the lines of code."""
        if shiftLevel<profile.numShiftControls:
            numChildren = self.numChildren
            if numChildren==1:
                return self._children[0].getLuaCode(profile,
                                                    shiftLevel + 1)
            else:
                shiftControl = profile.getShiftControl(shiftLevel)
                shiftStateName = "_jsprog_shift_%d" % (shiftLevel,)
                lines = shiftControl.getStateLuaCode(shiftStateName)
                index = 0
                for index in range(0, numChildren):
                    shiftHandler = self._children[index]
                    ifStatement = "if" if index==0 else "elseif"
                    if index==(numChildren-1):
                        lines.append("else")
                    elif shiftHandler.fromState==shiftHandler.toState:
                        lines.append("%s %s==%d then" % (ifStatement,
                                                         shiftStateName,
                                                         shiftHandler.fromState))
                    else:
                        lines.append("%s %s>=%d and %s<=%d then" %
                                     (ifStatement,
                                      shiftStateName, shiftHandler.fromState,
                                      shiftStateName, shiftHandler.toState))

                    handlerCode = shiftHandler.getLuaCode(profile,
                                                          shiftLevel + 1)
                    appendLinesIndented(lines, handlerCode)

                lines.append("end")

                return lines
        else:
            return self._children[0].getLuaCode()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ShiftHandler(HandlerTree):
    """Handler for a certain value or set of values for a shift
    control.

    Zero or more shift controls can be specified each having a value
    from 0 to a certain positive value (e.g. 1 in case of a key (i.e. button) -
    0=not pressed, 1=pressed). The shift controls are specified in a
    certain order and thus they form a hierarchy.

    For each key or other control the actual handlers should be
    specified in the context of the shift state. This context is
    defined by a hierarchy of shift handlers corresponding to the
    hierarchy of shift controls.

    Let's assume, that button A is the first shift control in the
    list, and button B is the second. Then for each key we have one
    ore more shift handlers describing one or more states
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
    level of them corresponding to a shift control."""
    def __init__(self, code):
        """Construct the key profile for the given key code."""
        super(KeyProfile, self).__init__()

        self._code = code

    @property
    def code(self):
        """Get the code of the key."""
        return self._code

    def getXML(self, document):
        """Get the XML element describing the key profile."""
        element = document.createElement("key")
        element.setAttribute("name", Key.getNameFor(self._code))

        for child in self._children:
            element.appendChild(child.getXML(document))

        return element

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
        lines.append("if value~=0 then")

        appendLinesIndented(lines,
                            super(KeyProfile, self).getLuaCode(profile))

        if self.needCancelThreadOnRelease:
            lines.append("else")
            lines.append("  jsprog_cancelpreviousofkey(code)")

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

    def __init__(self, name, identity, autoLoad = False):
        """Construct an empty profile for the joystick with the given
        identity."""
        self.name = name
        self.identity = identity
        self.autoLoad = autoLoad

        self._shiftControls = []

        self._keyProfiles = []
        self._keyProfileMap = {}

    @property
    def hasControlProfiles(self):
        """Determine if we have control (key or axis) profiles or not."""
        return bool(self._keyProfiles)

    @property
    def numShiftControls(self):
        """Determine the number of shift controls."""
        return len(self._shiftControls)

    def match(self, identity):
        """Get the match level for the given joystick identity."""
        return self.identity.match(identity)

    def addShiftControl(self, shiftControl):
        """Add the given shift control to the profile.

        @return a boolean indicating if the addition was successful,
        i.e. the given control does not overlap any other."""
        for sc in self._shiftControls:
            if sc.overlaps(shiftControl):
                return False

        self._shiftControls.append(shiftControl)

        return True

    def getShiftControl(self, level):
        """Get the shift control at the given level."""
        return self._shiftControls[level]

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

        if self._shiftControls:
            shiftControlsElement = document.createElement("shiftControls")
            for shiftControl in self._shiftControls:
                shiftControlsElement.appendChild(shiftControl.getXML(document))
            topElement.appendChild(shiftControlsElement)

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

        prologueElement = document.createElement("prologue")
        topElement.appendChild(prologueElement)

        for keyProfile in self._keyProfiles:
            topElement.appendChild(keyProfile.getDaemonXML(document, self))

        epilogueElement = document.createElement("epilogue")
        topElement.appendChild(epilogueElement)

        return document

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
