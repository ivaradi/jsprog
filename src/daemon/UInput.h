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

#ifndef UINPUT_H
#define UINPUT_H
//------------------------------------------------------------------------------

#include <lwt/ThreadedFD.h>

#include <linux/input.h>

//------------------------------------------------------------------------------

/**
 * Wrapper for the uinput device.
 */
class UInput : public lwt::ThreadedFD
{
private:
    /**
     * The only instance of this class.
     */
    static UInput* instance;

public:
    /**
     * Get the only instance of this class.
     */
    static UInput& get();

private:
    /**
     * An instance of an input event used by us.
     */
    struct input_event inputEvent;

public:
    /**
     * Construct the device.
     */
    UInput();

    /**
     * Destroy the device.
     */
    ~UInput();

    /**
     * Determine if the device is valid.
     */
    bool isValid() const;

    /**
     * Press the key with the given code (one of the KEY_XXX constants).
     */
    void pressKey(unsigned code);

    /**
     * Release the key with the given code (one of the KEY_XXX constants).
     */
    void releaseKey(unsigned code);

    /**
     * Produce a relative mouse movement.
     */
    void moveRelative(unsigned code, int value);

    /**
     * Synchronize the events with the device.
     */
    void synchronize();

private:
    /**
     * Perform an IOCTL. If an error occurs, it gets logged, the
     * device is invalidated, and false is returned.
     */
    bool ioctl(int request, long data);

    /**
     * Perform a writing to the device. If an error occurs, it is
     * logged, the device is invalidated and false is returned.
     */
    bool write(const void* buf, size_t count);

    /**
     * Send an event.
     */
    void sendEvent(unsigned type, unsigned code = 0, int value = 0);

    /**
     * Issue a key press or release event.
     */
    void sendKey(unsigned code, bool press);
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline UInput& UInput::get()
{
    return *instance;
}

//------------------------------------------------------------------------------

inline bool UInput::isValid() const
{
    return fd>=0;
}

//------------------------------------------------------------------------------

inline void UInput::pressKey(unsigned code)
{
    sendKey(code, true);
}

//------------------------------------------------------------------------------

inline void UInput::releaseKey(unsigned code)
{
    sendKey(code, false);
}

//------------------------------------------------------------------------------
#endif // UINPUT_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

