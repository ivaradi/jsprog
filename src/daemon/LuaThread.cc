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

#include "LuaThread.h"

#include "Control.h"
#include "Joystick.h"
#include "LuaState.h"
#include "LuaRunner.h"
#include "Log.h"

#include <cassert>

//------------------------------------------------------------------------------

LuaThread::LuaThread(Control& control, LuaState& luaState) :
    control(control),
    luaState(luaState),
    L(luaState.newThread(this)),
    timeout(INVALID_MILLIS),
    cancellable(false),
    cancelled(false)
{
    luaState.pushThreadFunction(L);
    control.getJoystick().addLuaThread(this);
}

//------------------------------------------------------------------------------

LuaThread::~LuaThread()
{
    control.getJoystick().removeLuaThread(this);
    luaState.deleteThread(L);
}

//------------------------------------------------------------------------------

bool LuaThread::start()
{
    timeout = currentTimeMillis();
    return doResume();
}

//------------------------------------------------------------------------------

bool LuaThread::cancelDelay()
{
    if (cancellable) {
        cancelled = true;
        timeout = currentTimeMillis();
    }
    return cancelled;
}

//------------------------------------------------------------------------------

bool LuaThread::resume()
{
    lua_pushboolean(L, !cancelled);
    return doResume(1);
}

//------------------------------------------------------------------------------

bool LuaThread::doResume(int narg)
{
    cancelled = false;
    cancellable = false;
    int result = lua_resume(L, 0, narg);
    if (result==LUA_YIELD) {
        int isnum = 0;
        int yieldReason = lua_tointegerx(L, -2, &isnum);
        if (isnum) {
            if (yieldReason==YIELD_DELAY || yieldReason==YIELD_CANCELLABLE_DELAY) {
                isnum = 0;
                int delay = lua_tointegerx(L, -1, &isnum);
                if (isnum) {
                    if (yieldReason==YIELD_CANCELLABLE_DELAY) {
                        cancellable = true;
                        if (!cancelled) {
                            timeout += delay;
                        }
                        return true;
                    } else {
                        timeout += delay;
                        return true;
                    }
                } else {
                    Log::warning("failed to execute thread: non-integer yield value\n");
                    return false;
                }
            } else {
                Log::warning("failed to execute thread: unknown yield reason: %d\n", yieldReason);
                return false;
            }
        } else {
            Log::warning("failed to execute thread: non-integer yield value for the yield reason\n");
            return false;
        }
    } else {
        if (result!=LUA_OK) {
            Log::warning("failed to execute thread: %s\n", lua_tostring(L, -1));
        }
        return false;
    }
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
