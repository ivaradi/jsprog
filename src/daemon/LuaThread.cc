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

#include "LuaState.h"
#include "LuaRunner.h"
#include "Log.h"

#include <cassert>

//------------------------------------------------------------------------------

LuaThread::Owner::~Owner()
{
    LuaRunner& luaRunner = LuaRunner::get();
    while(!threads.empty()) {
        LuaThread* luaThread = *threads.begin();
        luaRunner.deleteThread(luaThread);
    }
    assert(previousThread==0);
    assert(lastThread==0);
}

//------------------------------------------------------------------------------

void LuaThread::Owner::deleteAllThreads()
{
    LuaRunner& luaRunner = LuaRunner::get();

    threads_t::iterator i = threads.begin();
    while(i!=threads.end()) {
        threads_t::iterator j = i++;
        LuaThread* luaThread = *j;
        if (!luaRunner.isCurrent(luaThread)) {
            luaRunner.deleteThread(luaThread);
        }
    }
}

//------------------------------------------------------------------------------

void LuaThread::Owner::deletePreviousThread()
{
    if (previousThread==0) return;

    LuaRunner& luaRunner = LuaRunner::get();
    if (!luaRunner.isCurrent(previousThread)) {
        luaRunner.deleteThread(previousThread);
    }
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

LuaThread::LuaThread(Owner& owner, LuaState& luaState, 
                     const std::string& functionName,
                     int eventType, int eventCode, int eventValue) :
    owner(owner),
    luaState(luaState),
    L(luaState.newThread()),
    functionName(functionName),
    eventType(eventType),
    eventCode(eventCode),
    eventValue(eventValue),
    timeout(INVALID_MILLIS)
{
    owner.threads.insert(this);
    owner.previousThread = owner.lastThread;
    owner.lastThread = this;
}

//------------------------------------------------------------------------------

LuaThread::~LuaThread()
{
    if (owner.lastThread==this) owner.lastThread = 0;
    if (owner.previousThread==this) owner.previousThread = 0;
    owner.threads.erase(this);
    luaState.deleteThread(L);    
}

//------------------------------------------------------------------------------

bool LuaThread::start()
{
    timeout = currentTimeMillis();

    lua_getglobal(L, functionName.c_str());
    if (lua_isnil(L, 1)) {
        Log::debug("there is no function named '%s'\n", functionName.c_str());
        return false;
    }

    lua_pushinteger(L, eventType);
    lua_pushinteger(L, eventCode);
    lua_pushinteger(L, eventValue);    

    return doResume(3);
}

//------------------------------------------------------------------------------

bool LuaThread::doResume(int narg)
{
    int result = lua_resume(L, 0, narg);
    if (result==LUA_YIELD) {
        int isnum = 0;
        int delay = lua_tointegerx(L, -1, &isnum);
        if (isnum) {
            timeout += delay;
            return true;
        } else {
            Log::warning("failed to execute %s(%d, %d, %d): non-integer yield value\n",
                         functionName.c_str(), eventType, eventCode, eventValue);
            return false;
        }
    } else {
        if (result!=LUA_OK) {
            Log::warning("failed to execute %s(%d, %d, %d): %s\n",
                         functionName.c_str(), eventType, eventCode, eventValue,
                         lua_tostring(L, -1));
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

