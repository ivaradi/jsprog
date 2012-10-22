#include "INotify.h"

#include <lwt/Thread.h>
#include <lwt/EPoll.h>
#include <lwt/Scheduler.h>

#include <cstring>
#include <cstdio>

using lwt::Scheduler;

using std::string;

/**
 * A thread that listens to events on the /dev/input directory.
 */
class InputDeviceListener : public lwt::Thread
{
private:
    /**
     * The inotify file descriptor.
     */
    INotify* inotify;

public:
    /**
     * Construct the thread.
     */
    InputDeviceListener();

    /**
     * Destroy the thread.
     */
    ~InputDeviceListener();

    /**
     * Perform the thread's operation.
     */
    virtual void run();
};

InputDeviceListener::InputDeviceListener() :
    inotify(new INotify())
{
    int wd = inotify->addWatch("/dev/input", IN_CREATE|IN_DELETE|IN_ATTRIB);
    if (wd<0) {
        lwt::EPoll::get().destroy(inotify);
        inotify = 0;
        perror("inotify_add_watch");
    } else {
        printf("wd=%d\n", wd);
    }
}

InputDeviceListener::~InputDeviceListener()
{
    lwt::EPoll::get().destroy(inotify);
}

void InputDeviceListener::run()
{
    if (inotify==0) return;

    int wd;
    uint32_t mask;
    uint32_t cookie;
    string name;
    while(inotify->getEvent(wd, mask, cookie, name)) {
        printf("wd=%d, mask=0x%08x, cookie=%u, name='%s'\n",
               wd, mask, cookie, name.c_str());
    }
}


int main()
{
    Scheduler scheduler;
    
    InputDeviceListener inputDeviceListener;
    
    scheduler.run();

    return 0;
}
