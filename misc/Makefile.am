pkgdata_DATA=jsprog.gresource

pkgdata_iconsdir=$(pkgdatadir)/icons
pkgdata_icons_DATA=joystick.svg

applicationsdir=$(datadir)/applications
applications_DATA=jsprog.desktop

%.gresource: %.gresource.xml
	glib-compile-resources --sourcedir $(srcdir) --target $@ $<

clean-local:
	rm -f $(pkgdata_DATA)
