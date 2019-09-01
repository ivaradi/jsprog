pkgdata_DATA=jsprog.gresource

pkgdata_profilesdir=$(pkgdatadir)/profiles
pkgdata_profiles_DATA=saitekYokeJS.profile wingman2.profile x52.profile

pkgdata_iconsdir=$(pkgdatadir)/icons
pkgdata_icons_DATA=joystick.svg

%.gresource: %.gresource.xml
	glib-compile-resources --sourcedir $(srcdir) --target $@ $<
