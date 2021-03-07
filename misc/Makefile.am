pkgdata_DATA=jsprog.gresource

pkgdata_iconsdir=$(pkgdatadir)/icons
pkgdata_icons_DATA=joystick.svg

applicationsdir=$(datadir)/applications
applications_DATA=jsprog.desktop

appiconsdir=$(datadir)/icons/hicolor/scalable/apps
appicons_DATA=jsprog.svg

EXTRA_DIST=jsprog.desktop jsprog.gresource jsprog.svg joystick.svg

%.gresource: %.gresource.xml
	glib-compile-resources --sourcedir $(srcdir) --target $@ $<

clean-local:
	rm -f $(pkgdata_DATA)
