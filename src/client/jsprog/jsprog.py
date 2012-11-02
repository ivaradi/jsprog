# The main CLI for the client

from dbus import SessionBus, Interface
from dbus.mainloop.glib import DBusGMainLoop
from gobject import MainLoop

import dbus.service

import argparse
import sys
import os

#------------------------------------------------------------------------------

def getJSProg(connection):
    """Get the JSProg object via the given connection."""
    jsprog_proxy = connection.get_object("hu.varadiistvan.JSProg",
                                         "/hu/varadiistvan/JSProg")
    return Interface(jsprog_proxy, "hu.varadiistvan.JSProg")

#------------------------------------------------------------------------------

class GetJoysticks(object):
    """Command to get the list of joysticks known to the daemon."""

    _busNames = {
        0x01 : "pci",
        0x02 : "isapnp",
        0x03 : "usb",
        0x04 : "hil",
        0x05 : "bluetooth",
        0x06 : "virtual",
        0x10 : "isa",
        0x11 : "i8042",
        0x12 : "xtkbd",
        0x13 : "rs232",
        0x14 : "gameport",
        0x15 : "parport",
        0x16 : "amiga",
        0x17 : "adb",
        0x18 : "i2c",
        0x19 : "host",
        0x1a : "gsc",
        0x1b : "atari",
        0x1c : "spi"
        }

    _keyNames = [
        # 0 (0x000)
        "KEY_RESERVED",
        "KEY_ESC",
        "KEY_1",
        "KEY_2",
        "KEY_3",
        "KEY_4",
        "KEY_5",
        "KEY_6",
        # 8 (0x008)
        "KEY_7",
        "KEY_8",
        "KEY_9",
        "KEY_0",
        "KEY_MINUS",
        "KEY_EQUAL",
        "KEY_BACKSPACE",
        "KEY_TAB",
        # 16 (0x010)
        "KEY_Q",
        "KEY_W",
        "KEY_E",
        "KEY_R",
        "KEY_T",
        "KEY_Y",
        "KEY_U",
        "KEY_I",
        # 24 (0x018)
        "KEY_O",
        "KEY_P",
        "KEY_LEFTBRACE",
        "KEY_RIGHTBRACE",
        "KEY_ENTER",
        "KEY_LEFTCTRL",
        "KEY_A",
        "KEY_S",
        # 32 (0x020)
        "KEY_D",
        "KEY_F",
        "KEY_G",
        "KEY_H",
        "KEY_J",
        "KEY_K",
        "KEY_L",
        "KEY_SEMICOLON",
        # 40 (0x028)
        "KEY_APOSTROPHE",
        "KEY_GRAVE",
        "KEY_LEFTSHIFT",
        "KEY_BACKSLASH",
        "KEY_Z",
        "KEY_X",
        "KEY_C",
        "KEY_V",
        # 48 (0x030)
        "KEY_B",
        "KEY_N",
        "KEY_M",
        "KEY_COMMA",
        "KEY_DOT",
        "KEY_SLASH",
        "KEY_RIGHTSHIFT",
        "KEY_KPASTERISK",
        # 56 (0x038)
        "KEY_LEFTALT",
        "KEY_SPACE",
        "KEY_CAPSLOCK",
        "KEY_F1",
        "KEY_F2",
        "KEY_F3",
        "KEY_F4",
        "KEY_F5",
        # 64 (0x040)
        "KEY_F6",
        "KEY_F7",
        "KEY_F8",
        "KEY_F9",
        "KEY_F10",
        "KEY_NUMLOCK",
        "KEY_SCROLLLOCK",
        "KEY_KP7",
        # 72 (0x048)
        "KEY_KP8",
        "KEY_KP9",
        "KEY_KPMINUS",
        "KEY_KP4",
        "KEY_KP5",
        "KEY_KP6",
        "KEY_KPPLUS",
        "KEY_KP1",
        # 80 (0x050)
        "KEY_KP2",
        "KEY_KP3",
        "KEY_KP0",
        "KEY_KPDOT",
        "KEY_0X054",
        "KEY_ZENKAKUHANKAKU",
        "KEY_102ND",
        "KEY_F11",
        # 88 (0x058)
        "KEY_F12",
        "KEY_RO",
        "KEY_KATAKANA",
        "KEY_HIRAGANA",
        "KEY_HENKAN",
        "KEY_KATAKANAHIRAGANA",
        "KEY_MUHENKAN",
        "KEY_KPJPCOMMA",
        # 96 (0x060)
        "KEY_KPENTER",
        "KEY_RIGHTCTRL",
        "KEY_KPSLASH",
        "KEY_SYSRQ",
        "KEY_RIGHTALT",
        "KEY_LINEFEED",
        "KEY_HOME",
        "KEY_UP",
        # 104 (0x068)
        "KEY_PAGEUP",
        "KEY_LEFT",
        "KEY_RIGHT",
        "KEY_END",
        "KEY_DOWN",
        "KEY_PAGEDOWN",
        "KEY_INSERT",
        "KEY_DELETE",
        # 112 (0x070)
        "KEY_MACRO",
        "KEY_MUTE",
        "KEY_VOLUMEDOWN",
        "KEY_VOLUMEUP",
        "KEY_POWER",
        "KEY_KPEQUAL",
        "KEY_KPPLUSMINUS",
        "KEY_PAUSE",
        # 120 (0x078)
        "KEY_SCALE",
        "KEY_KPCOMMA",
        "KEY_HANGEUL",
        "KEY_HANJA",
        "KEY_YEN",
        "KEY_LEFTMETA",
        "KEY_RIGHTMETA",
        "KEY_COMPOSE",
        # 128 (0x080)
        "KEY_STOP",
        "KEY_AGAIN",
        "KEY_PROPS",
        "KEY_UNDO",
        "KEY_FRONT",
        "KEY_COPY",
        "KEY_OPEN",
        "KEY_PASTE",
        # 136 (0x088)
        "KEY_FIND",
        "KEY_CUT",
        "KEY_HELP",
        "KEY_MENU",
        "KEY_CALC",
        "KEY_SETUP",
        "KEY_SLEEP",
        "KEY_WAKEUP",
        # 144 (0x090)
        "KEY_FILE",
        "KEY_SENDFILE",
        "KEY_DELETEFILE",
        "KEY_XFER",
        "KEY_PROG1",
        "KEY_PROG2",
        "KEY_WWW",
        "KEY_MSDOS",
        # 152 (0x098)
        "KEY_COFFEE",
        "KEY_DIRECTION",
        "KEY_CYCLEWINDOWS",
        "KEY_MAIL",
        "KEY_BOOKMARKS",
        "KEY_COMPUTER",
        "KEY_BACK",
        "KEY_FORWARD",
        # 160 (0x0a0)
        "KEY_CLOSECD",
        "KEY_EJECTCD",
        "KEY_EJECTCLOSECD",
        "KEY_NEXTSONG",
        "KEY_PLAYPAUSE",
        "KEY_PREVIOUSSONG",
        "KEY_STOPCD",
        "KEY_RECORD",
        # 168 (0x0a8)
        "KEY_REWIND",
        "KEY_PHONE",
        "KEY_ISO",
        "KEY_CONFIG",
        "KEY_HOMEPAGE",
        "KEY_REFRESH",
        "KEY_EXIT",
        "KEY_MOVE",
        # 176 (0x0b0)
        "KEY_EDIT",
        "KEY_SCROLLUP",
        "KEY_SCROLLDOWN",
        "KEY_KPLEFTPAREN",
        "KEY_KPRIGHTPAREN",
        "KEY_NEW",
        "KEY_REDO",
        "KEY_F13",
        # 184 (0x0b8)
        "KEY_F14",
        "KEY_F15",
        "KEY_F16",
        "KEY_F17",
        "KEY_F18",
        "KEY_F19",
        "KEY_F20",
        "KEY_F21",
        # 192 (0x0c0)
        "KEY_F22",
        "KEY_F23",
        "KEY_F24",
        "KEY_0X0C3",
        "KEY_0X0C4",
        "KEY_0X0C5",
        "KEY_0X0C6",
        "KEY_0X0C7",
        # 200 (0x0c8)
        "KEY_PLAYCD",
        "KEY_PAUSECD",
        "KEY_PROG3",
        "KEY_PROG4",
        "KEY_DASHBOARD",
        "KEY_SUSPEND",
        "KEY_CLOSE",
        "KEY_PLAY",
        # 208 (0x0d0)
        "KEY_FASTFORWARD",
        "KEY_BASSBOOST",
        "KEY_PRINT",
        "KEY_HP",
        "KEY_CAMERA",
        "KEY_SOUND",
        "KEY_QUESTION",
        "KEY_EMAIL",
        # 216 (0x0d8)
        "KEY_CHAT",
        "KEY_SEARCH",
        "KEY_CONNECT",
        "KEY_FINANCE",
        "KEY_SPORT",
        "KEY_SHOP",
        "KEY_ALTERASE",
        "KEY_CANCEL",
        # 224 (0x0e0)
        "KEY_BRIGHTNESSDOWN",
        "KEY_BRIGHTNESSUP",
        "KEY_MEDIA",
        "KEY_SWITCHVIDEOMODE",
        "KEY_KBDILLUMTOGGLE",
        "KEY_KBDILLUMDOWN",
        "KEY_KBDILLUMUP",
        "KEY_SEND",
        # 232 (0x0e8)
        "KEY_REPLY",
        "KEY_FORWARDMAIL",
        "KEY_SAVE",
        "KEY_DOCUMENTS",
        "KEY_BATTERY",
        "KEY_BLUETOOTH",
        "KEY_WLAN",
        "KEY_UWB",
        # 240 (0x0f0)
        "KEY_UNKNOWN",
        "KEY_VIDEO_NEXT",
        "KEY_VIDEO_PREV",
        "KEY_BRIGHTNESS_CYCLE",
        "KEY_BRIGHTNESS_ZERO",
        "KEY_DISPLAY_OFF",
        "KEY_WIMAX",
        "KEY_RFKILL",
        # 248 (0x0f8)
        "KEY_MICMUTE",
        "KEY_0X0F9",
        "KEY_0X0FA",
        "KEY_0X0FB",
        "KEY_0X0FC",
        "KEY_0X0FD",
        "KEY_0X0FE",
        "KEY_0X0FF",
        # 256 (0x100)
        "BTN_0",
        "BTN_1",
        "BTN_2",
        "BTN_3",
        "BTN_4",
        "BTN_5",
        "BTN_6",
        "BTN_7",
        # 264 (0x108)
        "BTN_8",
        "BTN_9",
        "KEY_0X10A",
        "KEY_0X10B",
        "KEY_0X10C",
        "KEY_0X10D",
        "KEY_0X10E",
        "KEY_0X10F",
        # 272 (0x110)
        "BTN_LEFT",
        "BTN_RIGHT",
        "BTN_MIDDLE",
        "BTN_SIDE",
        "BTN_EXTRA",
        "BTN_FORWARD",
        "BTN_BACK",
        "BTN_TASK",
        # 280 (0x118)
        "KEY_0X118",
        "KEY_0X119",
        "KEY_0X11A",
        "KEY_0X11B",
        "KEY_0X11C",
        "KEY_0X11D",
        "KEY_0X11E",
        "KEY_0X11F",
        # 288 (0x120)
        "BTN_TRIGGER",
        "BTN_THUMB",
        "BTN_THUMB2",
        "BTN_TOP",
        "BTN_TOP2",
        "BTN_PINKIE",
        "BTN_BASE",
        "BTN_BASE2",
        # 296 (0x128)
        "BTN_BASE3",
        "BTN_BASE4",
        "BTN_BASE5",
        "BTN_BASE6",
        "KEY_0X12C",
        "KEY_0X12D",
        "KEY_0X12E",
        "BTN_DEAD",
        # 304 (0x130)
        "BTN_A",
        "BTN_B",
        "BTN_C",
        "BTN_X",
        "BTN_Y",
        "BTN_Z",
        "BTN_TL",
        "BTN_TR",
        # 312 (0x138)
        "BTN_TL2",
        "BTN_TR2",
        "BTN_SELECT",
        "BTN_START",
        "BTN_MODE",
        "BTN_THUMBL",
        "BTN_THUMBR",
        "KEY_0X13F",
        # 320 (0x140)
        "BTN_TOOL_PEN",
        "BTN_TOOL_RUBBER",
        "BTN_TOOL_BRUSH",
        "BTN_TOOL_PENCIL",
        "BTN_TOOL_AIRBRUSH",
        "BTN_TOOL_FINGER",
        "BTN_TOOL_MOUSE",
        "BTN_TOOL_LENS",
        # 328 (0x148)
        "BTN_TOOL_QUINTTAP",
        "KEY_0X149",
        "BTN_TOUCH",
        "BTN_STYLUS",
        "BTN_STYLUS2",
        "BTN_TOOL_DOUBLETAP",
        "BTN_TOOL_TRIPLETAP",
        "BTN_TOOL_QUADTAP",
        # 336 (0x150)
        "BTN_GEAR_DOWN",
        "BTN_GEAR_UP",
        "KEY_0X152",
        "KEY_0X153",
        "KEY_0X154",
        "KEY_0X155",
        "KEY_0X156",
        "KEY_0X157",
        # 344 (0x158)
        "KEY_0X158",
        "KEY_0X159",
        "KEY_0X15A",
        "KEY_0X15B",
        "KEY_0X15C",
        "KEY_0X15D",
        "KEY_0X15E",
        "KEY_0X15F",
        # 352 (0x160)
        "KEY_OK",
        "KEY_SELECT",
        "KEY_GOTO",
        "KEY_CLEAR",
        "KEY_POWER2",
        "KEY_OPTION",
        "KEY_INFO",
        "KEY_TIME",
        # 360 (0x168)
        "KEY_VENDOR",
        "KEY_ARCHIVE",
        "KEY_PROGRAM",
        "KEY_CHANNEL",
        "KEY_FAVORITES",
        "KEY_EPG",
        "KEY_PVR",
        "KEY_MHP",
        # 368 (0x170)
        "KEY_LANGUAGE",
        "KEY_TITLE",
        "KEY_SUBTITLE",
        "KEY_ANGLE",
        "KEY_ZOOM",
        "KEY_MODE",
        "KEY_KEYBOARD",
        "KEY_SCREEN",
        # 376 (0x178)
        "KEY_PC",
        "KEY_TV",
        "KEY_TV2",
        "KEY_VCR",
        "KEY_VCR2",
        "KEY_SAT",
        "KEY_SAT2",
        "KEY_CD",
        # 384 (0x180)
        "KEY_TAPE",
        "KEY_RADIO",
        "KEY_TUNER",
        "KEY_PLAYER",
        "KEY_TEXT",
        "KEY_DVD",
        "KEY_AUX",
        "KEY_MP3",
        # 392 (0x188)
        "KEY_AUDIO",
        "KEY_VIDEO",
        "KEY_DIRECTORY",
        "KEY_LIST",
        "KEY_MEMO",
        "KEY_CALENDAR",
        "KEY_RED",
        "KEY_GREEN",
        # 400 (0x190)
        "KEY_YELLOW",
        "KEY_BLUE",
        "KEY_CHANNELUP",
        "KEY_CHANNELDOWN",
        "KEY_FIRST",
        "KEY_LAST",
        "KEY_AB",
        "KEY_NEXT",
        # 408 (0x198)
        "KEY_RESTART",
        "KEY_SLOW",
        "KEY_SHUFFLE",
        "KEY_BREAK",
        "KEY_PREVIOUS",
        "KEY_DIGITS",
        "KEY_TEEN",
        "KEY_TWEN",
        # 416 (0x1a0)
        "KEY_VIDEOPHONE",
        "KEY_GAMES",
        "KEY_ZOOMIN",
        "KEY_ZOOMOUT",
        "KEY_ZOOMRESET",
        "KEY_WORDPROCESSOR",
        "KEY_EDITOR",
        "KEY_SPREADSHEET",
        # 424 (0x1a8)
        "KEY_GRAPHICSEDITOR",
        "KEY_PRESENTATION",
        "KEY_DATABASE",
        "KEY_NEWS",
        "KEY_VOICEMAIL",
        "KEY_ADDRESSBOOK",
        "KEY_MESSENGER",
        "KEY_DISPLAYTOGGLE",
        # 432 (0x1b0)
        "KEY_SPELLCHECK",
        "KEY_LOGOFF",
        "KEY_DOLLAR",
        "KEY_EURO",
        "KEY_FRAMEBACK",
        "KEY_FRAMEFORWARD",
        "KEY_CONTEXT_MENU",
        "KEY_MEDIA_REPEAT",
        # 440 (0x1b8)
        "KEY_10CHANNELSUP",
        "KEY_10CHANNELSDOWN",
        "KEY_IMAGES",
        "KEY_0X1BB",
        "KEY_0X1BC",
        "KEY_0X1BD",
        "KEY_0X1BE",
        "KEY_0X1BF",
        # 448 (0x1c0)
        "KEY_DEL_EOL",
        "KEY_DEL_EOS",
        "KEY_INS_LINE",
        "KEY_DEL_LINE",
        "KEY_0X1C4",
        "KEY_0X1C5",
        "KEY_0X1C6",
        "KEY_0X1C7",
        # 456 (0x1c8)
        "KEY_0X1C8",
        "KEY_0X1C9",
        "KEY_0X1CA",
        "KEY_0X1CB",
        "KEY_0X1CC",
        "KEY_0X1CD",
        "KEY_0X1CE",
        "KEY_0X1CF",
        # 464 (0x1d0)
        "KEY_FN",
        "KEY_FN_ESC",
        "KEY_FN_F1",
        "KEY_FN_F2",
        "KEY_FN_F3",
        "KEY_FN_F4",
        "KEY_FN_F5",
        "KEY_FN_F6",
        # 472 (0x1d8)
        "KEY_FN_F7",
        "KEY_FN_F8",
        "KEY_FN_F9",
        "KEY_FN_F10",
        "KEY_FN_F11",
        "KEY_FN_F12",
        "KEY_FN_1",
        "KEY_FN_2",
        # 480 (0x1e0)
        "KEY_FN_D",
        "KEY_FN_E",
        "KEY_FN_F",
        "KEY_FN_S",
        "KEY_FN_B",
        "KEY_0X1E5",
        "KEY_0X1E6",
        "KEY_0X1E7",
        # 488 (0x1e8)
        "KEY_0X1E8",
        "KEY_0X1E9",
        "KEY_0X1EA",
        "KEY_0X1EB",
        "KEY_0X1EC",
        "KEY_0X1ED",
        "KEY_0X1EE",
        "KEY_0X1EF",
        # 496 (0x1f0)
        "KEY_0X1F0",
        "KEY_BRL_DOT1",
        "KEY_BRL_DOT2",
        "KEY_BRL_DOT3",
        "KEY_BRL_DOT4",
        "KEY_BRL_DOT5",
        "KEY_BRL_DOT6",
        "KEY_BRL_DOT7",
        # 504 (0x1f8)
        "KEY_BRL_DOT8",
        "KEY_BRL_DOT9",
        "KEY_BRL_DOT10",
        "KEY_0X1FB",
        "KEY_0X1FC",
        "KEY_0X1FD",
        "KEY_0X1FE",
        "KEY_0X1FF",
        # 512 (0x200)
        "KEY_NUMERIC_0",
        "KEY_NUMERIC_1",
        "KEY_NUMERIC_2",
        "KEY_NUMERIC_3",
        "KEY_NUMERIC_4",
        "KEY_NUMERIC_5",
        "KEY_NUMERIC_6",
        "KEY_NUMERIC_7",
        # 520 (0x208)
        "KEY_NUMERIC_8",
        "KEY_NUMERIC_9",
        "KEY_NUMERIC_STAR",
        "KEY_NUMERIC_POUND",
        "KEY_0X20C",
        "KEY_0X20D",
        "KEY_0X20E",
        "KEY_0X20F",
        # 528 (0x210)
        "KEY_CAMERA_FOCUS",
        "KEY_WPS_BUTTON",
        "KEY_TOUCHPAD_TOGGLE",
        "KEY_TOUCHPAD_ON",
        "KEY_TOUCHPAD_OFF",
        "KEY_CAMERA_ZOOMIN",
        "KEY_CAMERA_ZOOMOUT",
        "KEY_CAMERA_UP",
        # 536 (0x218)
        "KEY_CAMERA_DOWN",
        "KEY_CAMERA_LEFT",
        "KEY_CAMERA_RIGHT",
        "KEY_0X21B",
        "KEY_0X21C",
        "KEY_0X21D",
        "KEY_0X21E",
        "KEY_0X21F",
        # 544 (0x220)
        "KEY_0X220",
        "KEY_0X221",
        "KEY_0X222",
        "KEY_0X223",
        "KEY_0X224",
        "KEY_0X225",
        "KEY_0X226",
        "KEY_0X227",
        # 552 (0x228)
        "KEY_0X228",
        "KEY_0X229",
        "KEY_0X22A",
        "KEY_0X22B",
        "KEY_0X22C",
        "KEY_0X22D",
        "KEY_0X22E",
        "KEY_0X22F",
        # 560 (0x230)
        "KEY_0X230",
        "KEY_0X231",
        "KEY_0X232",
        "KEY_0X233",
        "KEY_0X234",
        "KEY_0X235",
        "KEY_0X236",
        "KEY_0X237",
        # 568 (0x238)
        "KEY_0X238",
        "KEY_0X239",
        "KEY_0X23A",
        "KEY_0X23B",
        "KEY_0X23C",
        "KEY_0X23D",
        "KEY_0X23E",
        "KEY_0X23F",
        # 576 (0x240)
        "KEY_0X240",
        "KEY_0X241",
        "KEY_0X242",
        "KEY_0X243",
        "KEY_0X244",
        "KEY_0X245",
        "KEY_0X246",
        "KEY_0X247",
        # 584 (0x248)
        "KEY_0X248",
        "KEY_0X249",
        "KEY_0X24A",
        "KEY_0X24B",
        "KEY_0X24C",
        "KEY_0X24D",
        "KEY_0X24E",
        "KEY_0X24F",
        # 592 (0x250)
        "KEY_0X250",
        "KEY_0X251",
        "KEY_0X252",
        "KEY_0X253",
        "KEY_0X254",
        "KEY_0X255",
        "KEY_0X256",
        "KEY_0X257",
        # 600 (0x258)
        "KEY_0X258",
        "KEY_0X259",
        "KEY_0X25A",
        "KEY_0X25B",
        "KEY_0X25C",
        "KEY_0X25D",
        "KEY_0X25E",
        "KEY_0X25F",
        # 608 (0x260)
        "KEY_0X260",
        "KEY_0X261",
        "KEY_0X262",
        "KEY_0X263",
        "KEY_0X264",
        "KEY_0X265",
        "KEY_0X266",
        "KEY_0X267",
        # 616 (0x268)
        "KEY_0X268",
        "KEY_0X269",
        "KEY_0X26A",
        "KEY_0X26B",
        "KEY_0X26C",
        "KEY_0X26D",
        "KEY_0X26E",
        "KEY_0X26F",
        # 624 (0x270)
        "KEY_0X270",
        "KEY_0X271",
        "KEY_0X272",
        "KEY_0X273",
        "KEY_0X274",
        "KEY_0X275",
        "KEY_0X276",
        "KEY_0X277",
        # 632 (0x278)
        "KEY_0X278",
        "KEY_0X279",
        "KEY_0X27A",
        "KEY_0X27B",
        "KEY_0X27C",
        "KEY_0X27D",
        "KEY_0X27E",
        "KEY_0X27F",
        # 640 (0x280)
        "KEY_0X280",
        "KEY_0X281",
        "KEY_0X282",
        "KEY_0X283",
        "KEY_0X284",
        "KEY_0X285",
        "KEY_0X286",
        "KEY_0X287",
        # 648 (0x288)
        "KEY_0X288",
        "KEY_0X289",
        "KEY_0X28A",
        "KEY_0X28B",
        "KEY_0X28C",
        "KEY_0X28D",
        "KEY_0X28E",
        "KEY_0X28F",
        # 656 (0x290)
        "KEY_0X290",
        "KEY_0X291",
        "KEY_0X292",
        "KEY_0X293",
        "KEY_0X294",
        "KEY_0X295",
        "KEY_0X296",
        "KEY_0X297",
        # 664 (0x298)
        "KEY_0X298",
        "KEY_0X299",
        "KEY_0X29A",
        "KEY_0X29B",
        "KEY_0X29C",
        "KEY_0X29D",
        "KEY_0X29E",
        "KEY_0X29F",
        # 672 (0x2a0)
        "KEY_0X2A0",
        "KEY_0X2A1",
        "KEY_0X2A2",
        "KEY_0X2A3",
        "KEY_0X2A4",
        "KEY_0X2A5",
        "KEY_0X2A6",
        "KEY_0X2A7",
        # 680 (0x2a8)
        "KEY_0X2A8",
        "KEY_0X2A9",
        "KEY_0X2AA",
        "KEY_0X2AB",
        "KEY_0X2AC",
        "KEY_0X2AD",
        "KEY_0X2AE",
        "KEY_0X2AF",
        # 688 (0x2b0)
        "KEY_0X2B0",
        "KEY_0X2B1",
        "KEY_0X2B2",
        "KEY_0X2B3",
        "KEY_0X2B4",
        "KEY_0X2B5",
        "KEY_0X2B6",
        "KEY_0X2B7",
        # 696 (0x2b8)
        "KEY_0X2B8",
        "KEY_0X2B9",
        "KEY_0X2BA",
        "KEY_0X2BB",
        "KEY_0X2BC",
        "KEY_0X2BD",
        "KEY_0X2BE",
        "KEY_0X2BF",
        # 704 (0x2c0)
        "BTN_TRIGGER_HAPPY1",
        "BTN_TRIGGER_HAPPY2",
        "BTN_TRIGGER_HAPPY3",
        "BTN_TRIGGER_HAPPY4",
        "BTN_TRIGGER_HAPPY5",
        "BTN_TRIGGER_HAPPY6",
        "BTN_TRIGGER_HAPPY7",
        "BTN_TRIGGER_HAPPY8",
        # 712 (0x2c8)
        "BTN_TRIGGER_HAPPY9",
        "BTN_TRIGGER_HAPPY10",
        "BTN_TRIGGER_HAPPY11",
        "BTN_TRIGGER_HAPPY12",
        "BTN_TRIGGER_HAPPY13",
        "BTN_TRIGGER_HAPPY14",
        "BTN_TRIGGER_HAPPY15",
        "BTN_TRIGGER_HAPPY16",
        # 720 (0x2d0)
        "BTN_TRIGGER_HAPPY17",
        "BTN_TRIGGER_HAPPY18",
        "BTN_TRIGGER_HAPPY19",
        "BTN_TRIGGER_HAPPY20",
        "BTN_TRIGGER_HAPPY21",
        "BTN_TRIGGER_HAPPY22",
        "BTN_TRIGGER_HAPPY23",
        "BTN_TRIGGER_HAPPY24",
        # 728 (0x2d8)
        "BTN_TRIGGER_HAPPY25",
        "BTN_TRIGGER_HAPPY26",
        "BTN_TRIGGER_HAPPY27",
        "BTN_TRIGGER_HAPPY28",
        "BTN_TRIGGER_HAPPY29",
        "BTN_TRIGGER_HAPPY30",
        "BTN_TRIGGER_HAPPY31",
        "BTN_TRIGGER_HAPPY32",
        # 736 (0x2e0)
        "BTN_TRIGGER_HAPPY33",
        "BTN_TRIGGER_HAPPY34",
        "BTN_TRIGGER_HAPPY35",
        "BTN_TRIGGER_HAPPY36",
        "BTN_TRIGGER_HAPPY37",
        "BTN_TRIGGER_HAPPY38",
        "BTN_TRIGGER_HAPPY39",
        "BTN_TRIGGER_HAPPY40"
        ]

    _axisNames = [
       # 0 (0x000)
       "ABS_X",
       "ABS_Y",
       "ABS_Z",
       "ABS_RX",
       "ABS_RY",
       "ABS_RZ",
       "ABS_THROTTLE",
       "ABS_RUDDER",
       # 8 (0x008)
       "ABS_WHEEL",
       "ABS_GAS",
       "ABS_BRAKE",
       "ABS_0X00B",
       "ABS_0X00C",
       "ABS_0X00D",
       "ABS_0X00E",
       "ABS_0X00F",
       # 16 (0x010)
       "ABS_HAT0X",
       "ABS_HAT0Y",
       "ABS_HAT1X",
       "ABS_HAT1Y",
       "ABS_HAT2X",
       "ABS_HAT2Y",
       "ABS_HAT3X",
       "ABS_HAT3Y",
       # 24 (0x018)
       "ABS_PRESSURE",
       "ABS_DISTANCE",
       "ABS_TILT_X",
       "ABS_TILT_Y",
       "ABS_TOOL_WIDTH",
       "ABS_0X01D",
       "ABS_0X01E",
       "ABS_0X01F",
       # 32 (0x020)
       "ABS_VOLUME",
       "ABS_0X021",
       "ABS_0X022",
       "ABS_0X023",
       "ABS_0X024",
       "ABS_0X025",
       "ABS_0X026",
       "ABS_0X027",
       # 40 (0x028)
       "ABS_MISC",
       "ABS_0X029",
       "ABS_0X02A",
       "ABS_0X02B",
       "ABS_0X02C",
       "ABS_0X02D",
       "ABS_0X02E",
       "ABS_MT_SLOT",
       # 48 (0x030)
       "ABS_MT_TOUCH_MAJOR",
       "ABS_MT_TOUCH_MINOR",
       "ABS_MT_WIDTH_MAJOR",
       "ABS_MT_WIDTH_MINOR",
       "ABS_MT_ORIENTATION",
       "ABS_MT_POSITION_X",
       "ABS_MT_POSITION_Y",
       "ABS_MT_TOOL_TYPE",
       # 56 (0x038)
       "ABS_MT_BLOB_ID",
       "ABS_MT_TRACKING_ID",
       "ABS_MT_PRESSURE",
       "ABS_MT_DISTANCE"
       ]

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
            print "No joysticks detected."

        for joystick in joysticks:
            GetJoysticks.printJoystick(joystick, args.verbose)

    @staticmethod
    def printJoystick(joystick, verbose):
        """Print information about the given joystick."""
        id = joystick[0]
        name = joystick[2]
        phys = joystick[3]
        uniq = joystick[4]

        if uniq:
            print "%2d: %s (%s, %s)" % (id, name, phys, uniq)
        else:
            print "%2d: %s (%s)" % (id, name, phys)

        if verbose:
            inputID = joystick[1]
            print "    input ID: %s:%04x:%04x (ver: %04x)" % \
                  (GetJoysticks._getBusName(inputID[0]),
                   inputID[1], inputID[2], inputID[3])

            keys = joystick[5]
            print "    keys:"
            for key in keys:
                code = key[0]
                pressed = key[1]!=0
                print "        %s (0x%03x): %s" % \
                      (GetJoysticks.getKeyName(code), code,
                       "pressed" if pressed else "released")


            axes = joystick[6]
            print "    axes:"
            for axis in axes:
                code = axis[0]
                value = axis[1]
                minimum = axis[2]
                maximum = axis[3]
                print "        %s (0x%03x, %d..%d): %d" % \
                      (GetJoysticks.getAxisName(code), code,
                       minimum, maximum, value)

    @staticmethod
    def _getBusName(busID):
        """Get the name of the given input bus ID."""
        if busID in GetJoysticks._busNames:
            return GetJoysticks._busNames[busID]
        else:
            return "bus<%02x>" % (busID,)

    @staticmethod
    def getKeyName(code):
        """Get the name of the key for the given code."""
        if code<len(GetJoysticks._keyNames):
            return GetJoysticks._keyNames[code]
        else:
            return "KEY_0X%03X" % (code,)

    @staticmethod
    def getAxisName(code):
        """Get the name of the axis for the given code."""
        if code<len(GetJoysticks._axisNames):
            return GetJoysticks._axisNames[code]
        else:
            return "ABS_0X%03X" % (code,)

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
            print "Profile %s loaded for joystick %d" % (args.profile, id)
        else:
            print "Failed to load profile %s for joystick %d" % \
                  (args.profile, id)

#------------------------------------------------------------------------------

class Monitor(object):
    """Command to monitor the addition and removal of joysticks."""

    # The interface to monitor
    _interface = "hu.varadiistvan.JSProg"

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
        connection.add_match_string("interface='%s'" % (Monitor._interface,))
        connection.add_message_filter(lambda connection, message:
                                      Monitor.filterMessage(connection,
                                                            message,
                                                            args.verbose))

        mainloop = MainLoop()
        mainloop.run()

    @staticmethod
    def filterMessage(connection, message, verbose):
        """Callback for the messages."""
        if message.get_interface()==Monitor._interface:
            args = message.get_args_list()
            if message.get_member()=="joystickAdded":
                print "Added joystick:"
                GetJoysticks.printJoystick(args, verbose)
            elif message.get_member()=="joystickRemoved":
                print "Removed joystick with ID: %d" % (args[0],)

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
        print "Pressed key %d (0x%03x, %s)" % \
              (code, code, GetJoysticks.getKeyName(code))

    @dbus.service.method(dbus_interface = "hu.varadiistvan.JSProgListener",
                         in_signature = "uq", out_signature = "")
    def keyReleased(self, joystickID, code):
        """Called when a key is released."""
        print "Released key %d (0x%03x, %s)" % \
              (code, code, GetJoysticks.getKeyName(code))

    @dbus.service.method(dbus_interface = "hu.varadiistvan.JSProgListener",
                         in_signature = "uqi", out_signature = "")
    def axisChanged(self, joystickID, code, value):
        """Called when the value of an axis has changed."""
        print "Axis %d (0x%03x, %s) changed to %d" % \
              (code, code, GetJoysticks.getAxisName(code), value)

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

        path = "/hu/varadiistvan/JSProgListener/%d" % (pid,)
        listener = JSProgListener(connection, path)

        if jsprog.startMonitor(int(args.id), name.get_name(), path):
            mainloop = MainLoop()
            mainloop.run()
        else:
            print >> sys.stderr, "Could not start monitoring the joystick, perhaps the ID is wrong."

#------------------------------------------------------------------------------

def makeCommandFun(clazz):
    return lambda _args : clazz

#------------------------------------------------------------------------------

if __name__ == "__main__":
    mainParser = argparse.ArgumentParser(prog = "jsprog",
                                     description = "Command-line interface for the JSProg daemon")

    subParsers = mainParser.add_subparsers(title = "commands",
                                           description = "the commands the program accepts")

    for clazz in [GetJoysticks, LoadProfile, Monitor, MonitorControls]:
        parser = clazz.addParser(subParsers)
        parser.set_defaults(func = makeCommandFun(clazz))

    args = mainParser.parse_args(sys.argv[1:])

    #try:
    connection = SessionBus(mainloop = DBusGMainLoop())
    args.func(args).execute(connection, args)
    #except Exception, e:
    #    print str(e)
