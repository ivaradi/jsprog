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

#ifndef KEY_H
#define KEY_H
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

public:
    /**
     * Construct the key for the given id and initial state.
     */
    Key(unsigned id, bool pressed);
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline Key::Key(unsigned id, bool pressed) : 
    id(id),
    pressed(pressed)
{
}

//------------------------------------------------------------------------------
#endif // KEY_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

