#!/usr/bin/env python3

from joysim import CLI

from evdev import ecodes

if __name__ == "__main__":
    events = {
        ecodes.EV_ABS: [(ecodes.ABS_X, (128, 0, 255)),
                        (ecodes.ABS_Y, (128, 0, 255)),
                        (ecodes.ABS_Z, (128, 0, 255))],
        ecodes.EV_KEY: [ecodes.BTN_PINKIE, ecodes.BTN_BASE, ecodes.BTN_TRIGGER,
                        ecodes.BTN_TOP, ecodes.BTN_TOP2, ecodes.BTN_THUMB,
                        ecodes.BTN_THUMB2]
    }

    cli = CLI(events, "Logitech Inc. WingMan Force 3D", 0x046d, 0x4283,
              shortName = "WingMan")

    cli.cmdloop()
