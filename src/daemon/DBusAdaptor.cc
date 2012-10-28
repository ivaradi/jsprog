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

#include "DBusAdaptor.h"

#include "Joystick.h"

#include "Log.h"

//------------------------------------------------------------------------------

using DBus::Connection;
using DBus::Struct;

using std::string;
using std::vector;

//------------------------------------------------------------------------------

DBusAdaptor* DBusAdaptor::create()
{
    Connection connection = Connection::SessionBus();
    return new DBusAdaptor(connection);
}

//------------------------------------------------------------------------------

DBusAdaptor::DBusAdaptor(DBus::Connection& connection) :
    DBus::ObjectAdaptor(connection, "/hu/varadiistvan/JSProg")
{
}

//------------------------------------------------------------------------------

vector< Struct< string, string, string > > DBusAdaptor::getJoysticks()
{
    Log::debug("DBusAdaptor::getJoysticks\n");
    vector< Struct< string, string, string > > js;

    Struct< string, string, string > data;

    const Joystick::joysticks_t& joysticks = Joystick::getAll();
    for(Joystick::joysticks_t::const_iterator i = joysticks.begin();
        i!=joysticks.end(); ++i)
    {
        const Joystick* joystick = i->second;

        data._1 = joystick->getName();
        data._2 = joystick->getPhys();
        data._3 = joystick->getUniq();

        js.push_back(data);
    }

    return js;
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
