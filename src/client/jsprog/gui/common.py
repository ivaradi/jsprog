
from jsprog.common import *

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
from gi.repository import Gdk as gdk
from gi.repository import GdkPixbuf as gdkPixbuf
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Pango as pango
gi.require_version('Notify', '0.7')
from gi.repository import Notify as pynotify
appIndicator = True


NOTIFY_URGENCY_LOW = pynotify.Urgency.LOW

NOTIFY_URGENCY_NORMAL = pynotify.Urgency.NORMAL

NOTIFY_URGENCY_CRITICAL = pynotify.Urgency.CRITICAL

def notifySend(summary, body, timeout = None, urgency = None):
    """Send a notification."""
    notification = pynotify.Notification.new(summary, body, None)
    if timeout is not None:
        notification.set_timeout(int(timeout*1000))
    if urgency is not None:
        notification.set_urgency(urgency)
    if not notification.show():
        print("Failed to send notification", file=sys.stderr)

import cairo

#------------------------------------------------------------------------------

PROGRAM_NAME = "JSProg"

WINDOW_TITLE_BASE = PROGRAM_NAME + " " + _const.VERSION

#------------------------------------------------------------------------------
