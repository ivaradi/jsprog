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

#ifndef LUASTATE_H
#define LUASTATE_H
//------------------------------------------------------------------------------

extern "C" {
#include <lua.h>
}

//------------------------------------------------------------------------------

class Joystick;

//------------------------------------------------------------------------------

/**
 * An independent Lua state belonging to a Joystick instance. It
 * contains some global functions and variables, some of which are
 * specific to that joystick.
 */
class LuaState
{
private:
    /**
     * The global name for the lua state.
     */
    static const char* const GLOBAL_LUASTATE;

    /**
     * The global name for the table of the threads.
     */
    static const char* const GLOBAL_THREADS;

    /**
     * Global name: delay
     */
    static const char* const GLOBAL_DELAY;

    /**
     * Global name: presskey
     */
    static const char* const GLOBAL_PRESSKEY;

    /**
     * Global name: releasekey
     */
    static const char* const GLOBAL_RELEASEKEY;

private:
    /**
     * Get the LuaState object from the given state.
     */
    static LuaState* get(lua_State* L);

    /**
     * A function that causes a delay in the thread's execution
     */
    static int delay(lua_State* L);
    
    /**
     * A function that sends a key press event.
     */
    static int presskey(lua_State* L);
    
    /**
     * A function that sends a key release event.
     */
    static int releasekey(lua_State* L);
    
    /**
     * The joystick that this state belongs to.
     */
    Joystick& joystick;

    /**
     * The actual Lua state.
     */
    lua_State* L;

public:
    /**
     * Construct the Lua state.
     */
    LuaState(Joystick& joystick);

    /**
     * Destroy the Lua state. It destroy's the real Lua state as well.
     */
    ~LuaState();

    /**
     * Create a new Lua thread. The thread will be added to a global
     * table as a key to avoid its removal.
     */
    lua_State* newThread();

    /**
     *Delete a Lua thread. It will be removed from the global table.
     */
    void deleteThread(lua_State* thread);
};

//------------------------------------------------------------------------------
#endif // LUASTATE_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

