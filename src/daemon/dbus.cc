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

#include "dbus.h"

#include "Log.h"
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#include "JSProgDBus.h"
#pragma GCC diagnostic pop

#include <dbus-c++/dispatcher.h>
#include <dbus/dbus.h>

#include <lwt/PolledFD.h>
#include <lwt/EPoll.h>
#include <lwt/Timer.h>

//------------------------------------------------------------------------------

using lwt::EPoll;

//------------------------------------------------------------------------------

namespace {

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
     * The file descriptor.
     */
    WatchFD* watchFD;

public:
    /**
     * Construct the watch
     */
    DBusWatch(DBus::Watch::Internal* internal);

    /**
     * Destroy the watch.
     */
    virtual ~DBusWatch();

    /**
     * Toggle the watch.
     */
    virtual void toggle();
};

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
    Log::debug("DBusWatch::WatchFD::handleEvents: %04x\n", events);
    int flags = 0;
    if ((events&EPOLLIN)!=0) flags |= DBUS_WATCH_READABLE;
    if ((events&EPOLLOUT)!=0) flags |= DBUS_WATCH_WRITABLE;
    if ((events&EPOLLHUP)!=0) flags |= DBUS_WATCH_HANGUP;
    if ((events&EPOLLERR)!=0) flags |= DBUS_WATCH_ERROR;
    watch.handle(flags);
    DBus::default_dispatcher->dispatch_pending();
}

//------------------------------------------------------------------------------

DBusWatch::DBusWatch(DBus::Watch::Internal* internal) :
    DBus::Watch(internal),
    watchFD( enabled() ? new WatchFD(*this) : 0 )
{
    Log::debug("DBusWatch: descriptor=%d, flags=%d, enabled=%d\n",
               descriptor(), flags(), enabled());
}

//------------------------------------------------------------------------------

DBusWatch::~DBusWatch()
{
    if (watchFD!=0) {
        EPoll::get().destroy(watchFD);
    }
}

//------------------------------------------------------------------------------

void DBusWatch::toggle()
{
    Log::debug("DBusWatch::toggle: watchFD=%p, enabled=%d\n", watchFD, enabled());
    if (watchFD==0) {
        watchFD = new WatchFD(*this);
    } else {
        EPoll::get().destroy(watchFD);
        watchFD = 0;
    }
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

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
     * The current timer, if the timeout is enabled.
     */
    Timer* timer;

public:
    /**
     * Construct the timeout.
     */
    DBusTimeout(DBus::Timeout::Internal* internal);

    /**
     * Destroy the timeout
     */
    virtual ~DBusTimeout();

    /**
     * Toggle the timeout.
     */
    virtual void toggle();
};

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
    Log::debug("Timer::handleTimeout\n");

    handling = true;

    dbusTimeout.handle();

    handling = false;

    if (shouldDelete) {
        return false;
    } else {
        timeout += dbusTimeout.interval();
        return true;
    }
}

//------------------------------------------------------------------------------

DBusTimeout::DBusTimeout(DBus::Timeout::Internal* internal) :
    DBus::Timeout(internal),
    timer(enabled() ? new Timer(*this) : 0)
{
    Log::debug("DBusTimeout: interval=%d, enabled=%d\n",
               interval(), enabled());
}

//------------------------------------------------------------------------------

DBusTimeout::~DBusTimeout()
{
    if (timer!=0) Timer::destroy(timer);
}

//------------------------------------------------------------------------------

void DBusTimeout::toggle()
{
    Log::debug("DBusTimeout::toggle: timer=%p, enabled=%d\n", timer, enabled());
    if (timer==0) {
        timer = new Timer(*this);
    } else {
        Timer::destroy(timer);
        timer = 0;
    }
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

/**
 * A dispatcher that is integrated with the LWT event loop.
 */
class DBusDispatcher : public DBus::Dispatcher
{
public:
    virtual void enter();

    virtual void leave();

    virtual DBus::Timeout* add_timeout(DBus::Timeout::Internal* internal);

    virtual void rem_timeout(DBus::Timeout* timeout);

    virtual DBus::Watch* add_watch(DBus::Watch::Internal* internal);

    virtual void rem_watch(DBus::Watch* watch);
};

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
    Log::debug("DBusDispatcher::add_timeout: internal=%p\n", internal);
    return new DBusTimeout(internal);
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
    return new DBusWatch(internal);
}

//------------------------------------------------------------------------------

void DBusDispatcher::rem_watch(DBus::Watch* watch)
{
    Log::debug("DBusDispatcher::rem_watch: watch=%p\n", watch);
    delete watch;
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

class Adaptor : public hu::varadiistvan::JSProg_adaptor,
                public DBus::ObjectAdaptor
{
public:
    Adaptor(DBus::Connection& connection);

    virtual std::vector< ::DBus::Struct< std::string, std::string, std::string > > getJoysticks();
};

//------------------------------------------------------------------------------

Adaptor::Adaptor(DBus::Connection& connection) :
    DBus::ObjectAdaptor(connection, "/hu/varadiistvan/JSProg")
{
}

//------------------------------------------------------------------------------

std::vector< ::DBus::Struct< std::string, std::string, std::string > >
Adaptor::getJoysticks()
{
    Log::debug("Adaptor::getJoysticks\n");
    std::vector< ::DBus::Struct< std::string, std::string, std::string > > js;
    ::DBus::Struct< std::string, std::string, std::string > data;

    data._1 = "Saitek X52";
    data._2 = "usb0";
    data._3 = "";
    js.push_back(data);

    return js;
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

class DBusWrapper
{
private:
    DBus::Connection connection;

public:
    DBusWrapper();
};

//------------------------------------------------------------------------------

DBusWrapper::DBusWrapper() :
    connection(DBus::Connection::SessionBus())
{
    connection.request_name("hu.varadiistvan.JSProg");
    new Adaptor(connection);
}

//------------------------------------------------------------------------------


//------------------------------------------------------------------------------

} /* namespace */

//------------------------------------------------------------------------------

void initializeDBus()
{
    DBus::default_dispatcher = new DBusDispatcher();
    try {
        new DBusWrapper();
    } catch (const DBus::Error& e) {
        Log::error("initializeDBus: %s\n", e.what());
    }
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
