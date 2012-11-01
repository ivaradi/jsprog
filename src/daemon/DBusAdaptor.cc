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

DBusAdaptor* DBusAdaptor::instance = 0;

//------------------------------------------------------------------------------

void DBusAdaptor::inputID2DBus(Struct< uint16_t, uint16_t, uint16_t, uint16_t >& dest,
                               const struct input_id& inputID)
{
    dest._1 = inputID.bustype;
    dest._2 = inputID.vendor;
    dest._3 = inputID.product;
    dest._4 = inputID.version;
}

//------------------------------------------------------------------------------

void DBusAdaptor::keys2DBus(vector< Struct< uint16_t, int32_t > >& dest,
                            const Joystick& joystick)
{
    Struct< uint16_t, int32_t > keyData;
    for(int code = 0; code<KEY_CNT; ++code) {
        Key* key = joystick.findKey(code);
        if (key!=0) {
            keyData._1 = static_cast<uint16_t>(code);
            keyData._2 = key->isPressed() ? 1 : 0;
            dest.push_back(keyData);
        }
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::axes2DBus(vector< Struct< uint16_t, int32_t, int32_t, int32_t > >& dest,
                            const Joystick& joystick)
{
    Struct< uint16_t, int32_t, int32_t, int32_t > axisData;
    for(int code = 0; code<ABS_CNT; ++code) {
        Axis* axis = joystick.findAxis(code);
        if (axis!=0) {
            axisData._1 = static_cast<uint16_t>(code);
            axisData._2 = axis->getValue();
            axisData._3 = axis->getMinimum();
            axisData._4 = axis->getMaximum();
            dest.push_back(axisData);
        }
    }
}

//------------------------------------------------------------------------------

DBusAdaptor::DBusAdaptor(DBus::Connection& connection) :
    DBus::ObjectAdaptor(connection, "/hu/varadiistvan/JSProg")
{
    instance = this;
}

//------------------------------------------------------------------------------

DBusAdaptor::~DBusAdaptor()
{
    instance = 0;
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

        inputID2DBus(data._2, joystick->getInputID());

        data._3 = joystick->getName();
        data._4 = joystick->getPhys();
        data._5 = joystick->getUniq();

        keys2DBus(data._6, *joystick);

        axes2DBus(data._7, *joystick);

        js.push_back(data);
    }

    return js;
}

//------------------------------------------------------------------------------

bool DBusAdaptor::loadProfile(const uint32_t& id, const string& profileXML)
{
    Joystick* joystick = Joystick::find(id);
    if (joystick==0) return false;

    Profile profile(profileXML.c_str(), false);
    if (!profile) return false;

    return joystick->setProfile(profile);
}

//------------------------------------------------------------------------------

void DBusAdaptor::startControlSignals(const uint32_t& id)
{
    if (shouldSendControlSignals(id)) {
        ++joystick2numRequestors[id];
    } else {
        joystick2numRequestors[id] = 1;
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::stopControlSignals(const uint32_t& id)
{
    if (shouldSendControlSignals(id)) {
        if ((--joystick2numRequestors[id])==0) {
            joystick2numRequestors.erase(id);
        }
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendJoystickAdded(Joystick& joystick)
{
    Struct< uint16_t, uint16_t, uint16_t, uint16_t > inputID;
    inputID2DBus(inputID, joystick.getInputID());

    vector< Struct< uint16_t, int32_t > >  keys;
    keys2DBus(keys, joystick);

    vector< Struct< uint16_t, int32_t, int32_t, int32_t > > axes;
    axes2DBus(axes, joystick);

    joystickAdded(joystick.getID(), inputID,
                  joystick.getName(), joystick.getPhys(), joystick.getUniq(),
                  keys, axes);
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendKeyPressed(size_t joystickID, int code)
{
    if (shouldSendControlSignals(joystickID)) {
        keyPressed(joystickID, code);
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendKeyReleased(size_t joystickID, int code)
{
    if (shouldSendControlSignals(joystickID)) {
        keyReleased(joystickID, code);
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendAxisChanged(size_t joystickID, int code, int value)
{
    if (shouldSendControlSignals(joystickID)) {
        axisChanged(joystickID, code, value);
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendJoystickRemoved(Joystick& joystick)
{
    size_t joystickID = joystick.getID();
    joystick2numRequestors.erase(joystickID);
    joystickRemoved(joystickID);
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
