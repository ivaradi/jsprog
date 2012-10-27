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

#ifndef JSPROG_AXIS_H
#define JSPROG_AXIS_H
//------------------------------------------------------------------------------

#include "Control.h"

#include <string>

//------------------------------------------------------------------------------

/**
 * An axis of the joystick.
 */
class Axis : public Control
{
public:
    /**
     * Convert the given ABS_XXX constant to an axis name.
     * FIXME: this and fromString have very much in common with the
     * same functions of Key. Perhaps they should be moved to Control
     * or an intermediate template so that the name array and its size
     * could be provided separately.
     */
    static const char* toString(int code);

    /**
     * Convert the given name into an ABS_XXX constant, if valid.
     */
    static int fromString(const std::string& name);

private:
    /**
     * The current value of the axis
     */
    int value;

    /**
     * The minimum value of the axis.
     */
    int minimum;

    /**
     * The maximum value of the axis
     */
    int maximum;

    /**
     * The name of the Lua function. This is basically a cache here,
     * so that we don't have to compute it everytime an event is received.
     */
    std::string luaHandlerName;

public:
    /**
     * Construct the axis for the given joystick and initial state.
     */
    Axis(Joystick& joystick, int code, int value, int minimum, int maximum);

    /**
     * Set the value of the axis.
     */
    void setValue(int v);

    /**
     * Get the value of the axis.
     */
    int getValue() const;

    /**
     * Get the minimum value of the axis
     */
    int getMinimum() const;

    /**
     * Get the maximum value of the axis.
     */
    int getMaximum() const;

    /**
     * Get the name of the Lua function call for this key.
     */
    const std::string& getLuaHandlerName() const;
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline void Axis::setValue(int v)
{
    value = v;
}

//------------------------------------------------------------------------------

inline int Axis::getValue() const
{
    return value;
}

//------------------------------------------------------------------------------

inline int Axis::getMinimum() const
{
    return minimum;
}

//------------------------------------------------------------------------------

inline int Axis::getMaximum() const
{
    return maximum;
}

//------------------------------------------------------------------------------

inline const std::string& Axis::getLuaHandlerName() const
{
    return luaHandlerName;
}

//------------------------------------------------------------------------------
#endif // JSPROG_AXIS_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

