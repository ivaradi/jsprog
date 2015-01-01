import os

#-----------------------------------------------------------------------------

## @package jsprog.common
#
# Common definitions and utilities
#
# The main purpose of this module is to provide common definitions for things
# that are named differently in Gtk+ 2 and 3.

#-----------------------------------------------------------------------------

if os.name=="nt" or "FORCE_PYGTK" in os.environ:
    print "Using PyGTK"
    pygobject = False
    import gobject
    from gobject import MainLoop
else:
    print "Using PyGObject"
    pygobject = True
    from gi.repository import GObject as gobject
    from gi.repository.GObject import MainLoop

#------------------------------------------------------------------------------
