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

#ifndef LUA_THREAD_H
#define LUA_THREAD_H
//------------------------------------------------------------------------------

#include <lwt/util.h>

#include <string>

extern "C" {
#include <lua.h>
}

//------------------------------------------------------------------------------

class Control;
class LuaState;

//------------------------------------------------------------------------------

/**
 * Wrapper for a Lua thread. A Lua thread is used to execute the
 * actions belonging to a single event within the context of a Lua
 * state. It is always a function which may return or may only
 * yield. If it returns, that is the end of the thread. If it yields,
 * it should return a timeout after which the thread should be
 * resumed.
 */
class LuaThread
{
public:
    /**
     * Yield reason: uncancellable delay
     */
    static const int YIELD_DELAY = 1;

    /**
     * Yield reason: cancellable delay
     */
    static const int YIELD_CANCELLABLE_DELAY = 2;

private:
    /**
     * The control this thread belongs to.
     */
    Control& control;

    /**
     * The Lua state this thread belongs to.
     */
    LuaState& luaState;

    /**
     * The thread's own state.
     */
    lua_State* L;

    /**
     * The timeout of this thread.
     */
    millis_t timeout;

    /**
     * Indicate if the current delay is cancellable
     */
    bool cancellable;

    /**
     * Indicate if the thread is cancelled.
     */
    bool cancelled;

private:
    /**
     * Construct the thread for the given control and state. It will be
     * added to the control's joystick. It is assumed that the current Lua
     * stack contains the pointer of the function to call.
     */
    LuaThread(Control& control, LuaState& luaState);

    /**
     * Destroy the thread and remove it from the control.
     */
    ~LuaThread();

    /**
     * Get the control this thread runs on behalf of.
     */
    Control& getControl() const;

    /**
     * Get the thread's state.
     */
    lua_State* getState() const;

    /**
     * Start the thread by calling the function given in the constructor.
     *
     * @return if the thread's execution should continue or not.
     */
    bool start();

    /**
     * Cancel the delay in the thread, if the thread is cancellable.
     */
    bool cancelDelay();

    /**
     * Resume the thread.
     *
     * @return if the thread's execution should continue or not.
     */
    bool resume();

    /**
     * Get the timeout
     */
    millis_t getTimeout() const;

    /**
     * Call lua_resume() with the given nargs, and handle the result of it.
     *
     * If it returned LUA_YIELD, pop an integer from the stack, and
     * add that to the timeout, and return true. Otherwise return false.
     */
    bool doResume(int narg = 0);

    friend class LuaRunner;
    friend class LuaState;
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline Control& LuaThread::getControl() const
{
    return control;
}

//------------------------------------------------------------------------------

inline lua_State* LuaThread::getState() const
{
    return L;
}

//------------------------------------------------------------------------------

inline millis_t LuaThread::getTimeout() const
{
    return timeout;
}

//------------------------------------------------------------------------------
#endif // LUA_THREAD_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
