
from .joystick import JoystickType, Joystick
from .jswindow import JSWindow
from .typeeditor import TypeEditorWindow
from .profileseditor import ProfilesEditorWindow
from .common import *
from .common import _

from jsprog.const import dbusInterfaceName, dbusInterfacePath, VERSION
from jsprog.const import dbusListenerInterfaceName
from jsprog.util import getJSProg
import jsprog.joystick

import dbus.service

import io
import pathlib
import os.path

#--------------------------------------------------------------------------------

class JoystickListener(dbus.service.Object):
    """A listener for the control events.

    It implements interface 'hu.varadiistvan.JSProgListener', defined
    in jsproglistener.xml."""
    def __init__(self, gui, connection, path):
        """Construct the listener with the given path."""
        self._gui = gui
        super(JoystickListener, self).__init__(connection, path)

    @dbus.service.method(dbus_interface = dbusListenerInterfaceName,
                         in_signature = "uq", out_signature = "")
    def keyPressed(self, joystickID, code):
        """Called when a key is pressed."""
        self._gui._keyPressed(joystickID, code)

    @dbus.service.method(dbus_interface = dbusListenerInterfaceName,
                         in_signature = "uq", out_signature = "")
    def keyReleased(self, joystickID, code):
        """Called when a key is released."""
        self._gui._keyReleased(joystickID, code)

    @dbus.service.method(dbus_interface = dbusListenerInterfaceName,
                         in_signature = "uqi", out_signature = "")
    def axisChanged(self, joystickID, code, value):
        """Called when the value of an axis has changed."""
        self._gui._axisChanged(joystickID, code, value)

#--------------------------------------------------------------------------------

class GUI(Gtk.Application):
    """The main object."""
    def __init__(self, connection, extraDataDirectory, debug = False):
        """Construct the GUI."""
        super().__init__(application_id = "hu.varadiistvan.JSProgGUI",
                         flags = Gio.ApplicationFlags.FLAGS_NONE)
        self._connection = connection
        self._extraDataDirectory = extraDataDirectory
        self._debug = debug
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

        self._profilesEditorWindows = {}
        self._typeEditorWindows = {}
        self._joystickMonitorListeners = {}

        self._editedProfile = {}

    @property
    def debug(self):
        """Indicate if debugging is enabled."""
        return self._debug

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
        store their own profiles and device descriptors - possibly modified from
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

    @property
    def graphicsFontDescription(self):
        """Get the font description for the font to be used for graphics."""
        return self._graphicsFontDescription

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

            self._graphicsFontDescription = self._getGraphicsFontDescription()

            for joystickArgs in self._jsprog.getJoysticks():
                self._addJoystick(joystickArgs)

            pid = os.getpid()

            self._jsListenerBusName = \
                dbus.service.BusName("hu.varadiistvan.JSProgGUIListener-%d" % (pid,),
                                     bus = connection)

            self._jsListenerPath = "/hu/varadiistvan/JSProgGUIListener"

            self._jsListener = JoystickListener(self, self._jsListenerBusName,
                                                self._jsListenerPath)

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

        if not self._jsprog.loadProfile(id, daemonXML.getvalue()):
            raise Exception("The daemon failed to process the profile.")

    def showProfilesEditor(self, id):
        """Show the profiles editor window for the type of the given joystick."""
        joystick = self._joysticks[id]

        joystickType = joystick.type

        if joystickType not in self._profilesEditorWindows:
            ProfilesEditorWindow(self, joystick)

        self._profilesEditorWindows[joystickType].present()

    def addProfilesEditor(self, joystickType, profilesEditorWindow):
        """Add the given profiles editor window to the GUI."""
        assert joystickType not in self._profilesEditorWindows
        self._profilesEditorWindows[joystickType] = profilesEditorWindow

    def removeProfilesEditor(self, joystickType):
        """Remove the profiles editor window for the given joystick type from the
        GUI."""
        self.editingProfile(joystickType, None)
        #self.stopMonitorJoysticksFor(joystickType)
        del self._profilesEditorWindows[joystickType]

    def getEditedProfile(self, joystickType):
        """Get the profile being edited for the given joystick type."""
        return self._editedProfile.get(joystickType)

    def editingProfile(self, joystickType, profile):
        """Called when the editing of the given profile is started."""
        self._editedProfile[joystickType] = profile
        self.emit("editing-profile", joystickType, profile)

    def copyVersion(self, joystickType, version):
        """Copy the given version to the current profile in the profile editor
        of the given joystick type."""
        profileEditorWindow = self._profilesEditorWindows.get(joystickType)
        if profileEditorWindow is not None:
            profileEditorWindow.copyVersion(version)

    def copyPhys(self, joystickType, phys):
        """Copy the given physical location to the current profile in the
        profile editor of the given joystick type."""
        profileEditorWindow = self._profilesEditorWindows.get(joystickType)
        if profileEditorWindow is not None:
            profileEditorWindow.copyPhys(phys)

    def copyUniq(self, joystickType, uniq):
        """Copy the given unique identifier to the current profile in the
        profile editor of the given joystick type."""
        profileEditorWindow = self._profilesEditorWindows.get(joystickType)
        if profileEditorWindow is not None:
            profileEditorWindow.copyUniq(uniq)

    def showTypeEditor(self, id):
        """Show the type editor window for the type of the given joystick."""
        joystick = self._joysticks[id]

        joystickType = joystick.type

        if joystickType not in self._typeEditorWindows:
            TypeEditorWindow(self, joystickType)

        self._typeEditorWindows[joystickType].present()

    def addTypeEditor(self, joystickType, typeEditorWindow):
        """Add the given type editor window to the GUI."""
        assert joystickType not in self._typeEditorWindows
        self._typeEditorWindows[joystickType] = typeEditorWindow

    def removeTypeEditor(self, joystickType):
        """Remove the type editor window for the given joystick type from the
        GUI."""
        typeEditor = self._typeEditorWindows[joystickType]
        typeEditor.finalize()
        del self._typeEditorWindows[joystickType]

    def hasTypeEditor(self, joystickType):
        """Determine if there is a type editor window for the given joystick
        type."""
        return joystickType in self._typeEditorWindows

    def startMonitorJoysticksFor(self, joystickType, listener):
        """Start monitoring the joystick(s) of the given type via the given
        listener.

        listener is an object that will receive the following function calls:
        - keyPressed(code): when a key is pressed
        - keyReleased(code): when a key is released
        - axisChanged(code, value): when the value of an axis has changed

        Returns True if monitor was indeed started, False if it has already
        been started for that listener."""
        listeners = self._joystickMonitorListeners.get(joystickType)
        if listeners is not None and listener in listeners:
            return False

        if not listeners:
            for joystick in self._joysticks.values():
                if joystick.type is joystickType:
                    self._jsprog.startMonitor(joystick.id,
                                              self._jsListenerBusName.get_name(),
                                              self._jsListenerPath)

        if listeners is None:
            self._joystickMonitorListeners[joystickType] = [listener]
        else:
            listeners.append(listener)

        return True

    def getJoystickStatesFor(self, joystickType):
        """Get the state of the joysticks of the given type."""

        states = []

        for joystick in self._joysticks.values():
            if joystick.type is joystickType:
                states.append(self._jsprog.getJoystickState(joystick.id))

        return states

    def stopMonitorJoysticksFor(self, joystickType, listener):
        """Stop monitoring the joystick(s) of the given type for the given
        listener.

        Returns True if monitor was indeed stopped, False if it has already
        been stopped."""
        listeners = self._joystickMonitorListeners.get(joystickType)
        if listeners is None or listener not in listeners:
            return False

        listeners.remove(listener)

        if not listeners:
            for joystick in self._joysticks.values():
                if joystick.type is joystickType:
                    self._jsprog.stopMonitor(joystick.id,
                                             self._jsListenerPath)
            del self._joystickMonitorListeners[joystickType]

        return True

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
        (id, identity, keys, axes) = jsprog.joystick.Joystick.extractArgs(args)

        joystickType = JoystickType.get(self, identity, keys, axes)

        joystick = self._joysticks[id] = Joystick(id, identity,
                                                  joystickType, self)

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

        if joystickType in self._joystickMonitorListeners:
            self._jsprog.startMonitor(id,
                                      self._jsListenerBusName.get_name(),
                                      self._jsListenerPath)

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
                return True
        elif message.get_interface()==dbusListenerInterfaceName:
            return True
        else:
            print(message)
            return True

    def _keyPressed(self, joystickID, code):
        """Called when a key has been pressed on the given joystick."""
        joystick = self._joysticks.get(joystickID)
        if joystick is not None:
            listeners = self._joystickMonitorListeners[joystick.type]
            if listeners is not None:
                for listener in listeners:
                    listener.keyPressed(code)

    def _keyReleased(self, joystickID, code):
        """Called when a key has been released on the given joystick."""
        joystick = self._joysticks.get(joystickID)
        if joystick is not None:
            listeners = self._joystickMonitorListeners[joystick.type]
            if listeners is not None:
                for listener in listeners:
                    listener.keyReleased(code)

    def _axisChanged(self, joystickID, code, value):
        """Called when the value of an axis on the given joystick has
        changed."""
        joystick = self._joysticks.get(joystickID)
        if joystick is not None:
            listeners = self._joystickMonitorListeners[joystick.type]
            if listeners is not None:
                for listener in listeners:
                    listener.axisChanged(code, value)

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

    def _getGraphicsFontDescription(self):
        """Look for a font that is suitable to display in graphics
        (e.g. joystick control hotspot labels).

        The most liked one is the Sans Regular font, but any non-monospace
        Sans font with an appropriate face is suitable. If none is found, the
        system's default is used."""
        pangoContext = self._jsWindow.get_pango_context()

        defaultFontDescription = pangoContext.get_font_description()
        defaultFontFamilyName = defaultFontDescription.get_family()

        graphicsFontDescription = None
        for fontFamily in  pangoContext.get_font_map().list_families():
            if fontFamily.is_monospace():
                continue

            name = fontFamily.get_name()
            if name=="Sans":
                description = \
                    self._getSuitableGraphicsFontDescription(fontFamily)
                if description is not None:
                    graphicsFontDescription = description
                    break
            elif name.find("Sans")>=0 and graphicsFontDescription is None:
                description = \
                    self._getSuitableGraphicsFontDescription(fontFamily)
                if description is not None:
                    graphicsFontDescription = description

        if graphicsFontDescription is None:
            graphicsFontDescription = defaultFontDescription

        return graphicsFontDescription

    def _getSuitableGraphicsFontDescription(self, fontFamily):
        """Get the description of a suitable face from the given font family,
        if any."""
        for face in fontFamily.list_faces():
            description = face.describe()
            if description.get_style() == Pango.Style.NORMAL and \
               description.get_variant() == Pango.Variant.NORMAL and \
               description.get_weight() == Pango.Weight.NORMAL:
                return description

GObject.signal_new("editing-profile", GUI,
                   GObject.SignalFlags.RUN_FIRST, None, (object, object))
