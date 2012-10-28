// Copyright (c) 2012 by István Váradi

// This file is part of JSProg, a joystick programming utility

// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

//------------------------------------------------------------------------------

#include "Axis.h"

//------------------------------------------------------------------------------

const char* const axisNames[ABS_CNT] = {
    // 0 (0x000)
    "ABS_X",
    "ABS_Y",
    "ABS_Z",
    "ABS_RX",
    "ABS_RY",
    "ABS_RZ",
    "ABS_THROTTLE",
    "ABS_RUDDER",
    // 8 (0x008)
    "ABS_WHEEL",
    "ABS_GAS",
    "ABS_BRAKE",
    "ABS_0X00B",
    "ABS_0X00C",
    "ABS_0X00D",
    "ABS_0X00E",
    "ABS_0X00F",
    // 16 (0x010)
    "ABS_HAT0X",
    "ABS_HAT0Y",
    "ABS_HAT1X",
    "ABS_HAT1Y",
    "ABS_HAT2X",
    "ABS_HAT2Y",
    "ABS_HAT3X",
    "ABS_HAT3Y",
    // 24 (0x018)
    "ABS_PRESSURE",
    "ABS_DISTANCE",
    "ABS_TILT_X",
    "ABS_TILT_Y",
    "ABS_TOOL_WIDTH",
    "ABS_0X01D",
    "ABS_0X01E",
    "ABS_0X01F",
    // 32 (0x020)
    "ABS_VOLUME",
    "ABS_0X021",
    "ABS_0X022",
    "ABS_0X023",
    "ABS_0X024",
    "ABS_0X025",
    "ABS_0X026",
    "ABS_0X027",
    // 40 (0x028)
    "ABS_MISC",
    "ABS_0X029",
    "ABS_0X02A",
    "ABS_0X02B",
    "ABS_0X02C",
    "ABS_0X02D",
    "ABS_0X02E",
    "ABS_MT_SLOT",
    // 48 (0x030)
    "ABS_MT_TOUCH_MAJOR",
    "ABS_MT_TOUCH_MINOR",
    "ABS_MT_WIDTH_MAJOR",
    "ABS_MT_WIDTH_MINOR",
    "ABS_MT_ORIENTATION",
    "ABS_MT_POSITION_X",
    "ABS_MT_POSITION_Y",
    "ABS_MT_TOOL_TYPE",
    // 56 (0x038)
    "ABS_MT_BLOB_ID",
    "ABS_MT_TRACKING_ID",
    "ABS_MT_PRESSURE",
    "ABS_MT_DISTANCE",
};

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

