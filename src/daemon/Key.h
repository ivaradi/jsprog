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

#ifndef JSPROG_KEY_H
#define JSPROG_KEY_H
//------------------------------------------------------------------------------

#include <string>

//------------------------------------------------------------------------------

/**
 * A class representing a key (or button) that a joystick has.
 */
class Key
{
public:
    /**
     * Convert the given KEY_XXX or BTN_XXX constant to a key name.
     */
    static const char* toString(int code);

    /**
     * Convert the given name into a KEY_XXX or BTN_XXX constant, if valid.
     */
    static int fromString(const std::string& name);

private:
    /**
     * The identifier of the key (one of the KEY_XXX or BTN_XXX constants).
     */
    int code;

    /**
     * Indicate if the key is currently pressed.
     */
    bool pressed;

    /**
     * The name of the Lua function. This is basically a cache here,
     * so that we don't have to compute it everytime an event is received.
     */
    std::string luaHandlerName;

public:
    /**
     * Construct the key for the given id and initial state.
     */
    Key(int code, bool pressed);

    /**
     * Set whether the key is pressed or not.
     */
    void setPressed(bool p);

    /**
     * Get whether the key is pressed or not.
     */
    bool isPressed() const;

    /**
     * Get the name of the Lua function call for this key.
     */
    const std::string& getLuaHandlerName() const;
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline void Key::setPressed(bool p)
{
    pressed = p;
}

//------------------------------------------------------------------------------

inline bool Key::isPressed() const
{
    return pressed;
}

//------------------------------------------------------------------------------

inline const std::string& Key::getLuaHandlerName() const
{
    return luaHandlerName;
}

//------------------------------------------------------------------------------
#endif // JSPROG_KEY_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

