#!/usr/bin/env python

from joysim import CLI

from evdev import ecodes

if __name__ == "__main__":
    events = {
        ecodes.EV_ABS: [(ecodes.ABS_X, (0, 128, 255, 0)),
                        (ecodes.ABS_Y, (0, 128, 255, 0)),
                        (ecodes.ABS_Z, (0, 128, 255, 0))],
        ecodes.EV_KEY: [ecodes.BTN_PINKIE, ecodes.BTN_BASE, ecodes.BTN_TRIGGER,
                        ecodes.BTN_TOP, ecodes.BTN_TOP2, ecodes.BTN_THUMB,
                        ecodes.BTN_THUMB2]
    }

    cli = CLI(events, "Logitech Inc. WingMan Force 3D", 0x046d, 0xc283,
              shortName = "WingMan")

    cli.cmdloop()
