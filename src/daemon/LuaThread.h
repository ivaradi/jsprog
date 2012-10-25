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

#include <set>
#include <string>

extern "C" {
#include <lua.h>
}

//------------------------------------------------------------------------------

class LuaState;
class Joystick;

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
     * Base class for owners of Lua threads such as keys and axes.
     *
     * An owner always belongs to a Joystick instance, which it
     * references and can be queried.
     *
     * It maintains a set of all Lua threads that belong to this
     * owner, as well as the Lua thread created last, if it still
     * exists. 
     *
     * The Lua thread maintains a reference to this owner and
     * if the the thread gets deleted, it is also removed from the
     * owner. Likewise, if the owner is deleted, it calls the Lua
     * thread runner, to delete all its threads.
     */
    class Owner
    {
    private:
        /**
         * Type for the set of all Lua threads belonging to this
         * owner.         
         */
        typedef std::set<LuaThread*> threads_t;

        /**
         * The jostick this owner belongs to.
         */
        Joystick& joystick;

        /**
         * The set of all Lua threads belonging to this owner.
         */
        threads_t threads;

        /**
         * The thread started before the last one (if it is still running).
         */
        LuaThread* previousThread;

        /**
         * The thread started last (if it is still running).
         */
        LuaThread* lastThread;

    protected:
        /**
         * Construct the owner.
         */
        Owner(Joystick& joystick);

        /**
         * Destroy the owner. All threads will be deleted via the
         * thread runner.
         */
        ~Owner();

    public:
        /**
         * Get the joystick this owner belongs to.
         */
        Joystick& getJoystick() const;

        /**
         * Delete all threads (except the current one).
         */
        void deleteAllThreads();

        /**
         * Delete the previously started thread (if it is not the
         * currently running one).
         */
        void deletePreviousThread();

        friend class LuaThread;
    };

private:
    /**
     * The owner of this thread.
     */
    Owner& owner;
    
    /**
     * The Lua state this thread belongs to.
     */
    LuaState& luaState;

    /**
     * The thread's own state.
     */
    lua_State* L;

    /**
     * The name of the function to call.
     */
    std::string functionName;

    /**
     * The event type.
     */
    int eventType;

    /**
     * The event code.
     */
    int eventCode;

    /**
     * The event value.
     */
    int eventValue;

    /**
     * The timeout of this thread.
     */
    millis_t timeout;

private:
    /**
     * Construct the thread for the given owner and state. It will be
     * added to the owner as its last thread.
     */
    LuaThread(Owner& owner, LuaState& luaState, 
              const std::string& functionName,
              int eventType, int eventCode, int eventValue);

    /**
     * Destroy the thread and remove it from the owner.
     */
    ~LuaThread();

    /**
     * Get the owner of this thread.
     */
    Owner& getOwner() const;

    /**
     * Start the thread by calling the function given in the constructor.
     *
     * @return if the thread's execution should continue or not.
     */
    bool start();

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
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline LuaThread::Owner::Owner(Joystick& joystick) :
    joystick(joystick),
    previousThread(0),
    lastThread(0)
{
}

//------------------------------------------------------------------------------

inline Joystick& LuaThread::Owner::getJoystick() const
{
    return joystick;
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

inline LuaThread::Owner& LuaThread::getOwner() const
{
    return owner;
}

//------------------------------------------------------------------------------

inline bool LuaThread::resume()
{
    return doResume();
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

