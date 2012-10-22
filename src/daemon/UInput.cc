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

#include "UInput.h"

#include "Log.h"

#include <cstring>

#include <linux/uinput.h>

//------------------------------------------------------------------------------

UInput* UInput::instance = 0;

//------------------------------------------------------------------------------

UInput::UInput() :
    ThreadedFD(open("/dev/uinput", O_WRONLY | O_NONBLOCK))
{
    if (fd<0) {
        Log::error("UInput:: failed to open the device: errno=%d\n", errno);
        return;
    }

    ioctl(UI_SET_EVBIT, EV_SYN);
    ioctl(UI_SET_EVBIT, EV_KEY);
    ioctl(UI_SET_KEYBIT, KEY_G);

    struct uinput_user_dev uidev;
    memset(&uidev, 0, sizeof(uidev));

    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "JSProg keyboard & mouse");

    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 0x1111;
    uidev.id.product = 0x1111;
    uidev.id.version = 1;

    write(&uidev, sizeof(uidev));

    ioctl(UI_DEV_CREATE, 0);

    instance = this;

    memset(&inputEvent, 0, sizeof(inputEvent));
}

//------------------------------------------------------------------------------

UInput::~UInput()
{
    instance = 0;
}

//------------------------------------------------------------------------------

bool UInput::ioctl(int request, long data)
{
    if (!isValid()) return false;

    if (ThreadedFD::ioctl(request, data)<0) {
        Log::error("UInput: failed to perform ioctl(0x%08x, 0x%08lx): errno=%d\n",
                   request, data, errno);
        close();
        return false;
    }
    return true;
}

//------------------------------------------------------------------------------

bool UInput::write(const void* buf, size_t count)
{
    if (!isValid()) return false;
    if (ThreadedFD::write(buf, count)!=static_cast<ssize_t>(count)) {
        Log::error("UInput: failed to write to device: errno=%d\n",
                   errno);
        close();
        return false;
    }
    return true;
}

//------------------------------------------------------------------------------

inline void UInput::sendEvent(unsigned type, unsigned code, unsigned value)
{
    inputEvent.type = type;
    inputEvent.code = code;
    inputEvent.value = value;
    write(&inputEvent, sizeof(inputEvent));
}

//------------------------------------------------------------------------------

void UInput::sendKey(unsigned code, bool press)
{
    sendEvent(EV_KEY, code, press ? 1 : 0);
    sendEvent(EV_SYN); 
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

