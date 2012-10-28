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
#include "UInput.h"
#include "LuaRunner.h"
#include "Profile.h"
#include "dbus.h"
#include "Log.h"

#include <lwt/Scheduler.h>
#include <lwt/IOServer.h>
#include <lwt/Log.h>

//------------------------------------------------------------------------------

using lwt::Scheduler;
using lwt::IOServer;

//------------------------------------------------------------------------------

// FIXME: this is temporary only
extern const Profile* defaultProfile;

//------------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    lwt::Log::enableStdOut = true;
    lwt::Log::logFileName = "jsprogd.log";
    Log::level = Log::LEVEL_DEBUG;

    if (argc>1) {
        Profile* profile = new Profile(argv[1]);
        if (*profile) {
            defaultProfile = profile;
        } else {
            delete profile;
        }
    }

    Scheduler scheduler(65536);

    UInput uinput;

    IOServer ioServer(4);

    new InputDeviceListener();
    new LuaRunner();

    initializeDBus();

    scheduler.run();

    return 0;
}
//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
