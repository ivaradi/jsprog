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

#ifndef CONTROL_H
#define CONTROL_H
//------------------------------------------------------------------------------

#include <set>

//------------------------------------------------------------------------------

class LuaThread;
class Joystick;

//------------------------------------------------------------------------------

/**
 * Base class for the various controls of a joystick. It maintains 
 *
 * A control always belongs to a Joystick instance, which it references
 * and can be queried. 
 *
 * It maintains a set of all Lua threads that run on behalf of this
 * control, as well as the Lua threads created last and previously, if
 * they still  exists.  
 *
 * The Lua thread maintains a reference to this control and if the the
 * thread gets deleted, it is also removed from the control. Likewise,
 * if the control is deleted, it calls the Lua thread runner, to
 * delete all its threads. 
 */
class Control
{
private:
    /**
     * Type for the set of all Lua threads belonging to this
     * control.         
     */
    typedef std::set<LuaThread*> luaThreads_t;

    /**
     * The jostick this control belongs to.
     */
    Joystick& joystick;

    /**
     * The set of all Lua threads belonging to this control.
     */
    luaThreads_t luaThreads;

    /**
     * The thread started before the last one (if it is still running).
     */
    LuaThread* previousLuaThread;

    /**
     * The thread started last (if it is still running).
     */
    LuaThread* lastLuaThread;

protected:
    /**
     * Construct the control for the given joystick.
     */
    Control(Joystick& joystick);

    /**
     * Destroy the control. All threads will be deleted via the
     * thread runner.
     */
    ~Control();

public:
    /**
     * Get the joystick this control belongs to.
     */
    Joystick& getJoystick() const;

    /**
     * Delete all threads (except the current one).
     */
    void deleteAllLuaThreads();

    /**
     * Delete the previously started thread (if it is not the
     * currently running one).
     */
    void deletePreviousLuaThread();

private:
    /**
     * Add a Lua thread to the control.
     */
    void addLuaThread(LuaThread* luaThread);

    /**
     * Remove the Lua thread from this control.
     */
    void removeLuaThread(LuaThread* luaThread);

    friend class LuaThread;
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline Control::Control(Joystick& joystick) :
    joystick(joystick),
    previousLuaThread(0),
    lastLuaThread(0)
{
}

//------------------------------------------------------------------------------

inline Joystick& Control::getJoystick() const
{
    return joystick;
}

//------------------------------------------------------------------------------

inline void Control::addLuaThread(LuaThread* luaThread)
{
    luaThreads.insert(luaThread);
    previousLuaThread = lastLuaThread;
    lastLuaThread = luaThread;
}

//------------------------------------------------------------------------------

inline void Control::removeLuaThread(LuaThread* luaThread)
{
    if (lastLuaThread==luaThread) lastLuaThread = 0;
    else if (previousLuaThread==luaThread) previousLuaThread = 0;
    luaThreads.erase(luaThread);
}

//------------------------------------------------------------------------------
#endif // CONTROL_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

