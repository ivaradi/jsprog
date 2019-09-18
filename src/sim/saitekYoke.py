#!/usr/bin/env python3

from joysim import CLI

from evdev import ecodes

if __name__ == "__main__":
    events = {
        ecodes.EV_ABS: [(ecodes.ABS_X, (128, 0, 255)),
                        (ecodes.ABS_Y, (128, 0, 255)),
                        (ecodes.ABS_Z, (128, 0, 255)),
                        (ecodes.ABS_RX, (128, 0, 255)),
                        (ecodes.ABS_RY, (128, 0, 255)),
                        (ecodes.ABS_HAT0X, (0, -1, 1)),
                        (ecodes.ABS_HAT0Y, (0, -1, 1))],
        ecodes.EV_KEY: [ecodes.BTN_THUMB2, ecodes.BTN_TOP, ecodes.BTN_TOP2,
                        ecodes.BTN_PINKIE, ecodes.BTN_BASE, ecodes.BTN_BASE2,
                        ecodes.BTN_THUMB, ecodes.BTN_TRIGGER, ecodes.BTN_BASE3,
                        ecodes.BTN_BASE4, ecodes.BTN_BASE5, ecodes.BTN_BASE6,
                        300, 301, ecodes.BTN_TRIGGER_HAPPY1,
                        ecodes.BTN_TRIGGER_HAPPY2, ecodes.BTN_TRIGGER_HAPPY3,
                        302, ecodes.BTN_DEAD, ecodes.BTN_TRIGGER_HAPPY17,
                        ecodes.BTN_TRIGGER_HAPPY18, ecodes.BTN_TRIGGER_HAPPY19,
                        ecodes.BTN_TRIGGER_HAPPY20]
    }

    cli = CLI(events, "Saitek Saitek Pro Flight Yoke", 0x06a3, 0x0bac,
              version=0x0111, shortName = "SaitekYoke")

    cli.cmdloop()
