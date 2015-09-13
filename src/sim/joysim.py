from evdev import uinput, ecodes

import cmd
import sys

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

    @staticmethod
    def getHandleAxis(self, axisCode, minValue, maxValue):
        """Get the function to handle an axis."""
        return lambda args: self._handleAxis(args, axisCode, minValue, maxValue)

    @staticmethod
    def getHelpAxis(self, axisName):
        """Get the function to print the help for an axis command."""
        return lambda: self._helpAxis(axisName)

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

        if ecodes.EV_ABS in events:
            for (axisCode, (minValue, maxValue, _1, _2)) in events[ecodes.EV_ABS]:
                axisName = ecodes.ABS[axisCode]
                if isinstance(axisName, list):
                    axisName = axisName[-1]
                axisName = axisName.lower()
                self.__dict__["do_" + axisName] = \
                    self.getHandleAxis(self, axisCode, minValue, maxValue)
                self.__dict__["help_" + axisName] = self.getHelpAxis(self, axisName)

        self._btnStatus = {}

        if ecodes.EV_KEY in events:
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

    def _handleAxis(self, args, axisCode, minValue, maxValue):
        axisName = ecodes.ABS[axisCode]
        if isinstance(axisName, list):
            axisName = axuisName[-1]

        try:
            value = int(args)
            if value<minValue or value>maxValue:
                raise Exception("the value should be between %d and %d" %
                                (minValue, maxValue))

            print "Setting %s to %d" % (axisName, value)

            self._joystick.write(ecodes.EV_ABS, axisCode, value)
            self._joystick.syn()
        except Exception, e:
            print >> sys.stderr, "Failed to set %s: %s" % (axisName, str(e))

    def _helpAxis(self, axisName):
        print axisName + " <value>"
