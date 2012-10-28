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

vector< Struct< uint32_t,
                Struct< uint16_t, uint16_t, uint16_t, uint16_t >,
                string,
                string,
                string,
                vector< Struct< uint16_t, int32_t > >,
                vector< Struct< uint16_t, int32_t, int32_t, int32_t > > > >
DBusAdaptor::getJoysticks()
{
    Log::debug("DBusAdaptor::getJoysticks\n");

    vector< Struct< uint32_t,
                    Struct< uint16_t, uint16_t, uint16_t, uint16_t >,
                    string,
                    string,
                    string,
                    vector< Struct< uint16_t, int32_t > >,
                    vector< Struct< uint16_t, int32_t, int32_t, int32_t > > > > js;

    Struct< uint32_t,
            Struct< uint16_t, uint16_t, uint16_t, uint16_t >,
            string,
            string,
            string,
            vector< Struct< uint16_t, int32_t > >,
            vector< Struct< uint16_t, int32_t, int32_t, int32_t > > > data;

    const Joystick::joysticks_t& joysticks = Joystick::getAll();
    for(Joystick::joysticks_t::const_iterator i = joysticks.begin();
        i!=joysticks.end(); ++i)
    {
        const Joystick* joystick = i->second;

        data._1 = static_cast<uint32_t>(joystick->getID());

        const struct input_id& inputID = joystick->getInputID();
        data._2._1 = inputID.bustype;
        data._2._2 = inputID.vendor;
        data._2._3 = inputID.product;
        data._2._4 = inputID.version;

        data._3 = joystick->getName();
        data._4 = joystick->getPhys();
        data._5 = joystick->getUniq();

        Struct< uint16_t, int32_t > keyData;
        for(int code = 0; code<KEY_CNT; ++code) {
            Key* key = joystick->findKey(code);
            if (key!=0) {
                keyData._1 = static_cast<uint16_t>(code);
                keyData._2 = key->isPressed() ? 1 : 0;
                data._6.push_back(keyData);
            }
        }

        Struct< uint16_t, int32_t, int32_t, int32_t > axisData;
        for(int code = 0; code<ABS_CNT; ++code) {
            Axis* axis = joystick->findAxis(code);
            if (axis!=0) {
                axisData._1 = static_cast<uint16_t>(code);
                axisData._2 = axis->getValue();
                axisData._3 = axis->getMinimum();
                axisData._4 = axis->getMaximum();
                data._7.push_back(axisData);
            }
        }

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
