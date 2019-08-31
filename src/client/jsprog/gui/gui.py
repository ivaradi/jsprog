
from .joystick import Joystick
from .jswindow import JSWindow
from .common import *
from .common import _

from jsprog.const import dbusInterfaceName
from jsprog.util import getJSProg
from jsprog.profile import Profile

import io

#--------------------------------------------------------------------------------

class GUI(Gtk.Application):
    """The main object."""
    def __init__(self, connection, profileDirectory):
        """Construct the GUI."""
        super().__init__(application_id = "hu.varadiistvan.JSProgGUI",
                         flags = Gio.ApplicationFlags.FLAGS_NONE)
        self._connection = connection
        self._profileDirectory = profileDirectory
        self._jsprog = None
        self._jsWindow = None

    def do_startup(self):
        """Perform the startup of the application."""
        Gtk.Application.do_startup(self)

        quitAction = Gio.SimpleAction.new("quit", None)
        quitAction.connect("activate", self._handleQuit)
        self.add_action(quitAction)

        self.set_accels_for_action("app.quit", ["<Control>Q"])

    def do_activate(self):
        """Perform the activation of the GUI."""
        if self._jsprog is None:
            connection = self._connection

            connection.add_match_string("interface='%s'" % (dbusInterfaceName,))
            connection.add_message_filter(self._filterMessage)

            self._jsprog = getJSProg(connection)

            self._profiles = Profile.loadFrom(self._profileDirectory)

            self._addingJoystick = False
            self._joysticks = {}

            if not Notify.init("JSProg"):
                print("Failed to initialize notifications", file=sys.stderr)

            jsWindow = self._jsWindow = JSWindow(application = self)

            for joystickArgs in self._jsprog.getJoysticks():
                self._addJoystick(joystickArgs)

        self._jsWindow.present()

    def loadProfile(self, id, profile):
        """Load the given profile to the given joystick."""
        if id not in self._joysticks:
            return

        daemonXMLDocument = profile.getDaemonXMLDocument()
        daemonXML = io.StringIO()
        daemonXMLDocument.writexml(daemonXML)

        print("loadProfile")
        print(daemonXML.getvalue())

        try:
            joystick = self._joysticks[id]

            self._jsprog.loadProfile(id, daemonXML.getvalue())

            # FIXME: find a way to make some parts of the text bold,
            # if possible
            if not self._addingJoystick:
                notifySend(_("Downloaded profile"),
                           _("Downloaded profile '{0}' to '{1}'").\
                           format(profile.name, joystick.identity.name))
        except Exception as e:
            notifySend(_("Profile download failed"),
                       _("Failed to downloaded profile '{0}' to '{1}': {2}").\
                       format(profile.name, joystick.identity.name, str(e)))

    def do_shutdown(self):
        """Quit the main loop and the daemon as well."""
        if self._jsprog is not None:
            try:
                self._jsprog.exit()
            except Exception as e:
                print("Failed to stop the daemon:", e, file=sys.stderr)

            for joystick in self._joysticks.values():
                joystick.destroy()

        Gtk.Application.do_shutdown(self)

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
            notifySend(_("Joystick added"),
                       _("Joystick '{0}' has been added").format(joystick.identity.name),
                       timeout = 5)
        else:
            notifySend(_("Joystick added"),
                       _("Joystick '{0}' has been added with profile '{1}'").
                       format(joystick.identity.name, loadCandidate.name))

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
                    notifySend(_("Joystick removed"),
                               _("Joystick '{0}' has been removed").format(joystick.identity.name),
                               timeout = 5)
                    joystick.destroy()
                    del self._joysticks[id]
            else:
                print(message)

    def _handleQuit(self, action, parameter):
        """Quit the application."""
        self.quit()
