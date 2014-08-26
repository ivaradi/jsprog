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

#ifndef LOG_H
#define LOG_H
//------------------------------------------------------------------------------

#include <cstdarg>

#include <lwt/Log.h>

//------------------------------------------------------------------------------

/**
 * Class to handle different levels of logging.
 */
class Log
{
public:
    /**
     * Log level: debug
     */
    static const int LEVEL_DEBUG = 1;

    /**
     * Log level: info
     */
    static const int LEVEL_INFO = 2;

    /**
     * Log level: warning
     */
    static const int LEVEL_WARNING = 3;

    /**
     * Log level: error
     */
    static const int LEVEL_ERROR = 4;

    /**
     * The current log level.
     */
    static int level;

    /**
     * The log level of the last log message.
     */
    static int lastLevel;

    /**
     * Indicate if the last log message went to the error output.
     */
    static bool lastError;

    /**
     * Log a debug message.
     */
    static void debug(const char* format, ...);

    /**
     * Log an informational message.
     */
    static void info(const char* format, ...);

    /**
     * Log a warning message.
     */
    static void warning(const char* format, ...);

    /**
     * Log an error message.
     */
    static void error(const char* format, ...);

    /**
     * Continue the previous log message.
     */
    static void cont(const char* format, ...);

    /**
     * Continue the previous log message.
     */
    static void cont(const char* format, va_list& ap);

    /**
     * Perform the real logging at the given level. If the level is
     * lower than the current level, no logging is performed.
     */
    static void log(int l, bool error, const char* format, ...);

    /**
     * Perform the real logging at the given level. If the level is
     * lower than the current level, no logging is performed.
     */
    static void log(int l, bool error, const char* format, va_list& ap);
};

//------------------------------------------------------------------------------
// Inline definitions
//------------------------------------------------------------------------------

inline void Log::debug(const char* format, ...)
{
    va_list ap;
    va_start(ap, format);
    log(LEVEL_DEBUG, false, format, ap);
    va_end(ap);
}

//------------------------------------------------------------------------------

inline void Log::info(const char* format, ...)
{
    va_list ap;
    va_start(ap, format);
    log(LEVEL_INFO, false, format, ap);
    va_end(ap);
}

//------------------------------------------------------------------------------

inline void Log::warning(const char* format, ...)
{
    va_list ap;
    va_start(ap, format);
    log(LEVEL_WARNING, true, format, ap);
    va_end(ap);
}

//------------------------------------------------------------------------------

inline void Log::error(const char* format, ...)
{
    va_list ap;
    va_start(ap, format);
    log(LEVEL_ERROR, true, format, ap);
    va_end(ap);
}

//------------------------------------------------------------------------------

inline void Log::cont(const char* format, ...)
{
    if (lastLevel>=level) {
        va_list ap;
        va_start(ap, format);
        lwt::Log::cont(lastError, format, ap);
        va_end(ap);
    }
}

//------------------------------------------------------------------------------

inline void Log::cont(const char* format, va_list& ap)
{
    if (lastLevel>=level) {
        lwt::Log::cont(lastError, format, ap);
    }
}

//------------------------------------------------------------------------------

inline void Log::log(int l, bool error, const char* format, ...)
{
    va_list ap;
    va_start(ap, format);
    log(l, error, format, ap);
    va_end(ap);
}

//------------------------------------------------------------------------------

inline void Log::log(int l, bool error, const char* format, va_list& ap)
{
    if (l>=level) {
        lwt::Log::log(error, format, ap);
    }
    lastLevel = l;
    lastError = error;
}

//------------------------------------------------------------------------------
#endif // LOG_H

// Local Variables:
// mode: C++
// c-basic-offset: 4
// indent-tabs-mode: nil
// End:
