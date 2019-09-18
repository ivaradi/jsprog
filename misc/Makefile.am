pkgdata_DATA=jsprog.gresource

pkgdata_iconsdir=$(pkgdatadir)/icons
pkgdata_icons_DATA=joystick.svg

%.gresource: %.gresource.xml
	glib-compile-resources --sourcedir $(srcdir) --target $@ $<
