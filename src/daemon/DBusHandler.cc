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

#include "DBusHandler.h"

#include "Log.h"

#include <dbus/dbus.h>

#include <lwt/PolledFD.h>
#include <lwt/EPoll.h>
#include <lwt/Timer.h>

//------------------------------------------------------------------------------

using DBus::Connection;

using lwt::EPoll;

//------------------------------------------------------------------------------

/**
 * A timeout handler that works with the LWT event loop.
 */
class DBusTimeout : public DBus::Timeout
{
private:
    /**
     * LWT timer for this timeout.
     */
    class Timer : public lwt::Timer
    {
    public:
        /**
         * Destroy the given timer. If it is currently handling a
         * timeout, only the 'shouldDelete' variable will be set, and
         * the handler will then return false. Otherwise the time is
         * cancelled and deleted.
         */
        static void destroy(Timer* timer);

    private:
        /**
         * The timeout this timer belongs to.
         */
        DBusTimeout& dbusTimeout;

        /**
         * Indicate if a timeout is being handled by this timer.
         */
        bool handling;

        /**
         * Indicate if the timer should be deleted.
         */
        bool shouldDelete;

    public:
        /**
         * Construct the timer for the given timeout.
         */
        Timer(DBusTimeout& timeout);

    protected:
        /**
         * Handle the timeout.
         */
        virtual bool handleTimeout();
    };

private:
    /**
     * The dispatcher this timeout belongs to.
     */
    DBusDispatcher& dispatcher;

    /**
     * The current timer, if the timeout is enabled.
     */
    Timer* timer;

public:
    /**
     * Construct the timeout. It is added to the given dispatcher.
     */
    DBusTimeout(DBusDispatcher& dispatcher,
                DBus::Timeout::Internal* internal);

    /**
     * Destroy the timeout. It is removed from the dispatcher.
     */
    virtual ~DBusTimeout();

    /**
     * Toggle the timeout.
     */
    virtual void toggle();
};

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

/**
 * A DBus watch integrated with the LWT event loop.
 */
class DBusWatch : public DBus::Watch
{
private:
    /**
     * The polled file descriptor for this watch.
     */
    class WatchFD : public lwt::PolledFD
    {
    private:
        /**
         * Get the event flags for the given watch flags.
         */
        static uint32_t getEventsFor(int flags);

        /**
         * The DBusWatch this polled file descriptor belongs to.
         */
        DBusWatch& watch;

    public:
        /**
         * Construct the file descriptor for the given watch.
         */
        WatchFD(DBusWatch& watch);

        /**
         * Destroy the file descriptor. It clears the fd member
         * variable so that it does not get closed by the parent's
         * destructor.
         */
        virtual ~WatchFD();

    protected:
        /**
         * Handle the given events.
         */
        virtual void handleEvents(uint32_t events);
    };

private:
    /**
     * The dispatcher this watch belongs to.
     */
    DBusDispatcher& dispatcher;

    /**
     * The file descriptor.
     */
    WatchFD* watchFD;

public:
    /**
     * Construct the watch. It is added to the given dispatcher.
     */
    DBusWatch(DBusDispatcher& dispatcher, DBus::Watch::Internal* internal);

    /**
     * Destroy the watch. It is removed from the associated dispatcher.
     */
    virtual ~DBusWatch();

    /**
     * Toggle the watch.
     */
    virtual void toggle();

    /**
     * Disable the watch.
     */
    void disable();
};

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

/**
 * A dispatcher that is integrated with the LWT event loop.
 */
class DBusDispatcher : public DBus::Dispatcher
{
private:
    /**
     * The set of timeouts currently existing.
     */
    std::set<DBusTimeout*> timeouts;

    /**
     * The set of watches currently existing.
     */
    std::set<DBusWatch*> watches;

public:
    /**
     * Destroy the dispatcher. It deletes all timeouts and watches.
     */
    virtual ~DBusDispatcher();

    /**
     * Enter the dispatcher. Does not seem to be used.
     */
    virtual void enter();

    /**
     * Leave the dispatcher. Does not seem to be used.
     */
    virtual void leave();

    /**
     * Add a timeout with the given internal data. It creates a new
     * instance of DBusTimeout.
     */
    virtual DBus::Timeout* add_timeout(DBus::Timeout::Internal* internal);

    /**
     * Remove the given timeout. It is simply deleted.
     */
    virtual void rem_timeout(DBus::Timeout* timeout);

    /**
     * Add a watch with the given internal data. It creates a new
     * instance of DBusWatch.
     */
    virtual DBus::Watch* add_watch(DBus::Watch::Internal* internal);

    /**
     * Remove the given watch. It is simply deleted.
     */
    virtual void rem_watch(DBus::Watch* watch);

    /**
     * Stop the dispatcher. It disables all watches and timeouts.
     */
    void stop();

    friend class DBusTimeout;
    friend class DBusWatch;
};

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

void DBusTimeout::Timer::destroy(Timer* timer)
{
    if (timer->handling) {
        timer->shouldDelete = true;
    } else {
        timer->cancel();
        delete timer;
    }
}

//------------------------------------------------------------------------------

DBusTimeout::Timer::Timer(DBusTimeout& timeout) :
    lwt::Timer(currentTimeMillis() + timeout.interval()),
    dbusTimeout(timeout),
    handling(false),
    shouldDelete(false)
{
}

//------------------------------------------------------------------------------

bool DBusTimeout::Timer::handleTimeout()
{
    Log::debug("DBusTimeout[%p]::Timer::handleTimeout\n", &dbusTimeout);

    handling = true;

    dbusTimeout.handle();
    dbusTimeout.dispatcher.dispatch_pending();

    handling = false;

    if (shouldDelete) {
        return false;
    } else {
        timeout += dbusTimeout.interval();
        return true;
    }
}

//------------------------------------------------------------------------------

DBusTimeout::DBusTimeout(DBusDispatcher& dispatcher,
                         DBus::Timeout::Internal* internal) :
    DBus::Timeout(internal),
    dispatcher(dispatcher),
    timer(enabled() ? new Timer(*this) : 0)
{
    dispatcher.timeouts.insert(this);
    Log::debug("DBusTimeout[%p]: interval=%d, enabled=%d\n",
               this, interval(), enabled());
}

//------------------------------------------------------------------------------

DBusTimeout::~DBusTimeout()
{
    if (timer!=0) Timer::destroy(timer);
    dispatcher.timeouts.erase(this);
}

//------------------------------------------------------------------------------

void DBusTimeout::toggle()
{
    Log::debug("DBusTimeout[%p]::toggle: timer=%p, enabled=%d\n",
               this, timer, enabled());
    if (timer==0) {
        timer = new Timer(*this);
    } else {
        Timer::destroy(timer);
        timer = 0;
    }
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

uint32_t DBusWatch::WatchFD::getEventsFor(int flags)
{
    uint32_t events = EPOLLHUP|EPOLLERR;
    if ((flags&DBUS_WATCH_READABLE)) events |= EPOLLIN;
    if ((flags&DBUS_WATCH_WRITABLE)) events |= EPOLLOUT;
    return events;
}

//------------------------------------------------------------------------------

inline DBusWatch::WatchFD::WatchFD(DBusWatch& watch) :
    PolledFD(watch.descriptor(), getEventsFor(watch.flags())),
    watch(watch)
{
}

//------------------------------------------------------------------------------

DBusWatch::WatchFD::~WatchFD()
{
    fd = -1;
}

//------------------------------------------------------------------------------

void DBusWatch::WatchFD::handleEvents(uint32_t events)
{
    Log::debug("DBusWatch[%p]::WatchFD::handleEvents: %04x\n", &watch, events);
    int flags = 0;
    if ((events&EPOLLIN)!=0) flags |= DBUS_WATCH_READABLE;
    if ((events&EPOLLOUT)!=0) flags |= DBUS_WATCH_WRITABLE;
    if ((events&EPOLLHUP)!=0) flags |= DBUS_WATCH_HANGUP;
    if ((events&EPOLLERR)!=0) flags |= DBUS_WATCH_ERROR;
    if (watch.handle(flags)) {
        watch.dispatcher.dispatch_pending();
    }
}

//------------------------------------------------------------------------------

DBusWatch::DBusWatch(DBusDispatcher& dispatcher, DBus::Watch::Internal* internal) :
    DBus::Watch(internal),
    dispatcher(dispatcher),
    watchFD( enabled() ? new WatchFD(*this) : 0 )
{
    dispatcher.watches.insert(this);
    Log::debug("DBusWatch[%p]: descriptor=%d, flags=%d, enabled=%d\n",
               this, descriptor(), flags(), enabled());
}

//------------------------------------------------------------------------------

DBusWatch::~DBusWatch()
{
    if (watchFD!=0) {
        EPoll::get().destroy(watchFD);
    }
    dispatcher.watches.erase(this);
}

//------------------------------------------------------------------------------

void DBusWatch::toggle()
{
    Log::debug("DBusWatch[%p]::toggle: watchFD=%p, enabled=%d\n",
               this, watchFD, enabled());
    if (watchFD==0) {
        watchFD = new WatchFD(*this);
    } else {
        disable();
    }
}

//------------------------------------------------------------------------------

void DBusWatch::disable()
{
    EPoll::get().destroy(watchFD);
    watchFD = 0;
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

DBusDispatcher::~DBusDispatcher()
{
    while(!timeouts.empty()) {
        delete *timeouts.begin();
    }
    while(!watches.empty()) {
        delete *watches.begin();
    }
}

//------------------------------------------------------------------------------

void DBusDispatcher::enter()
{
    Log::debug("DBusDispatcher::enter\n");
}

//------------------------------------------------------------------------------

void DBusDispatcher::leave()
{
    Log::debug("DBusDispatcher::leave\n");
}

//------------------------------------------------------------------------------

DBus::Timeout* DBusDispatcher::add_timeout(DBus::Timeout::Internal* internal)
{
    Log::debug("DBusDispatcher::add_timeout\n", internal);
    return new DBusTimeout(*this, internal);
}

//------------------------------------------------------------------------------

void DBusDispatcher::rem_timeout(DBus::Timeout* timeout)
{
    Log::debug("DBusDispatcher::rem_timeout: timeout=%p\n", timeout);
    delete timeout;
}

//------------------------------------------------------------------------------

DBus::Watch* DBusDispatcher::add_watch(DBus::Watch::Internal* internal)
{
    Log::debug("DBusDispatcher::add_watch: internal=%p\n", internal);
    return new DBusWatch(*this, internal);
}

//------------------------------------------------------------------------------

void DBusDispatcher::rem_watch(DBus::Watch* watch)
{
    Log::debug("DBusDispatcher::rem_watch: watch=%p\n", watch);
    delete watch;
}

//------------------------------------------------------------------------------

void DBusDispatcher::stop()
{
    for(std::set<DBusWatch*>::iterator i = watches.begin();
        i!=watches.end(); ++i)
    {
        DBusWatch* watch = *i;
        watch->disable();
    }
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

DBusHandler::DBusHandler() :
    dispatcher(new DBusDispatcher()),
    connection(0)
{
    DBus::default_dispatcher = dispatcher;
    connection = new Connection(Connection::SessionBus());
}

//------------------------------------------------------------------------------

DBusHandler::~DBusHandler()
{
    delete connection;
    if (DBus::default_dispatcher==dispatcher) {
        DBus::default_dispatcher = 0;
    }
    delete dispatcher;
    dispatcher = 0;
}

//------------------------------------------------------------------------------

void DBusHandler::requestName(const char* name)
{
    connection->request_name(name);
}

//------------------------------------------------------------------------------

void DBusHandler::stop()
{
    dispatcher->stop();
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
