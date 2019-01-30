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

#ifndef LUARUNNER_H
#define LUARUNNER_H
//------------------------------------------------------------------------------

#include "LuaThread.h"

#include <lwt/Thread.h>
#include <lwt/BlockedThread.h>

#include <vector>
#include <set>

//------------------------------------------------------------------------------

class LuaState;

//------------------------------------------------------------------------------

/**
 * A thread that takes care of running the various Lua threads.
 */
class LuaRunner : public lwt::Thread
{
private:
    /**
     * A timeout handler for the Lua runner.
     */
    class TimeoutHandler;

    friend class TimeoutHandler;

    /**
     * A comparator for the running threads.
     */
    struct Less
    {
        bool operator()(const LuaThread* thread1,
                        const LuaThread* thread2) const;
    };

    /**
     * Type for the vector of pending threads.
     */
    typedef std::vector<LuaThread*> pendingThreads_t;

    /**
     * Type for the set of running threads.
     */
    typedef std::set<LuaThread*, Less> runningThreads_t;

    /**
     * An event to be handled.
     */
    struct Event
    {
        LuaState* luaState;

        Control* control;

        int type;

        int code;

        int value;

        Event(LuaState& luaState, Control& control,
              int type, int code, int event);
    };

    /**
     * Type for the vector of pending events.
     */
    typedef std::vector<Event> pendingEvents_t;

    /**
     * The only instance of this class.
     */
    static LuaRunner* instance;

public:
    /**
     * Get the only instance of this class.
     */
    static LuaRunner& get();

private:
    /**
     * The blocker on which this thread waits.
     */
    lwt::BlockedThread blocker;

    /**
     * The pending events.
     */
    pendingEvents_t pendingEvents;

    /**
     * The Lua threads waiting for execution.
     */
    pendingThreads_t pendingThreads;

    /**
     * The set of running threads ordered by the timeouts.
     */
    runningThreads_t runningThreads;

    /**
     * The control on behalf of which we currently execute code.
     */
    Control* currentControl;

    /**
     * Indicate if we should stop;
     */
    bool toStop;

public:
    /**
     * Construct the LuaRunner
     */
    LuaRunner();

    /**
     * Add a new event to be processed.
     */
    void newEvent(LuaState& luaState, Control& control,
                  int eventType, int eventCode, int eventValue);

    /**
     * Add a thread to the runner.
     */
    void newThread(LuaState& luaState);

    /**
     * Get the control whose thread is currently running. It should be
     * called only from within a thread!
     */
    Control& getCurrentControl() const;

    /**
     * Cancel the delay if the given thread, if it is cancellable.
     */
    bool cancelDelay(LuaThread* luaThread);

    /**
     * Resume the given thread joining another one.
     */
    void resumeJoiner(LuaThread* luaThread);

    /**
     * Stop the Lua runner.
     */
    void stop();

private:
    /**
     * Delete the given thread.
     */
    void deleteThread(LuaThread* luaThread);

    /**
     * Perform the operation of the thread.
     */
    virtual void run();

    /**
     * Handle the pending events, if any.
     */
    void handleEvents();

    /**
     * Resume the running threads that are eligible.
     */
    void resumeRunning();

    /**
     * Run the pending threads, if any.
     */
    void runPending();

    friend class Joystick;
};

//------------------------------------------------------------------------------
// Inline definition
//------------------------------------------------------------------------------

inline bool LuaRunner::Less::operator()(const LuaThread* thread1,
                                        const LuaThread* thread2) const
{
    millis_t t1 = thread1->getTimeout();
    millis_t t2 = thread2->getTimeout();
    return t1<t2 || (t1==t2 && thread1<thread2);
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

inline LuaRunner::Event::Event(LuaState& luaState, Control& control,
                               int type, int code, int value) :
    luaState(&luaState),
    control(&control),
    type(type),
    code(code),
    value(value)
{
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

inline LuaRunner& LuaRunner::get()
{
    return *instance;
}

//------------------------------------------------------------------------------

inline Control& LuaRunner::getCurrentControl() const
{
    assert(currentControl!=0);
    return *currentControl;
}

//------------------------------------------------------------------------------
#endif // LUARUNNER_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
