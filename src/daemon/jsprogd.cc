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
#include "Log.h"

#include <lwt/Scheduler.h>
#include <lwt/IOServer.h>
#include <lwt/Log.h>

//------------------------------------------------------------------------------

using lwt::Scheduler;
using lwt::IOServer;

//------------------------------------------------------------------------------

int main()
{
    lwt::Log::enableStdOut = true;
    Log::level = Log::LEVEL_DEBUG;

    Scheduler scheduler(65536);

    UInput uinput;

    IOServer ioServer(4);
    
    new InputDeviceListener();
    
    scheduler.run();

    return 0;
}
//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

