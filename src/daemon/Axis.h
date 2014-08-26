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

#include <linux/input.h>

//------------------------------------------------------------------------------

extern const char* const axisNames[];

//------------------------------------------------------------------------------

/**
 * An axis of the joystick.
 */
class Axis : public ControlTemplate<axisNames, ABS_CNT>
{
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

public:
    /**
     * Construct the axis for the given joystick and initial state.
     */
    Axis(Joystick& joystick, int value, int minimum, int maximum);

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
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline Axis::Axis(Joystick& joystick, int value, int minimum, int maximum):
    ControlTemplate(joystick),
    value(value),
    minimum(minimum),
    maximum(maximum)
{
}

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
#endif // JSPROG_AXIS_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
