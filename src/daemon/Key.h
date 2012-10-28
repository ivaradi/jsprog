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

#include "Control.h"

#include <linux/input.h>

//------------------------------------------------------------------------------

extern const char* const keyNames[];

//------------------------------------------------------------------------------

/**
 * A class representing a key (or button) that a joystick has.
 */
class Key : public ControlTemplate<keyNames, KEY_CNT>
{
private:
    /**
     * Indicate if the key is currently pressed.
     */
    bool pressed;

public:
    /**
     * Construct the key for the given id and initial state.
     */
    Key(Joystick& joystick, bool pressed);

    /**
     * Set whether the key is pressed or not.
     */
    void setPressed(bool p);

    /**
     * Get whether the key is pressed or not.
     */
    bool isPressed() const;
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline Key::Key(Joystick& joystick, bool pressed) :
    ControlTemplate(joystick),
    pressed(pressed)
{
}

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
#endif // JSPROG_KEY_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

