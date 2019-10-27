
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
    def __init__(self, joystickTypeClass, *jsTypeCtorArgs):
        """Construct the parser."""
        super(DeviceHandler, self).__init__(deviceVersionNeeded = False)

        self._joystickTypeClass = joystickTypeClass
        self._jsTypeCtorArgs = jsTypeCtorArgs
        self._joystickType = None
        self._key = None
        self._axis = None
        self._view = None
        self._hotspot = None

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
        elif name=="views":
            self._checkParent(name, "joystick")
            self._startViews(attrs)
        elif name=="view":
            self._checkParent(name, "views")
            self._startView(attrs)
        elif name=="hotspot":
            self._checkParent(name, "view")
            self._startHotspot(attrs)
        elif name=="dot":
            self._checkParent(name, "hotspot")
            self._startDot(attrs)
        else:
            super(DeviceHandler, self).doStartElement(name, attrs, "joystick")

    def doEndElement(self, name):
        """Handle the end element."""
        if name=="displayName":
            self._endDisplayName()
        elif name=="view":
            self._endView()
        elif name=="hotspot":
            self._endHotspot()
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
        self._joystickType = self._joystickTypeClass(identity,
                                                     *self._jsTypeCtorArgs)

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

    def _startViews(self, attrs):
        """Handle a views start tag."""
        if self._joystickType is None:
            self._fatal("the views section should start after the identity")

    def _startView(self, attrs):
        """Handle a view start tag."""
        name = self._getAttribute(attrs, "name")
        imageFileName = self._getAttribute(attrs, "imageFileName")

        if self._joystickType.findView(name) is not None:
            self._fatal("view '%s' is already defined" % (name,))

        self._view = View(name, imageFileName)

    def _startHotspot(self, attrs):
        """Handle a hotspot start tag."""
        hotspotType = self._getAttribute(attrs, "type")

        if hotspotType=="label":
            controlType = self._getAttribute(attrs, "controlType")
            controlName = self._getAttribute(attrs, "controlName")
            if controlType=="key":
                controlType = Hotspot.CONTROL_TYPE_KEY
                controlCode = Key.findCodeFor(controlName)
                if self._joystickType.findKey(controlCode) is None:
                    self._fatal("key '%s' is not present on this joystick" %
                                (controlName,))
            elif controlType=="axis":
                controlType = Hotspot.CONTROL_TYPE_AXIS
                controlCode = Axis.findCodeFor(controlName)
                if self._joystickType.findAxis(controlCode) is None:
                    self._fatal("axis '%s' is not present on this joystick" %
                                (controlName,))
            else:
                self._fatal("invalid control type '%s'" % (controlType,))
            if controlCode is None:
                self._fatal("invalid control name '%s'" % (controlName,))

            hotspot = Hotspot(x = int(self._getAttribute(attrs, "x")),
                              y = int(self._getAttribute(attrs, "y")),
                              controlType = controlType,
                              controlCode = controlCode,
                              fontSize = int(self._getAttribute(attrs, "fontSize")),
                              color = self._getColorAttribute(attrs, "color"),
                              bgColor = self._getColorAttribute(attrs, "bgColor"),
                              highlightColor = self._getColorAttribute(attrs, "highlightColor"),
                              highlightBGColor = self._getColorAttribute(attrs, "highlightBGColor"),
                              selectColor = self._getColorAttribute(attrs, "selectColor"))

            self._view.addHotspot(hotspot)

            self._hotspot = hotspot
        else:
            self._fatal("unknown hotspot type '%s'" % (hotspotType,))

    def _startDot(self, attrs):
        """Handle a dot start tag."""
        if self._hotspot.dot is not None:
            self._fatal("a hotspot can contain only one dot")

        self._hotspot.addDot(x = int(self._getAttribute(attrs, "x")),
                             y = int(self._getAttribute(attrs, "y")),
                             radius = int(self._getAttribute(attrs, "radius")),
                             color = self._getColorAttribute(attrs, "color"),
                             highlightColor = self._getColorAttribute(attrs, "highlightColor"),
                             lineWidth = int(self._getAttribute(attrs, "lineWidth")),
                             lineColor = self._getColorAttribute(attrs, "lineColor"),
                             lineHighlightColor = self._getColorAttribute(attrs, "lineHighlightColor"))

    def _endHotspot(self):
        """Handle a hotspot end tag."""
        self._hotspot = None

    def _endView(self):
        """Handle a view end tag."""
        self._joystickType.addView(self._view)
        self._view = None

    def _getColorAttribute(self, attrs, name):
        """Get the given attribute as a colour.

        The value should be a string of the format '#rrggbbaa'."""
        value = self._getAttribute(attrs, name)

        try:
            assert(len(value)==9)
            assert(value[0]=="#")

            red = int(value[1:3], 16)
            green = int(value[3:5], 16)
            blue = int(value[5:7], 16)
            alpha = int(value[7:9], 16)

            return (red/255.0, green/255.0, blue/255.0, alpha/255.0)
        except:
            self._fatal("invalid color value '%s'" % (value,))

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

class Hotspot(object):
    """A hotspot in a view denoting a control."""
    # Control type the hotspot belongs to: key (button)
    CONTROL_TYPE_KEY = 1

    # Control type the hotspot belongs to: axis
    CONTROL_TYPE_AXIS = 2

    class Dot(object):
        """A dot for a hotspot.

        It is an optional part of the hotspot when the label itself is placed
        apart from the actual control, which is marked by a dot instead.

        In such a case the label and the dot are connected by a line, the width
        and the colours of which are also stored in this object."""
        def __init__(self, x, y, radius, color, highlightColor,
                     lineWidth, lineColor, lineHighlightColor):
            """Construct the dot with the given data."""
            self.x = x
            self.y = y
            self.radius = radius
            self.color = color
            self.highlightColor = highlightColor

            self.lineWidth = lineWidth
            self.lineColor = lineColor
            self.lineHighlightColor = lineHighlightColor

        def getXML(self, document):
            """Get the XML representation of the dot."""
            element = document.createElement("dot")

            element.setAttribute("x", str(self.x))
            element.setAttribute("y", str(self.y))
            element.setAttribute("radius", str(self.radius))
            element.setAttribute("color", Hotspot.colorToXML(self.color))
            element.setAttribute("highlightColor",
                                 Hotspot.colorToXML(self.highlightColor))

            element.setAttribute("lineWidth", str(self.lineWidth))
            element.setAttribute("lineColor",
                                 Hotspot.colorToXML(self.lineColor))
            element.setAttribute("lineHighlightColor",
                                 Hotspot.colorToXML(self.lineHighlightColor))

            return element

        def clone(self):
            """Clone this dot."""
            return Hotspot.Dot(self.x, self.y, self.radius,
                               self.color, self.highlightColor,
                               self.lineWidth, self.lineColor,
                               self.lineHighlightColor)

    @staticmethod
    def colorToXML(color):
        """Convert the given colour to an XML representation."""
        return "#%02x%02x%02x%02x" % tuple([round(c*255.0) for c in color])

    def __init__(self, x, y, controlType, controlCode,
                 fontSize, color, bgColor, highlightColor, highlightBGColor,
                 selectColor):
        """Construct the hotspot."""
        self.x = x
        self.y = y
        self.controlType = controlType
        self.controlCode = controlCode
        self.fontSize = fontSize
        self.color = color
        self.bgColor = bgColor
        self.highlightColor = highlightColor
        self.highlightBGColor = highlightBGColor
        self.selectColor = selectColor

        self.dot = None

    def addDot(self, x, y, radius, color, highlightColor,
               lineWidth, lineColor, lineHighlightColor):
        """Add a dot to the hotspot."""
        assert self.dot is None

        self.dot = Hotspot.Dot(x, y, radius, color, highlightColor,
                               lineWidth, lineColor, lineHighlightColor)

    def getXML(self, document):
        """Get the XML representation of the hotspot."""
        element = document.createElement("hotspot")

        element.setAttribute("x", str(self.x))
        element.setAttribute("y", str(self.y))
        if self.controlType==Hotspot.CONTROL_TYPE_KEY:
            element.setAttribute("controlType", "key")
            element.setAttribute("controlName",
                                 Key.getNameFor(self.controlCode))
        elif self.controlType==Hotspot.CONTROL_TYPE_AXIS:
            element.setAttribute("controlType", "axis")
            element.setAttribute("controlName",
                                 Axis.getNameFor(self.controlCode))
        element.setAttribute("type", "label")
        element.setAttribute("fontSize", str(self.fontSize))
        element.setAttribute("color", Hotspot.colorToXML(self.color))
        element.setAttribute("bgColor", Hotspot.colorToXML(self.bgColor))
        element.setAttribute("highlightColor",
                             Hotspot.colorToXML(self.highlightColor))
        element.setAttribute("highlightBGColor",
                             Hotspot.colorToXML(self.highlightBGColor))
        element.setAttribute("selectColor",
                             Hotspot.colorToXML(self.selectColor))

        if self.dot is not None:
            element.appendChild(self.dot.getXML(document))

        return element

    def clone(self):
        """Clone this hotspot."""
        hotspot = Hotspot(self.x, self.y, self.controlType, self.controlCode,
                          self.fontSize, self.color, self.bgColor,
                          self.highlightColor, self.highlightBGColor,
                          self.selectColor)
        if self.dot is not None:
            hotspot.dot = self.dot.clone()

        return hotspot

#------------------------------------------------------------------------------

class View(object):
    """A view of a joystick.

    It has a name and is associated with an image file name. The image should
    be present in the profile's directory or in one of the profile
    directories used by the program.

    A view is also associated with a number of hotspots corresponding to the
    buttons or axes of the joystick."""
    def __init__(self, name, imageFileName):
        """Construct the view."""
        self.name = name
        self.imageFileName = imageFileName
        self._hotspots = []

    @property
    def hotspots(self):
        """Add an iterator over the hotspots."""
        return self._hotspots

    @property
    def lastHotspot(self):
        """Get the last hotspot, if any."""
        return self._hotspots[-1] if self._hotspots else None

    def addHotspot(self, hotspot):
        """Add the given hotspot to the view."""
        self._hotspots.append(hotspot)

    def modifyHotspot(self, origHotspot, newHotspot):
        """Replace the given original hotspot with the new one."""
        for i in range(0, len(self._hotspots)):
            if self._hotspots[i] is origHotspot:
                self._hotspots[i] = newHotspot
                break

    def removeHotspot(self, hotspot):
        """Remove the given hotspot."""
        self._hotspots.remove(hotspot)

    def getXML(self, document):
        """Get the XML element describing the view."""
        element = document.createElement("view")

        element.setAttribute("name", self.name)
        element.setAttribute("imageFileName", self.imageFileName)

        for hotspot in self._hotspots:
            element.appendChild(hotspot.getXML(document))

        return element

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class JoystickType(Joystick):
    """A joystick type.

    It has controls with display names as well as virtual controls. It can be
    loaded from a file and saved into one. Its identity has an empty physical
    location and unique identifier."""
    @classmethod
    def fromFile(clazz, path, *args):
        """Create a joystick type from the device file at the given path.

        Returns the joystick type object or None, if the file could not be
        parsed."""
        parser = make_parser()

        handler = DeviceHandler(clazz, *args)
        parser.setContentHandler(handler)

        try:
            parser.parse(path)

            return handler.joystickType
        except Exception as e:
            print(e, file=sys.stderr)

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
        super(JoystickType, self).__init__(0, identity.generic, [], [])

        self._indicatorIconName = "joystick.svg"
        self._virtualControls = []
        self._views = []

    @property
    def indicatorIconName(self):
        """Get the name of the indicator icon."""
        return self._indicatorIconName

    @property
    def views(self):
        """Get an iterator over the views of the device."""
        return iter(self._views)

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

    def findView(self, name):
        """Find a view with the given name.

        If no such view exists, return None."""
        for view in self._views:
            if view.name==name:
                return view

    def addView(self, view):
        """Added the given view to the list of the views."""
        assert self.findView(view.name) is None
        self._views.append(view)

    def removeView(self, view):
        """Remove the given view from the device."""
        self._views.remove(view)

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

        if len(self._views)>0:
            viewsElement = document.createElement("views")
            for view in self._views:
                element = view.getXML(document)
                viewsElement.appendChild(element)
            topElement.appendChild(viewsElement)

        return document

    def saveInto(self, path):
        """Save the joystick type into the file with the given path."""
        document = self.getXMLDocument()

        with open(path, "wt") as f:
            document.writexml(f, addindent = "  ", newl = "\n")

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
