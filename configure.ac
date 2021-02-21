AC_INIT(jsprog, 0.1, ivaradi@varadiistvan.hu)
AM_INIT_AUTOMAKE([foreign])

AM_PROG_AS
AC_PROG_CC
AC_PROG_CXX
AC_PROG_RANLIB
AC_PROG_SED
PKG_PROG_PKG_CONFIG

AC_ARG_WITH([liblwt],
        AS_HELP_STRING([--with-liblwt],
                       [Build with an external LibLWT package (default: no)]),
        [], [with_liblwt=no])

AM_CONDITIONAL([BUILTIN_LIBLWT], [test "$with_liblwt" = no])
if test "$with_liblwt" = "yes"; then
   PKG_CHECK_MODULES([LIBLWT], [liblwt >= 0.1])
else
   echo "Using built-in LibLWT"
   LIBLWT_CFLAGS="-I\$(top_srcdir)/submodules/lwt/src"
   LIBLWT_LIBS="-L\$(top_builddir)/submodules/lwt/src/lwt -llwt"
   AC_SUBST(LIBLWT_CFLAFGS)
fi

PKG_CHECK_MODULES([GLIB], [glib-2.0])
PKG_CHECK_MODULES([GIO], [gio-2.0])
PKG_CHECK_MODULES([GIO_UNIX], [gio-unix-2.0])
PKG_CHECK_MODULES([LUA], [lua5.2])
PKG_CHECK_MODULES([LIBXML], [libxml-2.0])

AM_PATH_PYTHON([3.6])
AC_PYTHON_MODULE(dbus, t)
AC_PYTHON_MODULE(gi, t)
AC_PYTHON_MODULE(gi.repository, t)

AC_MSG_CHECKING([checking the availability of the GI packages])
if /usr/bin/env PYTHONPATH=${srcdir}/src/client ${PYTHON} -c "import jsprog.gui.common" >&5 2>&1; then
   AC_MSG_RESULT([found])
else
   AC_MSG_FAILURE([not found])
fi

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

if test "x$with_liblwt" != "xyes"; then
   AC_CONFIG_SUBDIRS([submodules/lwt])
fi
AC_OUTPUT()
