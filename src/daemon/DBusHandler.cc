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

#include <gio/gio.h>

//------------------------------------------------------------------------------

void DBusHandler::busAcquiredCallback(GDBusConnection* connection,
                                      const gchar* name,
                                      gpointer userData)
{
    Log::debug("DBusHandler::busAcquiredCallback\n");
    auto handler = reinterpret_cast<DBusHandler*>(userData);
    handler->dbusAdaptor.exportInterface(connection);
}

//------------------------------------------------------------------------------

void DBusHandler::nameAcquiredCallback(GDBusConnection* connection,
                                       const gchar* name,
                                       gpointer userData)
{
    Log::debug("DBusHandler::nameAcquiredCallback\n");
}

//------------------------------------------------------------------------------

void DBusHandler::nameLostCallback(GDBusConnection* connection,
                                   const gchar* name,
                                   gpointer userData)
{
    Log::debug("DBusHandler::nameLostCallback\n");
}

//------------------------------------------------------------------------------

DBusHandler::DBusHandler() :
    dbusAdaptor(*this)
{
}

//------------------------------------------------------------------------------

DBusHandler::~DBusHandler()
{
    if (nameID!=0) {
        g_bus_unown_name(nameID);
    }
}

//------------------------------------------------------------------------------

void DBusHandler::requestName(const char* name)
{
    if (nameID!=0) {
        g_bus_unown_name(nameID);
    }

    Log::debug("DBusHandler::requestName: '%s'\n", name);

    g_bus_own_name(G_BUS_TYPE_SESSION, name,
                   static_cast<GBusNameOwnerFlags>(
                       G_BUS_NAME_OWNER_FLAGS_ALLOW_REPLACEMENT |
                       G_BUS_NAME_OWNER_FLAGS_REPLACE),
                   &busAcquiredCallback,
                   &nameAcquiredCallback,
                   &nameLostCallback,
                   this, nullptr);
}

//------------------------------------------------------------------------------

void DBusHandler::stop()
{
    if (nameID!=0) {
        g_bus_unown_name(nameID);
        nameID = 0;
    }
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
