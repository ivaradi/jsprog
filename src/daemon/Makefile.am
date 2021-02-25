libexec_PROGRAMS=jsprogd

jsprogd_SOURCES = \
	Log.cc				\
	GLibEPoll.cc			\
	INotify.cc			\
	InputDeviceListener.cc		\
	Profile.cc			\
	Joystick.cc			\
	JoystickHandler.cc		\
	UInput.cc			\
	LuaState.cc			\
	LuaThread.cc			\
	LuaRunner.cc			\
	Control.cc			\
	Key.cc				\
	Axis.cc				\
	Relative.cc			\
	DBusHandler.cc			\
	DBusAdaptor.cc			\
	jsprog-dbus.c			\
	jsproglistener-dbus.c		\
	jsprogd.cc

jsprogd_CXXFLAGS=$(LIBLWT_CFLAGS) $(GLIB_CFLAGS) $(GIO_CFLAGS) $(GIO_UNIX_CFLAGS) $(LUA_CFLAGS) $(LIBXML_CFLAGS)
jsprogd_CFLAGS=$(GLIB_CFLAGS) $(GIO_CFLAGS) $(GIO_UNIX_CFLAGS)
jsprogd_LDADD=$(LIBLWT_LIBS) $(GLIB_LIBS) $(GIO_LIBS) $(LUA_LIBS) $(LIBXML_LIBS) -lpthread

noinst_HEADERS = \
	Log.h				\
	GLibEPoll.h			\
	INotify.h			\
	InputDeviceListener.h		\
	Profile.h			\
	Joystick.h			\
	JoystickHandler.h		\
	UInput.h			\
	LuaState.h			\
	LuaThread.h			\
	LuaRunner.h			\
	Control.h			\
	Key.h				\
	Axis.h				\
	Relative.h			\
	DBusHandler.h			\
	DBusAdaptor.h

BUILT_SOURCES=jsprog-dbus.h jsprog-dbus.c jsproglistener-dbus.h jsproglistener-dbus.c

%-dbus.h: ../%.xml
	gdbus-codegen --output-directory $(@D) --c-generate-object-manager --interface-prefix hu.varadiistvan.$(basename $(notdir $^)) --c-namespace $(basename $(notdir $^)) --generate-c-code $(basename $(notdir $^))-dbus $^

%-dbus.c: %-dbus.h
	@if test ! -f $@; then rm -f $@ $(MAKE) $(AM_MAKEFLAGS) $@; fi

servicesdir=$(datadir)/dbus-1/services
services_DATA=\
	hu.varadiistvan.JSProg.service

%.service: %.service.in
	cat $^ | sed "s:\@libexecdir\@:$(prefix)/libexec:g" > $@

clean-local:
	rm -f *-dbus.h *-dbus.c $(services_DATA)
