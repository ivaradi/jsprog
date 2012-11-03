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
#include "DBusHandler.h"
#include "DBusAdaptor.h"
#include "Log.h"

#include <lwt/Scheduler.h>
#include <lwt/IOServer.h>
#include <lwt/Log.h>

//------------------------------------------------------------------------------

using lwt::Scheduler;
using lwt::IOServer;

//------------------------------------------------------------------------------

int usage(const char* programName, bool error)
{
    FILE* f = error ? stderr : stdout;
    fprintf(f, "Usage: %s [-h] [-d] [-s] [-l <logfile>]\n", programName);
    fprintf(f, "       -h: print this help message\n");
    fprintf(f, "       -d: log debug messages\n");
    fprintf(f, "       -s: log to the standard output\n");
    fprintf(f, "       -l <logfile>: log to the given file\n");
    return error ? 1 : 0;
}

//------------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    int opt;
    while ((opt=getopt(argc, argv, "hdsl:")) != -1) {
        switch (opt) {
          case 'h':
            return usage(argv[0], false);
          case 'd':
            Log::level = Log::LEVEL_DEBUG;
            break;
          case 's':
            lwt::Log::enableStdOut = true;
            break;
          case 'l':
            lwt::Log::logFileName = optarg;
            break;
          default:
            return usage(argv[0], true);
        }
    }

    Scheduler scheduler(65536);

    UInput uinput;

    IOServer ioServer(4);

    new InputDeviceListener();
    new LuaRunner();

    DBusHandler dbusHandler;
    dbusHandler.requestName("hu.varadiistvan.JSProg");
    DBusAdaptor dbusAdaptor(dbusHandler);

    scheduler.run();

    return 0;
}
//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
