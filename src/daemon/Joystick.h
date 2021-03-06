// Copyright (c) 2012 by Istv�n V�radi

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

#ifndef JOYSTICK_H
#define JOYSTICK_H
//------------------------------------------------------------------------------

#include "LuaState.h"

#include "Profile.h"
#include "Key.h"
#include "Axis.h"

#include <lwt/ThreadedFD.h>
#include <lwt/util.h>

#include <vector>
#include <set>

#include <linux/input.h>

//------------------------------------------------------------------------------

class LuaThread;
class Key;
class Axis;
class XMLDocument;

//------------------------------------------------------------------------------

/**
 * Class to handle joysticks.
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
class Joystick : public lwt::ThreadedFD
{
public:
    /**
     * Type for the mapping of IDs to joysticks.
     */
    typedef std::map<size_t, Joystick*> joysticks_t;

private:
    /**
     * Timeout handler.
     */
    class TimeoutHandler;

    friend class TimeoutHandler;

    /**
     * Type for the set of all Lua threads belonging to this
     * control.
     */
    typedef std::set<LuaThread*> luaThreads_t;

public:
    /**
     * Create a joystick object for the given device file, if that
     * really is a joystick.
     */
    static Joystick* create(const char* devicePath);

    /**
     * Get the joysticks that exist.
     */
    static const joysticks_t& getAll();

    /**
     * Find the joystick with the given ID.
     */
    static Joystick* find(size_t id);

    /**
     * Close all joysticks.
     */
    static void closeAll();

private:
    /**
     * The size of the buffer for the bits indicating the presence of
     * buttons (or keys).
     */
    static const size_t SIZE_KEY_BITS = (KEY_CNT+7)/8;

    /**
     * The size of the buffer for the bits indicating the presence of
     * absolute axes.
     */
    static const size_t SIZE_ABS_BITS = (ABS_CNT+7)/8;

    /**
     * The next ID for a joystick.
     */
    static size_t nextID;

    /**
     * The set of existing joystick instances.
     */
    static joysticks_t joysticks;

    /**
     * The ID of this joystick.
     */
    size_t id;

    /**
     * The ID of the device.
     */
    struct input_id inputID;

    /**
     * The name of the device.
     */
    std::string name;

    /**
     * The physical location of the device.
     */
    std::string phys;

    /**
     * The unique ID of the device.
     */
    std::string uniq;

    /**
     * The mapping from key codes to key objects.
     */
    Key* keys[KEY_CNT];

    /**
     * The number of keys.
     */
    size_t numKeys = 0;

    /**
     * The mapping from axis codes to axis objects.
     */
    Axis* axes[ABS_CNT];

    /**
     * The number of axes.
     */
    size_t numAxes = 0;

    /**
     * The Lua state that belongs to this joystick.
     */
    LuaState luaState;

    /**
     * The set of the codes of the keys that are currently pressed on
     * behalf of this joystick (i.e. these are the keys of the virtual
     * device provided by us not those of the joystick being handled).
     */
    std::set<int> pressedKeys;

    /**
     * The set of all Lua threads belonging to this control.
     */
    luaThreads_t luaThreads;

    /**
     * Construct the joystick for the given file descriptor.
     */
    Joystick(int fd, const struct input_id& inputID,
             const char* name, const char* phys, const char* uniq,
             const unsigned char* key, const unsigned char* abs);

protected:
    /**
     * The destructor is protected to avoid inadvertent deletion.
     */
    virtual ~Joystick();

public:
    /**
     * Get the ID of this joystick.
     */
    size_t getID() const;

    /**
     * Get the input ID of this joystick.
     */
    const struct input_id& getInputID() const;

    /**
     * Get the name.
     */
    const std::string& getName() const;

    /**
     * Get the physical location.
     */
    const std::string& getPhys() const;

    /**
     * Get the uniq ID of the joystick.
     */
    const std::string& getUniq() const;

    /**
     * Set the given profile. It clears some of the internal state of
     * the joystick:
     * - all threads on all controls are deleted,
     * - the pressed keys are released,
     * - the Lua state is reinitialized
     * - the code from the profile is added to the Lua state.
     *
     * @return whether the profile could be loaded.
     */
    bool setProfile(const Profile& profile);

    /**
     * Get the Lua state.
     */
    LuaState& getLuaState();

    /**
     * Get the number of keys.
     */
    size_t getNumKeys() const;

    /**
     * Find the key with the given code.
     */
    Key* findKey(int code) const;

    /**
     * Get the number of axes.
     */
    size_t getNumAxes() const;

    /**
     * Find the axis with the given code.
     */
    Axis* findAxis(int code) const;

    /**
     * Find the control with the given type and code.
     */
    Control* findControl(Control::type_t type, int code) const;

    /**
     * Indicate that the key with the given code has been pressed.
     */
    void keyPressed(int code);

    /**
     * Indicate that the key with the given code has been released.
     */
    void keyReleased(int code);

    /**
     * Delete all threads of all controls.
     */
    void deleteAllLuaThreads() const;

    /**
     * Release all pressed keys.
     */
    void releasePressedKeys();

private:
    /**
     * Reset the Lua handler names in all the controls that we have.
     */
    void clearLuaHandlerNames();

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

inline const Joystick::joysticks_t& Joystick::getAll()
{
    return joysticks;
}

//------------------------------------------------------------------------------

inline size_t Joystick::getID() const
{
    return id;
}

//------------------------------------------------------------------------------

inline const struct input_id& Joystick::getInputID() const
{
    return inputID;
}

//------------------------------------------------------------------------------

inline const std::string& Joystick::getName() const
{
    return name;
}

//------------------------------------------------------------------------------

inline const std::string& Joystick::getPhys() const
{
    return phys;
}

//------------------------------------------------------------------------------

inline const std::string& Joystick::getUniq() const
{
    return uniq;
}

//------------------------------------------------------------------------------

inline LuaState& Joystick::getLuaState()
{
    return luaState;
}

//------------------------------------------------------------------------------

inline size_t Joystick::getNumKeys() const
{
    return numKeys;
}

//------------------------------------------------------------------------------

inline Key* Joystick::findKey(int code) const
{
    return (code>=0 && code<KEY_CNT) ? keys[code] : 0;
}

//------------------------------------------------------------------------------

inline size_t Joystick::getNumAxes() const
{
    return numAxes;
}

//------------------------------------------------------------------------------

inline Axis* Joystick::findAxis(int code) const
{
    return (code>=0 && code<ABS_CNT) ? axes[code] : 0;
}

//------------------------------------------------------------------------------

inline Control* Joystick::findControl(Control::type_t type, int code) const
{
    return (type==Control::KEY) ?
        static_cast<Control*>(findKey(code)) :
        static_cast<Control*>(findAxis(code));
}

//------------------------------------------------------------------------------

inline void Joystick::keyPressed(int code)
{
    pressedKeys.insert(code);
}

//------------------------------------------------------------------------------

inline void Joystick::keyReleased(int code)
{
    pressedKeys.erase(code);
}

//------------------------------------------------------------------------------

inline void Joystick::addLuaThread(LuaThread* luaThread)
{
    luaThreads.insert(luaThread);
}

//------------------------------------------------------------------------------

inline void Joystick::removeLuaThread(LuaThread* luaThread)
{
    luaThreads.erase(luaThread);
}

//------------------------------------------------------------------------------
#endif // JOYSTICK_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
