
from const import dbusInterfaceName, dbusInterfacePath

from dbus import Interface

#-------------------------------------------------------------------------------

## @package jsprog.util
#
# Various utility functions and classes used by the program.

#------------------------------------------------------------------------------

def getJSProg(connection):
    """Get the JSProg object via the given connection."""
    jsprog_proxy = connection.get_object(dbusInterfaceName, dbusInterfacePath)
    return Interface(jsprog_proxy, dbusInterfaceName)

#------------------------------------------------------------------------------

def appendLinesIndented(dest, lines, indentation = "  "):
    """Append the given lines with the given indentation to dest."""
    dest += map(lambda l: indentation + l, lines)
    return dest

#-------------------------------------------------------------------------------
