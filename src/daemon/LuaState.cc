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

#include "LuaState.h"

#include "UInput.h"
#include "Log.h"

extern "C" {
#include <lauxlib.h>
}

//------------------------------------------------------------------------------

const char* const LuaState::GLOBAL_LUASTATE = "jsprog_luastate";

const char* const LuaState::GLOBAL_THREADS = "jsprog_threads";

const char* const LuaState::GLOBAL_DELAY = "jsprog_delay";

const char* const LuaState::GLOBAL_PRESSKEY = "jsprog_presskey";

const char* const LuaState::GLOBAL_RELEASEKEY = "jsprog_releasekey";

//------------------------------------------------------------------------------

LuaState* LuaState::get(lua_State* L)
{
    lua_getglobal(L, GLOBAL_LUASTATE);
    LuaState* luaState = reinterpret_cast<LuaState*>(lua_touserdata(L, 1));
    lua_pop(L, 1);
    return luaState;
}

//------------------------------------------------------------------------------

int LuaState::delay(lua_State* L)
{
    lua_yield(L, 1);
    return 0;
}

//------------------------------------------------------------------------------

int LuaState::presskey(lua_State* L)
{
    int numArguments = lua_gettop(L);
    if (numArguments!=1) {        
        Log::warning("%s called with %d arguments\n", GLOBAL_PRESSKEY, numArguments);
        if (numArguments<1) return 0;
    }
    
    int isnum = 0;
    int key = lua_tointegerx(L, 1, &isnum);
    if (isnum) {
        UInput::get().pressKey(key);
    } else {
        Log::warning("%s called with a non-integer argument\n", GLOBAL_PRESSKEY);
    }
    return 0;
}

//------------------------------------------------------------------------------

int LuaState::releasekey(lua_State* L)
{
    int numArguments = lua_gettop(L);
    if (numArguments!=1) {        
        Log::warning("%s called with %d arguments\n", 
                     GLOBAL_RELEASEKEY, numArguments);
        if (numArguments<1) return 0;
    }
    
    int isnum = 0;
    int key = lua_tointegerx(L, 1, &isnum);
    if (isnum) {
        UInput::get().releaseKey(key);
    } else {
        Log::warning("%s called with a non-integer argument\n", GLOBAL_RELEASEKEY);
    }
    return 0;
}

//------------------------------------------------------------------------------

LuaState::LuaState(Joystick& joystick) :
    joystick(joystick),
    L(luaL_newstate())
{
    static const char* const program =
"jsprog_event_key_012c = function(type, code, value)\n"
"   if value ~= 0 then\n"
"       local count=0\n"
"       while count<20 do\n"        
"         jsprog_presskey(34)\n"
"         jsprog_releasekey(34)\n"
"         jsprog_delay(500)\n"
"         count = count+1\n"
"       end\n"
"   end\n"
"end\n"
"jsprog_event_key_012a = function(type, code, value)\n"
"   if value ~= 0 then\n"
"       local count=0\n"
"       while count<30 do\n"        
"         jsprog_presskey(30)\n"
"         jsprog_releasekey(30)\n"
"         jsprog_delay(333)\n"
"         count = count+1\n"
"       end\n"
"   end\n"
"end\n";

    lua_pushlightuserdata(L, this);
    lua_setglobal(L, GLOBAL_LUASTATE);

    lua_pushcfunction(L, &delay);
    lua_setglobal(L, GLOBAL_DELAY);

    lua_pushcfunction(L, &presskey);
    lua_setglobal(L, GLOBAL_PRESSKEY);

    lua_pushcfunction(L, &releasekey);
    lua_setglobal(L, GLOBAL_RELEASEKEY);

    lua_newtable(L);
    lua_setglobal(L, GLOBAL_THREADS);

    luaL_loadstring(L, program);
    int result = lua_pcall(L, 0, LUA_MULTRET, 0);
    if (result!=LUA_OK) {
        Log::error("failed to run script: %s\n", lua_tostring(L, -1));
    }    
}

//------------------------------------------------------------------------------

LuaState::~LuaState()
{
    lua_close(L);
}

//------------------------------------------------------------------------------

lua_State* LuaState::newThread()
{
    lua_getglobal(L, GLOBAL_THREADS);
    lua_State* thread  = lua_newthread(L);
    lua_pushinteger(L, 1);
    lua_settable(L, 1);
    lua_pop(L, 1);
    return thread;
}

//------------------------------------------------------------------------------

void LuaState::deleteThread(lua_State* thread)
{
    lua_settop(thread, 0);
    lua_getglobal(thread, GLOBAL_THREADS);
    lua_pushthread(thread);
    lua_pushnil(thread);
    lua_settable(thread, 1);
    lua_pop(thread, 1);
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

