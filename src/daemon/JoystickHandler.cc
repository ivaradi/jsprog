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

#include "JoystickHandler.h"

#include "Joystick.h"
#include "UInput.h"
#include "Log.h"

#include <lwt/EPoll.h>
#include <lwt/util.h>

#include <linux/input.h>

//------------------------------------------------------------------------------

using lwt::EPoll;

//------------------------------------------------------------------------------

void JoystickHandler::run()
{
    UInput& uinput = UInput::get();

    int mouseXLastValue = 8;
    int mouseYLastValue = 8;
    
    char buf[1024];
    while(true) {
        bool timedOut = false;
        millis_t timeout = currentTimeMillis() + 25;
        ssize_t length = joystick->timedRead(timedOut, buf, sizeof(buf), 
                                             timeout);
        

        for(ssize_t offset = 0; offset<length; offset += sizeof(input_event) )
        {
            struct input_event* event =
                reinterpret_cast<struct input_event*>(buf + offset);
            if (event->type!=0 && (event->type!=0x03 || event->code!=0x05)) {
                Log::debug("type=0x%04x, code=0x%04x, value=%d\n", 
                           (unsigned)event->type, (unsigned)event->code, 
                           event->value);
                if (event->type==EV_KEY && event->code==0x02de) {
                    if (event->value==0) uinput.releaseKey(BTN_LEFT);
                    else uinput.pressKey(BTN_LEFT);
                } else if (event->type==EV_KEY && event->value!=0) {
                    if (event->code==0x012c) {
                        Log::debug("sending KEY_G\n");
                        uinput.pressKey(KEY_G);
                        uinput.releaseKey(KEY_G);
                    } else if (event->code==0x02e0) {
                        uinput.moveRelative(REL_WHEEL, -1);
                    } else if (event->code==0x02e1) {
                        uinput.moveRelative(REL_WHEEL, 1);
                    } else if (event->code==0x02de) {
                    } 
                } else if (event->type==EV_ABS) {
                    if (event->code==0x28) {
                        mouseXLastValue = event->value;
                        if (mouseXLastValue>10 || mouseXLastValue<5) {
                            uinput.moveRelative(REL_X, mouseXLastValue-8);
                        }
                    } else if (event->code==0x29) {
                        mouseYLastValue = event->value;
                        if (mouseYLastValue>10 || mouseYLastValue<5) {
                            uinput.moveRelative(REL_Y, mouseYLastValue-8);
                        }
                    }
                }
                uinput.synchronize();
            }

        }

        if (mouseXLastValue>8) {
            uinput.moveRelative(REL_X, 2+(mouseXLastValue-9)*2);
        } else if (mouseXLastValue<7) {
            uinput.moveRelative(REL_X, -2-(6-mouseXLastValue)*2);
        }
        if (mouseYLastValue>8) {
            uinput.moveRelative(REL_Y, 2+(mouseYLastValue-9)*2);
        } else if (mouseYLastValue<7) {
            uinput.moveRelative(REL_Y, -2-(6-mouseYLastValue)*2);
        }
        uinput.synchronize();
    }

    Log::info("joystick is gone, quitting...\n");
    EPoll::get().destroy(joystick);
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

