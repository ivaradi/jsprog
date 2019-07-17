from evdev import uinput, ecodes

import cmd
import sys
import time

class CLI(cmd.Cmd):
    """Command-line interface for a joystick simulator."""
    @staticmethod
    def getAxisName(code):
        """Get the name of the axis with the given code."""
        return ecodes.ABS.get(code, "ABS_" + str(code))

    @staticmethod
    def getButtonName(code):
        """Get the name of the button with the given code."""
        return ecodes.BTN.get(code, "BTN_" + str(code))

    @staticmethod
    def getName(nameOrList):
        """Extract the name from the given name or list.

        If it is a list, the last item will be returned."""
        return nameOrList[-1] if  isinstance(nameOrList, list) \
            else nameOrList

    @staticmethod
    def getHandleButton(btnCode):
        """Get the function to handle a button."""
        return lambda self, args: self._handleButton(args, btnCode)

    @staticmethod
    def getHelpButton(btnName):
        """Get the function to print the help for a button command."""
        return lambda self: self._helpButton(btnName)

    @staticmethod
    def getHandleAxis(axisCode, minValue, maxValue):
        """Get the function to handle an axis."""
        return lambda self, args: self._handleAxis(args, axisCode, minValue, maxValue)

    @staticmethod
    def getHelpAxis(axisName):
        """Get the function to print the help for an axis command."""
        return lambda self: self._helpAxis(axisName)

    def __init__(self, events, name, vendor, product, shortName = None,
                 busType = 3, version = 0x0100):
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
                                       bustype = busType)

        if ecodes.EV_ABS in events:
            for (axisCode, absInfo) in events[ecodes.EV_ABS]:
                minValue = absInfo[1]
                maxValue = absInfo[2]
                axisName = CLI.getName(CLI.getAxisName(axisCode))
                axisName = axisName.lower()
                setattr(CLI, "do_" + axisName,
                        self.getHandleAxis(axisCode, minValue, maxValue))
                setattr(CLI, "help_" + axisName, self.getHelpAxis(axisName))

        self._name2Button = {}
        self._btnStatus = {}

        if ecodes.EV_KEY in events:
            for btnCode in events[ecodes.EV_KEY]:
                btnName = CLI.getName(CLI.getButtonName(btnCode))
                btnName = btnName[4:].lower()
                self._name2Button[btnName] = btnCode
                self._btnStatus[btnCode] = False
                setattr(CLI, "do_" + btnName, self.getHandleButton(btnCode))
                setattr(CLI, "help_" + btnName, self.getHelpButton(btnName))

    def default(self, line):
        """Handle unhandle commands."""
        if line=="EOF":
            print()
            return self.do_quit("")
        else:
            return cmd.Cmd.default(self, line)

    def do_buttonTest1(self, args):
        """Test a button being pressed, held for a while, released and then
        immediately pressed again, and repeat this a few times."""

        words = [w for w in args.split(" ") if w]

        if len(words)<1:
            print("At least the button name should be given", file=sys.stderr)
            return

        btnName = words[0]
        btnCode = self._name2Button.get(btnName, -1)
        if btnCode<0:
            print("Unknown button:", btnName, file=sys.stderr)
            return

        numPresses = 3
        holdTime = 1000
        if len(words)>1:
            try:
                numPresses = int(words[1])
            except:
                print("Invalid number of presses:", words[1], file=sys.stderr)
                return

            if len(words)>2:
                try:
                    holdTime = int(words[2])
                except:
                    print("Invalid hold time:", words[2], file=sys.stderr)
                    return

        while numPresses>0:
            numPresses -= 1

            self._handleButton("press", btnCode)
            time.sleep(holdTime / 1000.0)
            print()
            self._handleButton("release", btnCode)

    def help_buttonTest1(self):
        print("buttonTest1 <button name> [<repeats> [<hold time>]]")
        print()
        print("    Press and hold the given button for a while, then release, ")
        print("    and immediately press again")
        print()
        print("    <button name>: the name of the button to press and release")
        print("    <repeats>: the number of repeats (default: 3)")
        print("    <hold time>: the length of time for which the button is")
        print("        held in milliseconds (default: 1000)")

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
                print("Invalid argument:", args, file=sys.stderr)
                return
        else:
            btnStatus = not btnStatus

        btnName = CLI.getName(CLI.getButtonName(btnCode))

        print("%s %s" % ("Pressing" if btnStatus else "Releasing",
                         btnName))

        self._joystick.write(ecodes.EV_KEY, btnCode,
                             1 if btnStatus else 0)
        self._joystick.syn()
        self._btnStatus[btnCode] = btnStatus

    def _helpButton(self, btnName):
        print(btnName + " [on|off]")

    def _handleAxis(self, args, axisCode, minValue, maxValue):
        axisName = CLI.getName(CLI.getAxisName(axisCode))

        try:
            value = int(args)
            if value<minValue or value>maxValue:
                raise Exception("the value should be between %d and %d" %
                                (minValue, maxValue))

            print("Setting %s to %d" % (axisName, value))

            self._joystick.write(ecodes.EV_ABS, axisCode, value)
            self._joystick.syn()
        except Exception as e:
            print("Failed to set %s: %s" % (axisName, str(e)), file=sys.stderr)

    def _helpAxis(self, axisName):
        print(axisName + " <value>")
