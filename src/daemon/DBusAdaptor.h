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
                    public DBus::ObjectAdaptor,
                    public DBus::IntrospectableAdaptor
{
private:
    /**
     * The only instance of the adaptor.
     */
    static DBusAdaptor* instance;

public:
    /**
     * Get the only instance of the adaptor.
     */
    static DBusAdaptor& get();

public:
    /**
     * Construct the adaptor with the given connection.
     */
    DBusAdaptor(DBus::Connection& connection);

    /**
     * Destroy the adaptor.
     */
    virtual ~DBusAdaptor();

    /**
     * The implementation of the getJoysticks() call.
     */
    virtual std::vector< ::DBus::Struct< uint32_t, ::DBus::Struct< uint16_t, uint16_t, uint16_t, uint16_t >, std::string, std::string, std::string, std::vector< ::DBus::Struct< uint16_t, int32_t > >, std::vector< ::DBus::Struct< uint16_t, int32_t, int32_t, int32_t > > > >
    getJoysticks();

    /**
     * The implementation of the loadProfile() call
     */
    virtual bool loadProfile(const uint32_t& id, const std::string& profileXML);
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline DBusAdaptor& DBusAdaptor::get()
{
    return *instance;
}

//------------------------------------------------------------------------------
#endif // JSPROG_DBUSADAPTOR_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
