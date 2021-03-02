SUBDIRS=gui

pkgpython_PYTHON=__init__.py common.py jsprog.py joystick.py const.py util.py action.py profile.py parser.py device.py _autoconf.py

EXTRA_DIST=_autoconf.py.in

_autoconf.py: _autoconf.py.in
	rm -f $@
	$(SED) -e "s:[@]pkgdatadir@:$(pkgdatadir):" $< > $@
	chmod a-w $@

clean-local:
	rm -f _autoconf.py
