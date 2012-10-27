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

#ifndef JOYSTICK_H
#define JOYSTICK_H
//------------------------------------------------------------------------------

#include "LuaState.h"

#include <lwt/ThreadedFD.h>
#include <lwt/util.h>

#include <vector>

#include <linux/input.h>

//------------------------------------------------------------------------------

class Key;
class Axis;

//------------------------------------------------------------------------------

/**
 * Class to handle joysticks.
 */
class Joystick : public lwt::ThreadedFD
{
private:
    /**
     * Timeout handler.
     */
    class TimeoutHandler;

    friend class TimeoutHandler;

public:
    /**
     * Create a joystick object for the given device file, if that
     * really is a joystick.
     */
    static Joystick* create(const char* devicePath);

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
     * Put a bitmap into a boolean vector.
     */
    static void setupBitVector(std::vector<bool>& dest, 
                               const unsigned char* src, size_t length,
                               const char* debugPrefix);

    /**
     * The mapping from key codes to key objects.
     */
    Key* keys[KEY_CNT];

    /**
     * The mapping from axis codes to axis objects.
     */
    Axis* axes[ABS_CNT];

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
     * Construct the joystick for the given file descriptor.
     */
    Joystick(int fd, const unsigned char* key, const unsigned char* abs);

public:
    /**
     * Read from the joystick with the given timeout.
     */
    ssize_t timedRead(bool& timedOut, void* buf, size_t count, millis_t timeout);

    /**
     * Get the Lua state.
     */
    LuaState& getLuaState();

    /**
     * Find the key with the given code.
     */
    Key* findKey(int code) const;

    /**
     * Find the axis with the given code.
     */
    Axis* findAxis(int code) const;

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

protected:
    /**
     * The destructor is protected to avoid inadvertent deletion.
     */
    virtual ~Joystick();
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline LuaState& Joystick::getLuaState()
{
    return luaState;
}

//------------------------------------------------------------------------------

inline Key* Joystick::findKey(int code) const
{
    return (code>=0 && code<KEY_CNT) ? keys[code] : 0;
}

//------------------------------------------------------------------------------

inline Axis* Joystick::findAxis(int code) const
{
    return (code>=0 && code<ABS_CNT) ? axes[code] : 0;
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
#endif // JOYSTICK_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

