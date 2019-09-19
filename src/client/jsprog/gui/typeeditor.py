# Joystick type editor window

#-------------------------------------------------------------------------------

from .common import *
from .common import _

#-------------------------------------------------------------------------------

## @package jsprog.gui.typeeditor
#
# The window to edit a joystick type, i.e. to give human-readable names to
# the buttons and axes, to provide a joystick image with hotspots as well as
# icons for various purposes and to edit the virtual controls.

#-------------------------------------------------------------------------------

class TypeEditorWindow(Gtk.ApplicationWindow):
    """The type editor window."""
    def __init__(self, gui, joystickType, *args, **kwargs):
        """Construct the window."""
        super().__init__(*args, **kwargs)

        self._joystickType = joystickType

        self.set_wmclass("jsprog", joystickType.identity.name)
        self.set_role(PROGRAM_NAME)

        self.set_border_width(4)
        self.set_default_size(500, 750)

        self.set_default_icon_name(PROGRAM_ICON_NAME)

        headerBar = Gtk.HeaderBar()
        headerBar.set_show_close_button(True)
        headerBar.props.title = joystickType.identity.name
        headerBar.set_subtitle(_("Joystick editor"))

        saveButton = self._saveButton = \
            Gtk.Button.new_from_icon_name("document-save-symbolic",
                                          Gtk.IconSize.BUTTON)
        self._saveButton.set_tooltip_text(_("Save the joystick definition"))
        self._saveButton.set_sensitive(False)
        self._saveButton.connect("clicked", self._save)
        headerBar.pack_start(saveButton)

        self.set_titlebar(headerBar)

        self.connect("destroy",
                     lambda _window: gui.removeTypeEditor(joystickType))

        self._keys = Gtk.ListStore(int, str, str)
        for key in joystickType.iterKeys:
            self._keys.append([key.code, key.name, key.displayName])

        self._axes = Gtk.ListStore(int, str, str)
        for axis in joystickType.iterAxes:
            self._axes.append([axis.code, axis.name, axis.displayName])

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        keysFrame = self._createControlListView(_("Buttons"), self._keys)
        vbox.pack_start(keysFrame, True, True, 4)

        axesFrame = self._createControlListView(_("Axes"), self._axes)
        vbox.pack_start(axesFrame, True, True, 4)

        self.add(vbox)

        gui.addTypeEditor(joystickType, self)

        self.show_all()

        joystickType.connect("key-display-name-changed",
                             self._displayNameChanged)
        joystickType.connect("axis-display-name-changed",
                             self._displayNameChanged)

    def _createControlListView(self, label, model):
        """Create a tree view for displaying and editing the controls (keys or
        axes) in the given model.

        Return the frame containing the view."""
        frame = Gtk.Frame.new(label)

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)

        view = Gtk.TreeView.new_with_model(model)

        nameRenderer = Gtk.CellRendererText.new()
        nameColumn = Gtk.TreeViewColumn(title = _("Identifier"),
                                         cell_renderer = nameRenderer,
                                         text = 1)

        view.append_column(nameColumn)

        displayNameRenderer = Gtk.CellRendererText.new()
        displayNameRenderer.set_property("editable", True)
        displayNameRenderer.connect("edited", self._displayNameEdited,
                                    model)

        displayNameColumn = Gtk.TreeViewColumn(title = _("Name"),
                                               cell_renderer =
                                               displayNameRenderer,
                                               text = 2)

        view.append_column(displayNameColumn)

        scrolledWindow.add(view)

        frame.add(scrolledWindow)

        return frame

    def _displayNameEdited(self, widget, path, text, model):
        """Called when a display name has been edited."""
        model[path][2] = text
        if model is self._keys:
            self._joystickType.setKeyDisplayName(model[path][0], text)
        else:
            self._joystickType.setAxisDisplayName(model[path][0], text)

    def _displayNameChanged(self, *args):
        """Called when the display name of a key or an exist has indeed changed.

        Saving will be enabled."""
        self._saveButton.set_sensitive(True)

    def _save(self, button):
        """Save the joystick type definition."""
        try:
            self._joystickType.save()
            self._saveButton.set_sensitive(False)
        except Exception as e:
            dialog = Gtk.MessageDialog(parent = self,
                                       type = Gtk.MessageType.ERROR,
                                       buttons = Gtk.ButtonsType.OK,
                                       message_format = _("Failed to save the joystick definition"))
            dialog.format_secondary_text(str(e))

            dialog.run()
            dialog.destroy()
