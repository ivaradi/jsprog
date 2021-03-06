// Copyright (c) 2012 by Istv�n V�radi

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

#include "Joystick.h"

#include "LuaRunner.h"

#include "Key.h"
#include "Axis.h"
#include "UInput.h"
#include "Log.h"

#include <lwt/Timer.h>

#include <algorithm>

#include <cstring>

//------------------------------------------------------------------------------

using lwt::BlockedThread;

using std::vector;
using std::string;

//------------------------------------------------------------------------------

class Joystick::TimeoutHandler : public lwt::Timer
{
private:
    /**
     * The waiter that should be used to unblock the thread waiting on
     * this timer.
     */
    lwt::BlockedThread& waiter;

    /**
     * The reference to the boolean variable that should be set when
     * the timeout fires.
     */
    bool& timedOut;

public:
    /**
     * Construct the timeout handler.
     */
    TimeoutHandler(millis_t timeout, lwt::BlockedThread& waiter, bool& timedOut);

protected:
    /**
     * Handle the timeout.
     */
    virtual bool handleTimeout();
};

//------------------------------------------------------------------------------

Joystick::TimeoutHandler::TimeoutHandler(millis_t timeout,
                                         BlockedThread& waiter, bool& timedOut) :
    Timer(timeout),
    waiter(waiter),
    timedOut(timedOut)
{
}

//------------------------------------------------------------------------------

bool Joystick::TimeoutHandler::handleTimeout()
{
    timedOut = true;
    waiter.unblock();
    return false;
}

//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

size_t Joystick::nextID = 1;

Joystick::joysticks_t Joystick::joysticks;

//------------------------------------------------------------------------------

Joystick* Joystick::find(size_t id)
{
    joysticks_t::const_iterator i = joysticks.find(id);
    return (i==joysticks.end()) ? 0 : (i->second);
}

//------------------------------------------------------------------------------

void Joystick::closeAll()
{
    for(joysticks_t::iterator i = joysticks.begin(); i!=joysticks.end(); ++i) {
        Joystick* joystick = i->second;
        joystick->close();
    }
}

//------------------------------------------------------------------------------

Joystick* Joystick::create(const char* devicePath)
{
    int fd = open(devicePath, O_RDONLY);
    if (fd<0) {
        Log::warning("could not open joystick device '%s': errno=%d\n",
                     devicePath, errno);
        return 0;
    }

    uint32_t syn = 0;
    if (::ioctl(fd, EVIOCGBIT(EV_SYN, sizeof(syn)), &syn)<0) {
        Log::warning("could not query the event types from '%s': errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }

    if ((syn&(1<<EV_ABS))==0) {
        Log::warning("device '%s' is not a joystick, since it does not support absolute events\n",
                     devicePath);
        ::close(fd);
        return 0;
    }

    unsigned char abs[SIZE_ABS_BITS];
    memset(abs, 0, sizeof(abs));
    if (::ioctl(fd, EVIOCGBIT(EV_ABS, sizeof(abs)), abs)<0) {
        Log::warning("could not query the absolute axes of '%s': errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }

    bool allZero = true;
    for(size_t i = 0; i<sizeof(abs) && allZero; ++i) {
        allZero = abs[i]==0;
    }

    if (allZero) {
        Log::warning("device '%s' is not a joystick, since none of the absolute axes are present: errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }

    struct input_id inputID;
    if (::ioctl(fd, EVIOCGID, &inputID)<0) {
        Log::warning("could not query the ID of '%s': errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }

    Log::debug("the ID of %s is: bustype=%u, vendor=0x%04x, product=0x%04x, version=0x%04x\n",
               devicePath, inputID.bustype, inputID.vendor, inputID.product,
               inputID.version);

    char name[256];
    if (::ioctl(fd, EVIOCGNAME(sizeof(name)), name)<0) {
        Log::warning("could not query the name of '%s': errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }

    Log::debug("the name of %s is: '%s'\n", devicePath, name);

    char phys[256];
    if (::ioctl(fd, EVIOCGPHYS(sizeof(phys)), phys)<0) {
        int errorNumber = errno;
        Log::warning("could not query the physical location of '%s': errno=%d\n",
                     devicePath, errno);
        if (errorNumber==ENOENT) {
            phys[0] = '\0';
        } else {
            ::close(fd);
            return 0;
        }
    }

    Log::debug("the physical location of %s is: '%s'\n", devicePath, phys);

    char uniq[256];
    if (::ioctl(fd, EVIOCGUNIQ(sizeof(uniq)), uniq)<0) {
        int errorNumber = errno;
        Log::warning("could not query the unique ID of '%s': errno=%d\n",
                     devicePath, errorNumber);
        if (errorNumber==ENOENT) {
            uniq[0] = '\0';
        } else {
            ::close(fd);
            return 0;
        }
    }

    Log::debug("the unique ID of %s is: '%s'\n", devicePath, uniq);

    unsigned char key[SIZE_KEY_BITS];
    memset(key, 0, sizeof(key));
    if (::ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(key)), key)<0) {
        Log::warning("could not query the keys of '%s': errno=%d\n",
                     devicePath, errno);
        ::close(fd);
        return 0;
    }

    Log::info("%s is a joystick device\n", devicePath);

    return new Joystick(fd, inputID, name, phys, uniq, key, abs);
}

//------------------------------------------------------------------------------

Joystick::Joystick(int fd, const struct input_id& inputID,
                   const char* name, const char* phys, const char* uniq,
                   const unsigned char* key, const unsigned char* abs) :
    ThreadedFD(fd),
    id(nextID++),
    inputID(inputID),
    name(name),
    phys(phys),
    uniq(uniq),
    luaState(*this)
{
    memset(keys, 0, sizeof(keys));

    unsigned char keyStates[SIZE_KEY_BITS];
    memset(keyStates, 0, sizeof(keyStates));
    bool keyStatesValid = true;
    if (::ioctl(fd, EVIOCGKEY(sizeof(keyStates)), &keyStates)<0) {
        Log::warning("could not query the key states, assuming all released: errno=%d\n",
                     errno);
        keyStatesValid = false;
    }

    Log::debug("keys:");
    bool firstKey = true;
    for(size_t i = 0; i<SIZE_KEY_BITS; ++i) {
        unsigned char k = key[i];
        unsigned char s = keyStates[i];
        for(size_t j = 0; j<8; ++j) {
            if ( ((k>>j)&0x01)==0x01 ) {
                int code = i*8 + j;
                bool pressed = keyStatesValid ? (((s>>j)&0x01)==0x01) : false;
                keys[code] = new Key(*this, pressed);
                ++numKeys;
                if (!firstKey) Log::cont(",");
                Log::cont(" 0x%03x", code);
                const char* name = Key::toString(code);
                if (name!=0) {
                    Log::cont(" (%s)", name);
                }
                firstKey = false;
            }
        }
    }
    Log::cont("\n");

    memset(axes, 0, sizeof(axes));

    for(size_t i = 0; i<SIZE_ABS_BITS; ++i) {
        unsigned char a = abs[i];
        for(size_t j = 0; j<8; ++j) {
            if ( ((a>>j)&0x01)==0x01 ) {
                int code = i*8 + j;

                struct input_absinfo absInfo;
                if (::ioctl(fd, EVIOCGABS(code), &absInfo)<0) {
                    Log::warning("could not query the state of absolute axis %d, assuming it is set to 0, errno=%d\n",
                                 code, errno);
                    absInfo.value = 0;
                    absInfo.minimum = 0;
                    absInfo.maximum = 0;
                    absInfo.fuzz = 0;
                    absInfo.flat = 0;
                    absInfo.resolution = 0;
                }

                Log::debug("information for axis %d (%s): value=%d, minimum=%d, maximum=%d, fuzz=%d, flat=%d, resolution=%d\n",
                           code, Axis::toString(code),
                           absInfo.value, absInfo.minimum,
                           absInfo.maximum, absInfo.fuzz, absInfo.flat,
                           absInfo.resolution);

                axes[code] = new Axis(*this, absInfo.value,
                                      absInfo.minimum, absInfo.maximum);
                ++numAxes;
            }
        }
    }

    joysticks[id] = this;
}

//------------------------------------------------------------------------------

Joystick::~Joystick()
{
    joysticks.erase(id);

    releasePressedKeys();

    for(int i = 0; i<KEY_CNT; ++i) {
        delete keys[i];
    }
    for(int i = 0; i<ABS_CNT; ++i) {
        delete axes[i];
    }

    LuaRunner& luaRunner = LuaRunner::get();
    while(!luaThreads.empty()) {
        LuaThread* luaThread = *luaThreads.begin();
        luaRunner.deleteThread(luaThread);
    }
}

//------------------------------------------------------------------------------

bool Joystick::setProfile(const Profile& profile)
{
    deleteAllLuaThreads();
    releasePressedKeys();
    clearLuaHandlerNames();

    string profileCode, luaCode;

    if (profile.getPrologue(luaCode)) {
        profileCode.append(luaCode);
        profileCode.append("\n");
    }

    profile.resetControls();
    Control::type_t type;
    int code;
    while (profile.getNextControl(type, code, luaCode)) {
        Control* control = findControl(type, code);
        if (control==0) {
            Log::warning("Joystick::setProfile: joystick has no %s with code %d\n",
                         (type==Control::KEY) ? "key" : "axis", code);
        } else {
            control->setupLuaHandlerName(type, code);
            profileCode.append("function " + control->getLuaHandlerName() + "(type, code, value)\n");
            profileCode.append(luaCode);
            profileCode.append("\nend\n");
        }
    }

    if (profile.getEpilogue(luaCode)) {
        profileCode.append(luaCode);
    }

    Log::debug("Joystick::setProfile: the profile code:\n");

    size_t lineNumber = 1;
    static const string delim("\n");
    string::const_iterator lineStart = profileCode.begin();
    string::const_iterator end = profileCode.end();
    while (true) {
        string::const_iterator lineEnd = std::search(lineStart, end,
                                                     delim.begin(), delim.end());
        string line(lineStart, lineEnd);
        Log::debug("%zu: %s\n", lineNumber, line.c_str());
        if (lineEnd==end) break;
        lineStart = lineEnd + delim.size();
        ++lineNumber;
    }

    return luaState.loadProfile(profileCode);
}

//------------------------------------------------------------------------------

void Joystick::deleteAllLuaThreads() const
{
    LuaRunner& luaRunner = LuaRunner::get();

    luaThreads_t::iterator i = luaThreads.begin();
    while(i!=luaThreads.end()) {
        luaThreads_t::iterator j = i++;
        LuaThread* luaThread = *j;
        luaRunner.deleteThread(luaThread);
    }
}

//------------------------------------------------------------------------------

void Joystick::releasePressedKeys()
{
    UInput& uinput = UInput::get();
    for(std::set<int>::iterator i = pressedKeys.begin(); i!=pressedKeys.end();
        ++i)
    {
        uinput.releaseKey(*i);
    }
    uinput.synchronize();
    pressedKeys.clear();
}

//------------------------------------------------------------------------------

void Joystick::clearLuaHandlerNames()
{
    for(int i = 0; i<KEY_CNT; ++i) {
        Key* key = keys[i];
        if (key!=0) key->clearLuaHandlerName();
    }
    for(int i = 0; i<ABS_CNT; ++i) {
        Axis* axis = axes[i];
        if (axis!=0) axis->clearLuaHandlerName();
    }
}

//------------------------------------------------------------------------------

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
