
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

appIndicator = False

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import cairo
from gi.repository import Pango
gi.require_version('PangoCairo', '1.0')
from gi.repository import PangoCairo

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
    appIndicator = True
except:
    print("Failed to import AppIndicator3")

#------------------------------------------------------------------------------

PROGRAM_NAME = "JSProg"

PROGRAM_TITLE = _("Joystick Programmer")

PROGRAM_ICON_NAME = "joystick"

#------------------------------------------------------------------------------

def yesNoDialog(parent, text, secondaryText = None):
    """Present a dialog asking the user a yes/no question.

    Return True if the answer is yes."""
    messageDialog = Gtk.MessageDialog(parent, 0,
                                      Gtk.MessageType.QUESTION,
                                      Gtk.ButtonsType.YES_NO,
                                      text)
    if secondaryText is not None:
        messageDialog.format_secondary_text(secondaryText)

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

    dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    okButton = dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
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
        box the includes both boxes."""
        self.x0 = min(self.x0, other.x0)
        self.y0 = min(self.y0, other.y0)
        self.x1 = max(self.x1, other.x1)
        self.y1 = max(self.y1, other.y1)

#------------------------------------------------------------------------------
