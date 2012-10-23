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

#include <lwt/ThreadedFD.h>
#include <lwt/util.h>

#include <vector>

#include <linux/input.h>

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
     * The bitmap for the presence of buttons.
     */
    std::vector<bool> key;

    /**
     * The bitmap for the presence of absolute axes.
     */
    std::vector<bool> abs;

    /**
     * Construct the joystick for the given file descriptor.
     */
    Joystick(int fd, const unsigned char* key, const unsigned char* abs);

public:
    /**
     * Read from the joystick with the given timeout.
     */
    ssize_t timedRead(bool& timedOut, void* buf, size_t count, millis_t timeout);

protected:
    /**
     * The destructor is protected to avoid inadvertent deletion.
     */
    virtual ~Joystick();
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline Joystick::~Joystick()
{
}

//------------------------------------------------------------------------------
#endif // JOYSTICK_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

