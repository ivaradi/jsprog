
from jsprog.common import *
from jsprog.common import _

import jsprog.const as _const

from collections import namedtuple
import os
import sys

#-----------------------------------------------------------------------------

## @package jsprog.gui.common
#
# Common definitions and utilities for the GUI
#
# Besides this there are some common utility classes and functions.

#-----------------------------------------------------------------------------

from .gicommon import *

#------------------------------------------------------------------------------

PROGRAM_NAME = "JSProg"

PROGRAM_TITLE = _("Joystick Programmer")

PROGRAM_ICON_NAME = "jsprog"

#------------------------------------------------------------------------------

def yesNoDialog(parent, text, secondaryText = None):
    """Present a dialog asking the user a yes/no question.

    Return True if the answer is yes."""
    messageDialog = Gtk.MessageDialog(parent, 0,
                                      Gtk.MessageType.QUESTION,
                                      Gtk.ButtonsType.YES_NO)
    messageDialog.set_markup(text)

    if secondaryText is not None:
        messageDialog.format_secondary_markup(secondaryText)

    response = messageDialog.run()

    yes = response==Gtk.ResponseType.YES

    messageDialog.destroy()

    return yes

#------------------------------------------------------------------------------

def errorDialog(parent, text, secondaryText = None):
    """Present an error dialog with the given text(s)."""
    messageDialog = Gtk.MessageDialog(parent, 0,
                                      Gtk.MessageType.ERROR,
                                      Gtk.ButtonsType.OK,
                                      text)
    if secondaryText is not None:
        messageDialog.format_secondary_text(secondaryText)
    messageDialog.run()
    messageDialog.destroy()


#------------------------------------------------------------------------------

def entryDialog(parent, title, label, initialValue = "", text = None):
    """Present a dialog asking the user to enter a textual value."""
    dialog = Gtk.Dialog()
    dialog.set_transient_for(parent)
    dialog.set_destroy_with_parent(True)
    dialog.set_title(title)
    dialog.set_modal(True)
    dialog.set_border_width(6)

    dialog.set_resizable(False)

    contentArea = dialog.get_content_area()

    if text is not None:
        textLabel = Gtk.Label()
        textLabel.set_markup(text)
        contentArea.pack_start(textLabel, True, True, 4)

    entryBox = Gtk.Box(Gtk.Orientation.HORIZONTAL)

    entryLabel = Gtk.Label(label)
    entryBox.pack_start(entryLabel, False, False, 4)

    entry = Gtk.Entry()
    entry.set_text(initialValue)
    entry.set_activates_default(True)
    entryBox.pack_start(entry, True, True, 4)

    entryBox.set_margin_bottom(16)

    contentArea.pack_start(entryBox, True, True, 4)

    dialog.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
    okButton = dialog.add_button("_OK", Gtk.ResponseType.OK)
    okButton.set_can_default(True)
    okButton.grab_default()

    dialog.show_all()

    response = dialog.run()

    text = entry.get_text()

    dialog.destroy()

    if response==Gtk.ResponseType.OK:
        return text


#-------------------------------------------------------------------------------

class ScalableImage(Gtk.Image):
    """A scalable image which can be fairly small."""
    # The minimal size
    MIN_SIZE = 50

    def __init__(self):
        """Construct the image."""
        super().__init__()
        self.basePixbuf = None

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.WIDTH_FOR_HEIGHT

    def do_get_preferred_width(self):
        """Get the preferred width.

        The minimum is MIN_SIZE, the preferred one is the base pixbuf's width,
        if it exists, or MIN_SIZE."""
        pixbuf = self.basePixbuf
        return (ScalableImage.MIN_SIZE,
                max(ScalableImage.MIN_SIZE,
                    ScalableImage.MIN_SIZE if pixbuf is None else
                    pixbuf.get_width()))

    def do_get_preferred_height_for_width(self, width):
        """Get the preferred height for the given width.

        The minimum is MIN_SIZE, the preferred one base pixbuf's height scaled
        by the proportion of the given width to the pixbuf's width. If there is
        no base pixbuf, the preferred height is the width."""
        pixbuf = self.get_pixbuf()
        return (ScalableImage.MIN_SIZE,
                max(ScalableImage.MIN_SIZE,
                    width if pixbuf is None else
                    pixbuf.get_height() * width / pixbuf.get_width()))

#------------------------------------------------------------------------------

class BoundingBox(object):
    """A bounding box."""
    def __init__(self, x0, y0, x1, y1):
        """Construct the bounding box."""
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def extend(self, margin):
        """Extend the box in all directions with the given margin."""
        self.x0 -= margin
        self.y0 -= margin
        self.x1 += margin
        self.y1 += margin

    def merge(self, other):
        """Merge the bounding box with the given other box to produce a large
        box the includes both boxes.

        If the other box is None, nothing happens."""
        if other is not None:
            self.x0 = min(self.x0, other.x0)
            self.y0 = min(self.y0, other.y0)
            self.x1 = max(self.x1, other.x1)
            self.y1 = max(self.y1, other.y1)

#------------------------------------------------------------------------------

class ValueEntry(Gtk.Entry):
    """An entry that has 'value-themed' functions and signals."""
    def __init__(self):
        """Construct the entry."""
        super().__init__()

        self.connect("changed", self._changed)

    @property
    def value(self):
        """Get the value of the entry, which is its string contents."""
        return self.get_text()

    @value.setter
    def value(self, text):
        """Set the value of the entry, which is its string contents."""
        self.set_text(text)

    def get_value(self):
        """Get the value of the entry, which is ts string contents."""
        return self.get_text()

    def set_value(self, text):
        """Set the value of the entry, which is ts string contents."""
        return self.set_text(text)

    def _changed(self, entry):
        """Called when a 'changed' signal is emitted. It emits a value-changed
        signal."""
        self.emit("value-changed", self.get_text())

GObject.signal_new("value-changed", ValueEntry,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

#------------------------------------------------------------------------------

def int2str(value, base):
    """Convert the given non-negative integer into a string with the given base."""
    s = ""
    while value>0:
        digit = value % base

        s = (chr(ord('0') + digit) if digit<10 else chr((ord('a') + digit - 10))) + s

        value //= base

    if not s:
        s = "0"

    return s

#------------------------------------------------------------------------------

class IntegerEntry(Gtk.Entry):
    """An entry field for integers with a base"""
    def __init__(self, maxWidth = 8, base = 10, zeroPadded = True):
        super().__init__()

        self.set_max_length(maxWidth)
        self.set_max_width_chars(maxWidth)
        self.set_width_chars(maxWidth)
        self.set_overwrite_mode(zeroPadded)

        self._maxWidth = maxWidth
        self._base = base
        self._zeroPadded = zeroPadded
        self._value = None
        self._text = self.get_text()
        self._selfSetting = False

        self.connect("changed", self._changed)

    @property
    def value(self):
        """Get the value of the entry. It is None, if the input field is empty."""
        return self._value

    @value.setter
    def value(self, value):
        """Set the value of the entry. Use None for no value (empty input
        field). If it is different from the current value, a 'value-changed'
        signal is emitted."""
        self.set_value(value)

    def get_value(self):
        """Get the value of the entry. It is None, if the input field is empty."""
        return self._value

    def set_value(self, value):
        """Set the value to the given integer or None. If it is different from
        the current value, a 'value-changed' signal is emitted."""
        if self._updateValue(value):
            self._updateText()

    def _changed(self, entry):
        """Called when the entry has changed.

        It checks if the entered value is a valid hexadecimal string and if so,
        updates the current value and emits the value-changed signal."""
        previousText = self._text
        self._text = text = self.get_text()

        if self._selfSetting:
            return

        if text:
            try:
                self._updateValue(int(text, self._base))
            except:
                self._selfSetting = True
                self.set_text(previousText)
                self._selfSetting = False
        else:
            self._updateValue(None)

    def _updateValue(self, value):
        """Update the value to the given one. If the value has changed, the
        'value-changed' signal is emitted.

        Returns a boolean indicate if the value has changed."""
        self._text = self.get_text()

        if value==self._value:
            return False

        self._value = value
        self.emit("value-changed", value)

        return True

    def _updateText(self):
        """Update the text from the current value."""
        self._selfSetting = True

        value = self._value
        if value is None:
            self.set_text("")
        else:
            s  = int2str(value, self._base)
            if self._zeroPadded:
                slen = len(s)
                if slen<self._maxWidth:
                    s = "0" * (self._maxWidth-slen) + s
            self.set_text(s)

        self._selfSetting = False

GObject.signal_new("value-changed", IntegerEntry,
                   GObject.SignalFlags.RUN_FIRST, None, (object,))

#------------------------------------------------------------------------------

class SeparatorDrawer(object):
    """An object that can be used to draw a separator.

    It creates a style context, adds the separator class and when instructed,
    draws a background and a frame to emulate what the separator does."""
    def __init__(self):
        """Construct the drawer."""
        self._horizontalSeparator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        self._horizontalSC = self._horizontalSeparator.get_style_context()

        self._verticalSeparator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self._verticalSC = self._verticalSeparator.get_style_context()

    def drawHorizontal(self, cr, x, y, length):
        """Draw a horizontal separator of the given length, starting at the
        given coordinates."""
        self._draw(self._horizontalSC, cr, x, y, length, 1)

    def drawVertical(self, cr, x, y, length):
        """Draw a vertical separator of the given length, starting at the
        given coordinates."""
        self._draw(self._verticalSC, cr, x, y, 1, length)

    def _draw(self, sc, cr, x, y, width, height):
        """Draw the separator with the given style class and dimensions."""
        Gtk.render_background(sc, cr, x, y, width, height)
        Gtk.render_frame(sc, cr, x, y, width, height)

#------------------------------------------------------------------------------

separatorDrawer = SeparatorDrawer()

#------------------------------------------------------------------------------

def getTextSizes(layout, text):
    """Get the width and the height of the given text with the given layout.

    The text is also set to the layout."""
    layout.set_text(text, len(text))
    (_ink, logical) = layout.get_extents()
    return (((logical.x + logical.width) / Pango.SCALE),
            ((logical.y + logical.height) / Pango.SCALE))

#------------------------------------------------------------------------------

class ButtonStyle(object):
    """A style to draw a button background."""
    def __init__(self):
        """Construct the style."""
        self._button = button = Gtk.Button.new()
        button.set_state_flags(Gtk.StateFlags.NORMAL, False)
        self._styleContext = button.get_style_context()

    @property
    def styleContext(self):
        """Get the style context to draw a highlighted background."""
        return self._styleContext

buttonStyle = ButtonStyle()

#------------------------------------------------------------------------------

class HighlightStyle(object):
    """A style to draw a highlighted background."""
    def __init__(self):
        """Construct the style."""
        self._button = button = Gtk.Button.new()
        button.set_state_flags(Gtk.StateFlags.PRELIGHT, False)
        self._styleContext = button.get_style_context()

    @property
    def styleContext(self):
        """Get the style context to draw a highlighted background."""
        return self._styleContext

highlightStyle = HighlightStyle()

#------------------------------------------------------------------------------

class EntryStyle(object):
    """A style to draw an entry-like widget."""
    def __init__(self):
        """Construct the style."""
        self._entry = entry = Gtk.Entry.new()
        self._styleContext = entry.get_style_context()

    @property
    def styleContext(self):
        """Get the style context for drawing."""
        return self._styleContext

entryStyle = EntryStyle()

#------------------------------------------------------------------------------

#_typeClasses = {}

def appendPathType(widgetPath, typeName):
    """Append a type to the given widget path."""
    try:
        widgetPath.append_type(GObject.GType.from_name(typeName))
    except:
        class TypeClass(GObject.Object):
            __gtype_name__ = typeName
        widgetPath.append_type(TypeClass)

#------------------------------------------------------------------------------

def getWidgetPathFor(*typeNames):
    """Get a widget path for the given type names."""
    widgetPath = Gtk.WidgetPath.new()
    for (index, typeName) in enumerate(typeNames):
        names = typeName.split(".")
        typeName = names[0]
        appendPathType(widgetPath, typeName)
        for clazz in names[1:]:
            widgetPath.iter_add_class(index, clazz)
    return widgetPath

#------------------------------------------------------------------------------

def getStyleContextFor(*typeNames):
    """Get a style context for the given type names"""
    styleContext = Gtk.StyleContext()
    styleContext.set_path(getWidgetPathFor(*typeNames))
    return styleContext

#------------------------------------------------------------------------------

def isInClip(cr, x, y, xEnd, yEnd):
    """Determine if the given rectangle has a non-empty intersection with the
    clip region of the given context."""
    (x1, y1, x2, y2) = cr.clip_extents()
    return not(xEnd<x1 or x>x2 or yEnd<y1 or y>y2)
