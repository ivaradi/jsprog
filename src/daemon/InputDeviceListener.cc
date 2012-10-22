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

#include <lwt/EPoll.h>

#include <cstdio>

//------------------------------------------------------------------------------

using lwt::EPoll;

using std::string;

//------------------------------------------------------------------------------

InputDeviceListener::InputDeviceListener() :
    inotify(new INotify())
{
    int wd = inotify->addWatch("/dev/input", IN_CREATE|IN_DELETE|IN_ATTRIB);
    if (wd<0) {
        EPoll::get().destroy(inotify);
        inotify = 0;
        perror("inotify_add_watch");
    } else {
        printf("wd=%d\n", wd);
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

    int wd;
    uint32_t mask;
    uint32_t cookie;
    string name;
    while(inotify->getEvent(wd, mask, cookie, name)) {
        printf("wd=%d, mask=0x%08x, cookie=%u, name='%s'\n",
               wd, mask, cookie, name.c_str());
    }
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

