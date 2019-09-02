
from .joystick import Joystick
from .jswindow import JSWindow
from .common import *
from .common import _

from jsprog.const import dbusInterfaceName, VERSION
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
        self._aboutDialog = None

        resourcePath = os.path.join(pkgdatadir, "jsprog.gresource")
        if os.path.exists(resourcePath):
            res = Gio.Resource.load(resourcePath)
            res._register()

            iconTheme = Gtk.IconTheme.get_default()
            iconTheme.add_resource_path("/hu/varadiistvan/JSProgGUI")

    @property
    def profiles(self):
        """Return an iterator over the profiles loaded."""
        return iter(self._profiles)

    def do_startup(self):
        """Perform the startup of the application."""
        Gtk.Application.do_startup(self)

        aboutAction = Gio.SimpleAction.new("about", None)
        aboutAction.connect("activate", self._handleAbout)
        self.add_action(aboutAction)

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
        joystick = self._joysticks[id] = Joystick.fromArgs(args, self)

        joystick.selectProfiles(self)

        autoLoadProfile = joystick.autoLoadProfile

        if autoLoadProfile is None:
            notifySend(_("Joystick added"),
                       _("Joystick '{0}' has been added").format(joystick.identity.name),
                       timeout = 5)
        else:
            notifySend(_("Joystick added"),
                       _("Joystick '{0}' has been added with profile '{1}'").
                       format(joystick.identity.name, autoLoadProfile.name))

            self._addingJoystick = True
            joystick.statusIcon.setActive(autoLoadProfile)
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

    def _handleAbout(self, action, parameter):
        """Quit the application."""
        if self._aboutDialog is None:
            self._aboutDialog = Gtk.AboutDialog(transient_for = self._jsWindow,
                                                modal = True)
            self._aboutDialog.set_program_name(PROGRAM_TITLE)
            self._aboutDialog.set_logo_icon_name(PROGRAM_ICON_NAME)
            self._aboutDialog.set_version(VERSION)
            self._aboutDialog.set_comments(_("Flexible programming of your joysticks"))
            self._aboutDialog.set_copyright("Copyright \u00a9 2019 István Váradi")
            self._aboutDialog.set_authors(["István Váradi"])
            self._aboutDialog.set_license(_("""{0} is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.""").format(PROGRAM_TITLE))

        self._aboutDialog.show_all()
        self._aboutDialog.run()
        self._aboutDialog.hide()

    def _handleQuit(self, action, parameter):
        """Quit the application."""
        self.quit()
