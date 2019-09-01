
#------------------------------------------------------------------------------

## @package jsprog.device
#
# The handling of joystick device types

#------------------------------------------------------------------------------

from .joystick import Joystick, JoystickIdentity, Key, Axis
from .parser import BaseHandler, VirtualControl, VirtualState

from xml.sax import make_parser
from xml.dom.minidom import getDOMImplementation

import sys

#------------------------------------------------------------------------------

class DeviceHandler(BaseHandler):
    """XML content handler for a device file."""
    def __init__(self):
        """Construct the parser."""
        super(DeviceHandler, self).__init__(deviceVersionNeeded = False)

        self._joystickType = None
        self._key = None
        self._axis = None

    @property
    def joystickType(self):
        """Get the profile parsed."""
        return self._joystickType

    def startDocument(self):
        """Called at the beginning of the document."""
        super(DeviceHandler, self).startDocument()
        self._joystickType = None

    def doStartElement(self, name, attrs):
        """Called for each start tag."""
        if name=="displayName":
            self._checkParent(name, "key", "axis")
            self._startDisplayName(attrs)
        elif name in ["uniq", "phys"]:
            self._fatal("unhandled tag")
        else:
            super(DeviceHandler, self).doStartElement(name, attrs, "joystick")

    def doEndElement(self, name):
        """Handle the end element."""
        if name=="displayName":
            self._endDisplayName()
        else:
            super(DeviceHandler, self).doEndElement(name, "joystick")

    def _startTopLevelElement(self, attrs):
        """Handle the joystick start tag."""
        if self._joystickType is not None:
            self._fatal("there should be only one 'joystick' element")

    def _endIdentity(self):
        """Handle the identity end tag."""
        if self._inputID is None:
            self._fatal("the input ID is missing from the identity")
        if self._name is None:
            self._fatal("the name is missing from the identity")
        identity = JoystickIdentity(self._inputID, self._name,
                                    self._phys, self._uniq)
        self._identity = identity
        self._joystickType = JoystickType(identity)

    def _startVirtualControls(self, attrs):
        """Handle the virtualControls start tag."""
        pass

    def _addVirtualControl(self, name, attrs):
        """Add a virtual control with the given name."""
        return self._joystickType.\
            addVirtualControl(name, attrs.get("displayName", None))

    def _startVirtualState(self, attrs):
        """Handle the virtualState start tag."""
        if "displayName" not in attrs:
            self._fatal("a virtual state must have a display name")
        self._virtualState = DisplayVirtualState(attrs["displayName"])

    def _endVirtualState(self):
        """Handle the virtualState end tag."""
        virtualState = self._virtualState

        if not virtualState.isValid:
            self._fatal("the virtual state has conflicting controls")

        if not self._virtualControl.addState(virtualState):
            self._fatal("the virtual state is not unique for the virtual control")

        self._virtualState = None

    def _handleStartKey(self, code, attrs):
        """Handle the key start tag for a key with the given code."""
        if self._joystickType.findKey(code) is not None:
            self._fatal("the key is already defined")

        self._key = self._joystickType.addKey(code)

    def _handleStartAxis(self, code, attrs):
        """Handle the axis start tag."""
        if self._joystickType.findAxis(code) is not None:
            self._fatal("the axis is already defined")

        self._axis = self._joystickType.addAxis(code)

    def _startDisplayName(self, attrs):
        """Handle a displayName start tag."""
        self._startCollectingCharacters()

    def _endDisplayName(self):
        """Handle a displayName end tag."""
        displayName = self._getCollectedCharacters()
        if self._parent=="key":
            self._key.displayName = displayName
        else:
            self._axis.displayName = displayName

    def _endKey(self):
        """Handle the key end tag."""
        if self._parent=="controls":
            self._key = None

    def _endAxis(self):
        """Handle the axis end tag."""
        if self._parent=="controls":
            self._axis = None

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class DisplayKey(Key):
    """A key that has a display name."""
    def __init__(self, code):
        """Construct the key for the given code."""
        super(DisplayKey, self).__init__(code)
        self.displayName = Key.getNameFor(code)

    def getXML(self, document):
        """Get the XML representation of the key."""
        element = document.createElement("key")

        element.setAttribute("name", Key.getNameFor(self.code))

        element.appendChild(JoystickType.getTextXML(document,
                                                    "displayName",
                                                    self.displayName))

        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class DisplayAxis(Axis):
    """An axis that has a display name."""
    def __init__(self, code):
        """Construct the axis for the given code."""
        super(DisplayAxis, self).__init__(code, 0, 255)
        self.displayName = Axis.getNameFor(code)


    def getXML(self, document):
        """Get the XML representation of the axis."""
        element = document.createElement("axis")

        element.setAttribute("name", Axis.getNameFor(self.code))

        element.appendChild(JoystickType.getTextXML(document,
                                                    "displayName",
                                                    self.displayName))

        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class DisplayVirtualState(VirtualState):
    """A virtual state that has a display name."""
    def __init__(self, displayName):
        """Create the virtual state with the given display name."""
        super(DisplayVirtualState, self).__init__()
        self.displayName = displayName


    def getXML(self, document):
        """Get an XML element describing this virtual state."""
        element = super(DisplayVirtualState, self).getXML(document)
        element.setAttribute("displayName", self.displayName)

        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class DisplayVirtualControl(VirtualControl):
    """A virtual control that may have a display name."""
    def __init__(self, name, code, displayName=None):
        """Create the virtual control with the given display name."""
        super(DisplayVirtualControl, self).__init__(name, code)
        self.displayName = displayName

    def _createXMLElement(self, document):
        """Create the XML element corresponding to this virtual control."""
        element = super(DisplayVirtualControl, self)._createXMLElement(document)

        if self.displayName is not None and self.displayName!=self.name:
            element.setAttribute("displayName", self.displayName)

        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class JoystickType(Joystick):
    """A joystick type.

    It has controls with display names as well as virtual controls. It can be
    loaded from a file and saved into one. Its identity has an empty physical
    location and unique identifier."""
    @staticmethod
    def fromFile(path):
        """Create a joystick type from the device file at the given path."""

    @staticmethod
    def getTextXML(document, name, text):
        """Create a tag with the given name containing the given
        text."""
        # FIXME: there is the same function in profile.Profile
        element = document.createElement(name)
        value = document.createTextNode(text)
        element.appendChild(value)
        return element

    @staticmethod
    def getInputIDXML(document, inputID):
        """Get the XML representation of the given input ID."""
        # FIXME: there is almost same function in profile.Profile
        inputIDElement = document.createElement("inputID")

        inputIDElement.setAttribute("busType", inputID.busName)
        inputIDElement.setAttribute("vendor", "%04x" % (inputID.vendor,))
        inputIDElement.setAttribute("product", "%04x" % (inputID.product,))

        return inputIDElement

    @staticmethod
    def getIdentityXML(document, identity):
        """Get the XML representation of the given identity."""
        # FIXME: there is almost same function in profile.Profile
        identityElement = document.createElement("identity")

        inputIDElement = JoystickType.getInputIDXML(document, identity.inputID)
        identityElement.appendChild(inputIDElement)

        identityElement.appendChild(JoystickType.getTextXML(document,
                                                            "name",
                                                            identity.name))

        return identityElement

    def __init__(self, identity):
        """Construct a joystick type for the given identity."""
        super(JoystickType, self).__init__(0, identity, [], [])

        self._indicatorIconName = "joystick.svg"
        self._virtualControls = []

    @property
    def indicatorIconName(self):
        """Get the name of the indicator icon."""
        return self._indicatorIconName

    def addVirtualControl(self, name, displayName):
        """Add a virtual control with the given name."""
        virtualControl = DisplayVirtualControl(name,
                                               len(self._virtualControls)+1,
                                               displayName = displayName)
        self._virtualControls.append(virtualControl)
        return virtualControl

    def findKey(self, code):
        """Find the key for the given code."""
        for key in self._keys:
            if key.code==code:
                return key

    def addKey(self, code):
        """Add a key for the given code."""
        key = DisplayKey(code)
        self._keys.append(key)
        return key

    def findAxis(self, code):
        """Find the axis for the given code."""
        for axis in self._axes:
            if axis.code==code:
                return axis

    def addAxis(self, code):
        """Add an axis for the given code."""
        axis = DisplayAxis(code)
        self._axes.append(axis)
        return axis

    def getXMLDocument(self):
        """Get the XML document describing the profile."""
        document = getDOMImplementation().createDocument(None,
                                                         "joystick",
                                                         None)

        topElement = document.documentElement

        identityElement = JoystickType.getIdentityXML(document, self.identity)
        topElement.appendChild(identityElement)

        controlsElement = document.createElement("controls")
        for key in self._keys:
            controlsElement.appendChild(key.getXML(document))
        for axis in self._axes:
            controlsElement.appendChild(axis.getXML(document))
        topElement.appendChild(controlsElement)

        if self._virtualControls:
            virtualControlsElement = document.createElement("virtualControls")
            for virtualControl in self._virtualControls:
                element = virtualControl.getXML(document)
                virtualControlsElement.appendChild(element)
            topElement.appendChild(virtualControlsElement)

        return document


#------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = make_parser()

    handler = DeviceHandler()
    parser.setContentHandler(handler)

    parser.parse(sys.argv[1])

    joystickType = handler.joystickType

    document = joystickType.getXMLDocument()

    with open("device.xml", "wt") as f:
        document.writexml(f, addindent = "  ", newl = "\n")

#------------------------------------------------------------------------------
