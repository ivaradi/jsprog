from evdev import uinput, ecodes

import time
import cmd

class CLI(cmd.Cmd):
    """Command-line interface for a joystick simulator."""
    @staticmethod
    def getHandleButton(self, btnCode):
        """Get the function to handle a button."""
        return lambda args: self._handleButton(args, btnCode)

    @staticmethod
    def getHelpButton(self, btnName):
        """Get the function to print the help for a button command."""
        return lambda: self._helpButton(btnName)

    def __init__(self, events, name, vendor, product, shortName = None,
                 phys = "usb-0000:00:1d.1-1/input0", busType = 3, version = 0x0100):
        """Construct the joystick simulator."""
        cmd.Cmd.__init__(self)

        self.use_rawinput = True
        self.intro = "\nJoystick simulator command prompt\n"

        if shortName is None:
            shortName = name
        self.prompt = shortName + "> "

        self.daemon = True

        self._joystick = uinput.UInput(events = events, name = name,
                                       vendor = vendor, product = product,
                                       version = version,
                                       bustype = busType, phys = phys)

        self._btnStatus = {}

        for btnCode in events[ecodes.EV_KEY]:
            btnName = ecodes.BTN[btnCode]
            if isinstance(btnName, list):
                btnName = btnName[-1]
            btnName = btnName[4:].lower()
            self._btnStatus[btnCode] = False
            self.__dict__["do_" + btnName] = self.getHandleButton(self, btnCode)
            self.__dict__["help_" + btnName] = self.getHelpButton(self, btnName)

    def default(self, line):
        """Handle unhandle commands."""
        if line=="EOF":
            print
            return self.do_quit("")
        else:
            return cmd.Cmd.default(self, line)

    def do_quit(self, args):
        """Handle the quit command."""
        return True

    def _handleButton(self, args, btnCode):
        btnStatus = self._btnStatus[btnCode]

        if args:
            if args in ["on", "press"]:
                btnStatus = True
            elif args in ["off", "release"]:
                btnStatus = False
            else:
                print >> sys.stderr, "Invalid argument:", args
                return
        else:
            btnStatus = not btnStatus

        btnName = ecodes.BTN[btnCode]
        if isinstance(btnName, list):
            btnName = btnName[-1]

        print "%s %s" % ("Pressing" if btnStatus else "Releasing",
                         btnName)

        self._joystick.write(ecodes.EV_KEY, btnCode,
                             1 if btnStatus else 0)
        self._joystick.syn()
        self._btnStatus[btnCode] = btnStatus

    def _helpButton(self, btnName):
        print btnName + " [on|off]"
