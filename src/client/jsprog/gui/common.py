
from jsprog.common import *
from jsprog.common import _

import jsprog.const as _const

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


#------------------------------------------------------------------------------
