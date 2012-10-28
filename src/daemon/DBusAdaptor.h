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

#ifndef JSPROG_DBUSADAPTOR_H
#define JSPROG_DBUSADAPTOR_H
//------------------------------------------------------------------------------

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#include "JSProgDBus.h"
#pragma GCC diagnostic pop

#include <dbus-c++/dispatcher.h>

//------------------------------------------------------------------------------

/**
 * The D-Bus adaptor implementing our calls.
 */
class DBusAdaptor : public hu::varadiistvan::JSProg_adaptor,
                    public DBus::ObjectAdaptor
{
public:
    /**
     * Create an instance of the adaptor with a connection to the session bus.
     */
    static DBusAdaptor* create();

public:
    /**
     * Construct the adaptor with the given connection.
     */
    DBusAdaptor(DBus::Connection& connection);

    /**
     * The implementation of the getJoysticks() call.
     */
    virtual std::vector< ::DBus::Struct< std::string, std::string, std::string > >
    getJoysticks();
};

//------------------------------------------------------------------------------
#endif // JSPROG_DBUSADAPTOR_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
