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
#include "LuaRunner.h"
#include "Joystick.h"
#include "Key.h"
#include "Axis.h"
#include "Relative.h"
#include "Log.h"

extern "C" {
#include <lualib.h>
#include <lauxlib.h>
}

//------------------------------------------------------------------------------

namespace {

//------------------------------------------------------------------------------

/**
 * A function to process the argument list of functions that expect
 * only an integer identifying a control.
 */
int handleControlFunction(lua_State* L, const char* name)
{
    int numArguments = lua_gettop(L);
    if (numArguments!=1) {
        Log::warning("%s called with %d arguments\n", name, numArguments);
        if (numArguments<1) return -1;
    }

    int isnum = 0;
    int code = lua_tointegerx(L, 1, &isnum);
    if (isnum) {
        return code;
    } else {
        Log::warning("%s called with a non-integer argument\n", name);
        return -1;
    }
}

//------------------------------------------------------------------------------

} /* anonymous namespace */

//------------------------------------------------------------------------------

const char* const LuaState::GLOBAL_LUASTATE = "jsprog_luastate";

const char* const LuaState::GLOBAL_THREADS = "jsprog_threads";

const char* const LuaState::GLOBAL_THREADFUNCTION = "jsprog_threadfunction";

const char* const LuaState::GLOBAL_DELAY = "jsprog_delay";

const char* const LuaState::GLOBAL_ISKEYPRESSED = "jsprog_iskeypressed";

const char* const LuaState::GLOBAL_GETABS = "jsprog_getabs";

const char* const LuaState::GLOBAL_GETABSMIN = "jsprog_getabsmin";

const char* const LuaState::GLOBAL_GETABSMAX = "jsprog_getabsmax";

const char* const LuaState::GLOBAL_PRESSKEY = "jsprog_presskey";

const char* const LuaState::GLOBAL_RELEASEKEY = "jsprog_releasekey";

const char* const LuaState::GLOBAL_MOVEREL = "jsprog_moverel";

const char* const LuaState::GLOBAL_STARTTHREAD = "jsprog_startthread";

const char* const LuaState::GLOBAL_KILLTHREAD = "jsprog_killthread";

//------------------------------------------------------------------------------

LuaState& LuaState::get(lua_State* L)
{
    lua_getglobal(L, GLOBAL_LUASTATE);
    LuaState* luaState = reinterpret_cast<LuaState*>(lua_touserdata(L, -1));
    lua_pop(L, 1);
    return *luaState;
}

//------------------------------------------------------------------------------

int LuaState::delay(lua_State* L)
{
    lua_yield(L, 1);
    return 0;
}

//------------------------------------------------------------------------------

int LuaState::iskeypressed(lua_State* L)
{
    int code = handleControlFunction(L, GLOBAL_ISKEYPRESSED);
    if (code>=0) {
        LuaState& luaState = LuaState::get(L);
        Key* key = luaState.joystick.findKey(code);
        if (key!=0) {
            lua_pushboolean(L, key->isPressed());
        } else {
            lua_pushinteger(L, 0);
        }
        return 1;
    } else {
        return 0;
    }
}

//------------------------------------------------------------------------------

int LuaState::getabs(lua_State* L)
{
    int code = handleControlFunction(L, GLOBAL_GETABS);
    if (code>=0) {
        LuaState& luaState = LuaState::get(L);
        Axis* axis = luaState.joystick.findAxis(code);
        if (axis!=0) {
            lua_pushinteger(L, axis->getValue());
        } else {
            lua_pushinteger(L, 0);
        }
        return 1;
    } else {
        return 0;
    }
}

//------------------------------------------------------------------------------

int LuaState::getabsmin(lua_State* L)
{
    int code = handleControlFunction(L, GLOBAL_GETABSMIN);
    if (code>=0) {
        LuaState& luaState = LuaState::get(L);
        Axis* axis = luaState.joystick.findAxis(code);
        if (axis!=0) {
            lua_pushinteger(L, axis->getMinimum());
        } else {
            lua_pushinteger(L, 0);
        }
        return 1;
    } else {
        return 0;
    }
}

//------------------------------------------------------------------------------

int LuaState::getabsmax(lua_State* L)
{
    int code = handleControlFunction(L, GLOBAL_GETABSMAX);
    if (code>=0) {
        LuaState& luaState = LuaState::get(L);
        Axis* axis = luaState.joystick.findAxis(code);
        if (axis!=0) {
            lua_pushinteger(L, axis->getMaximum());
        } else {
            lua_pushinteger(L, 0);
        }
        return 1;
    } else {
        return 0;
    }
}

//------------------------------------------------------------------------------

int LuaState::presskey(lua_State* L)
{
    int code = handleControlFunction(L, GLOBAL_PRESSKEY);
    if (code>=0) {
        UInput::get().pressKey(code);
        LuaState::get(L).joystick.keyPressed(code);
    }
    return 0;
}

//------------------------------------------------------------------------------

int LuaState::releasekey(lua_State* L)
{
    int code = handleControlFunction(L, GLOBAL_RELEASEKEY);
    if (code>=0) {
        UInput::get().releaseKey(code);
        LuaState::get(L).joystick.keyReleased(code);
    }
    return 0;
}

//------------------------------------------------------------------------------

int LuaState::moverel(lua_State* L)
{
    int numArguments = lua_gettop(L);
    if (numArguments<2) {
        luaL_error(L, "%s called with too few arguments (%d)\n",
                   GLOBAL_MOVEREL, numArguments);
    } else if (numArguments>2) {
        Log::warning("%s called with too many arguments (%d), ignoring the ones after the first two\n",
                     GLOBAL_MOVEREL, numArguments);
    }

    int isnum = 0;
    int code = lua_tointegerx(L, 1, &isnum);
    if (!isnum) {
        luaL_error(L, "%s called with a non-integer first argument\n",
                   GLOBAL_MOVEREL);
    }

    int value = lua_tointegerx(L, 2, &isnum);
    if (!isnum) {
        luaL_error(L, "%s called with a non-integer second argument\n",
                   GLOBAL_MOVEREL);
    }

    UInput::get().moveRelative(code, value);

    return 0;
}

//------------------------------------------------------------------------------

int LuaState::startthread(lua_State* L)
{
    int numArguments = lua_gettop(L);
    if (numArguments<1) {
        luaL_error(L, "%s called with too few arguments (%d)\n",
                   GLOBAL_STARTTHREAD, numArguments);
    } else if (numArguments>1) {
        Log::warning("%s called with too many arguments (%d), ignoring the ones after the first two\n",
                     GLOBAL_STARTTHREAD, numArguments);
    }

    lua_setglobal(L, GLOBAL_THREADFUNCTION);

    LuaRunner::get().newThread(LuaState::get(L));

    return 0;
}

//------------------------------------------------------------------------------

LuaState::LuaState(Joystick& joystick) :
    joystick(joystick),
    L(luaL_newstate())
{
    initialize();
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

bool LuaState::loadProfile(const std::string& profileCode)
{
    reset();

    int result = luaL_dostring(L, profileCode.c_str());
    if (result!=LUA_OK) {
        Log::error("LuaState::loadProfile: failed to run script: %s\n",
                   lua_tostring(L, -1));
    }
    lua_settop(L, 0);
    return result==LUA_OK;
}

//------------------------------------------------------------------------------

void LuaState::reset()
{
    lua_close(L);
    L = luaL_newstate();
    initialize();
}

//------------------------------------------------------------------------------

void LuaState::initialize()
{
    luaL_openlibs(L);

    lua_pushlightuserdata(L, this);
    lua_setglobal(L, GLOBAL_LUASTATE);

    lua_pushcfunction(L, &delay);
    lua_setglobal(L, GLOBAL_DELAY);

    lua_pushcfunction(L, &iskeypressed);
    lua_setglobal(L, GLOBAL_ISKEYPRESSED);

    lua_pushcfunction(L, &getabs);
    lua_setglobal(L, GLOBAL_GETABS);

    lua_pushcfunction(L, &getabsmin);
    lua_setglobal(L, GLOBAL_GETABSMIN);

    lua_pushcfunction(L, &getabsmax);
    lua_setglobal(L, GLOBAL_GETABSMAX);

    lua_pushcfunction(L, &presskey);
    lua_setglobal(L, GLOBAL_PRESSKEY);

    lua_pushcfunction(L, &releasekey);
    lua_setglobal(L, GLOBAL_RELEASEKEY);

    lua_pushcfunction(L, &moverel);
    lua_setglobal(L, GLOBAL_MOVEREL);

    lua_pushcfunction(L, &startthread);
    lua_setglobal(L, GLOBAL_STARTTHREAD);

    lua_newtable(L);
    lua_setglobal(L, GLOBAL_THREADS);

    lua_pushnil(L);
    lua_setglobal(L, GLOBAL_THREADFUNCTION);

    for(int i = 0; i<KEY_CNT; ++i) {
        const char* name = Key::toString(i);
        if (name!=0) {
            char buf[128];
            snprintf(buf, sizeof(buf), "jsprog_%s", name);
            lua_pushinteger(L, i);
            lua_setglobal(L, buf);
        }
    }

    for(int i = 0; i<REL_CNT; ++i) {
        const char* name = Relative::toString(i);
        if (name!=0) {
            char buf[128];
            snprintf(buf, sizeof(buf), "jsprog_%s", name);
            lua_pushinteger(L, i);
            lua_setglobal(L, buf);
        }
    }

    lua_settop(L, 0);
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
