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

#include "Control.h"

#include "LuaRunner.h"

#include <cstdio>

//------------------------------------------------------------------------------

Control::~Control()
{
    LuaRunner& luaRunner = LuaRunner::get();
    while(!luaThreads.empty()) {
        LuaThread* luaThread = *luaThreads.begin();
        luaRunner.deleteThread(luaThread);
    }
    assert(previousLuaThread==0);
    assert(lastLuaThread==0);
}

//------------------------------------------------------------------------------

void Control::setupLuaHandlerName(type_t type, int code)
{
    char buf[64];
    snprintf(buf, sizeof(buf), "_jsprog_event_%s_%04x",
             (type==KEY) ? "key" : "axis", code);
    luaHandlerName = buf;
}

//------------------------------------------------------------------------------

void Control::deleteAllLuaThreads()
{
    LuaRunner& luaRunner = LuaRunner::get();

    luaThreads_t::iterator i = luaThreads.begin();
    while(i!=luaThreads.end()) {
        luaThreads_t::iterator j = i++;
        LuaThread* luaThread = *j;
        if (!luaRunner.isCurrent(luaThread)) {
            luaRunner.deleteThread(luaThread);
        }
    }
}

//------------------------------------------------------------------------------

void Control::deletePreviousLuaThread()
{
    if (previousLuaThread==0) return;

    LuaRunner& luaRunner = LuaRunner::get();
    if (!luaRunner.isCurrent(previousLuaThread)) {
        luaRunner.deleteThread(previousLuaThread);
    }
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
