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
#include "jsproglistener-dbus.h"

#include "Joystick.h"
#include "InputDeviceListener.h"
#include "LuaRunner.h"
#include "UInput.h"
#include "GLibEPoll.h"

#include "Log.h"

#include <lwt/IOServer.h>

#include <memory>
#include <tuple>

//------------------------------------------------------------------------------

// using hu::varadiistvan::JSProgListener_proxy;

using lwt::IOServer;

using std::string;
using std::vector;
using std::pair;
using std::make_pair;
using std::unique_ptr;
using std::tuple;
using std::tuple_size;
using std::make_tuple;

//------------------------------------------------------------------------------

class DBusAdaptor::JSProgListener
{
private:
    /**
     * The callback for the proxy creation.
     */
    static void readyCallback(GObject* sourceObject,
                              GAsyncResult* res, gpointer userData);

    /**
     * Called when a keyPressed call has been processed.
     */
    static void keyPressedReady(GObject* sourceObject,
                                GAsyncResult* res, gpointer userData);

    /**
     * Called when a keyReleased call has been processed.
     */
    static void keyReleasedReady(GObject* sourceObject,
                                 GAsyncResult* res, gpointer userData);

    /**
     * Called when an axisChanged call has been processed.
     */
    static void axisChangedReady(GObject* sourceObject,
                                 GAsyncResult* res, gpointer userData);

    /**
     * The listener instance.
     */
    jsproglistenerHuVaradiistvanJSProgListener* listener = nullptr;

    /**
     * The path of the listener.
     */
    std::string path;

public:
    /**
     * Construct the listener proxy.
     */
    JSProgListener(GDBusConnection* connection, const std::string& path,
                   const std::string& destination);

    /**
     * Destroy the proxy.
     */
    ~JSProgListener();

    /**
     * Get the path of the listener.
     */
    const std::string& getPath() const;

    /**
     * Called when a key is pressed.
     */
    void keyPressed(unsigned joystickID, unsigned code);

    /**
     * Called when a key is released
     */
    void keyReleased(unsigned joystickID, unsigned code);

    /**
     * Called when the value of an axis has changed.
     */
    void axisChanged(unsigned joystickID, unsigned code, int value);
};

//------------------------------------------------------------------------------

void DBusAdaptor::JSProgListener::readyCallback(GObject* sourceObject,
                                                GAsyncResult* res,
                                                gpointer userData)
{
    auto listener = reinterpret_cast<JSProgListener*>(userData);

    GError* error = nullptr;
    listener->listener =
        jsproglistener_hu_varadiistvan_jsprog_listener_proxy_new_finish(res,
                                                                        &error);
    if (listener->listener==nullptr || error!=nullptr) {
        Log::error("JSProgListener::readyCallback: failed\n");
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::JSProgListener::keyPressedReady(GObject* sourceObject,
                                                  GAsyncResult* res,
                                                  gpointer userData)
{
    auto listener = reinterpret_cast<JSProgListener*>(userData);

    GError* error = nullptr;
    if (!jsproglistener_hu_varadiistvan_jsprog_listener_call_key_pressed_finish(
            listener->listener, res, &error))
    {
        Log::error("JSProgListener::keyPressedReady: failed\n");
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::JSProgListener::keyReleasedReady(GObject* sourceObject,
                                                  GAsyncResult* res,
                                                  gpointer userData)
{
    auto listener = reinterpret_cast<JSProgListener*>(userData);

    GError* error = nullptr;
    if (!jsproglistener_hu_varadiistvan_jsprog_listener_call_key_released_finish(
            listener->listener, res, &error))
    {
        Log::error("JSProgListener::keyReleasedReady: failed\n");
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::JSProgListener::axisChangedReady(GObject* sourceObject,
                                                   GAsyncResult* res,
                                                   gpointer userData)
{
    auto listener = reinterpret_cast<JSProgListener*>(userData);

    GError* error = nullptr;
    if (!jsproglistener_hu_varadiistvan_jsprog_listener_call_axis_changed_finish(
            listener->listener, res, &error))
    {
        Log::error("JSProgListener::axisChangedReady: failed\n");
    }
}

//------------------------------------------------------------------------------

inline
DBusAdaptor::JSProgListener::JSProgListener(GDBusConnection* connection,
                                            const std::string& path,
                                            const std::string& destination) :
    path(path)
{
    Log::debug("JSProgListener: path='%s', destination='%s'\n",
               path.c_str(), destination.c_str());
    jsproglistener_hu_varadiistvan_jsprog_listener_proxy_new(
        connection, static_cast<GDBusProxyFlags>(
             G_DBUS_PROXY_FLAGS_DO_NOT_LOAD_PROPERTIES|
             G_DBUS_PROXY_FLAGS_DO_NOT_CONNECT_SIGNALS),
        destination.c_str(), path.c_str(),
        nullptr, &readyCallback, this);
}

//------------------------------------------------------------------------------

inline DBusAdaptor::JSProgListener::~JSProgListener()
{
    if (listener!=nullptr) {
        g_object_unref(listener);
    }
}

//------------------------------------------------------------------------------

inline const std::string& DBusAdaptor::JSProgListener::getPath() const
{
    return path;
}

//------------------------------------------------------------------------------

void DBusAdaptor::JSProgListener::
keyPressed(unsigned joystickID, unsigned code)
{
    if (listener!=nullptr) {
        jsproglistener_hu_varadiistvan_jsprog_listener_call_key_pressed(
            listener, joystickID, code, nullptr,
            &keyPressedReady, this);
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::JSProgListener::
keyReleased(unsigned joystickID, unsigned code)
{
    if (listener!=nullptr) {
        jsproglistener_hu_varadiistvan_jsprog_listener_call_key_released(
            listener, joystickID, code, nullptr,
            &keyReleasedReady, this);
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::JSProgListener::
axisChanged(unsigned joystickID, unsigned code, int value)
{
    if (listener!=nullptr) {
        jsproglistener_hu_varadiistvan_jsprog_listener_call_axis_changed(
            listener, joystickID, code, value, nullptr,
            &axisChangedReady, this);
    }
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

DBusAdaptor* DBusAdaptor::instance = nullptr;

//------------------------------------------------------------------------------

gboolean DBusAdaptor::handleGetJoysticks(jsprogHuVaradiistvanJSProg* object,
                                         GDBusMethodInvocation* invocation,
                                         gpointer userData)
{
    auto adaptor = reinterpret_cast<DBusAdaptor*>(userData);

    jsprog_hu_varadiistvan_jsprog_complete_get_joysticks(
        object, invocation, adaptor->getJoysticks());

    return true;
}

//------------------------------------------------------------------------------

gboolean DBusAdaptor::handleLoadProfile(jsprogHuVaradiistvanJSProg* object,
                                        GDBusMethodInvocation* invocation,
                                        guint arg_id,
                                        const gchar* arg_profileXML,
                                        gpointer userData)
{
    auto adaptor = reinterpret_cast<DBusAdaptor*>(userData);

    jsprog_hu_varadiistvan_jsprog_complete_load_profile(
        object, invocation, adaptor->loadProfile(arg_id, arg_profileXML));

    return true;
}

//------------------------------------------------------------------------------

gboolean DBusAdaptor::
handleStartMonitor(jsprogHuVaradiistvanJSProg* object,
                   GDBusMethodInvocation* invocation,
                   guint arg_id,
                   const gchar* arg_sender,
                   const gchar* arg_listener,
                   gpointer userData)
{
    auto adaptor = reinterpret_cast<DBusAdaptor*>(userData);

    jsprog_hu_varadiistvan_jsprog_complete_start_monitor(
        object, invocation, adaptor->startMonitor(arg_id, arg_sender,
                                                  arg_listener));

    return true;
}

//------------------------------------------------------------------------------

gboolean DBusAdaptor::
handleStopMonitor(jsprogHuVaradiistvanJSProg* object,
                  GDBusMethodInvocation* invocation,
                  guint arg_id,
                  const gchar* arg_listener,
                  gpointer userData)
{
    auto adaptor = reinterpret_cast<DBusAdaptor*>(userData);

    adaptor->stopMonitor(arg_id, arg_listener);

    jsprog_hu_varadiistvan_jsprog_complete_stop_monitor(
        object, invocation);

    return true;
}

//------------------------------------------------------------------------------

gboolean DBusAdaptor::handleExit(jsprogHuVaradiistvanJSProg* object,
                                 GDBusMethodInvocation* invocation,
                                 gpointer userData)
{
    auto adaptor = reinterpret_cast<DBusAdaptor*>(userData);

    adaptor->exit();

    jsprog_hu_varadiistvan_jsprog_complete_exit(object, invocation);

    adaptor->finalizeExit();

    return true;
}

//------------------------------------------------------------------------------

GVariant* DBusAdaptor::inputID2DBus(const struct input_id& inputID)
{
    unique_ptr<GVariant*[]> inputIDVariants(new GVariant*[4]);
    inputIDVariants[0] = g_variant_new_uint16(inputID.bustype);
    inputIDVariants[1] = g_variant_new_uint16(inputID.vendor);
    inputIDVariants[2] = g_variant_new_uint16(inputID.product);
    inputIDVariants[3] = g_variant_new_uint16(inputID.version);

    auto result = g_variant_new_tuple(inputIDVariants.get(), 4);

    return result;
}

//------------------------------------------------------------------------------

GVariant* DBusAdaptor::keys2DBus(const Joystick& joystick)
{
    static const GVariantType* const elementTypes[] = {
        G_VARIANT_TYPE_UINT16,
        G_VARIANT_TYPE_INT32
    };
    static const GVariantType* elementType =
        g_variant_type_new_tuple(elementTypes,
                                 sizeof(elementTypes)/sizeof(elementTypes[0]));

    auto numKeys = joystick.getNumKeys();

    unique_ptr<GVariant*[]> keyVariants(new GVariant*[numKeys]);

    size_t numKeysProcessed = 0;
    for(int code = 0; code<KEY_CNT && numKeysProcessed<numKeys; ++code) {
        Key* key = joystick.findKey(code);
        if (key!=0) {
            unique_ptr<GVariant*[]> keyDataVariant(new GVariant*[2]);
            keyDataVariant[0] = g_variant_new_uint16(code);
            keyDataVariant[1] =
                g_variant_new_int32(key->isPressed() ? 1 : 0);
            keyVariants[numKeysProcessed++] =
                g_variant_new_tuple(keyDataVariant.get(), 2);
        }
    }

    auto result = g_variant_new_array(elementType,
                                      keyVariants.get(), numKeysProcessed);
    return result;
}

//------------------------------------------------------------------------------

GVariant* DBusAdaptor::axes2DBus(const Joystick& joystick)
{
    static const GVariantType* const elementTypes[] = {
        G_VARIANT_TYPE_UINT16,
        G_VARIANT_TYPE_INT32,
        G_VARIANT_TYPE_INT32,
        G_VARIANT_TYPE_INT32
    };
    static const GVariantType* elementType =
        g_variant_type_new_tuple(elementTypes,
                                 sizeof(elementTypes)/sizeof(elementTypes[0]));

    auto numAxes = joystick.getNumAxes();

    unique_ptr<GVariant*[]> axisVariants(new GVariant*[numAxes]);

    size_t numAxesProcessed = 0;
    for(int code = 0; code<ABS_CNT; ++code) {
        Axis* axis = joystick.findAxis(code);
        if (axis!=0) {
            unique_ptr<GVariant*[]> axisDataVariant(new GVariant*[4]);
            axisDataVariant[0] = g_variant_new_uint16(code);
            axisDataVariant[1] = g_variant_new_int32(axis->getValue());
            axisDataVariant[2] = g_variant_new_int32(axis->getMinimum());
            axisDataVariant[3] = g_variant_new_int32(axis->getMaximum());
            axisVariants[numAxesProcessed++] =
                g_variant_new_tuple(axisDataVariant.get(), 4);
        }
    }

    auto result = g_variant_new_array(elementType,
                                      axisVariants.get(), numAxesProcessed);
    return result;
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
    dbusHandler(dbusHandler),
    interfaceSkeleton(jsprog_hu_varadiistvan_jsprog_skeleton_new())
{
    g_signal_connect(interfaceSkeleton, "handle-get-joysticks",
                     G_CALLBACK(&handleGetJoysticks), this);
    g_signal_connect(interfaceSkeleton, "handle-load-profile",
                     G_CALLBACK(&handleLoadProfile), this);
    g_signal_connect(interfaceSkeleton, "handle-start-monitor",
                     G_CALLBACK(&handleStartMonitor), this);
    g_signal_connect(interfaceSkeleton, "handle-stop-monitor",
                     G_CALLBACK(&handleStopMonitor), this);
    g_signal_connect(interfaceSkeleton, "handle-exit",
                     G_CALLBACK(&handleExit), this);
    instance = this;
}

//------------------------------------------------------------------------------

DBusAdaptor::~DBusAdaptor()
{
    cleanup();

    g_object_unref(interfaceSkeleton);
    instance = nullptr;
}

//------------------------------------------------------------------------------

void DBusAdaptor::exportInterface(GDBusConnection* connection)
{
    GError* error = nullptr;
    if (g_dbus_interface_skeleton_export(
            G_DBUS_INTERFACE_SKELETON(interfaceSkeleton),
            connection, "/hu/varadiistvan/JSProg", &error))
    {
        interfaceExported = true;
        this->connection = connection;
    } else {
        Log::error("exportInterface: error!\n");
    }
}

//------------------------------------------------------------------------------

GVariant* DBusAdaptor::getJoysticks()
{
    static const GVariantType* elementType =
        G_VARIANT_TYPE("(u(qqqq)sssa(qi)a(qiii))");

    Log::debug("DBusAdaptor::getJoysticks\n");

    const Joystick::joysticks_t& joysticks = Joystick::getAll();

    auto numJoysticks = joysticks.size();
    unique_ptr<GVariant*[]> joystickVariants(new GVariant*[numJoysticks]);

    size_t index = 0;
    for(auto& jsData: joysticks) {
        auto joystick = jsData.second;

        unique_ptr<GVariant*[]> joystickDataVariants(new GVariant*[7]);

        joystickDataVariants[0] = g_variant_new_uint32(joystick->getID());
        joystickDataVariants[1] = inputID2DBus(joystick->getInputID());
        joystickDataVariants[2] =
            g_variant_new_string(joystick->getName().c_str());
        joystickDataVariants[3] =
            g_variant_new_string(joystick->getPhys().c_str());
        joystickDataVariants[4] =
            g_variant_new_string(joystick->getUniq().c_str());
        joystickDataVariants[5] = keys2DBus(*joystick);
        joystickDataVariants[6] = axes2DBus(*joystick);

        joystickVariants[index++] =
            g_variant_new_tuple(joystickDataVariants.get(), 7);
    }

    return g_variant_new_array(elementType,
                               joystickVariants.get(), index);
}

//------------------------------------------------------------------------------

bool DBusAdaptor::loadProfile(uint32_t id, const string& profileXML)
{
    Joystick* joystick = Joystick::find(id);
    if (joystick==0) return false;

    Profile profile(profileXML.c_str(), false);
    if (!profile) return false;

    return joystick->setProfile(profile);
}

//------------------------------------------------------------------------------

bool DBusAdaptor::startMonitor(const uint32_t id, const string& sender,
                               const string& listener)
{
    if (Joystick::find(id)==0) return false;

    Log::debug("DBusAdaptor::startMonitor: joystick %u to %s\n",
               id, listener.c_str());

    listeners_t& listeners = getListeners(id);
    listeners.push_back(new JSProgListener(connection, listener, sender));
    return true;
}

//------------------------------------------------------------------------------

void DBusAdaptor::stopMonitor(const uint32_t id, const string& listener)
{
    listeners_t* listeners = findListeners(id);
    if (listeners!=0) {
        for(listeners_t::iterator i = listeners->begin(); i!=listeners->end();
            ++i)
        {
            if ((*i)->getPath()==listener) {
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
}

//------------------------------------------------------------------------------

void DBusAdaptor::finalizeExit()
{
    cleanup();

    GLibEPoll::get().releaseContext();
}

//------------------------------------------------------------------------------

void DBusAdaptor::sendJoystickAdded(Joystick& joystick)
{
    if (interfaceExported) {
        jsprog_hu_varadiistvan_jsprog_emit_joystick_added(
            interfaceSkeleton, joystick.getID(),
            inputID2DBus(joystick.getInputID()),
            joystick.getName().c_str(),
            joystick.getPhys().c_str(),
            joystick.getUniq().c_str(),
            keys2DBus(joystick),
            axes2DBus(joystick));
    }
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
                               (*l)->getPath().c_str());
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
                               (*l)->getPath().c_str());
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
                               (*l)->getPath().c_str());
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
    if (interfaceExported) {
        jsprog_hu_varadiistvan_jsprog_emit_joystick_removed(
            interfaceSkeleton, joystick.getID());
    }
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

void DBusAdaptor::unexportInterface()
{
    if (interfaceExported) {
        g_dbus_interface_skeleton_unexport(
            G_DBUS_INTERFACE_SKELETON(interfaceSkeleton));
        interfaceExported = false;
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::flushInterface()
{
    if (interfaceExported) {
        g_dbus_interface_skeleton_flush(
            G_DBUS_INTERFACE_SKELETON(interfaceSkeleton));
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::flushConnectionSync()
{
    if (connection!=nullptr) {
        GError* error = nullptr;
        if (!g_dbus_connection_flush_sync(connection, nullptr, &error)) {
            Log::error("DBusAdaptor::finalizeExit: failed to flush the D-Bus connection\n");
        }
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::closeConnectionSync()
{
    if (connection!=nullptr) {
        GError* error = nullptr;
        if (!g_dbus_connection_close_sync(connection, nullptr, &error)) {
            Log::error("DBusAdaptor::finalizeExit: failed to close the D-Bus connection\n");
        }

        connection = nullptr;
    }
}

//------------------------------------------------------------------------------

void DBusAdaptor::cleanup()
{
    flushInterface();

    unexportInterface();

    flushConnectionSync();

    dbusHandler.stop();

    closeConnectionSync();

    connection = nullptr;
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
