
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
