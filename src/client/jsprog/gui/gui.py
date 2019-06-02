
from .joystick import Joystick
from .common import *

from jsprog.const import dbusInterfaceName
from jsprog.util import getJSProg
from jsprog.profile import Profile

import io

#--------------------------------------------------------------------------------

class GUI(object):
    """The main object."""
    def __init__(self, connection, profileDirectory):
        """Construct the GUI."""
        connection.add_match_string("interface='%s'" % (dbusInterfaceName,))
        connection.add_message_filter(self._filterMessage)

        self._jsprog = getJSProg(connection)

        self._profiles = Profile.loadFrom(profileDirectory)

        self._addingJoystick = False
        self._joysticks = {}

    def run(self):
        """Run the GUI."""
        if not Notify.init("JSProg"):
            print("Failed to initialize notifications", file=sys.stderr)

        for joystickArgs in self._jsprog.getJoysticks():
            self._addJoystick(joystickArgs)

        Gtk.main()
        # mainloop = MainLoop()
        # mainloop.run()

    def loadProfile(self, id, profile):
        """Load the given profile to the given joystick."""
        if id not in self._joysticks:
            return

        daemonXMLDocument = profile.getDaemonXMLDocument()
        daemonXML = io.StringIO()
        daemonXMLDocument.writexml(daemonXML)

        try:
            joystick = self._joysticks[id]

            self._jsprog.loadProfile(id, daemonXML.getvalue())

            # FIXME: find a way to make some parts of the text bold,
            # if possible
            if not self._addingJoystick:
                notifySend("Downloaded profile",
                           "Downloaded profile '%s' to '%s'" % \
                               (profile.name, joystick.identity.name))
        except Exception as e:
            notifySend("Profile download failed",
                       "Failed to downloaded profile '%s' to '%s': %s" % \
                           (profile.name, joystick.identity.name, e))

    def quit(self):
        """Quit the main loop and the daemon as well."""
        try:
            self._jsprog.exit()
        except Exception as e:
            print("Failed to stop the daemon:", e, file=sys.stderr)

        for joystick in self._joysticks.values():
            joystick.destroy()

        Gtk.main_quit()

    def _addJoystick(self, args):
        """Add a joystick from the given arguments."""
        id = int(args[0])
        joystick = self._joysticks[id] = Joystick.fromArgs(args)

        statusIcon = joystick.statusIcon
        statusIcon.gui = self

        loadCandidate = None
        loadCandidateMatch = 0
        for profile in self._profiles:
            score = profile.match(joystick.identity)
            if score>0:
                statusIcon.addProfile(self, profile)
                if profile.autoLoad and score>loadCandidateMatch:
                    loadCandidate = profile
                    loadCandidateMatch = score

        statusIcon.finalize(self)

        if loadCandidate is None:
            notifySend("Joystick added",
                       "Joystick '%s' has been added" % (joystick.identity.name,),
                       timeout = 5)
        else:
            notifySend("Joystick added",
                       "Joystick '%s' has been added with profile '%s'" %
                       (joystick.identity.name, loadCandidate.name))

            self._addingJoystick = True
            statusIcon.setActive(loadCandidate)
            self._addingJoystick = False

    def _filterMessage(self, connection, message):
        """Handle notifications."""
        if message.get_interface()==dbusInterfaceName:
            args = message.get_args_list()
            if message.get_member()=="joystickAdded":
                id = args[0]
                if id not in self._joysticks:
                    self._addJoystick(args);
            elif message.get_member()=="joystickRemoved":
                id = args[0]
                print("Removed joystick:", id)
                if id in self._joysticks:
                    joystick = self._joysticks[id]
                    notifySend("Joystick removed",
                               "Joystick '%s' has been removed" % (joystick.identity.name,),
                               timeout = 5)
                    joystick.destroy()
                    del self._joysticks[id]
            else:
                print(message)
