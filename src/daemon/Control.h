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

#include <cstdlib>

#include <string>
#include <map>
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
public:
    /**
     * Type for the controls.
     */
    enum type_t {
        // No type
        NONE,

        // Key or button
        KEY,

        // (Absolute) axis
        AXIS,

        // Relative axis
        RELATIVE
    };

private:
    /**
     * Type for the set of all Lua threads belonging to this
     * control.
     */
    typedef std::set<LuaThread*> luaThreads_t;

protected:
    /**
     * The name of the Lua function. This is basically a cache here,
     * so that we don't have to compute it everytime an event is received.
     */
    std::string luaHandlerName;

private:
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
     * Clear the Lua handler name.
     */
    void clearLuaHandlerName();

    /**
     * Setup the Lua handler name for the given parameters.
     */
    void setupLuaHandlerName(type_t type, int code);

    /**
     * Get the name of the Lua function call for this key.
     */
    const std::string& getLuaHandlerName() const;

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

/**
 * Base class template for controls that provide for mapping between
 * codes and names.
 */
template <const char* const* names, size_t numNames>
class ControlTemplate : public Control
{
private:
    /**
     * A class the instance of which is created for each
     * instantiation.
     */
    class Codes
    {
    private:
        /**
         * Type for the mapping.
         */
        typedef std::map<std::string, unsigned> codes_t;

        /**
         * The mapping
         */
        codes_t codes;

    public:
        /**
         * Create the mapping.
         */
        Codes();

        /**
         * Get the code for the given name, if it exists. Otherwise
         * return -1.
         */
        int findCode(const std::string& name);
    };

    /**
     * An instance of the codes.
     */
    static Codes codes;

public:
    /**
     * Convert the given control code constant to a control name.
     */
    static const char* toString(int code);

    /**
     * Convert the given name into a control code constant, if valid.
     */
    static int fromString(const std::string& name);

protected:
    /**
     * Construct the control.
     */
    ControlTemplate(Joystick& joystick);
};

//------------------------------------------------------------------------------
// Template definitions
//------------------------------------------------------------------------------

template <const char* const* names, size_t numNames>
ControlTemplate<names, numNames>::Codes::Codes()
{
    for(size_t i = 0; i<numNames; ++i) {
        const char* name = names[i];
        if (name!=0) {
            codes[name] = static_cast<unsigned>(i);
        }
    }
}

//------------------------------------------------------------------------------

template <const char* const* names, size_t numNames>
inline int
ControlTemplate<names, numNames>::Codes::findCode(const std::string& name)
{
    codes_t::iterator i = codes.find(name);
    return (i==codes.end()) ? -1 : static_cast<int>(i->second);
}

//------------------------------------------------------------------------------

template <const char* const* names, size_t numNames>
typename ControlTemplate<names, numNames>::Codes
ControlTemplate<names, numNames>::codes;

//------------------------------------------------------------------------------

template <const char* const* names, size_t numNames>
inline const char* ControlTemplate<names, numNames>::toString(int code)
{
    return (code>=0 && code<static_cast<int>(numNames-1)) ? names[code] : 0;
}

//------------------------------------------------------------------------------

template <const char* const* names, size_t numNames>
int ControlTemplate<names, numNames>::fromString(const std::string& name)
{
    return codes.findCode(name);
}

//------------------------------------------------------------------------------

template <const char* const* names, size_t numNames>
inline ControlTemplate<names, numNames>::ControlTemplate(Joystick& joystick) :
    Control(joystick)
{
}

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

inline void Control::clearLuaHandlerName()
{
    luaHandlerName = "";
}

//------------------------------------------------------------------------------

inline const std::string& Control::getLuaHandlerName() const
{
    return luaHandlerName;
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

