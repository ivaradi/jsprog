AC_INIT(jsprog, 0.1, ivaradi@gmail.com)
AM_INIT_AUTOMAKE([foreign])

AM_PROG_AS
AC_PROG_CC
AC_PROG_CXX
AC_PROG_RANLIB
PKG_PROG_PKG_CONFIG
AM_PATH_PYTHON

PKG_CHECK_MODULES([LIBLWT], [liblwt >= 0.1])
PKG_CHECK_MODULES([LUA], [lua5.2])
PKG_CHECK_MODULES([LIBXML], [libxml-2.0])
PKG_CHECK_MODULES([LIBDBUSCPP], [dbus-c++-1])
PKG_CHECK_MODULES([DBUSPYTHON], [dbus-python])

AC_CONFIG_FILES([
        Makefile
        src/Makefile
        src/daemon/Makefile
        src/client/Makefile
        src/client/jsprog/Makefile
        src/client/jsprog/gui/Makefile
        scripts/Makefile
        misc/Makefile
])

AC_OUTPUT()
