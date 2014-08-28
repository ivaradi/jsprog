
from joystick import Joystick
from common import *

from jsprog.const import dbusInterfaceName
from jsprog.util import getJSProg

#--------------------------------------------------------------------------------

class GUI(object):
    """The main object."""
    def __init__(self, connection):
        """Construct the GUI."""
        connection.add_match_string("interface='%s'" % (dbusInterfaceName,))
        connection.add_message_filter(self._filterMessage)

        self._jsprog = getJSProg(connection)

        self._joysticks = {}

    def run(self):
        """Run the GUI."""
        for joystickArgs in self._jsprog.getJoysticks():
            self._addJoystick(joystickArgs)

        gtk.main()
        # mainloop = MainLoop()
        # mainloop.run()

    def _addJoystick(self, args):
        """Add a joystick from the given arguments."""
        id = int(args[0])
        self._joysticks[id] = Joystick.fromArgs(args)

    def _filterMessage(self, connection, message):
        """Handle notifications."""
        if message.get_interface()==dbusInterfaceName:
            args = message.get_args_list()
            if message.get_member()=="joystickAdded":
                self._addJoystick(args);
            elif message.get_member()=="joystickRemoved":
                id = args[0]
                print "Removed joystick:", id
                if id in self._joysticks:
                    self._joysticks[id].destroy()
                    del self._joysticks[id]
