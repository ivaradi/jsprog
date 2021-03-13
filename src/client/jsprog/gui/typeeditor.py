# Joystick type editor window

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from .vceditor import VirtualControlSetEditor
from .jsview import JSViewer, PaddedImage

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

class IconEditor(Gtk.Box):
    """An editor for a single icon."""
    def __init__(self, window, joystickType, frameTitle,
                 iconName, icon, iconNameSetFn, iconResetFn,
                 checkerBoard = False):
        """Construct the editor."""
        super().__init__()
        self.set_property("orientation", Gtk.Orientation.HORIZONTAL)
        self.set_spacing(8)

        self._window = window
        self._joystickType = joystickType
        self._iconNameSetFn = iconNameSetFn
        self._iconResetFn = iconResetFn

        frame = Gtk.Frame.new(frameTitle)

        self._iconImage = iconImage = PaddedImage(checkerBoard = checkerBoard)
        iconImage.connect("size-allocate", self._iconResized)
        iconImage.preparePixbuf(icon)
        iconImage.padToSize(128, 128)

        frame.add(iconImage)

        self.pack_start(frame, False, False, 0)

        buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.VERTICAL)
        buttonBox.set_spacing(8)

        self._loadIconButton = loadIconButton = \
            Gtk.Button.new_from_icon_name("document-open",
                                          Gtk.IconSize.BUTTON)
        loadIconButton.set_tooltip_text(_("Load a new icon file"))
        loadIconButton.connect("clicked", self._loadIconClicked)
        buttonBox.pack_start(loadIconButton, False, True, 0)

        self._resetIconButton = resetIconButton = \
            Gtk.Button.new_from_icon_name("edit-delete",
                                          Gtk.IconSize.BUTTON)
        resetIconButton.set_tooltip_text(_("Reset the icon to the default one"))
        resetIconButton.connect("clicked", self._resetIconClicked)
        resetIconButton.set_sensitive(iconName is not None)
        buttonBox.pack_start(resetIconButton, False, True, 0)
        buttonBox.set_valign(Gtk.Align.CENTER)
        buttonBox.set_vexpand(False)

        self.pack_start(buttonBox, False, False, 0)
        self.set_vexpand(False)

    def changeIcon(self, iconName, icon):
        """Change the icon."""
        self._iconImage.preparePixbuf(icon)
        self._iconImage.padToSize(128, 128)
        self._resetIconButton.set_sensitive(iconName is not None)

    def _iconResized(self, image, rectangle):
        """Called when the icon is resized.

        It enqueues a call to _redrawIcon(), as such operations cannot be
        called from this event handler.
        """
        GLib.idle_add(self._redrawIcon, None)

    def _redrawIcon(self, *args):
        """Redraw the icon image by finalizing the pixbuf."""
        self._iconImage.finalizePixbuf()

    def _loadIconClicked(self, button):
        """Called when the button to load an icon has been clicked."""
        (filePath, shallCopy) = \
            TypeEditorWindow.getImageFilePath(self._window, self._joystickType)
        if filePath is None:
            return

        if shallCopy and not TypeEditorWindow.copyDeviceFile(self._joystickType,
                                                             filePath):
            return

        self._iconNameSetFn(os.path.basename(filePath))

    def _resetIconClicked(self, button):
        """Called when the button to reset the icon has been clicked."""
        if yesNoDialog(self._window,
                       _("Are you sure to reset the icon to the default one?")):
            self._iconResetFn()

#-------------------------------------------------------------------------------

class IconsEditor(Gtk.Box):
    """Editor for the icons belonging to the joystick."""
    def __init__(self, typeEditor, joystickType):
        """Construct the editor."""
        super().__init__()
        self.set_property("orientation", Gtk.Orientation.HORIZONTAL)
        self.set_spacing(32)

        self._typeEditor = typeEditor
        self._joystickType = joystickType
        joystickType.connect("icon-changed", self._iconChanged)
        joystickType.connect("indicator-icon-changed", self._indicatorIconChanged)

        self._iconEditor = iconEditor = IconEditor(typeEditor,
                                                   joystickType,
                                                   _("Icon"),
                                                   joystickType.iconName,
                                                   joystickType.icon,
                                                   self._setIconName,
                                                   self._resetIconName)


        iconEditor.set_halign(Gtk.Align.CENTER)

        self.pack_start(iconEditor, False, False, 0)

        self._indicatorIconEditor = indicatorIconEditor = IconEditor(typeEditor,
                                                                     joystickType,
                                                                     _("Indicator icon"),
                                                                     joystickType.indicatorIconName,
                                                                     joystickType.indicatorIcon,
                                                                     self._setIndicatorIconName,
                                                                     self._resetIndicatorIconName,
                                                                     checkerBoard = True)


        indicatorIconEditor.set_halign(Gtk.Align.CENTER)

        self.pack_start(indicatorIconEditor, False, False, 0)

        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_margin_top(16)

        self.show_all()

    def _setIconName(self, iconName):
        """Set the name of the icon."""
        self._joystickType.setIconName(iconName)

    def _resetIconName(self):
        """Reset the name of the icon."""
        self._joystickType.resetIcon()

    def _iconChanged(self, joystickType, iconName):
        """Called when the icon has changed."""
        self._iconEditor.changeIcon(iconName, joystickType.icon)

    def _setIndicatorIconName(self, iconName):
        """Set the name of the indicator icon."""
        self._joystickType.setIndicatorIconName(iconName)

    def _resetIndicatorIconName(self):
        """Reset the name of the indicator icon."""
        self._joystickType.resetIndicatorIcon()

    def _indicatorIconChanged(self, joystickType, iconName):
        """Called when the indicator icon has changed."""
        self._indicatorIconEditor.changeIcon(iconName, joystickType.indicatorIcon)

#-------------------------------------------------------------------------------

class TypeEditorWindow(Gtk.ApplicationWindow):
    """The type editor window."""
    @staticmethod
    def askImageFilePath(window):
        """Ask for the path of an image file."""
        dialog = Gtk.FileChooserDialog(_("Select view image"),
                                       window,
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
        filter.add_mime_type("image/svg+xml")
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

    def getImageFilePath(window, joystickType):
        """Get the path of an image file.

        If one is selected, but it is not in a standard location, the user will
        be asked if it should be copied to the user's device directory.

        Return a tuple of
        - the path of the file,
        - a boolean indicating if it should be copied

        If no file was selected, or the user refused to copy the file (if it
        would otherwise be necessary), both values will be None."""
        filePath = TypeEditorWindow.askImageFilePath(window)
        if filePath is None:
            return (None, None)

        imageFileName = os.path.basename(filePath)

        shallCopy = False
        userDeviceDirectoryPath = joystickType.userDeviceDirectory
        if not joystickType.isDeviceDirectory(os.path.dirname(filePath)):

            if not yesNoDialog(window,
                               _("Should the image be copied to your JSProg device directory?"),
                               _("The image is not in any of the standard locations, so JSProg will not find it later. If you answer 'yes', it will be copied to your user device directory %s." %
                                 (userDeviceDirectoryPath,))):
                return (None, None)

            shallCopy = True

        return (filePath, shallCopy)

    def copyDeviceFile(joystickType, filePath):
        """Copy the given file into the user's device directory.

        Returns a boolean indicating if the copying was successful."""
        try:
            userDeviceDirectoryPath = joystickType.userDeviceDirectory
            os.makedirs(userDeviceDirectoryPath, exist_ok = True)

            imageFileName = os.path.basename(filePath)
            shutil.copyfile(filePath,
                            os.path.join(userDeviceDirectoryPath,
                                         imageFileName))
            return True
        except Exception as e:
            errorDialog(self, _("File copying failed"),
                        secondaryText = str(e))
            return False

    def __init__(self, gui, joystickType, *args, **kwargs):
        """Construct the window."""
        super().__init__(*args, **kwargs)

        self._gui = gui
        self._joystickType = joystickType
        self._focused = False

        self._jsViewer = jsViewer = JSViewer(gui, joystickType, self,
                                             editable = True)
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
                              self)

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

        self._keys = Gtk.ListStore(int, str, str, int)
        for key in joystickType.iterKeys:
            self._keys.append([key.code, key.name, key.displayName, 0])

        self._axes = Gtk.ListStore(int, str, str, int)
        for axis in joystickType.iterAxes:
            self._axes.append([axis.code, axis.name, axis.displayName, 0])

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

        self._iconsEditor = iconsEditor = IconsEditor(self, joystickType)

        label = Gtk.Label.new(_("_Icons"))
        label.set_use_underline(True)

        notebook.append_page(iconsEditor, label)

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
        i = self._getKeyIterForCode(code)
        self._keysView.scroll_to_cell(self._keys.get_path(i), None,
                                      False, 0.0, 0.0)

    def keyReleased(self, code):
        """Called when a key has been released on a joystick whose type is
        handled by this editor window."""
        pass

    def axisChanged(self, code, value):
        """Called when the value of an axis had changed on a joystick whose
        type is handled by this editor window."""
        i = self._getAxisIterForCode(code)
        self._axesView.scroll_to_cell(self._axes.get_path(i), None,
                                      False, 0.0, 0.0)

    def setKeyHighlight(self, code, value):
        """Set the highlighing of the key with the given code."""
        i = self._getKeyIterForCode(code)
        if i is not None:
            self._keys.set_value(i, 3, value)

    def setAxisHighlight(self, code, value):
        """Stop highlighting the axis with the given code."""
        i = self._getAxisIterForCode(code)
        if i is not None:
            self._axes.set_value(i, 3, value)

    def finalize(self):
        """Finalize the type editor by stopping any joystick monitoring."""
        self._gui.stopMonitorJoysticksFor(self._joystickType, self)

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

    def _displayNameEdited(self, widget, path, text, model):
        """Called when a display name has been edited."""
        code = model[path][0]
        if model is self._keys:
            model[path][2] = self._joystickType.setKeyDisplayName(code, text)
        else:
            model[path][2] = self._joystickType.setAxisDisplayName(code, text)

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
        highlight = model.get_value(iter, 3)
        if highlight>0:
            alpha = 0.5 * highlight / 100
            cellRenderer.set_property("background-rgba", Gdk.RGBA(0.0, 0.5,
                                                                  0.8, alpha))
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
            self._jsViewer.startMonitorJoysticks()
        else:
            self._jsViewer.stopMonitorJoysticks()

    def _addView(self, button):
        """Called when a new view is to be added."""
        (filePath, shallCopy) = TypeEditorWindow.getImageFilePath(self, self._joystickType)
        if filePath is None:
            return

        numViews = self._jsViewer.numViews
        viewName = self._queryViewName(viewName = _("View #%d") % (numViews,))
        if viewName is None:
            return

        if shallCopy:
            if not TypeEditorWindow.copyDeviceFile(self._joystickType,
                                                   filePath):
                return

        self._jsViewer.addView(viewName, os.path.basename(filePath))

        self._viewSelector.set_active(numViews)
        self._editViewNameButton.set_sensitive(True)
        self._removeViewButton.set_sensitive(True)

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
