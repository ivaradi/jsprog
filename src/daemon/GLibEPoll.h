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

#pragma once

//-----------------------------------------------------------------------------

#include <lwt/EPoll.h>

#include <vector>
#include <map>
#include <memory>

#include <cassert>

#include <glib.h>

//-----------------------------------------------------------------------------

/**
 * EPoll implementation that works with a GLib main loop context. Before each
 * poll it queries the context for the file descriptors to poll. Each file
 * descriptor will be wrapped into a PolledFD which updates the file descriptor
 * array according to the events that occurred. After the polls, the GLib loop
 * will be called with the updated file descriptor data.
 */
class GLibEPoll : public lwt::EPoll
{
private:
    /**
     * File descriptor wrapper for a GLib file descriptor.
     */
    class GLibFD : public lwt::PolledFD
    {
    public:
        /**
         * Get the events for the given GLib poll filedescriptor converted to
         * epoll events.
         */
        static uint32_t getEvents(const GPollFD& gpollFD);

        /**
         * Set the revents member of the given GLib poll filedescriptor from
         * the given epoll events.
         */
        static void setREvents(GPollFD& gpollFD, uint32_t epollEvents);

    public:
        /**
         * The epoll object this file descriptor belongs to.
         */
        GLibEPoll& epoll;

        /**
         * The index within the file descriptor array.
         */
        size_t index;

    public:
        /**
         * Construct a file descriptor for the given OS-level file descriptor,
         * events and index.
         */
        GLibFD(GLibEPoll& epoll, int fd, uint32_t events, size_t index);

        /**
         * Destroy the wrapper. The file descriptor will be cleared to avoid
         * closing it.
         */
        virtual ~GLibFD();

        /**
         * Update the index.
         */
        void setIndex(size_t i);

    private:
        /**
         * Handle the events by updating the GPollFD array.
         */
        virtual void handleEvents(uint32_t events) override;
    };

    /**
     * Type for the vector of GLib poll file descriptors.
     */
    using gPollFileDescriptors_t = std::vector<GPollFD>;

    /**
     * Type for a mapping of file descriptors
     */
    using fileDescriptors_t = std::map<int, std::unique_ptr<GLibFD>>;

    /**
     * The thread-specific instance of the epoll handler.
     */
    static thread_local GLibEPoll* instance;

public:
    /**
     * Get the only instance of the epoll handler.
     */
    static GLibEPoll& get();

private:
    /**
     * The GLib main loop context we work with.
     */
    GMainContext* context;

    /**
     * The GLib poll descriptors.
     */
    gPollFileDescriptors_t gPollFileDescriptors;

    /**
     * Our own file descriptors.
     */
    fileDescriptors_t fileDescriptors;

public:
    /**
     * Construct the epoll handler with the given main context.
     */
    GLibEPoll(GMainContext* context = g_main_context_default());

    /**
     * Destroy the epoll handler.
     */
    ~GLibEPoll();

    /**
     * Release the GLib main context.
     */
    void releaseContext();

    /**
     * Wait for events with the given timeout. Any events received
     * will be processed, i.e. the corresponding file descriptors will
     * be called.
     */
    virtual int wait(bool& hadEvents, int timeout = -1);
};

//-----------------------------------------------------------------------------
// Inline definitions
//-----------------------------------------------------------------------------

inline GLibEPoll::GLibFD::
GLibFD(GLibEPoll& epoll, int fd, uint32_t events, size_t index) :
    lwt::PolledFD(fd, events),
    epoll(epoll),
    index(index)
{
}

//-----------------------------------------------------------------------------

inline void GLibEPoll::GLibFD::setIndex(size_t i)
{
    index = i;
}

//-----------------------------------------------------------------------------
//-----------------------------------------------------------------------------

inline GLibEPoll& GLibEPoll::get()
{
    assert(instance!=nullptr);

    return *instance;
}

//-----------------------------------------------------------------------------

// Local variables:
// mode: c++
// End:
