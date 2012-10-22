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

//------------------------------------------------------------------------------

#include "InputDeviceListener.h"

#include "INotify.h"
#include "Joystick.h"
#include "JoystickHandler.h"
#include "Log.h"

#include <lwt/EPoll.h>
#include <lwt/Dirent.h>

#include <cstdio>

//------------------------------------------------------------------------------

using lwt::EPoll;
using lwt::OpenDir;
using lwt::ReadDir;
using lwt::CloseDir;

using std::string;

//------------------------------------------------------------------------------

const char* const InputDeviceListener::inputDirectory = "/dev/input";

//------------------------------------------------------------------------------

InputDeviceListener::InputDeviceListener() :
    inotify(new INotify())
{
    setLogContext("InputDeviceListener");
    int wd = inotify->addWatch("/dev/input", IN_CREATE|IN_DELETE|IN_ATTRIB);
    if (wd<0) {
        Log::error("failed to add a watch for /dev/input: errno=%d\n", errno);
        EPoll::get().destroy(inotify);
        inotify = 0;
    } else {
        Log::debug("wd=%d\n", wd);
    }
}

//------------------------------------------------------------------------------

InputDeviceListener::~InputDeviceListener()
{
    EPoll::get().destroy(inotify);
}

//------------------------------------------------------------------------------

void InputDeviceListener::run()
{
    if (inotify==0) return;

    scanDevices();

    int wd;
    uint32_t mask;
    uint32_t cookie;
    string name;
    while(inotify->getEvent(wd, mask, cookie, name)) {
        Log::debug("wd=%d, mask=0x%08x, cookie=%u, name='%s'\n",
                   wd, mask, cookie, name.c_str());

        if ( (mask&IN_DELETE)!=0) {
            joystickNames.erase(name);
        }

        if ( (mask&(IN_CREATE|IN_ATTRIB))!=0 && 
             joystickNames.find(name)==joystickNames.end()) 
        {
            checkDevice(name);
        }
    }
}

//------------------------------------------------------------------------------

void InputDeviceListener::scanDevices()
{
    DIR* dirp = OpenDir::call(inputDirectory);
    if (dirp==0) {
        Log::error("scanDevices: could not open directory '%s': errno=%d\n",
                   inputDirectory, errno);
        return;
    }
    
    struct dirent dirent;
    struct dirent* result;
    
    while (ReadDir::call(dirp, &dirent, &result)==0 && result==&dirent) {
        if (dirent.d_type==DT_CHR) {
            checkDevice(dirent.d_name);
        }
    }

    CloseDir::call(dirp);
}

//------------------------------------------------------------------------------

void InputDeviceListener::checkDevice(const string& fileName)
{
    if (!fileName.find("event")==0 ) return;

    string devicePath(inputDirectory);
    devicePath.append("/");
    devicePath.append(fileName);

    Joystick* joystick = Joystick::create(devicePath.c_str());
    if (joystick!=0) {
        Log::info("%s is a joystick device\n", fileName.c_str());
        joystickNames.insert(fileName);
        new JoystickHandler(joystick, fileName);
    }
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

