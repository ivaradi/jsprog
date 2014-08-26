
from common import *

#-------------------------------------------------------------------------------

## @package jsprog.gui.statusicon
#
# The status icon.
#

#-------------------------------------------------------------------------------

class StatusIcon(object):
    """The class handling the status icon."""
    def __init__(self, id, name):
        """Construct the status icon."""
        menu = gtk.Menu()

        nameMenuItem = gtk.MenuItem()
        nameMenuItem.set_label(name)
        nameMenuItem.show()
        menu.append(nameMenuItem)

        menu.show()

        # FIXME: find out the icon name properly
        #iconFile = os.path.join(iconDirectory, "logo.ico")
        iconFile = "/home/vi/munka/jsprog/src/client/logo.ico"

        if appIndicator:
            if pygobject:
                # FIXME: do we need a unique name here?
                indicator = appindicator.Indicator.new ("jsprog-%d" % (id,), iconFile,
                                                        appindicator.IndicatorCategory.APPLICATION_STATUS)
                indicator.set_status (appindicator.IndicatorStatus.ACTIVE)
            else:
                indicator = appindicator.Indicator ("jsprog-%d" % (id,), iconFile,
                                                    appindicator.CATEGORY_APPLICATION_STATUS)
                indicator.set_status (appindicator.STATUS_ACTIVE)

            indicator.set_menu(menu)
            self._indicator = indicator
        else:
            def popup_menu(status, button, time):
                menu.popup(None, None, gtk.status_icon_position_menu,
                           button, time, status)

            statusIcon = gtk.StatusIcon()
            statusIcon.set_from_file(iconFile)
            statusIcon.set_visible(True)
            statusIcon.connect('popup-menu', popup_menu)
            self._statusIcon = statusIcon

    def destroy(self):
        """Hide and destroy the status icon."""
        if appIndicator:
            if pygobject:
                self._indicator.set_status(appindicator.IndicatorStatus.PASSIVE)
            else:
                self._indicator.set_status(appindicator.STATUS_PASSIVE)
        else:
            self._statusIcon.set_visible(False)

#-------------------------------------------------------------------------------
