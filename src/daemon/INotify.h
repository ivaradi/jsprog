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

#ifndef INOTIFY_H
#define INOTIFY_H
//------------------------------------------------------------------------------

#include <lwt/ThreadedFD.h>

#include <string>

#include <sys/inotify.h>

//------------------------------------------------------------------------------

/**
 * Wrapper for the inotify API
 */
class INotify : public lwt::ThreadedFD
{
private:
    /**
     * Size of the buffer.
     */
    static const size_t bufferSize = 512;

    /**
     * The buffer for the incoming data.
     */
    char buffer[bufferSize];

    /**
     * The length of the data in the buffer.
     */
    size_t length;

    /**
     * The offset in the buffer.
     */
    size_t offset;

public:
    /**
     * Construct the inotify file descriptor.
     */
    INotify();

protected:
    /**
     * The destructor is protected to prevent inadvertent deletion
     */
    virtual ~INotify();

public:
    /**
     * Add a watch for the given path.
     *
     * @return the watch descriptor.
     */
    int addWatch(const char* pathName, uint32_t mask);

    /**
     * Remove the watch with the given descriptor.
     */
    int removeWatch(int wd);

    /**
     * Get an event. If no event is available, it blocks until an
     * event becomes available or an error occurs.
     *
     * @return if an event could be retrieved.
     */
    bool getEvent(int& wd, uint32_t& mask, uint32_t& cookie, std::string& name);
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline INotify::INotify() :
    ThreadedFD(inotify_init()),
    length(0),
    offset(0)
{
}

//------------------------------------------------------------------------------

inline INotify::~INotify()
{
}

//------------------------------------------------------------------------------

inline int INotify::addWatch(const char* pathName, uint32_t mask)
{
    return inotify_add_watch(fd, pathName, mask);
}

//------------------------------------------------------------------------------

inline int INotify::removeWatch(int wd)
{
    return inotify_rm_watch(fd, wd);
}

//------------------------------------------------------------------------------
#endif // INOTIFY_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
