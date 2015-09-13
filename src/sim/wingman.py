#!/usr/bin/env python

from evdev import uinput, ecodes

import time
import cmd

class CLI(cmd.Cmd):
    @staticmethod
    def getHandleButton(self, btnCode):
        return lambda args: self._handleButton(args, btnCode)

    @staticmethod
    def getHelpButton(self, btnName):
        return lambda: self._helpButton(btnName)

    def __init__(self):
        cmd.Cmd.__init__(self)

        self.use_rawinput = True
        self.intro = "\nJoystick simulator command prompt\n"
        self.prompt = "WingMan> "

        self.daemon = True

        events = {
            ecodes.EV_ABS: [(ecodes.ABS_X, (0, 255, 0, 0)),
                            (ecodes.ABS_Y, (0, 255, 0, 0)),
                            (ecodes.ABS_Z, (0, 255, 0, 0))],
            ecodes.EV_KEY: [ecodes.BTN_PINKIE, ecodes.BTN_BASE, ecodes.BTN_TRIGGER,
                            ecodes.BTN_TOP, ecodes.BTN_TOP2, ecodes.BTN_THUMB,
                            ecodes.BTN_THUMB2]
            }

        self._joystick = uinput.UInput(events = events,
                                       name = "Logitech Inc. WingMan Force 3D",
                                       vendor=0x46d, product=0xc283, version=0x0100,
                                       bustype = 3, phys="usb-0000:00:1d.1-1/input0")

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
            return super(CLI, self).default(line)

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

        print "%s %s" % ("Pressing" if btnStatus else "Releasing",
                         ecodes.BTN[btnCode])

        self._joystick.write(ecodes.EV_KEY, btnCode,
                             1 if btnStatus else 0)
        self._joystick.syn()
        self._btnStatus[btnCode] = btnStatus

    def _helpButton(self, btnName):
        print btnName + " [on|off]"

if __name__ == "__main__":
    CLI().cmdloop()
