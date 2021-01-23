# Joystick type editor window

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from .vceditor import VirtualControlSetEditor
from .jsview import JSViewer

from jsprog.device import View, Hotspot
from jsprog.joystick import Key, Axis
from jsprog.parser import Control, VirtualControl
from jsprog.parser import checkVirtualControlName

import shutil
import math

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
        self._monitoringJoystick = False
        self._forceMonitoringJoystick = False
        self._focused = False

        self._jsViewer = jsViewer = JSViewer(gui, joystickType, self)
        hasView = jsViewer.hasView

        self.set_wmclass("jsprog", joystickType.identity.name)
        self.set_role(PROGRAM_NAME)

        self.set_border_width(4)
        self.set_default_size(1200, 750)

        self.set_default_icon_name(PROGRAM_ICON_NAME)

        headerBar = Gtk.HeaderBar()
        headerBar.set_show_close_button(True)
        headerBar.props.title = joystickType.identity.name
        headerBar.set_subtitle(_("Joystick editor"))

        viewLabel = Gtk.Label.new(_("View:"))
        headerBar.pack_start(viewLabel)

        self._viewSelector = Gtk.ComboBox.new_with_model(self._jsViewer.views)
        viewNameRenderer = self._viewNameRenderer = Gtk.CellRendererText.new()
        self._viewSelector.pack_start(viewNameRenderer, True)
        self._viewSelector.add_attribute(viewNameRenderer, "text", 0)
        self._viewSelector.connect("changed", self._jsViewer.viewChanged)
        self._viewSelector.set_size_request(150, -1)
        jsViewer.setCallbacks(self._viewSelector.get_active_iter,
                              self._getSelectedControls,
                              self._getHighlightedControls)

        headerBar.pack_start(self._viewSelector)

        editViewNameButton = self._editViewNameButton = \
            Gtk.Button.new_from_icon_name(Gtk.STOCK_EDIT, Gtk.IconSize.BUTTON)
        editViewNameButton.set_tooltip_text(_("Edit the current view's name"))
        editViewNameButton.set_sensitive(hasView)
        editViewNameButton.connect("clicked", self._editViewName)

        headerBar.pack_start(editViewNameButton)

        addViewButton = self._addViewButton = \
            Gtk.Button.new_from_icon_name("list-add-symbolic",
                                          Gtk.IconSize.BUTTON)
        addViewButton.set_tooltip_text(_("Add new view"))
        addViewButton.set_sensitive(True)
        addViewButton.connect("clicked", self._addView)

        headerBar.pack_start(addViewButton)

        removeViewButton = self._removeViewButton = \
            Gtk.Button.new_from_icon_name("list-remove-symbolic",
                                          Gtk.IconSize.BUTTON)
        removeViewButton.set_tooltip_text(_("Remove the current view"))
        removeViewButton.set_sensitive(True)
        removeViewButton.connect("clicked", self._removeView)

        headerBar.pack_start(removeViewButton)

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

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        scrolledWindow.add(jsViewer)

        paned.pack1(scrolledWindow, True, True)

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        (keysFrame, self._keysView) = \
            self._createControlListView(_("Buttons"), self._keys)
        vbox.pack_start(keysFrame, True, True, 4)

        (axesFrame, self._axesView) = \
            self._createControlListView(_("Axes"), self._axes)
        vbox.pack_start(axesFrame, True, True, 4)

        vbox.set_margin_left(8)

        notebook = Gtk.Notebook.new()
        label = Gtk.Label(_("_Physical controls"))
        label.set_use_underline(True)
        notebook.append_page(vbox, label)

        virtualControlSetEditor = VirtualControlSetEditor(self, joystickType)
        virtualControlSetEditor.set_position(200)

        label = Gtk.Label(_("_Virtual controls"))
        label.set_use_underline(True)

        notebook.append_page(virtualControlSetEditor, label)

        paned.pack2(notebook, False, False)

        paned.set_wide_handle(True)
        paned.set_position(900)

        self.add(paned)

        gui.addTypeEditor(joystickType, self)

        self.set_titlebar(headerBar)

        self.show_all()

        jsViewer.setupWindowEvents()

        joystickType.connect("save-failed", self._saveFailed)

        if hasView:
            self._viewSelector.set_active(0)

    @property
    def joystickType(self):
        """Get the joystick type this window works for."""
        return self._joystickType

    @property
    def gui(self):
        """Get the GUI the type editor works with."""
        return self._gui

    @property
    def _view(self):
        """Get the currently selected view."""
        return self._jsViewer.view

    def keyPressed(self, code):
        """Called when a key has been pressed on a joystick whose type is
        handled by this editor window."""
        if not self._monitoringJoystick:
            return

        i = self._getKeyIterForCode(code)
        self._keys.set_value(i, 3, True)
        self._keysView.scroll_to_cell(self._keys.get_path(i), None,
                                      False, 0.0, 0.0)

        self._jsViewer.setKeyHotspotHighlight(code, True)

    def keyReleased(self, code):
        """Called when a key has been released on a joystick whose type is
        handled by this editor window."""
        if not self._monitoringJoystick:
            return

        i = self._getKeyIterForCode(code)
        self._keys.set_value(i, 3, False)

        self._jsViewer.setKeyHotspotHighlight(code, False)

    def axisChanged(self, code, value):
        """Called when the value of an axis had changed on a joystick whose
        type is handled by this editor window."""
        if not self._monitoringJoystick:
            return

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
        self._jsViewer.setAxisHotspotHighlight(code, 100)
        self._axesView.scroll_to_cell(self._axes.get_path(i), None,
                                      False, 0.0, 0.0)

    def _createControlListView(self, label, model):
        """Create a tree view for displaying and editing the controls (keys or
        axes) in the given model.

        Return the frame containing the view."""
        frame = Gtk.Frame.new(label)

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)

        view = Gtk.TreeView.new_with_model(model)
        view.get_selection().connect("changed", self._controlRowSelected)

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

    def _controlRowSelected(self, selection):
        """Called when a row in one of the control views is selected."""
        self._jsViewer.updateHotspotSelection()

    def _getSelectedControls(self):
        """Get the controls currently selected."""
        selectedControls = []

        (_model, i) =  self._keysView.get_selection().get_selected()
        if i is not None:
            selectedControls.append((Hotspot.CONTROL_TYPE_KEY,
                                     self._keys.get_value(i, 0)))
        (_model, i) =  self._axesView.get_selection().get_selected()
        if i is not None:
            selectedControls.append((Hotspot.CONTROL_TYPE_AXIS,
                                     self._axes.get_value(i, 0)))

        return selectedControls

    def _getHighlightedControls(self):
        """Get the currently highlighted controls."""
        highlightedKeys = []
        i = self._keys.get_iter_first()
        while i is not None:
            if self._keys.get_value(i, 3):
                highlightedKeys.append(self._keys.get_value(i, 0))
            i = self._keys.iter_next(i)

        highlightedAxes = []
        i = self._axes.get_iter_first()
        while i is not None:
            if self._axes.get_value(i, 3):
                highlightedAxes.append(self._axes.get_value(i, 0))
            i = self._axes.iter_next(i)

        return (highlightedKeys, highlightedAxes)

    def _displayNameEdited(self, widget, path, text, model):
        """Called when a display name has been edited."""
        code = model[path][0]
        if model is self._keys:
            model[path][2] = self._joystickType.setKeyDisplayName(code, text)
            self._updateHotspotLabel(Hotspot.CONTROL_TYPE_KEY, code)
        else:
            model[path][2] = self._joystickType.setAxisDisplayName(code, text)
            self._updateHotspotLabel(Hotspot.CONTROL_TYPE_AXIS, code)

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

    def _saveFailed(self, jt, e):
        """Called when saving the joystick type data has failed."""
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
            self._focused = (event.new_window_state&Gdk.WindowState.FOCUSED)!=0
            self._updateJoystickMonitoring()

    def _updateJoystickMonitoring(self):
        """Uppdate the monitoring of the joysticks based on the current focus
        state."""
        if self._focused:
            if not self._monitoringJoystick:
                if self._gui.startMonitorJoysticksFor(self._joystickType):
                    self._monitoringJoystick = True
                    for state in self._gui.getJoystickStatesFor(self._joystickType):
                        for keyData in state[0]:
                            code = keyData[0]
                            value = keyData[1]
                            if value>0:
                                self._keys.set_value(self._getKeyIterForCode(code),
                                                     3, True)

        else:
            if self._monitoringJoystick and \
               not self._forceMonitoringJoystick:
                if self._gui.stopMonitorJoysticksFor(self._joystickType):
                    self._monitoringJoystick = False
                    for (timeoutID, _step) in self._axisHighlightTimeouts.values():
                        GLib.source_remove(timeoutID)
                    self._axisHighlightTimeouts = {}

                    self._clearHighlights(self._keys)
                    self._clearHighlights(self._axes)

        self._jsViewer.setupHotspotHighlights()

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
            self._jsViewer.setAxisHotspotHighlight(code, 80 - step * 20)
            self._axisHighlightTimeouts[code] = (timeoutID, step + 1)
            return GLib.SOURCE_CONTINUE

    def _addView(self, button):
        """Called when a new view is to be added."""
        filePath = self._askImageFilePath()
        if filePath is None:
            return

        imageFileName = os.path.basename(filePath)

        shallCopy = False
        userDeviceDirectoryPath = self._joystickType.userDeviceDirectory
        if not self._joystickType.isDeviceDirectory(os.path.dirname(filePath)):

            if not yesNoDialog(self,
                               _("Should the image be copied to your JSProg device directory?"),
                               _("The image is not in any of the standard locations, soJSProg will not find it later. If you answer 'yes', it will be copied to your user device directory %s." %
                                 (userDeviceDirectoryPath,))):
                return

            shallCopy = True

        numViews = self._jsViewer.numViews
        viewName = self._queryViewName(viewName = _("View #%d") % (numViews,))
        if viewName is None:
            return

        if shallCopy:
            try:
                os.makedirs(userDeviceDirectoryPath, exist_ok = True)
                shutil.copyfile(filePath,
                                os.path.join(userDeviceDirectoryPath,
                                             imageFileName))
            except Exception as e:
                errorDialog(self, _("File copying failed"),
                            secondaryText = str(e))
                return

        self._jsViewer.addView(viewName, imageFileName)

        self._viewSelector.set_active(numViews)
        self._editViewNameButton.set_sensitive(True)
        self._removeViewButton.set_sensitive(True)

    def _askImageFilePath(self):
        """Ask the user to select an image file.

        Returns the selected path, or None if the selection was cancelled."""
        dialog = Gtk.FileChooserDialog(_("Select view image"),
                                       self,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN,
                                        Gtk.ResponseType.OK))

        filter = Gtk.FileFilter()
        filter.set_name(_("Image files"))
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/gif")
        filter.add_mime_type("image/svg")
        filter.add_mime_type("image/tiff")

        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name(_("All files"))
        filter.add_pattern("*")

        dialog.add_filter(filter)

        response = dialog.run()

        filePath = dialog.get_filename() if response==Gtk.ResponseType.OK \
            else None

        dialog.destroy()

        return filePath

    def _editViewName(self, button):
        """Called when the current view's name should be edited."""
        jsViewer = self._jsViewer

        origViewName = jsViewer.viewName
        view = jsViewer.view

        viewName = self._queryViewName(viewName = origViewName, view = view)
        if viewName:
            jsViewer.viewName = viewName

    def _queryViewName(self, viewName = "", view = None):
        """Query the view name starting with the given ones, if given."""
        text = None
        while True:
            viewName = entryDialog(self, "Enter view name", "View name:",
                                   initialValue = viewName, text = text)

            if viewName:
                v = self._joystickType.findView(viewName)
                if v is None:
                    return viewName
                elif v is view:
                    return None
                else:
                    text = _("<span color=\"#ff0000\"><b>There is already a view with this name, choose another one!</b></span>")
            else:
                return None

    def _removeView(self, button):
        """Called when the current view should be removed."""
        jsViewer = self._jsViewer

        viewName = jsViewer.viewName

        if yesNoDialog(self,
                       _("Are you sure to remove view '{0}'?").format(viewName)):
            toActivate = jsViewer.removeCurrentView()

            if toActivate is None:
                self._editViewNameButton.set_sensitive(False)
                self._removeViewButton.set_sensitive(False)
            else:
                self._viewSelector.set_active_iter(toActivate)
