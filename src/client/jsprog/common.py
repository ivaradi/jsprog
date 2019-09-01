import os

#-----------------------------------------------------------------------------

## @package jsprog.common
#
# Common definitions and utilities
#
# The main purpose of this module is to provide common definitions for things
# that are named differently in Gtk+ 2 and 3.

#-----------------------------------------------------------------------------

from gi.repository import GObject as gobject
from gi.repository.GObject import MainLoop

try:
    from .defs import *
except:
    pkgdatadir="/pkgdata"

#------------------------------------------------------------------------------
