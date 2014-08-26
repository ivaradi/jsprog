
from statusicon import StatusIcon
from common import *

from jsprog.const import dbusInterfaceName

#--------------------------------------------------------------------------------

class GUI(object):
    """The main object."""
    def __init__(self, connection):
        """Construct the GUI."""
        connection.add_match_string("interface='%s'" % (dbusInterfaceName,))
        connection.add_message_filter(self._filterMessage)

        self._joysticks = {}

    def run(self):
        """Run the GUI."""
        gtk.main()
        # mainloop = MainLoop()
        # mainloop.run()

    def _filterMessage(self, connection, message):
        """Handle notifications."""
        if message.get_interface()==dbusInterfaceName:
            args = message.get_args_list()
            id = args[0]

            if message.get_member()=="joystickAdded":
                name = args[2]
                print "Added joystick:", id, name
                self._joysticks[id] = StatusIcon(id, name)
            elif message.get_member()=="joystickRemoved":
                print "Removed joystick:", id
                if id in self._joysticks:
                    self._joysticks[id].destroy()
                    del self._joysticks[id]
