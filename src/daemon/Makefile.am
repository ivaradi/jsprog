bin_PROGRAMS=jsprogd

jsprogd_SOURCES = \
	Log.cc				\
	INotify.cc			\
	InputDeviceListener.cc		\
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
	jsprogd.cc

jsprogd_CXXFLAGS=$(LIBLWT_CFLAGS) $(LUA_CFLAGS)
jsprogd_LDADD=$(LIBLWT_LIBS) $(LUA_LIBS) -lpthread

noinst_HEADERS = \
	Log.h				\
	INotify.h			\
	InputDeviceListener.h		\
	Joystick.h			\
	JoystickHandler.h		\
	UInput.h			\
	LuaState.h			\
	LuaThread.h			\
	LuaRunner.h			\
	Control.h			\
	Key.h				\
	Axis.h				\
	Relative.h

