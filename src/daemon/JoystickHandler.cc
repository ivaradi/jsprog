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
#include "Key.h"
#include "Axis.h"
#include "UInput.h"
#include "LuaThread.h"
#include "LuaRunner.h"
#include "DBusAdaptor.h"
#include "Log.h"

#include <lwt/EPoll.h>
#include <lwt/util.h>

#include <linux/input.h>

//------------------------------------------------------------------------------

using lwt::EPoll;

using std::string;

//------------------------------------------------------------------------------

void JoystickHandler::run()
{
    LuaRunner& luaRunner = LuaRunner::get();
    LuaState& luaState = joystick->getLuaState();
    DBusAdaptor& dbusAdaptor = DBusAdaptor::get();

    dbusAdaptor.sendJoystickAdded(*joystick);

    char buf[1024];
    while(true) {
        ssize_t length = joystick->read(buf, sizeof(buf));
        if (length<=0) break;

        for(ssize_t offset = 0; offset<length; offset += sizeof(input_event) )
        {
            struct input_event* event =
                reinterpret_cast<struct input_event*>(buf + offset);
            if (event->type!=0 && (event->type!=0x03 || event->code!=0x05)) {
                Log::debug("type=0x%04x, code=0x%04x, value=%d\n",
                           (unsigned)event->type, (unsigned)event->code,
                           event->value);
                Control* control = 0;
                if (event->type==EV_KEY) {
                    Key* key = joystick->findKey(event->code);
                    if (key!=0) {
                        key->setPressed(event->value!=0);
                        control = key;
                        if (event->value==0) {
                            dbusAdaptor.sendKeyReleased(joystick->getID(),
                                                        event->code);
                        } else {
                            dbusAdaptor.sendKeyPressed(joystick->getID(),
                                                       event->code);
                        }
                    }
                } else if (event->type==EV_ABS) {
                    Axis* axis = joystick->findAxis(event->code);
                    if (axis!=0) {
                        axis->setValue(event->value);
                        dbusAdaptor.sendAxisChanged(joystick->getID(),
                                                    event->code,
                                                    event->value);
                        control = axis;
                    }
                }

                if (control==0) {
                    if (event->type==EV_KEY || event->type==EV_ABS) {
                        Log::warning("event arrived for unknown %s 0x%04x\n",
                                     (event->type==EV_KEY) ? "key" : "axis",
                                     event->code);
                    }
                } else {
                    const string& luaHandlerName = control->getLuaHandlerName();
                    if (!luaHandlerName.empty()) {
                        luaRunner.newThread(*control, luaState, luaHandlerName,
                                            event->type, event->code,
                                            event->value);
                    }
                }
            }

        }
    }

    Log::info("joystick is gone, quitting...\n");
    dbusAdaptor.sendJoystickRemoved(*joystick);
    EPoll::get().destroy(joystick);
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
