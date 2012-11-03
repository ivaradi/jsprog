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

#include "LuaRunner.h"

#include "UInput.h"
#include "Log.h"

#include <lwt/Timer.h>

//------------------------------------------------------------------------------

class LuaRunner::TimeoutHandler : public lwt::Timer
{
private:
    /**
     * The blocker to unblock when the timeout fires.
     */
    lwt::BlockedThread& blocker;

    /**
     * The boolean variable to set when the timeout fires.
     */
    bool& timedOut;

public:
    /**
     * Construct the timeout handler.
     */
    TimeoutHandler(millis_t timeout,
                   lwt::BlockedThread& blocker, bool& timedOut);

protected:
    /**
     * Handle the timeout by unblocking the blocked thread and setting
     * the timedOut variable to true. It returns false, so that the
     * caller will delete it.
     */
    virtual bool handleTimeout();
};

//------------------------------------------------------------------------------

inline LuaRunner::TimeoutHandler::
TimeoutHandler(millis_t timeout, lwt::BlockedThread& blocker, bool& timedOut) :
    Timer(timeout),
    blocker(blocker),
    timedOut(timedOut)
{
}

//------------------------------------------------------------------------------

bool LuaRunner::TimeoutHandler::handleTimeout()
{
    blocker.unblock();
    timedOut = true;
    return false;
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

LuaRunner* LuaRunner::instance = 0;

//------------------------------------------------------------------------------

LuaRunner::LuaRunner() :
    currentThread(0),
    toStop(false)
{
    setLogContext("LuaRunner");
    instance = this;
}

//------------------------------------------------------------------------------

void LuaRunner::newThread(Control& control, LuaState& luaState,
                          const std::string& functionName,
                          int eventType, int eventCode, int eventValue)
{
    LuaThread* luaThread = new LuaThread(control, luaState, functionName,
                                         eventType, eventCode, eventValue);
    pendingThreads.push_back(luaThread);
    blocker.unblock();
}

//------------------------------------------------------------------------------

void LuaRunner::deleteThread(LuaThread* luaThread)
{
    if (runningThreads.erase(luaThread)>0) {
        delete luaThread;
        return;
    }

    for(pendingThreads_t::iterator i = pendingThreads.begin();
        i!=pendingThreads.end(); ++i)
    {
        if ((*i)==luaThread) {
            pendingThreads.erase(i);
            delete luaThread;
            return;
        }
    }

    assert(false || "Thread whose deletion was requested is not present anywhere!");
}

//------------------------------------------------------------------------------

void LuaRunner::run()
{
    UInput& uinput = UInput::get();

    while(true) {
        resumeRunning();
        runPending();

        uinput.synchronize();

        bool timedOut = false;
        TimeoutHandler* timeoutHandler = 0;
        if (!runningThreads.empty()) {
            millis_t timeout = (*runningThreads.begin())->getTimeout();
            timeoutHandler = new TimeoutHandler(timeout, blocker, timedOut);
        }
        blocker.blockCurrent();
        if (timeoutHandler!=0 && !timedOut) {
            timeoutHandler->cancel();
            delete timeoutHandler;
        }
        if (toStop) break;
    }
    Log::debug("quitting...\n");
}

//------------------------------------------------------------------------------

void LuaRunner::stop()
{
    toStop = true;
    blocker.unblock();
}

//------------------------------------------------------------------------------

void LuaRunner::resumeRunning()
{
    static const millis_t tolerance = 5;

    millis_t now = currentTimeMillis() + tolerance;
    while(!runningThreads.empty()) {
        runningThreads_t::iterator i = runningThreads.begin();
        LuaThread* luaThread = *i;

        if (luaThread->getTimeout() > now) break;

        runningThreads.erase(i);
        currentThread = luaThread;
        bool shouldContinue = luaThread->resume();
        currentThread = 0;
        if (shouldContinue) {
            runningThreads.insert(luaThread);
        } else {
            delete luaThread;
        }
    }
}

//------------------------------------------------------------------------------

void LuaRunner::runPending()
{
    pendingThreads_t newThreads;
    newThreads.swap(pendingThreads);

    for(pendingThreads_t::iterator i = newThreads.begin(); i!=newThreads.end();
        ++i)
    {
        LuaThread* luaThread = *i;
        currentThread = luaThread;
        bool shouldContinue = luaThread->start();
        currentThread = 0;
        if (shouldContinue) {
            runningThreads.insert(luaThread);
        } else {
            delete luaThread;
        }
    }
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:

