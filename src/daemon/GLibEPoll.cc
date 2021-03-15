//-----------------------------------------------------------------------------

#include "GLibEPoll.h"

#include "Log.h"

//-----------------------------------------------------------------------------

using std::min;
using std::make_unique;

//-----------------------------------------------------------------------------

uint32_t GLibEPoll::GLibFD::getEvents(const GPollFD& gpollFD)
{
    uint32_t epollEvents = 0;

    unsigned events = gpollFD.events;

    if ((events&G_IO_IN)!=0) {
        epollEvents |= EPOLLIN;
    }
    if ((events&G_IO_OUT)!=0) {
        epollEvents |= EPOLLOUT;
    }
    if ((events&G_IO_HUP)!=0) {
        epollEvents |= EPOLLHUP;
    }
    if ((events&G_IO_ERR)!=0) {
        epollEvents |= EPOLLERR;
    }

    return epollEvents;
}

//-----------------------------------------------------------------------------

void GLibEPoll::GLibFD::setREvents(GPollFD& gpollFD, uint32_t epollEvents)
{
    auto& revents = gpollFD.revents;
    if ((epollEvents&EPOLLIN)!=0) {
        revents |= G_IO_IN;
    }
    if ((epollEvents&EPOLLOUT)!=0) {
        revents |= G_IO_OUT;
    }
    if ((epollEvents&EPOLLHUP)!=0) {
        revents |= G_IO_HUP;
    }
    if ((epollEvents&EPOLLERR)!=0) {
        revents |= G_IO_ERR;
    }
}

//-----------------------------------------------------------------------------

GLibEPoll::GLibFD::~GLibFD()
{
    clearFD();
}

//-----------------------------------------------------------------------------

void GLibEPoll::GLibFD::handleEvents(uint32_t events)
{
    setREvents(epoll.gPollFileDescriptors[index], events);
}

//-----------------------------------------------------------------------------
//-----------------------------------------------------------------------------

thread_local GLibEPoll* GLibEPoll::instance = nullptr;

//-----------------------------------------------------------------------------

GLibEPoll::GLibEPoll(GMainContext* context) :
    context(context),
    gPollFileDescriptors(16)
{
    g_main_context_acquire(context);
    instance = this;
}

//-----------------------------------------------------------------------------

GLibEPoll::~GLibEPoll()
{
    releaseContext();
    instance = nullptr;
}

//-----------------------------------------------------------------------------

void GLibEPoll::releaseContext()
{
    if (context!=nullptr) {
        g_main_context_release(context);
        g_main_context_unref(context);
        context = nullptr;
        fileDescriptors.clear();
    }
}

//-----------------------------------------------------------------------------

int GLibEPoll::wait(bool& hadEvents, int timeout)
{
    gint priority = 0;
    if (context!=nullptr && g_main_context_prepare(context, &priority)) {
        Log::debug("GLibEPoll::wait: g_main_context_prepare returned true\n");
        g_main_context_dispatch(context);
    }

    gint gTimeout = -1;
    size_t nFDs = 0;
    while(context!=nullptr) {
        auto fdSize = gPollFileDescriptors.size();
        nFDs = g_main_context_query(context, priority, &gTimeout,
                                    gPollFileDescriptors.data(), fdSize);
        if (nFDs!=fdSize) {
            gPollFileDescriptors.resize(nFDs);
        }

        if (nFDs<=fdSize) {
            if (gTimeout>=0) {
                timeout = (timeout<0) ? gTimeout : min(timeout, gTimeout);
            }
            break;
        }
    }

    if (context!=nullptr) {
        fileDescriptors_t newFileDescriptors;

        for(size_t i = 0; i<nFDs; ++i) {
            auto& gPollFD = gPollFileDescriptors[i];
            auto j = fileDescriptors.find(gPollFD.fd);
            if (j==fileDescriptors.end()) {
                newFileDescriptors.emplace(
                    gPollFD.fd,
                    make_unique<GLibFD>(*this, gPollFD.fd,
                                        GLibFD::getEvents(gPollFD),
                                        newFileDescriptors.size()));
            } else {
                auto fd = std::move(j->second);
                fd->setRequestedEvents(GLibFD::getEvents(gPollFD));
                fd->setIndex(newFileDescriptors.size());
                newFileDescriptors.emplace(gPollFD.fd, std::move(fd));
            }
        }

        fileDescriptors.swap(newFileDescriptors);
    }

    auto result = EPoll::wait(hadEvents, timeout);

    if (context!=nullptr) {
        if (g_main_context_check(context, priority,
                                 gPollFileDescriptors.data(),
                                 gPollFileDescriptors.size()))
        {
            g_main_context_dispatch(context);
        }
    }

    return result;
}

//-----------------------------------------------------------------------------
