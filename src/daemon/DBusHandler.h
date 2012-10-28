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

#ifndef JSPROG_DBUSHANDLER_H
#define JSPROG_DBUSHANDLER_H
//------------------------------------------------------------------------------

#include <dbus-c++/dispatcher.h>

//------------------------------------------------------------------------------

class DBusDispatcher;

//------------------------------------------------------------------------------

/**
 * The central class for communicating via D-Bus. It sets up a
 * default dispatcher, that works with the LWT library.
 */
class DBusHandler
{
private:
    /**
     * The D-Bus dispatcher created by this handler.
     */
    DBusDispatcher* dispatcher;

    /**
     * The connection instance to use.
     */
    DBus::Connection* connection;

public:
    /**
     * Construct the handler. It creates and registers a dispatcher.
     */
    DBusHandler();

    /**
     * Destroy the handler. It destroys the dispatcher as well.
     */
    ~DBusHandler();

    /**
     * Get the connection.
     */
    DBus::Connection& getConnection();

    /**
     * Request a server name.
     */
    void requestName(const char* name);
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline DBus::Connection& DBusHandler::getConnection()
{
    return *connection;
}

//------------------------------------------------------------------------------
#endif // JSPROG_DBUSHANDLER_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
