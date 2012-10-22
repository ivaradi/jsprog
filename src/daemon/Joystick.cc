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

#include "Joystick.h"

#include "Log.h"

#include <cstring>

//------------------------------------------------------------------------------

Joystick* Joystick::create(const char* devicePath)
{
    int fd = open(devicePath, O_RDONLY);
    if (fd<0) {
        Log::warning("could not open joystick device '%s': errno=%d\n",
                     devicePath, errno);
        return 0;
    }

    uint32_t syn = 0;
    if (::ioctl(fd, EVIOCGBIT(EV_SYN, sizeof(syn)), &syn)<0) {
        Log::warning("could not query the event types from '%s': errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }
    
    if ((syn&(1<<EV_ABS))==0) {
        Log::warning("device '%s' is not a joystick, since it does not support absolute events\n",
                     devicePath);
        ::close(fd);
        return 0;
    }

    unsigned char abs[SIZE_ABS_BITS];
    memset(abs, 0, sizeof(abs));
    if (::ioctl(fd, EVIOCGBIT(EV_ABS, sizeof(abs)), abs)<0) {
        Log::warning("could not query the absolute axes of '%s': errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }
    
    bool allZero = true;
    for(size_t i = 0; i<sizeof(abs) && allZero; ++i) {
        allZero = abs[i]==0;
    }

    if (allZero) {
        Log::warning("device '%s' is not a joystick, since none of the absolute axes are present: errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }

    unsigned char key[SIZE_KEY_BITS];
    memset(key, 0, sizeof(key));
    if (::ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(key)), key)<0) {
        Log::warning("could not query the keys of '%s': errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }

    return new Joystick(fd, key, abs);
}

//------------------------------------------------------------------------------

Joystick::Joystick(int fd, const unsigned char* key, const unsigned char* abs) :
    ThreadedFD(fd)
{
    memcpy(this->key, key, SIZE_KEY_BITS);
    memcpy(this->abs, abs, SIZE_ABS_BITS);
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

