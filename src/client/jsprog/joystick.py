#-------------------------------------------------------------------------------

from functools import total_ordering

#-------------------------------------------------------------------------------

## @package jsprog.joystick
#
# The handling of the joysticks

#-------------------------------------------------------------------------------

@total_ordering
class InputID(object):
    """An input ID."""

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

    @staticmethod
    def getBusNameFor(busType):
        """Get the bus name for the given bus type."""
        return InputID._busNames.get(busType, "bus<%02x>" % (busType,))

    @staticmethod
    def findBusTypeFor(busName):
        """Get the bus type for the given name.

        If not found, return None."""
        for (type, name) in InputID._busNames.items():
            if name==busName:
                return type

        if busName.startswith("bus<") and busName.endsWith(">"):
            try:
                return int(busName[4:-1], 16)
            except:
                pass

        return None

    @staticmethod
    def fromArgs(args):
        """Construct an input ID from an array of arguments of a D-Bus
        message."""
        return InputID(int(args[0]), int(args[1]), int(args[2]), int(args[3]))

    def __init__(self, busType, vendor, product, version):
        """Construct the input ID from the given argument of a D-Bus
        message."""
        self._busType = busType
        self._vendor = vendor
        self._product = product
        self._version = version

    @property
    def busType(self):
        """Get the bus type."""
        return self._busType

    @property
    def busName(self):
        """Get the name of the bus."""
        return InputID.getBusNameFor(self._busType)

    @property
    def vendor(self):
        """Get the vendor ID"""
        return self._vendor

    @property
    def product(self):
        """Get the product ID"""
        return self._product

    @property
    def version(self):
        """Get the version"""
        return self._version

    def __cmp__(self, other):
        """Compare this input ID with another."""
        a = self._busType - other._busType
        if a==0:
            a = self._vendor - other._vendor
        if a==0:
            a = self._product - other._product
        if a==0:
            a = self._version - other._version
        return a

    def __eq__(self, other):
        """Equality comparison"""
        return self.__cmp__(other)==0

    def __lt__(self, other):
        """Less-than comparison"""
        return self.__cmp__(other)<0

    def __hash__(self):
        """Compute a hash of this object."""
        return (((((self._busType + 41) ^ \
                     self._vendor) + 41) ^ \
                      self._product) + 41) ^ \
                       self._version

    def __repr__(self):
        """Get a representation of the input ID"""
        if self._version:
            return "InputID(%s:%04x:%04x, %04x)" % \
                (self.busName, self._vendor, self._product, self._version)
        else:
            return "InputID(%s:%04x:%04x)" % \
                (self.busName, self._vendor, self._product)

    def __str__(self):
        """Get a string version of the input ID"""
        if self._version:
            return "%s:%04x:%04x (ver: %04x)" % \
                (self.busName, self._vendor, self._product, self._version)
        else:
            return "%s:%04x:%04x" % (self.busName, self._vendor, self._product)

#-------------------------------------------------------------------------------

class JoystickIdentity(object):
    """The identity of a joystick."""

    ## Constant for no match of joystick IDs
    MATCH_NONE = 0

    ## Constant for a full match of joystick IDs
    MATCH_FULL = 100

    @staticmethod
    def fromArgs(args):
        """Construct a joystick identity from the given D-Bus message
        arguments."""
        return JoystickIdentity(InputID.fromArgs(args[1]),
                                args[2], args[3],
                                args[4] if args[4] else None)

    def __init__(self, inputID, name, phys, uniq):
        """Construct the joystick identity."""
        self._inputID = inputID
        self._name = name
        self._phys = phys
        self._uniq = uniq

    @property
    def inputID(self):
        """Get the input ID of the joystick."""
        return self._inputID

    @property
    def name(self):
        """Get the name of the joystick."""
        return self._name

    @property
    def phys(self):
        """Get the physical location of the joystick."""
        return self._phys

    @property
    def uniq(self):
        """Get the unique identifier of the joystick."""
        return self._uniq

    @property
    def generic(self):
        """Get a generic version of this joystick identity.

        The physical location and the unique identifier are cleared."""
        return JoystickIdentity(self._inputID, self._name, None, None)

    def match(self, other):
        """Compute how much the joystick ID matches the other one.

        The joystick IDs match if the bus type, vendor and product of
        the input IDs and the names are the same. If these conditions
        do not hold, there is no match.

        If the unique identifiers also match, then the match is full.

        Otherwise extra score is given when the versions of the
        input ID match or when the physical locations match.

        @return a score, where the higher score means a better
        match. A score of 0 means no match."""
        if self._inputID._busType != other._inputID._busType or \
           self._inputID._vendor != other._inputID._vendor or \
           self._inputID._product != other._inputID._product or \
           self._name != other._name:
            return JoystickIdentity.MATCH_NONE

        if self._uniq is not None and self._uniq == other._uniq:
            return JoystickIdentity.MATCH_FULL

        score = 1

        if self._inputID._version == other._inputID._version:
            score += 1

        if self._phys == other._phys:
            score += 1

        return score

    def __repr__(self):
        """Get the string representation of the identity"""
        return "JoystickIdentity(%s, %s, %s, %s)" % \
            (repr(self._inputID), self._name, self._phys, self._uniq)

    def __str__(self):
        """Convert the identity to a string"""
        if self._uniq:
            return "%s (%s, %s, %s)" % (self._name, self._inputID,
                                        self._phys, self._uniq)
        elif self._phys:
            return "%s (%s, %s)" % (self._name, self._inputID, self._phys)
        else:
            return "%s (%s)" % (self._name, self._inputID)

#-------------------------------------------------------------------------------

class Key(object):
    """A key (button) on a joystick."""

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

    @staticmethod
    def getNameFor(code):
        """Get the name for the given code."""
        keyNames = Key._keyNames
        return keyNames[code] if code<len(keyNames) \
            else "KEY_0X%03X" % (code,)

    @staticmethod
    def findCodeFor(name):
        """Get the code for the given name.

        If not found, return None."""
        keyNames = Key._keyNames

        for i in range(0, len(keyNames)):
            if keyNames[i]==name:
                return i

        if name.startswith("KEY_0X"):
            try:
                return int(name[6:], 16)
            except:
                pass

        return None

    @staticmethod
    def fromArgs(args):
        """Get a key from the given arguments that are part of the
        arguments of a D-Bus message."""
        return Key(int(args[0]), pressed = int(args[1])!=0)

    @staticmethod
    def iterArgs(args):
        """Return an iterator of keys constructed from the given list
        of D-Bus message arguments."""
        for key in args:
            yield Key.fromArgs(key)

    @staticmethod
    def listArgs(args):
        """Return a list of keys constructed from the given list of
        D-Bus message arguments."""
        return list(Key.iterArgs(args))

    def __init__(self, code, pressed = False):
        """Construct the key with the given code and pressed state."""
        self._code = code
        self.pressed = pressed

    @property
    def code(self):
        """Get the code of the key."""
        return self._code

    @property
    def name(self):
        """Get the name of the key."""
        return Key.getNameFor(self._code)

    def __repr__(self):
        """Get the string representation of the key"""
        return "Key(0x%03x (%s), %s)" % \
            (self._code, Key.getNameFor(self._code),
             self.pressed)

    def __str__(self):
        """Convert the key to a string."""
        return "%s (0x%03x): %s" % \
            (Key.getNameFor(self._code), self._code,
             "pressed" if self.pressed else "released")

#-------------------------------------------------------------------------------

class Axis(object):
    """An axis of a joystick."""
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
    def getNameFor(code):
        """Get the name for the given code."""
        axisNames = Axis._axisNames
        return axisNames[code] if code<len(axisNames) \
            else "ABS_0X%03X" % (code,)

    @staticmethod
    def findCodeFor(name):
        """Get the code for the given name.

        If not found, return None."""
        axisNames = Axis._axisNames

        for i in range(0, len(axisNames)):
            if axisNames[i]==name:
                return i

        if name.startswith("AXIS_0X"):
            try:
                return int(name[7:], 16)
            except:
                pass

        return None

    @staticmethod
    def fromArgs(args):
        """Get an axis from the given arguments that are part of the
        arguments of a D-Bus message."""
        return Axis(int(args[0]), int(args[2]), int(args[3]),
                    value = int(args[1]))

    @staticmethod
    def iterArgs(args):
        """Return an iterator of axes constructed from the given list
        of D-Bus message arguments."""
        for axis in args:
            yield Axis.fromArgs(axis)

    @staticmethod
    def listArgs(args):
        """Return a list of axes constructed from the given list of
        D-Bus message arguments."""
        return list(Axis.iterArgs(args))

    def __init__(self, code, minimum, maximum, value = None):
        """Construct the axis with the given code, range and value."""
        self._code = code
        self._minimum = minimum
        self._maximum = maximum
        self.value = value

    @property
    def code(self):
        """Get the code of the axis."""
        return self._code

    @property
    def name(self):
        """Get the name of the axis."""
        return Axis.getNameFor(self._code)

    @property
    def minimum(self):
        """Get the minimum value of the axis."""
        return self._minimum

    @property
    def maximum(self):
        """Get the maximum value of the axis."""
        return self._maximum

    def __repr__(self):
        """Get the string representation of the axis"""
        return "Axis(0x%03x (%s), %d..%d, %d)" % \
            (self._code, Axis.getNameFor(self._code),
             self._minimum, self._maximum, self.value)

    def __str__(self):
        """Convert the axis to a string."""
        return "%s (0x%03x, %d..%d): %d" % \
            (Axis.getNameFor(self._code), self._code,
             self._minimum, self._maximum, self.value)

#-------------------------------------------------------------------------------

class Joystick(object):
    """A joystick."""
    @staticmethod
    def extractArgs(dbusArgs):
        """Extract the given D-Bus message arguments into a tuple of
        - the ID (numeric identifier) of the joystick
        - the identity of the joystick
        - the list of keys
        - the list of axes."""
        return (int(dbusArgs[0]), JoystickIdentity.fromArgs(dbusArgs),
                Key.listArgs(dbusArgs[5]), Axis.listArgs(dbusArgs[6]))

    @classmethod
    def fromArgs(clazz, dbusArgs, *args, **kwargs):
        """Construct a joystick object based on the given D-Bus
        message arguments and other optional ones."""
        (id, identity, keys, axes) = Joystick.extractArgs(dbusArgs)
        return clazz(id, identity, keys, axes, *args, **kwargs)

    def __init__(self, id, identity, keys, axes):
        """Construct the joystick with the given attributes."""
        self._id = id
        self._identity = identity
        self._keys = keys
        self._axes = axes

    @property
    def id(self):
        """Get the identifier of the joystick."""
        return self._id

    @property
    def identity(self):
        """Get the identity of the joystick."""
        return self._identity

    @property
    def keys(self):
        """Get the list of the keys (buttons) of the joystick."""
        return self._keys

    @property
    def iterKeys(self):
        """Get an iterator over the keys (buttons) of the joystick."""
        return iter(self._keys)

    @property
    def firstKey(self):
        """Get the first key, if any."""
        return self._keys[0] if self._keys else None

    @property
    def axes(self):
        """Get the list of the axes of the joystick."""
        return self._axes

    @property
    def iterAxes(self):
        """Get an iterator over the axes the joystick."""
        return iter(self._axes)

    @property
    def firstAxis(self):
        """Get the first axis, if any."""
        return self._axes[0] if self._axes else None

#-------------------------------------------------------------------------------
