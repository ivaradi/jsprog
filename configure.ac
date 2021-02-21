AC_INIT(jsprog, 0.1, ivaradi@gmail.com)
AM_INIT_AUTOMAKE([foreign])

AM_PROG_AS
AC_PROG_CC
AC_PROG_CXX
AC_PROG_RANLIB
AC_PROG_SED
PKG_PROG_PKG_CONFIG
AM_PATH_PYTHON([3.6])

PKG_CHECK_MODULES([LIBLWT], [liblwt >= 0.1])
PKG_CHECK_MODULES([GLIB], [glib-2.0])
PKG_CHECK_MODULES([GIO], [gio-2.0])
PKG_CHECK_MODULES([GIO_UNIX], [gio-unix-2.0])
PKG_CHECK_MODULES([LUA], [lua5.2])
PKG_CHECK_MODULES([LIBXML], [libxml-2.0])

AC_CONFIG_FILES([
        Makefile
        src/Makefile
        src/daemon/Makefile
        src/client/Makefile
        src/client/jsprog/Makefile
        src/client/jsprog/gui/Makefile
        scripts/Makefile
        scripts/jsprog
        data/Makefile
        misc/Makefile
])

AC_OUTPUT()
