# The main CLI for the client

from .gui import gui as gui

from .joystick import Joystick, Key, Axis
from .const import dbusInterfaceName, dbusInterfacePath
from .util import getJSProg
from .common import *

from dbus import SessionBus
from dbus.mainloop.glib import DBusGMainLoop

import dbus.service

import argparse
import sys
import os

#------------------------------------------------------------------------------

class GetJoysticks(object):
    """Command to get the list of joysticks known to the daemon."""

    @staticmethod
    def addParser(parsers):
        """Add the parser for this command."""
        parser = parsers.add_parser("list",
                                    help = "list of joysticks known the daemon")
        parser.add_argument("-v", "--verbose", action = "store_true",
                            help = "list the joysticks verbosely")
        return parser

    @staticmethod
    def execute(connection, args):
        """Perform the operation"""
        jsprog = getJSProg(connection)
        joysticks = jsprog.getJoysticks()

        if not joysticks:
            print("No joysticks detected.")

        for joystick in joysticks:
            GetJoysticks.printJoystick(joystick, args.verbose)

    @staticmethod
    def printJoystick(joystickArgs, verbose):
        """Print information about the given joystick."""
        joystick = Joystick.fromArgs(joystickArgs)
        identity = joystick.identity

        print("%2d: %s" % (joystick.id, identity))

        if verbose:
            print("    input ID: " + str(identity.inputID))

            print("    keys:")
            for key in joystick.keys:
                print("        %s" % (key,))

            print("    axes:")
            for axis in joystick.axes:
                print("        %s" % (axis,))

#------------------------------------------------------------------------------

class LoadProfile(object):
    """Command to load a profile top a joystick."""
    @staticmethod
    def addParser(parsers):
        """Add the parser for this command."""
        parser = parsers.add_parser("load",
                                    help = "load a profile to the joystick with the given ID")
        parser.add_argument(dest = "id",
                            help = "the identifier of the joystick")
        parser.add_argument(dest = "profile",
                            help = "the file containing the profile")
        return parser

    @staticmethod
    def execute(connection, args):
        """Load the profile."""
        jsprog = getJSProg(connection)

        id = int(args.id)
        with open(args.profile, "rt") as f:
            profile = f.read()

        if jsprog.loadProfile(id, profile):
            print("Profile %s loaded for joystick %d" % (args.profile, id))
        else:
            print("Failed to load profile %s for joystick %d" % \
                  (args.profile, id))

#------------------------------------------------------------------------------

class Monitor(object):
    """Command to monitor the addition and removal of joysticks."""

    @staticmethod
    def addParser(parsers):
        """Add the parser for this command."""
        parser = parsers.add_parser("monitor",
                                    help = "monitor the addition and removal of joysticks")
        parser.add_argument("-v", "--verbose", action = "store_true",
                            help = "the information of joysticks added will be printed verbosely")
        return parser

    @staticmethod
    def execute(connection, args):
        """Load the profile."""
        connection.add_match_string("interface='%s'" % (dbusInterfaceName,))
        connection.add_message_filter(lambda connection, message:
                                      Monitor.filterMessage(connection,
                                                            message,
                                                            args.verbose))

        mainloop = MainLoop()
        mainloop.run()

    @staticmethod
    def filterMessage(connection, message, verbose):
        """Callback for the messages."""
        if message.get_interface()==dbusInterfaceName:
            args = message.get_args_list()
            if message.get_member()=="joystickAdded":
                print("Added joystick:")
                GetJoysticks.printJoystick(args, verbose)
            elif message.get_member()=="joystickRemoved":
                print("Removed joystick with ID: %d" % (args[0],))

#------------------------------------------------------------------------------

class JSProgListener(dbus.service.Object):
    """A listener for the control events.

    It implements interface 'hu.varadiistvan.JSProgListener', defined
    in jsproglistener.xml."""
    def __init__(self, connection, path):
        """Construct the listener with the given path."""
        super(JSProgListener, self).__init__(connection, path)

    @dbus.service.method(dbus_interface = "hu.varadiistvan.JSProgListener",
                         in_signature = "uq", out_signature = "")
    def keyPressed(self, joystickID, code):
        """Called when a key is pressed."""
        print("Pressed key %d (0x%03x, %s)" % \
              (code, code, Key.getNameFor(code)))

    @dbus.service.method(dbus_interface = "hu.varadiistvan.JSProgListener",
                         in_signature = "uq", out_signature = "")
    def keyReleased(self, joystickID, code):
        """Called when a key is released."""
        print("Released key %d (0x%03x, %s)" % \
              (code, code, Key.getNameFor(code)))

    @dbus.service.method(dbus_interface = "hu.varadiistvan.JSProgListener",
                         in_signature = "uqi", out_signature = "")
    def axisChanged(self, joystickID, code, value):
        """Called when the value of an axis has changed."""
        print("Axis %d (0x%03x, %s) changed to %d" % \
              (code, code, Axis.getNameFor(code), value))

#------------------------------------------------------------------------------

class MonitorControls(object):
    """Command to monitor the various control (key or axis) events of a
    joystick."""
    @staticmethod
    def addParser(parsers):
        """Add the parser for this command."""
        parser = parsers.add_parser("monitorjs",
                                    help = "Monitor the control events of a joystick")
        parser.add_argument(dest = "id",
                            help = "the identifier of the joystick")
        return parser

    @staticmethod
    def execute(connection, args):
        """Perform the monitoring of the events."""
        pid = os.getpid()

        name = dbus.service.BusName("hu.varadiistvan.JSProgListener-%d" % (pid,),
                                    connection)

        jsprog = getJSProg(connection)

        path = "%s/%d" % (dbusInterfacePath, pid)
        listener = JSProgListener(connection, path)

        if jsprog.startMonitor(int(args.id), name.get_name(), path):
            mainloop = MainLoop()
            mainloop.run()
        else:
            print("Could not start monitoring the joystick, perhaps the ID is wrong.", file=sys.stderr)

#------------------------------------------------------------------------------

class Stop(object):
    """Command to stop the daemon."""
    @staticmethod
    def addParser(parsers):
        """Add the parser for this command."""
        parser = parsers.add_parser("stop", help = "stop the daemon")
        return parser

    @staticmethod
    def execute(connection, args):
        """Perform the operation"""
        jsprog = getJSProg(connection)
        jsprog.exit()

#------------------------------------------------------------------------------

class GUI(object):
    """Command to start the client as a GUI."""
    @staticmethod
    def addParser(parsers):
        """Add the parser for this command."""
        parser = parsers.add_parser("gui", help = "start the client as a GUI")
        parser.add_argument(dest = "profileDirectory",
                            help = "the directory containing the profiles")
        return parser

    @staticmethod
    def execute(connection, args):
        """Perform the operation"""
        gui.GUI(connection, args.profileDirectory).run([])

#------------------------------------------------------------------------------

def makeCommandFun(clazz):
    return lambda _args : clazz

#------------------------------------------------------------------------------

if __name__ == "__main__":
    mainParser = argparse.ArgumentParser(prog = "jsprog",
                                     description = "Command-line interface for the JSProg daemon")

    subParsers = mainParser.add_subparsers(title = "commands",
                                           description = "the commands the program accepts")

    for clazz in [GetJoysticks, LoadProfile, Monitor, MonitorControls,
                  Stop, GUI]:
        parser = clazz.addParser(subParsers)
        parser.set_defaults(func = makeCommandFun(clazz))

    args = mainParser.parse_args(sys.argv[1:])

    #try:
    connection = SessionBus(mainloop = DBusGMainLoop())
    args.func(args).execute(connection, args)
    #except Exception, e:
    #    print str(e)
