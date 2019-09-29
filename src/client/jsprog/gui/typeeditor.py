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

        self._gui = gui
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

        self.connect("window-state-event", self._windowStateChanged)
        self.connect("destroy",
                     lambda _window: gui.removeTypeEditor(joystickType))

        self._keys = Gtk.ListStore(int, str, str, bool)
        for key in joystickType.iterKeys:
            self._keys.append([key.code, key.name, key.displayName, False])

        self._axes = Gtk.ListStore(int, str, str, bool)
        for axis in joystickType.iterAxes:
            self._axes.append([axis.code, axis.name, axis.displayName, False])
        self._axisHighlightTimeouts = {}

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        (keysFrame, self._keysView) = \
            self._createControlListView(_("Buttons"), self._keys)
        vbox.pack_start(keysFrame, True, True, 4)

        (axesFrame, self._axesView) = \
            self._createControlListView(_("Axes"), self._axes)
        vbox.pack_start(axesFrame, True, True, 4)

        self.add(vbox)

        gui.addTypeEditor(joystickType, self)

        self.show_all()

        joystickType.connect("key-display-name-changed",
                             self._displayNameChanged)
        joystickType.connect("axis-display-name-changed",
                             self._displayNameChanged)

    @property
    def joystickType(self):
        """Get the joystick type this window works for."""
        return self._joystickType

    def keyPressed(self, code):
        """Called when a key has been pressed on a joystick whose type is
        handled by this editor window."""
        i = self._getKeyIterForCode(code)
        self._keys.set_value(i, 3, True)
        self._keysView.scroll_to_cell(self._keys.get_path(i), None,
                                      False, 0.0, 0.0)

    def keyReleased(self, code):
        """Called when a key has been released on a joystick whose type is
        handled by this editor window."""
        i = self._getKeyIterForCode(code)
        self._keys.set_value(i, 3, False)

    def axisChanged(self, code, value):
        """Called when the value of an axis had changed on a joystick whose
        type is handled by this editor window."""
        i = self._getAxisIterForCode(code)
        if code in self._axisHighlightTimeouts:
            GLib.source_remove(self._axisHighlightTimeouts[code][0])
        try:
            self._axisHighlightTimeouts[code] = \
                (GLib.timeout_add(75, self._handleAxisHighlightTimeout, code),
                 0)
        except Exception as e:
            print(e)
        self._axes.set_value(i, 3, True)
        self._axesView.scroll_to_cell(self._axes.get_path(i), None,
                                      False, 0.0, 0.0)

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
        nameColumn.set_cell_data_func(nameRenderer, self._identifierDataFunc,
                                      None)

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

        return (frame, view)

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

    def _getKeyIterForCode(self, code):
        """Get the iterator of the key model for the given code."""
        return self._getIterForCode(self._keys, code)

    def _getAxisIterForCode(self, code):
        """Get the iterator of the axis model for the given code."""
        return self._getIterForCode(self._axes, code)

    def _getIterForCode(self, model, code):
        """Get the iterator of the given model for the given key or axis
        code."""
        i = model.get_iter_first()
        while i is not None:
            value = model.get_value(i, 0)
            if value==code:
                return i
            i = model.iter_next(i)

    def _identifierDataFunc(self, column, cellRenderer, model, iter, *data):
        if model.get_value(iter, 3):
            if model is self._axes:
                code = model.get_value(iter, 0)
                alpha = 0.5 - 0.1 * self._axisHighlightTimeouts[code][1]
                cellRenderer.set_property("background-rgba", Gdk.RGBA(0.0, 0.5,
                                                                      0.8, alpha))
            else:
                cellRenderer.set_property("background-rgba", Gdk.RGBA(0.0, 0.5,
                                                                      0.8, 0.5))

            cellRenderer.set_property("background-set", True)
        else:
            cellRenderer.set_property("background-set", False)

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

    def _windowStateChanged(self, window, event):
        """Called when the window's state has changed.

        If the window became focused, the monitoring of the joysticks of its
        type is started. If the window lost the focus, the monitoring is
        stopped."""
        if (event.changed_mask&Gdk.WindowState.FOCUSED)!=0:
            if (event.new_window_state&Gdk.WindowState.FOCUSED)!=0:
                if self._gui.startMonitorJoysticksFor(self._joystickType):
                    for state in self._gui.getJoystickStatesFor(self._joystickType):
                        for keyData in state[0]:
                            code = keyData[0]
                            value = keyData[1]
                            if value>0:
                                self._keys.set_value(self._getKeyIterForCode(code),
                                                     3, True)
            else:
                if self._gui.stopMonitorJoysticksFor(self._joystickType):
                    for (timeoutID, _step) in self._axisHighlightTimeouts.values():
                        GLib.source_remove(timeoutID)
                    self._axisHighlightTimeouts = {}

                    self._clearHighlights(self._keys)
                    self._clearHighlights(self._axes)

    def _clearHighlights(self, model):
        """Clear the highlights on the given model."""
        i = model.get_iter_first()
        while i is not None:
            model.set_value(i, 3, False)
            i = model.iter_next(i)

    def _handleAxisHighlightTimeout(self, code):
        """Handle the timeout of an axis highlight."""
        (timeoutID, step) = self._axisHighlightTimeouts[code]

        i = self._getAxisIterForCode(code)

        if step>=5:
            self._axes.set_value(i, 3, False)
            del self._axisHighlightTimeouts[code]
            return GLib.SOURCE_REMOVE
        else:
            self._axes.set_value(i, 3, True)
            self._axisHighlightTimeouts[code] = (timeoutID, step + 1)
            return GLib.SOURCE_CONTINUE
