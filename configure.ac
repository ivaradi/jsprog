AC_INIT(jsprog, 0.1, ivaradi@gmail.com)
AM_INIT_AUTOMAKE([foreign])

AM_PROG_AS
AC_PROG_CC
AC_PROG_CXX
AC_PROG_RANLIB
PKG_PROG_PKG_CONFIG

PKG_CHECK_MODULES([LIBLWT], [liblwt >= 0.1])

AC_CONFIG_FILES([
        Makefile
        src/Makefile
        src/daemon/Makefile
])

AC_OUTPUT()
