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

#include "jsprog-dbus.h"

#include <list>
#include <map>
#include <vector>
#include <string>

#include <inttypes.h>

//------------------------------------------------------------------------------

class Joystick;
class DBusHandler;

//------------------------------------------------------------------------------

/**
 * The D-Bus adaptor implementing our calls.
 */
class DBusAdaptor
{
private:
    /**
     * The implementation of the JSProg listener.
     */
    class JSProgListener;

    /**
     * Type for a vector of listener information.
     */
    typedef std::list<JSProgListener*> listeners_t;

    /**
     * Type for a mapping of joystick IDs to the listeners.
     */
    typedef std::map<size_t, listeners_t > joystick2Listeners_t;

    /**
     * The only instance of the adaptor.
     */
    static DBusAdaptor* instance;

    /**
     * The callback for the getJoysticks() call.
     */
    static gboolean handleGetJoysticks(jsprogHuVaradiistvanJSProg* object,
                                       GDBusMethodInvocation* invocation,
                                       gpointer userData);

    /**
     * The callback for the getJoystickState() call.
     */
    static gboolean handleGetJoystickState(jsprogHuVaradiistvanJSProg* object,
                                           GDBusMethodInvocation* invocation,
                                           guint arg_id, gpointer userData);

    /**
     * The callback for the loadProfile() call.
     */
    static gboolean handleLoadProfile(jsprogHuVaradiistvanJSProg* object,
                                      GDBusMethodInvocation* invocation,
                                      guint arg_id,
                                      const gchar* arg_profileXML,
                                      gpointer userData);

    /**
     * The callback for the startMonitor() call.
     */
    static gboolean handleStartMonitor(jsprogHuVaradiistvanJSProg* object,
                                       GDBusMethodInvocation* invocation,
                                       guint arg_id,
                                       const gchar* arg_sender,
                                       const gchar* arg_listener,
                                       gpointer userData);

    /**
     * The callback for the stopMonitor() call.
     */
    static gboolean handleStopMonitor(jsprogHuVaradiistvanJSProg* object,
                                      GDBusMethodInvocation* invocation,
                                      guint arg_id,
                                      const gchar* arg_listener,
                                      gpointer userData);

    /**
     * The callback for the exit() call.
     */
    static gboolean handleExit(jsprogHuVaradiistvanJSProg* object,
                               GDBusMethodInvocation* invocation,
                               gpointer userData);

public:
    /**
     * Get the only instance of the adaptor.
     */
    static DBusAdaptor& get();

    /**
     * Convert the given input ID into the given DBus structure.
     */
    static GVariant* inputID2DBus(const struct input_id& inputID);

    /**
     * Create the array of key information for the given joystick.
     */
    static GVariant* keys2DBus(const Joystick& joystick);

    /**
     * Create the array of axis information for the given joystick.
     */
    static GVariant* axes2DBus(const Joystick& joystick,
                               bool valuesOnly = false);

private:
    /**
     * The D-Bus handler this adaptor works with.
     */
    DBusHandler& dbusHandler;

    /**
     * The bus connection we use.
     */
    GDBusConnection* connection = nullptr;

    /**
     * The interface skeleton.
     */
    jsprogHuVaradiistvanJSProg* interfaceSkeleton;

    /**
     * Indicate if the interface is exported.
     */
    bool interfaceExported = false;

    /**
     * Mapping from joystick IDs to listeners.
     */
    joystick2Listeners_t joystick2Listeners;

public:
    /**
     * Construct the adaptor with the given connection.
     */
    DBusAdaptor(DBusHandler& dbusHandler);

    /**
     * Destroy the adaptor.
     */
    ~DBusAdaptor();

    /**
     * Export the adaptor with the given connection
     */
    void exportInterface(GDBusConnection* connection);

    /**
     * Get whether control signals should be sent for the joysyick
     * with the given ID.
     */
    bool shouldSendControlSignals(size_t joystickID);

    /**
     * The implementation of the getJoysticks() call.
     */
    GVariant* getJoysticks();

    /**
     * The implementation of the getJoystickState() call.
     */
    GVariant* getJoystickState(uint32_t id);

    /**
     * The implementation of the loadProfile() call
     */
    bool loadProfile(uint32_t id, const std::string& profileXML);

    /**
     * Start monitoring the keys and axes of the joystick with the
     * given ID through the given listener.
     */
    bool startMonitor(const uint32_t id, const std::string& sender,
                      const std::string& listener);

    /**
     * Stop monitoring the keys and axes of the joystick with the
     * given ID through the given listener.
     */
    void stopMonitor(const uint32_t id, const std::string& listener);

    /**
     * Exit the program.
     */
    void exit();

    /**
     * Finalize the exiting from the program.
     */
    void finalizeExit();

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

private:
    /**
     * Find the listeners for the given joystick ID, if present.
     */
    listeners_t* findListeners(size_t joystickID);

    /**
     * Get the listeners for the given joystick ID. If the vector does
     * not exist yet, it will be created.
     */
    listeners_t& getListeners(size_t joystickID);

    /**
     * Remove a listener denoted by the given iterator.
     *
     * @return whether the list of listeners got empty.
     */
    bool removeListener(size_t joystickID, listeners_t* listeners,
                        listeners_t::iterator i);

    /**
     * Unexport the interface, if exported.
     */
    void unexportInterface();

    /**
     * Flush the interface skeleton.
     */
    void flushInterface();

    /**
     * Flush the D-Bus connection synchronously.
     */
    void flushConnectionSync();

    /**
     * Close the D-Bus connection synchronously.
     */
    void closeConnectionSync();

    /**
     * Cleanup the adaptor. It flushes and unexports the interface, and flushes
     * and closes the connection.
     */
    void cleanup();
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline DBusAdaptor& DBusAdaptor::get()
{
    return *instance;
}

//------------------------------------------------------------------------------

inline DBusAdaptor::listeners_t*
DBusAdaptor::findListeners(size_t joystickID)
{
    joystick2Listeners_t::iterator i = joystick2Listeners.find(joystickID);
    return (i==joystick2Listeners.end()) ?
        static_cast<DBusAdaptor::listeners_t*>(0) : (&i->second);
}

//------------------------------------------------------------------------------

inline bool DBusAdaptor::shouldSendControlSignals(size_t joystickID)
{
    return findListeners(joystickID)!=0;
}

//------------------------------------------------------------------------------
#endif // JSPROG_DBUSADAPTOR_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
