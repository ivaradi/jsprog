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

class Joystick;

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
     * Type for a mapping of joystick IDs to the number of clients
     * that requested signals for that joystick.
     */
    typedef std::map<size_t, size_t> joystick2numRequestors_t;

    /**
     * The only instance of the adaptor.
     */
    static DBusAdaptor* instance;

public:
    /**
     * Get the only instance of the adaptor.
     */
    static DBusAdaptor& get();

    /**
     * Convert the given input ID into the given DBus structure.
     */
    static void inputID2DBus(::DBus::Struct< uint16_t, uint16_t, uint16_t, uint16_t >& dest,
                             const struct input_id& inputID);

    /**
     * Create the array of key information for the given joystick.
     */
    static void keys2DBus(std::vector< ::DBus::Struct< uint16_t, int32_t > >& dest,
                          const Joystick& joystick);

    /**
     * Create the array of axis information for the given joystick.
     */
    static void axes2DBus(std::vector< ::DBus::Struct< uint16_t, int32_t, int32_t, int32_t > >& dest,
                          const Joystick& joystick);

private:
    /**
     * Indicate the number of signal requestors.
     */
    joystick2numRequestors_t joystick2numRequestors;

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
     * Get whether control signals should be sent for the joysyick
     * with the given ID.
     */
    bool shouldSendControlSignals(size_t joystickID);

    /**
     * The implementation of the getJoysticks() call.
     */
    virtual std::vector< ::DBus::Struct< uint32_t, ::DBus::Struct< uint16_t, uint16_t, uint16_t, uint16_t >, std::string, std::string, std::string, std::vector< ::DBus::Struct< uint16_t, int32_t > >, std::vector< ::DBus::Struct< uint16_t, int32_t, int32_t, int32_t > > > >
    getJoysticks();

    /**
     * The implementation of the loadProfile() call
     */
    virtual bool loadProfile(const uint32_t& id, const std::string& profileXML);

    /**
     * Start sending signals about control movements for a client
     * about the joystick with the given ID.
     */
    virtual void startControlSignals(const uint32_t& id);

    /**
     * Stop sending control signals for a client about the joystick
     * with the given ID.
     */
    virtual void stopControlSignals(const uint32_t& id);

    /**
     * Send the D-Bus signal about the given joystick having been added.
     */
    void sendJoystickAdded(Joystick& joystick);

    /**
     * Send the D-Bus signal about the given key of the given joystick
     * having been pressed, if signals for that joystick are requested.
     */
    void sendKeyPressed(size_t joystickID, int code);

    /**
     * Send the D-Bus signal about the given key of the given joystick
     * having been released, if signals for that joystick are requested.
     */
    void sendKeyReleased(size_t joystickID, int code);

    /**
     * Send the D-Bus signal about the given axis of the given
     * joystick having changed, if signals for the joystick are
     * requested.
     */
    void sendAxisChanged(size_t joystickID, int code, int value);

    /**
     * Send the D-Bus signal about the given joystick having been removed.
     */
    void sendJoystickRemoved(Joystick& joystick);
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline DBusAdaptor& DBusAdaptor::get()
{
    return *instance;
}

//------------------------------------------------------------------------------

inline bool DBusAdaptor::shouldSendControlSignals(size_t joystickID)
{
    return joystick2numRequestors.find(joystickID)!=
        joystick2numRequestors.end();
}

//------------------------------------------------------------------------------
#endif // JSPROG_DBUSADAPTOR_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
