
from .joystick import Joystick
from .jswindow import JSWindow
from .common import *
from .common import _

from jsprog.const import dbusInterfaceName, VERSION
from jsprog.util import getJSProg

import io
import pathlib
import os.path

#--------------------------------------------------------------------------------

class GUI(Gtk.Application):
    """The main object."""
    def __init__(self, connection, extraDataDirectory):
        """Construct the GUI."""
        super().__init__(application_id = "hu.varadiistvan.JSProgGUI",
                         flags = Gio.ApplicationFlags.FLAGS_NONE)
        self._connection = connection
        self._extraDataDirectory = extraDataDirectory
        self._jsprog = None
        self._jsWindow = None
        self._aboutDialog = None

        resourcePath = os.path.join(pkgdatadir, "jsprog.gresource")
        if os.path.exists(resourcePath):
            res = Gio.Resource.load(resourcePath)
            res._register()

            iconTheme = Gtk.IconTheme.get_default()
            iconTheme.add_resource_path("/hu/varadiistvan/JSProgGUI")

        self._addingJoystick = False
        self._activatingProfile = False
        self._nextNotificationID = 1
        self._pendingNotifications = []

    @property
    def joysticksWindow(self):
        """Get the window containing the joysticks."""
        return self._jsWindow

    @property
    def userDataDirectory(self):
        """Get the data directory of the user."""
        return os.path.join(str(pathlib.Path.home()), ".local",
                            "share", "jsprog")

    @property
    def dataDirectories(self):
        """Get an iterator over the data directory path to be used for profiles
        and other files.

        The directories are returned in priority order, with the one of the
        highest priority first. This is the user's data directory used to
        store their own profiles and device descriptors - possibly modifed from
        system-provided ones. It is followed by the extra data directory
        (read-only), if provided. Finally, the global data directory under
        <prefix>/share is returned.

        Each item is a tuple of:
        - the path
        - the type of the directory as a string ("user", "extra" or "system")
        """
        yield (self.userDataDirectory, "user")

        if self._extraDataDirectory:
            yield (self._extraDataDirectory, "extra")

        yield (pkgdatadir, "system")

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

            self._addingJoystick = False
            self._joysticks = {}
            self._joysticksByName = {}

            jsWindow = self._jsWindow = JSWindow(application = self)

            for joystickArgs in self._jsprog.getJoysticks():
                self._addJoystick(joystickArgs)

        self._jsWindow.present()

    def _loadProfile(self, id, profile):
        """Load the given profile to the given joystick."""
        daemonXMLDocument = profile.getDaemonXMLDocument()
        daemonXML = io.StringIO()
        daemonXMLDocument.writexml(daemonXML)

        joystick = self._joysticks[id]

        print("Loading profile '%s' for joystick %s (%d)" %
              (profile.name, joystick.identity, id))
        #print(daemonXML.getvalue())

        self._jsprog.loadProfile(id, daemonXML.getvalue())

    def activateProfile(self, id, profile):
        """Active the given profile on the joystick with the given ID.

        If no activation is in progress, the activation request is propagated
        to the various menus, and the profile is downloaded to the joystick."""
        if id not in self._joysticks:
            return

        if self._activatingProfile:
            return

        self._activatingProfile = True

        joystick = self._joysticks[id]

        try:
            self._loadProfile(id, profile)
            joystick.setActiveProfile(profile, notify = not self._addingJoystick)
        except Exception as e:
            joystick.profileDownloadFailed(profile, e)

        self._activatingProfile = False

    def sendNotify(self, summary, body = None, timeout = 30,
                   priority = None, icon = None):
        """Send a transient notification to the user."""
        notification = Gio.Notification.new(summary)

        if body is not None:
            notification.set_body(body)

        if icon is not None:
            notification.set_icon(icon)

        if priority is not None:
            notification.set_priority(priority)

        notificationID = "notification" + str(self._nextNotificationID)
        self._nextNotificationID += 1

        self.send_notification(notificationID, notification)
        self._pendingNotifications.append(notificationID)

        if timeout is not None:
            GLib.timeout_add(int(timeout*1000),
                             self._withdrawNotification, notificationID)

    def do_shutdown(self):
        """Quit the main loop and the daemon as well."""
        if self._jsprog is not None:
            try:
                self._jsprog.exit()
            except Exception as e:
                print("Failed to stop the daemon:", e, file=sys.stderr)

            for joystick in self._joysticks.values():
                joystick.destroy(notify = False)

        for notificationID in self._pendingNotifications:
            self.withdraw_notification(notificationID)

        Gtk.Application.do_shutdown(self)

    def _addJoystick(self, args):
        """Add a joystick from the given arguments."""
        id = int(args[0])
        joystick = self._joysticks[id] = Joystick.fromArgs(args, self)

        name  = joystick.identity.name
        if name in self._joysticksByName:
            joysticks = self._joysticksByName[name]
            if len(joysticks)==1:
                joysticks[0].extendDisplayedNames()
            joystick.extendDisplayedNames()
            joysticks.append(joystick)
        else:
            self._joysticksByName[name] = [joystick]

        autoLoadProfile = joystick.autoLoadProfile

        if autoLoadProfile is not None:
            self._addingJoystick = True
            self.activateProfile(id, autoLoadProfile)
            self._addingJoystick = False

    def _removeJoystick(self, id):
        """Remove the joystick with the given ID."""
        print("Removed joystick:", id)

        joystick = self._joysticks[id]

        name  = joystick.identity.name
        joysticks = self._joysticksByName[name]
        joysticks.remove(joystick)
        if len(joysticks)==0:
            del self._joysticksByName[name]
        elif len(joysticks)==1:
            joysticks[0].simplifyDisplayedNames()

        joystick.destroy()
        del self._joysticks[id]

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
                if id in self._joysticks:
                    self._removeJoystick(id);
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

    def _withdrawNotification(self, notificationID):
        """Withdraw the notification with the given ID."""
        self.withdraw_notification(notificationID)
        self._pendingNotifications.remove(notificationID)
        return False
