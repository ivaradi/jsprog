
from joystick import InputID, JoystickIdentity, Key

from xml.sax.handler import ContentHandler
from xml.sax import SAXParseException

from xml.dom.minidom import getDOMImplementation

#------------------------------------------------------------------------------

## @package jsprog.profile
#
# The handling of the profiles

#------------------------------------------------------------------------------

class Parser(ContentHandler):
    """XML parser for a profile file."""
    def __init__(self):
        """Construct the parser."""
        self._locator = None

        self._context = []
        self._characterContext = []

        self._profile = None

        self._inputID = None
        self._name = None
        self._phys = None
        self._uniq = None

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

    def setDocumentLocator(self, locator):
        """Called to set the locator."""
        self._locator = locator

    def startDocument(self):
        """Called at the beginning of the document."""
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
        elif name=="keys":
            self._checkParent(name, "joystickProfile")
        elif name=="key":
            self._checkParent(name, "keys")
            self._startKey(attrs)
        elif name=="keyCombination":
            self._checkParent(name, "key")
            self._startKeyCombination(attrs)
        else:
            self._fatal("unhandled tag")
        self._context.append(name)
        if len(self._characterContext)<len(self._context):
            self._characterContext.append(None)

    def endElement(self, name):
        """Called for each end tag."""
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
        elif name=="keyCombination":
            self._endKeyCombination()
        del self._context[-1]

    def characters(self, content):
        """Called for character content."""
        if content.strip():
            self._appendCharacters(content)

    def endDocument(self):
        """Called at the end of the document."""

    def _startJoystickProfile(self, attrs):
        """Handle the joystickProfile start tag."""
        if self._profile is not None:
            self._fatal("there should be only one 'joystickProfile' element")

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
        self._profile = Profile(identity)

    def _startKey(self, attrs):
        """Handle the key start tag."""
        code = None
        if "code" in attrs:
            code = self._getIntAttribute(attrs, "code")
        elif "name" in attrs:
            code = Key.findCodeFor(attrs["name"])

        if code is None:
            self._fatal("either a valid code or name is expected")

        if self._profile.findKeyHandler(code) is not None:
            self._fatal("a handler for the key is already defined")

        type = KeyHandler.findTypeFor(self._getAttribute(attrs, "type"))
        if type is None:
            self._fatal("invalid type")

        if type==KeyHandler.TYPE_SIMPLE:
            self._keyHandler = SimpleKeyHandler(code,
                                                self._findIntAttribute(attrs, "repeatDelay"))
        else:
            self._fatal("unhandled key type")

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

    def _endKey(self):
        """Handle the key end tag."""
        if self._keyHandler.type == KeyHandler.TYPE_SIMPLE:
            if not self._keyHandler.valid:
                self._fatal("key handler has no key combinations")
        else:
            self._fatal("unhandled key handler type")
        self._profile.addKeyHandler(self._keyHandler)
        self._keyHandler = None

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

    def _checkParent(self, element, parentElement):
        """Check if the last element of the context is the given
        one."""
        if self._context[-1]!=parentElement:
            self._fatal("tag '%s' should appear within '%s'" %
                        (element, parentElement))

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
            elif value.startswith("0"):
                return int(value[1:], 8)
            else:
                return int(value)
        except:
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

    def __init__(self, type, code):
        """Construct a key handler with the given type and for the
        given key (button) code."""
        self._type = type
        self.code = code

    @property
    def type(self):
        """Get the type of the key handler."""
        return self._type

    @property
    def typeName(self):
        """Get the type name of the key handler."""
        return KeyHandler._typeNames[self._type]

    def getXML(self, document):
        """Get the element for the key handler."""
        element = document.createElement("key")

        element.setAttribute("code", "0x%x" % (self.code,))
        element.setAttribute("type", self.typeName)

        self._extendXML(document, element)

        return element

    def getDaemonXML(self, document):
        """Get the XML element for the XML document to be sent to the
        daemon."""
        element = document.createElement("key")

        element.setAttribute("name", Key.getNameFor(self.code))

        luaCode = map(lambda l: "    " + l, self.getLuaCode())
        luaText = "\n" + "\n".join(luaCode)

        element.appendChild(document.createTextNode(luaText))

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

    def __init__(self, code, repeatDelay = None):
        """Construct the simple key handler with the given repeat
        delay."""
        super(SimpleKeyHandler, self).__init__(KeyHandler.TYPE_SIMPLE,
                                               code)
        self.repeatDelay = repeatDelay
        self._keyCombinations = []

    @property
    def valid(self):
        """Determine if the key handler is valid, i.e. if it has any
        key combinations."""
        return bool(self._keyCombinations)

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
        lines.append("if value~=0 then")

        indentation = "  "
        if self.repeatDelay is not None:
            lines.append("  while true do")
            indentation = "    "

        for keyCombination in self._keyCombinations:
            lines += map(lambda l: indentation + l,
                         keyCombination.getLuaCode())

        if self.repeatDelay is not None:
            lines.append("    jsprog_delay(%d)" % (self.repeatDelay,))
            lines.append("  end")

        if self.repeatDelay is not None:
            lines.append("else")
            lines.append("  jsprog_cancelpreviousofkey(%d)" % (self.code,))

        lines.append("end")

        return lines

    def _extendXML(self, document, element):
        """Extend the given element with specific data."""
        if self.repeatDelay is not None:
            element.setAttribute("repeatDelay", str(self.repeatDelay))

        for keyCombination in self._keyCombinations:
            element.appendChild(keyCombination.getXML(document))

#------------------------------------------------------------------------------

class Profile(object):
    """A joystick profile."""
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

    def __init__(self, identity):
        """Construct an empty profile for the joystick with the given
        identity."""
        self._identity = identity
        self._keyHandlers = []
        self._keyHandlerMap = {}

    def addKeyHandler(self, keyHandler):
        """Add the given key handler to the list of key handlers."""
        self._keyHandlers.append(keyHandler)
        self._keyHandlerMap[keyHandler.code] = keyHandler

    def findKeyHandler(self, code):
        """Find the key handler for the given code.

        Returns the key handler or None if, not found."""
        return self._keyHandlerMap.get(code)

    def getXMLDocument(self):
        """Get the XML document describing the profile."""
        document = getDOMImplementation().createDocument(None,
                                                         "joystickProfile",
                                                         None)
        topElement = document.documentElement

        identityElement = Profile.getIdentityXML(document,
                                                 self._identity)
        topElement.appendChild(identityElement)

        if self._keyHandlers:
            keysElement = document.createElement("keys")
            for keyHandler in self._keyHandlers:
                keysElement.appendChild(keyHandler.getXML(document))
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

        for keyHandler in self._keyHandlers:
            topElement.appendChild(keyHandler.getDaemonXML(document))

        epilogueElement = document.createElement("epilogue")
        topElement.appendChild(epilogueElement)

        return document

#------------------------------------------------------------------------------

if __name__ == "__main__":
    from xml.sax import make_parser
    import sys

    parser = make_parser()

    handler = Parser()
    parser.setContentHandler(handler)

    parser.parse(sys.argv[1])

    profile = handler.profile

    #document = profile.getXMLDocument()
    document = profile.getDaemonXMLDocument()

    with open("profile.xml", "wt") as f:
        document.writexml(f, addindent = "  ", newl = "\n")

#------------------------------------------------------------------------------
