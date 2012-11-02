libexec_PROGRAMS=jsprogd

jsprogd_SOURCES = \
	Log.cc				\
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
	jsprogd.cc

jsprogd_CXXFLAGS=$(LIBLWT_CFLAGS) $(LUA_CFLAGS) $(LIBXML_CFLAGS) $(LIBDBUSCPP_CFLAGS)
jsprogd_LDADD=$(LIBLWT_LIBS) $(LUA_LIBS) $(LIBXML_LIBS) $(LIBDBUSCPP_LIBS) -lpthread

noinst_HEADERS = \
	Log.h				\
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

BUILT_SOURCES=JSProgDBus.h JSProgListenerDBus.h

JSProgDBus.h: ../jsprog.xml
	dbusxx-xml2cpp $^ --adaptor=$@

JSProgListenerDBus.h: ../jsproglistener.xml
	dbusxx-xml2cpp $^ --proxy=$@

servicesdir=$(datadir)/dbus-1/services
services_DATA=\
	hu.varadiistvan.JSProg.service

%.service: %.service.in
	cat $^ | sed "s:\@libexecdir\@:$(prefix)/libexec:g" > $@
