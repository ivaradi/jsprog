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

#include "DBusHandler.h"
#include "JSProgListenerDBus.h"

#include "Joystick.h"
#include "InputDeviceListener.h"
#include "LuaRunner.h"
#include "UInput.h"

#include "Log.h"

#include <lwt/IOServer.h>

//------------------------------------------------------------------------------

using hu::varadiistvan::JSProgListener_proxy;

using lwt::IOServer;

using DBus::Connection;
using DBus::Struct;

using std::string;
using std::vector;
using std::pair;
using std::make_pair;

//------------------------------------------------------------------------------

class DBusAdaptor::JSProgListener :
    public hu::varadiistvan::JSProgListener_proxy,
    public ::DBus::ObjectProxy
{
public:
    /**
     * Construct the listener proxy.
     */
    JSProgListener(::DBus::Connection& connection, const ::DBus::Path& path,
                   const char* destination);
};

//------------------------------------------------------------------------------

inline
DBusAdaptor::JSProgListener::JSProgListener(::DBus::Connection& connection,
                                            const ::DBus::Path& path,
                                            const char* destination) :
    ObjectProxy(connection, path, destination)
{
}

//------------------------------------------------------------------------------
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

inline bool
DBusAdaptor::removeListener(size_t joystickID, listeners_t* listeners,
                            listeners_t::iterator i)
{
    JSProgListener* listener = *i;
    listeners->erase(i);
    delete listener;
    if (listeners->empty()) {
        joystick2Listeners.erase(joystickID);
        return true;
    } else {
        return false;
    }
}

//------------------------------------------------------------------------------

DBusAdaptor::DBusAdaptor(DBusHandler& dbusHandler) :
    DBus::ObjectAdaptor(dbusHandler.getConnection(), "/hu/varadiistvan/JSProg"),
    dbusHandler(dbusHandler)
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

        data._6.clear();
        keys2DBus(data._6, *joystick);

        data._7.clear();
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

bool DBusAdaptor::startMonitor(const uint32_t& id, const string& sender,
                               const ::DBus::Path& listener)
{
    if (Joystick::find(id)==0) return false;

    Log::debug("DBusAdaptor::startMonitor: joystick %u to %s\n",
               id, listener.c_str());

    listeners_t& listeners = getListeners(id);
    listeners.push_back(new JSProgListener(conn(), listener, sender.c_str()));
    return true;
}

//------------------------------------------------------------------------------

void DBusAdaptor::stopMonitor(const uint32_t& id, const ::DBus::Path& listener)
{
    listeners_t* listeners = findListeners(id);
    if (listeners!=0) {
        for(listeners_t::iterator i = listeners->begin(); i!=listeners->end();
            ++i)
        {
            if ((*i)->path()==listener) {
                removeListener(id, listeners, i);
                break;
            }
        }
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::exit()
{
    InputDeviceListener::get().stop();
    LuaRunner::get().stop();
    UInput::get().close();
    IOServer::get().stop();
    Joystick::closeAll();
    dbusHandler.stop();
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
    listeners_t* listeners = findListeners(joystickID);
    if (listeners!=0) {
        listeners_t::iterator i = listeners->begin();
        while(i!=listeners->end()) {
              listeners_t::iterator l = i++;
              try {
                  (*l)->keyPressed(joystickID, code);
              } catch(...) {
                  Log::warning("DBusAdaptor::sendKeyPressed: failed to call listener %s, erasing\n",
                               (*l)->path().c_str());
                  if (removeListener(joystickID, listeners, l)) break;
              }
        }
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendKeyReleased(size_t joystickID, int code)
{
    listeners_t* listeners = findListeners(joystickID);
    if (listeners!=0) {
        listeners_t::iterator i = listeners->begin();
        while(i!=listeners->end()) {
              listeners_t::iterator l = i++;
              try {
                  (*l)->keyReleased(joystickID, code);
              } catch(...) {
                  Log::warning("DBusAdaptor::sendKeyReleased: failed to call listener %s, erasing\n",
                               (*l)->path().c_str());
                  if (removeListener(joystickID, listeners, l)) break;
              }
        }
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendAxisChanged(size_t joystickID, int code, int value)
{
    listeners_t* listeners = findListeners(joystickID);
    if (listeners!=0) {
        listeners_t::iterator i = listeners->begin();
        while(i!=listeners->end()) {
              listeners_t::iterator l = i++;
              try {
                  (*l)->axisChanged(joystickID, code, value);
              } catch(...) {
                  Log::warning("DBusAdaptor::sendAxisChanged: failed to call listener %s, erasing\n",
                               (*l)->path().c_str());
                  if (removeListener(joystickID, listeners, l)) break;
              }
        }
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendJoystickRemoved(Joystick& joystick)
{
    size_t joystickID = joystick.getID();
    listeners_t* listeners = findListeners(joystickID);
    if (listeners!=0) {
        for(listeners_t::iterator i = listeners->begin(); i!=listeners->end();
            ++i)
        {
            delete *i;
        }
        joystick2Listeners.erase(joystickID);
    }
    joystickRemoved(joystickID);
}

//------------------------------------------------------------------------------

DBusAdaptor::listeners_t& DBusAdaptor::getListeners(size_t joystickID)
{
    listeners_t* listeners = findListeners(joystickID);
    if (listeners==0) {
        pair<joystick2Listeners_t::iterator, bool> result =
            joystick2Listeners.insert(make_pair(joystickID, listeners_t()));
        listeners = &(result.first->second);
    }
    return *listeners;
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
