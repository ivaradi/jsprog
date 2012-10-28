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
#include "Log.h"

#include <lwt/Scheduler.h>
#include <lwt/IOServer.h>
#include <lwt/Log.h>

//------------------------------------------------------------------------------

using lwt::Scheduler;
using lwt::IOServer;

//------------------------------------------------------------------------------

// FIXME: this is temporary only
extern const char* scriptPath;

//------------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    lwt::Log::enableStdOut = true;
    lwt::Log::logFileName = "jsprogd.log";
    Log::level = Log::LEVEL_DEBUG;

    if (argc>1) {
        Profile profile(argv[1]);
        if (profile) {
            std::string contents;
            bool found = profile.getPrologue(contents);
            //Log::debug("prologue (%d): '%s' (%d)\n", found, contents.c_str());
            found = profile.getEpilogue(contents);
            //Log::debug("epilogue (%d): '%s'\n", found, contents.c_str());
            std::string type;
            int code = -1;
            while (profile.getNextControl(type, code, contents)) {
                Log::debug("control: type='%s', code=%d (0x%x), contents='%s'\n",
                           type.c_str(), code, code, contents.c_str());
            }
        }
    }

    Scheduler scheduler(65536);

    UInput uinput;

    IOServer ioServer(4);

    new InputDeviceListener();
    new LuaRunner();

    scheduler.run();

    return 0;
}
//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
