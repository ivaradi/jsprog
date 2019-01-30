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

#include <string>
#include <map>

extern "C" {
#include <lua.h>
}

//------------------------------------------------------------------------------

class Joystick;
class LuaThread;

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
     * Type for a mapping of Lua thread states to our thread objects.
     */
    typedef std::map<lua_State*, LuaThread*> threads_t;

    /**
     * The global name for the lua state.
     */
    static const char* const GLOBAL_LUASTATE;

    /**
     * The global name for the table of the threads.
     */
    static const char* const GLOBAL_THREADS;

    /**
     * The global name for a variable containing the thread function to call.
     */
    static const char* const GLOBAL_THREADFUNCTION;

    /**
     * Global name: iskeypressed
     */
    static const char* const GLOBAL_ISKEYPRESSED;

    /**
     * Global name: getabs
     */
    static const char* const GLOBAL_GETABS;

    /**
     * Global name: getabsmin
     */
    static const char* const GLOBAL_GETABSMIN;

    /**
     * Global name: getabsmax
     */
    static const char* const GLOBAL_GETABSMAX;

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

    /**
     * Global name: moverel
     */
    static const char* const GLOBAL_MOVEREL;

    /**
     * Global name: startthread
     */
    static const char* const GLOBAL_STARTTHREAD;

    /**
     * Global name: canceldelay
     */
    static const char* const GLOBAL_CANCELDELAY;

public:
    /**
     * Get the LuaState object from the given state.
     */
    static LuaState& get(lua_State* L);

private:
    /**
     * A function that causes a delay in the thread's execution
     */
    static int delay(lua_State* L);

    /**
     * A function that returns whether a key is pressed or not.
     */
    static int iskeypressed(lua_State* L);

    /**
     * A function that returns the current value of an absolute axis.
     */
    static int getabs(lua_State* L);

    /**
     * A function that returns the minimal value of an absolute axis.
     */
    static int getabsmin(lua_State* L);

    /**
     * A function that returns the maximal value of an absolute axis.
     */
    static int getabsmax(lua_State* L);

    /**
     * A function that sends a key press event.
     */
    static int presskey(lua_State* L);

    /**
     * A function that sends a key release event.
     */
    static int releasekey(lua_State* L);

    /**
     * A function that sends a relative move event.
     */
    static int moverel(lua_State* L);

    /**
     * A function that starts a new thread.
     */
    static int startthread(lua_State* L);

    /**
     * A function that cancels a delay in another thread.
     */
    static int canceldelay(lua_State* L);

    /**
     * The joystick that this state belongs to.
     */
    Joystick& joystick;

    /**
     * The actual Lua state.
     */
    lua_State* L;

    /**
     * The threads we know of.
     */
    threads_t threads;

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
     * Get the wrapped state.
     */
    lua_State* get() const;

    /**
     * Create a new Lua thread. The thread will be added to a global
     * table as a key to avoid its removal.
     */
    lua_State* newThread(LuaThread* luaThread);

    /**
     * Push the current thread function to the given stack.
     */
    void pushThreadFunction(lua_State* L) const;

    /**
     * Delete a Lua thread. It will be removed from the global table.
     */
    void deleteThread(lua_State* thread);

    /**
     * Load the given string as the profile code. It resets the state
     * and loads and runs the given code.
     *
     * @return if the script could be run
     */
    bool loadProfile(const std::string& profileCode);

private:
    /**
     * Reset the Lua state. The old one will be closed and a new one
     * will be created and initialized.
     */
    void reset();

    /**
     * Initialize the Lua state by creating the default global stuff.
     */
    void initialize();
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline lua_State* LuaState::get() const
{
    return L;
}

//------------------------------------------------------------------------------

inline void LuaState::pushThreadFunction(lua_State* L) const
{
    lua_getglobal(L, GLOBAL_THREADFUNCTION);
}

//------------------------------------------------------------------------------
#endif // LUASTATE_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
