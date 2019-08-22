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

#include "DBusAdaptor.h"

#include <gio/gio.h>

//------------------------------------------------------------------------------

/**
 * The central class for communicating via D-Bus. It wraps some of the
 * functions of GLib's D-Bus interface.
 */
class DBusHandler
{
private:
    /**
     * Called when the bus has been acquired.
     */
    static void busAcquiredCallback(GDBusConnection* connection,
                                    const gchar* name,
                                    gpointer userData);

    /**
     * Called when the name has been acquired.
     */
    static void nameAcquiredCallback(GDBusConnection* connection,
                                     const gchar* name,
                                     gpointer userData);

    /**
     * Called when the name has been lost.
     */
    static void nameLostCallback(GDBusConnection* connection,
                                 const gchar* name,
                                 gpointer userData);

    /**
     * The ID of the requested name.
     */
    unsigned nameID = 0;

    /**
     * The D-Bus adaptor this handler manages.
     */
    DBusAdaptor dbusAdaptor;

public:
    /**
     * Construct the handler.
     */
    DBusHandler();

    /**
     * Destroy the handler. It unknowns the name, if any.
     */
    ~DBusHandler();

    /**
     * Try owning the given name on the session bus.
     */
    void requestName(const char* name);

    /**
     * Stop the handler by closing the connection.
     */
    void stop();
};

//------------------------------------------------------------------------------
#endif // JSPROG_DBUSHANDLER_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
