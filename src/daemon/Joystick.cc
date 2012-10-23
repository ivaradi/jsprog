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

#include <lwt/Timer.h>

#include <cstring>

//------------------------------------------------------------------------------

using lwt::BlockedThread;

using std::vector;

//------------------------------------------------------------------------------

class Joystick::TimeoutHandler : public lwt::Timer
{
private:
    /**
     * The waiter that should be used to unblock the thread waiting on
     * this timer.
     */
    lwt::BlockedThread& waiter;

    /**
     * The reference to the boolean variable that should be set when
     * the timeout fires.
     */
    bool& timedOut;

public:
    /**
     * Construct the timeout handler.
     */
    TimeoutHandler(millis_t timeout, lwt::BlockedThread& waiter, bool& timedOut);

protected:
    /**
     * Handle the timeout.
     */
    virtual bool handleTimeout();
};

//------------------------------------------------------------------------------

Joystick::TimeoutHandler::TimeoutHandler(millis_t timeout, 
                                         BlockedThread& waiter, bool& timedOut) :
    Timer(timeout),
    waiter(waiter),
    timedOut(timedOut)
{
}

//------------------------------------------------------------------------------

bool Joystick::TimeoutHandler::handleTimeout()
{
    timedOut = true;
    waiter.unblock();
    return false;
}

//------------------------------------------------------------------------------
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

    Log::info("%s is a joystick device\n", devicePath);

    return new Joystick(fd, key, abs);
}

//------------------------------------------------------------------------------

void Joystick::setupBitVector(vector<bool>& dest, const unsigned char* src,
                              size_t length, const char* debugPrefix)
{
    dest.reserve(length*8);
    for(size_t i = 0; i<length; ++i) {
        unsigned char x = src[i];
        for(size_t j = 0; j<8; ++j, x>>=1) {
            dest.push_back( (x&1)==1 );
        }
    }
    Log::debug(debugPrefix);
    bool hadValue = false;
    for(size_t i = 0; i<dest.size(); ++i) {
        if (dest[i]) {
            if (hadValue) Log::cont(",");
            Log::cont(" 0x%03x", i);
        }
    }
    Log::cont("\n");
}

//------------------------------------------------------------------------------

Joystick::Joystick(int fd, const unsigned char* key, const unsigned char* abs) :
    ThreadedFD(fd),
    luaState(*this)
{
    setupBitVector(this->key, key, SIZE_KEY_BITS, "Buttons:");
    setupBitVector(this->abs, abs, SIZE_ABS_BITS, "Axes:");
}

//------------------------------------------------------------------------------

ssize_t Joystick::timedRead(bool& timedOut, void* buf, size_t count, 
                            millis_t timeout)
{
    timedOut = false;
    while(true) {
        ssize_t result = PolledFD::read(buf, count);
        if (result<0 && (errno==EAGAIN || errno==EWOULDBLOCK)) {
            TimeoutHandler* timeoutHandler = 
                new TimeoutHandler(timeout, readWaiter, timedOut);
            if (!waitRead()) {
                delete timeoutHandler;
                return -1;
            } else if (timedOut) {
                return 0;
            } else {
                timeoutHandler->cancel();
                delete timeoutHandler;
            }
        } else {
            return result;
        }
    }
    
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

