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

#ifndef INPUTDEVICELISTENER_H
#define INPUTDEVICELISTENER_H
//------------------------------------------------------------------------------

#include <lwt/Thread.h>

#include <set>
#include <string>

//------------------------------------------------------------------------------

class INotify;
class Joystick;

//------------------------------------------------------------------------------

/**
 * A thread that listens to events on the /dev/input directory.
 */
class InputDeviceListener : public lwt::Thread
{
private:
    /**
     * Type set of device names already seen and handled as joysticks.
     */
    typedef std::set<std::string> joystickNames_t;

    /**
     * The directory to watch.
     */
    static const char* const inputDirectory;

    /**
     * The only instance of the device listener.
     */
    static InputDeviceListener* instance;

public:
    /**
     * Get the only instance of the device listener.
     */
    static InputDeviceListener& get();

private:
    /**
     * The inotify file descriptor.
     */
    INotify* inotify;

    /**
     * The names of the joystick devices currently being handled.
     */
    joystickNames_t joystickNames;

public:
    /**
     * Construct the thread.
     */
    InputDeviceListener();

    /**
     * Destroy the thread.
     */
    ~InputDeviceListener();

    /**
     * Perform the thread's operation.
     */
    virtual void run();

    /**
     * Stop the listener.
     */
    void stop();

private:
    /**
     * Scan the devices.
     */
    void scanDevices();

    /**
     * Check the input device with the given file name (relative to
     * /dev/input).
     */
    void checkDevice(const std::string& fileName);
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline InputDeviceListener& InputDeviceListener::get()
{
    return *instance;
}

//------------------------------------------------------------------------------
#endif // INPUTDEVICELISTENER_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
