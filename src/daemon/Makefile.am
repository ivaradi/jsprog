bin_PROGRAMS=jsprogd

jsprogd_SOURCES = \
	Log.cc				\
	INotify.cc			\
	InputDeviceListener.cc		\
	Joystick.cc			\
	JoystickHandler.cc		\
	jsprogd.cc

jsprogd_CXXFLAGS=$(LIBLWT_CFLAGS)
jsprogd_LDADD=$(LIBLWT_LIBS) -lpthread

noinst_HEADERS = \
	Log.h				\
	INotify.h			\
	InputDeviceListener.h		\
	Joystick.h			\
	JoystickHandler.h
