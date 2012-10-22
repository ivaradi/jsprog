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

#include <linux/input.h>

//------------------------------------------------------------------------------

using lwt::EPoll;

//------------------------------------------------------------------------------

void JoystickHandler::run()
{
    UInput& uinput = UInput::get();

    char buf[1024];
    ssize_t length = joystick->read(buf, sizeof(buf));
    while(length>0) {
        for(ssize_t offset = 0; offset<length; offset += sizeof(input_event) )
        {
            struct input_event* event =
                reinterpret_cast<struct input_event*>(buf + offset);
            if (event->type!=0 && (event->type!=0x03 || event->code!=0x05)) {
                Log::debug("type=0x%04x, code=0x%04x, value=%d\n", 
                           (unsigned)event->type, (unsigned)event->code, 
                           event->value);
                if (event->type==EV_KEY && event->code==0x012c) {
                    Log::debug("sending KEY_G\n");
                    if (event->value==1) {
                        uinput.pressKey(KEY_G);
                        uinput.releaseKey(KEY_G);
                    }
                }
            }
        }
        length = joystick->read(buf, sizeof(buf));
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

