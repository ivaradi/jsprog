pkgdata_DATA=jsprog.gresource

applicationsdir=$(datadir)/applications
applications_DATA=hu.varadiistvan.JSProgGUI.desktop

appiconsdir=$(datadir)/icons/hicolor/scalable/apps
appicons_DATA=jsprog.svg

statusiconsdir=$(datadir)/icons/hicolor/scalable/status
statusicons_DATA=jsprog-default-indicator.svg

deviceiconsdir=$(datadir)/icons/hicolor/scalable/devices
deviceicons_DATA=jsprog-default-joystick.svg

modulesloaddir=$(sysconfdir)/modules-load.d
modulesload_DATA=jsprog.conf

EXTRA_DIST=hu.varadiistvan.JSProgGUI.desktop jsprog.gresource jsprog.svg jsprog-default-indicator.svg jsprog-default-joystick.svg jsprog.conf

%.gresource: %.gresource.xml
	glib-compile-resources --sourcedir $(srcdir) --target $@ $<

clean-local:
	rm -f $(pkgdata_DATA)
