pkgdata_DATA=jsprog.gresource

applicationsdir=$(datadir)/applications
applications_DATA=jsprog.desktop

appiconsdir=$(datadir)/icons/hicolor/scalable/apps
appicons_DATA=jsprog.svg

statusiconsdir=$(datadir)/icons/hicolor/scalable/status
statusicons_DATA=jsprog-default-indicator.svg

EXTRA_DIST=jsprog.desktop jsprog.gresource jsprog.svg jsprog-default-indicator.svg

%.gresource: %.gresource.xml
	glib-compile-resources --sourcedir $(srcdir) --target $@ $<

clean-local:
	rm -f $(pkgdata_DATA)
