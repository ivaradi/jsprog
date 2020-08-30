# Joystick profiles editor window

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from jsprog.profile import Profile
from .joystick import ProfileList

#-------------------------------------------------------------------------------

class ProfileNameDialog(Gtk.Dialog):
    """A dialog to edit the name and file name of a new or an existing profile"""
    def __init__(self, profilesEditor, title, profile = None, initialName = None):
        """Construct the profile creator dialog."""
        super().__init__(use_header_bar = True)
        self.set_title(title)

        self._profilesEditor = profilesEditor
        self._profile = profile

        self._fileNameEdited = profile is not None
        self._generatingFileName = False

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self._addButton = button = self.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        grid = self._grid = Gtk.Grid.new()
        grid.set_column_spacing(16)
        grid.set_row_spacing(8)

        label = Gtk.Label(_("_Name:"))
        label.set_use_underline(True)
        label.props.halign = Gtk.Align.START
        grid.attach(label, 0, 0, 1, 1)

        self._nameEntry = nameEntry = Gtk.Entry()
        if profile is not None:
            nameEntry.set_text(profile.name)
        nameEntry.connect("changed", self._nameChanged)
        grid.attach(nameEntry, 1, 0, 1, 1)
        label.set_mnemonic_widget(nameEntry)

        label = Gtk.Label(_("_File name:"))
        label.set_use_underline(True)
        label.props.halign = Gtk.Align.START
        grid.attach(label, 0, 1, 1, 1)

        self._fileNameEntry = fileNameEntry = Gtk.Entry()
        if profile is not None:
            fileNameEntry.set_text(profile.fileName)
        fileNameEntry.connect("changed", self._fileNameChanged)
        grid.attach(fileNameEntry, 1, 1, 1, 1)
        label.set_mnemonic_widget(fileNameEntry)

        contentArea.pack_start(grid, True, True, 8)

        self.show_all()

        self._updateButtons()

        if initialName:
            nameEntry.set_text(initialName)

    @property
    def name(self):
        """Get the name entered."""
        return self._nameEntry.get_text().strip()

    @property
    def fileName(self):
        """Get the file name entered."""
        return self._fileNameEntry.get_text().strip()

    @property
    def _joystickType(self):
        """Get the joystick type we are adding a profile for."""
        return self._profilesEditor.joystickType

    @property
    def _fileNameValid(self):
        """Determine if the file named is valid."""
        fileName = self.fileName
        return fileName and \
            not self._joystickType.hasUserProfileFileName(fileName,
                                                          excludeProfile = self._profile)

    def _nameChanged(self, nameEntry):
        """Called when the name has been changed."""
        if not self._fileNameEdited:
            assert self._profile is None

            joystickType = self._joystickType

            name = self.name
            fileName = None

            profiles = joystickType.findProfiles(name)
            for profile in profiles:
                if not joystickType.hasUserProfileFileName(profile.fileName):
                    fileName = profile.fileName
                    break

            if fileName is None:
                fileName = fileNameBase = name.replace("/", "_")
                number = 1
                while joystickType.hasUserProfileFileName(fileName):
                    fileName = fileNameBase + str(number)
                    number += 1

            self._generatingFileName = True
            self._fileNameEntry.set_text(fileName)
            self._generatingFileName = False

        self._updateButtons()

    def _fileNameChanged(self, _fileNameChanged):
        """Called when the file name has changed."""
        if not self._generatingFileName:
            self._fileNameEdited = True
        self._updateButtons()

    def _updateButtons(self):
        """Update the state of the buttons based on the name and the file
        name."""
        self._addButton.set_sensitive(self._fileNameValid)

#-------------------------------------------------------------------------------

class IdentityWidget(Gtk.Box):
    """The widget containing the editable parts of the joystick identity."""

    class Entry(Gtk.Box):
        """An entry which is a label and an entry field for a part of the
        identity."""
        def __init__(self, labelText, createEntryFn, tooltipText, changedFn):
            super().__init__(Gtk.Orientation.HORIZONTAL)

            label = Gtk.Label(labelText)
            label.set_use_underline(True)

            self.pack_start(label, False, False, 2)

            entry = self._entry = createEntryFn()
            entry.connect("value-changed", changedFn)

            label.set_mnemonic_widget(entry)

            self.pack_start(entry, False, False, 2)

        def clear(self):
            """Empty the contents of the entry widget."""
            self._entry.set_text("")

        def set(self, value):
            """Set the contents of the entry field from the given value."""
            self._entry.set_value(value)

    def __init__(self, profilesEditorWindow):
        """Construct the widget for the given editor window."""
        super().__init__(Gtk.Orientation.HORIZONTAL)

        self.set_homogeneous(False)
        self.set_halign(Gtk.Align.CENTER)

        versionEntry = self._versionEntry = \
            IdentityWidget.Entry(_("_Version:"),
                                 lambda : IntegerEntry(maxWidth=4, base = 16),
                                 _("When matching the profile for automatic loading, this value, if not empty, will be used as an extra condition. The value should be hexadecimal."),
                                 profilesEditorWindow._versionChanged)
        self.pack_start(versionEntry, False, False, 0)

        separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 8)

        physEntry = self._physEntry = \
            IdentityWidget.Entry(_("_Physical location:"),
                                 ValueEntry,
                                 _("When matching the profile for automatic loading, this value, if not empty, will be used as an extra condition."),
                                 profilesEditorWindow._physChanged)
        self.pack_start(physEntry, False, False, 0)

        separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 8)

        uniqEntry = self._uniqEntry = \
            IdentityWidget.Entry(_("_Unique ID:"),
                                 ValueEntry,
                                 _("When matching the profile for automatic loading, this value, if not empty, will be used as an extra condition."),
                                 profilesEditorWindow._uniqChanged)
        self.pack_start(uniqEntry, False, False, 0)

        self.set_sensitive(False)

    def clear(self):
        """Clear the contents of and disable the identity widget."""
        self._versionEntry.clear()
        self._physEntry.clear()
        self._uniqEntry.clear()
        self.set_sensitive(False)

    def setFrom(self, identity):
        """Set the contents of the entry fields from the given identity and
        enable this widget."""
        self._versionEntry.set(identity.inputID.version)
        self._physEntry.set(identity.phys)
        if identity.uniq:
            self._uniqEntry.set(identity.uniq)
        else:
            self._uniqEntry.set("")
        self.set_sensitive(True)

    def setVersion(self, version):
        """Set the version to the given value."""
        self._versionEntry.set(version)

    def setPhys(self, phys):
        """Set the physical location to the given value."""
        self._physEntry.set(phys)

    def setUniq(self, uniq):
        """Set the unique identifier to the given value."""
        self._uniqEntry.set(uniq)

#-------------------------------------------------------------------------------

# FIXME:
# - the handling of the profiles at the top is very similar to the
#   handling of the types in the TypeEditor
# - joystick monitoring is also very similar
class ProfilesEditorWindow(Gtk.ApplicationWindow):
    """The type editor window."""
    def __init__(self, gui, joystick, *args, **kwargs):
        """Construct the window."""
        super().__init__(*args, **kwargs)

        self._gui = gui
        self._joystickType = joystickType = joystick.type
        self._identity = joystick.identity
        self._monitoringJoystick = False
        self._forceMonitoringJoystick = False
        self._focused = False
        self._activeIndex = -1
        self._changingProfile = False

        self._profileList = profileList = ProfileList(joystickType, joystickType.identity)
        profileList.connect("profile-added", self._profileAdded)
        profileList.connect("profile-renamed", self._profileRenamed)
        profileList.connect("profile-removed", self._profileRemoved)

        self._profiles = profiles = Gtk.ListStore(str, object)
        #self._profiles.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        # hasProfile = False
        # for profile in joystickType.profiles:
        #     hasProfile = True
        #     self._profiles.append([profile.name, profile])

        self.set_wmclass("jsprog", joystickType.identity.name + _("Profiles Editor"))
        self.set_role(PROGRAM_NAME)

        self.set_border_width(4)
        self.set_default_size(1300, 800)

        self.set_default_icon_name(PROGRAM_ICON_NAME)

        headerBar = Gtk.HeaderBar()
        headerBar.set_show_close_button(True)
        headerBar.props.title = joystickType.identity.name
        headerBar.set_subtitle(_("Profiles editor"))

        profileLabel = Gtk.Label.new(_("Profile:"))
        headerBar.pack_start(profileLabel)

        self._profileSelector = Gtk.ComboBox.new_with_model(self._profiles)
        profileNameRenderer = self._profileNameRenderer = Gtk.CellRendererText.new()
        self._profileSelector.pack_start(profileNameRenderer, True)
        self._profileSelector.add_attribute(profileNameRenderer, "text", 0)
        self._profileSelector.connect("changed", self._profileSelectionChanged)
        self._profileSelector.set_size_request(200, -1)

        headerBar.pack_start(self._profileSelector)

        editProfileNameButton = self._editProfileNameButton = \
            Gtk.Button.new_from_icon_name(Gtk.STOCK_EDIT, Gtk.IconSize.BUTTON)
        editProfileNameButton.set_tooltip_text(_("Edit the current profile's name and/or file name"))
        editProfileNameButton.set_sensitive(False)
        editProfileNameButton.connect("clicked", self._editProfileName)

        headerBar.pack_start(editProfileNameButton)

        addProfileButton = self._addProfileButton = \
            Gtk.Button.new_from_icon_name("list-add-symbolic",
                                          Gtk.IconSize.BUTTON)
        addProfileButton.set_tooltip_text(_("Add new profile"))
        addProfileButton.set_sensitive(True)
        addProfileButton.connect("clicked", self._addProfile)

        headerBar.pack_start(addProfileButton)

        removeProfileButton = self._removeProfileButton = \
            Gtk.Button.new_from_icon_name("list-remove-symbolic",
                                          Gtk.IconSize.BUTTON)
        removeProfileButton.set_tooltip_text(_("Remove the current profile"))
        removeProfileButton.set_sensitive(False)
        removeProfileButton.connect("clicked", self._removeProfile)

        headerBar.pack_start(removeProfileButton)

        copyProfileButton = self._copyProfileButton = \
            Gtk.Button.new_from_icon_name("edit-copy-symbolic",
                                          Gtk.IconSize.BUTTON)
        copyProfileButton.set_tooltip_text(_("Create a new profile as the copy of the current profile"))
        copyProfileButton.set_sensitive(False)
        copyProfileButton.connect("clicked", self._copyProfile)

        headerBar.pack_start(copyProfileButton)

        self.connect("window-state-event", self._windowStateChanged)
        self.connect("destroy",
                     lambda _window: gui.removeProfilesEditor(joystickType))

        # self._keys = Gtk.ListStore(int, str, str, bool)
        # for key in joystickType.iterKeys:
        #     self._keys.append([key.code, key.name, key.displayName, False])

        # self._axes = Gtk.ListStore(int, str, str, bool)
        # for axis in joystickType.iterAxes:
        #     self._axes.append([axis.code, axis.name, axis.displayName, False])
        # self._axisHighlightTimeouts = {}

        # self._magnification = 1.0

        # paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        # self._imageOverlay = imageOverlay = Gtk.Overlay()

        # self._image = PaddedImage()
        # self._image.connect("size-allocate", self._imageResized)

        # imageOverlay.add(self._image)
        # imageOverlay.connect("button-press-event",
        #                      self._overlayButtonEvent);
        # imageOverlay.connect("button-release-event",
        #                      self._overlayButtonEvent);
        # imageOverlay.connect("motion-notify-event",
        #                      self._overlayMotionEvent);
        # imageOverlay.connect("scroll-event",
        #                      self._overlayScrollEvent);

        # self._imageFixed = Gtk.Fixed()
        # imageOverlay.add_overlay(self._imageFixed)

        # self._hotspotWidgets = []
        # self._draggedHotspot = None
        # self._mouseHighlightedHotspotWidget = None

        # scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        # scrolledWindow.add(imageOverlay)

        # paned.pack1(scrolledWindow, True, True)

        # vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        # (keysFrame, self._keysView) = \
        #     self._createControlListView(_("Buttons"), self._keys)
        # vbox.pack_start(keysFrame, True, True, 4)

        # (axesFrame, self._axesView) = \
        #     self._createControlListView(_("Axes"), self._axes)
        # vbox.pack_start(axesFrame, True, True, 4)

        # vbox.set_margin_left(8)

        # notebook = Gtk.Notebook.new()
        # label = Gtk.Label(_("_Physical controls"))
        # label.set_use_underline(True)
        # notebook.append_page(vbox, label)

        # vcPaned = Gtk.Paned.new(Gtk.Orientation.VERTICAL)

        # vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        # buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        # buttonBox.set_layout(Gtk.ButtonBoxStyle.END)

        # addVirtualControlButton = Gtk.Button.new_from_icon_name("list-add",
        #                                             Gtk.IconSize.BUTTON)
        # addVirtualControlButton.connect("clicked",
        #                                 self._addVirtualControlButtonClicked)
        # buttonBox.add(addVirtualControlButton)

        # self._removeVirtualControlButton = removeVirtualControlButton = \
        #     Gtk.Button.new_from_icon_name("list-remove",
        #                                   Gtk.IconSize.BUTTON)
        # removeVirtualControlButton.set_sensitive(False)
        # removeVirtualControlButton.connect("clicked",
        #                                    self._removeVirtualControlButtonClicked)
        # buttonBox.add(removeVirtualControlButton)

        # vbox.pack_start(buttonBox, False, False, 4)

        # virtualControls = self._virtualControls = Gtk.ListStore(object,
        #                                                         str, str)
        # for virtualControl in joystickType.virtualControls:
        #     displayName = virtualControl.displayName
        #     if not displayName:
        #         displayName = virtualControl.name
        #     virtualControls.append([virtualControl,
        #                             virtualControl.name, displayName])

        # scrolledWindow = Gtk.ScrolledWindow.new(None, None)

        # self._virtualControlsView = view = Gtk.TreeView.new_with_model(virtualControls)

        # nameRenderer = Gtk.CellRendererText.new()
        # nameRenderer.props.editable = True
        # nameRenderer.connect("edited", self._virtualControlNameEdited)
        # nameColumn = Gtk.TreeViewColumn(title = _("Name"),
        #                                 cell_renderer = nameRenderer,
        #                                 text = 1)
        # nameColumn.set_resizable(True)
        # view.append_column(nameColumn)

        # displayNameRenderer = Gtk.CellRendererText.new()
        # displayNameRenderer.props.editable = True
        # displayNameRenderer.connect("edited", self._virtualControlDisplayNameEdited)
        # displayNameColumn = Gtk.TreeViewColumn(title = _("Display name"),
        #                                        cell_renderer =
        #                                        displayNameRenderer,
        #                                        text = 2)
        # view.append_column(displayNameColumn)
        # view.get_selection().connect("changed", self._virtualControlSelected)

        # scrolledWindow.add(view)

        # vbox.pack_start(scrolledWindow, True, True, 0)

        # vcPaned.add1(vbox)

        # vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        # buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        # buttonBox.set_layout(Gtk.ButtonBoxStyle.END)

        # self._editVirtualStateButton = editVirtualStateButton = \
        #     Gtk.Button.new_from_icon_name(Gtk.STOCK_EDIT, Gtk.IconSize.BUTTON)
        # editVirtualStateButton.connect("clicked",
        #                                self._editVirtualStateButtonClicked)
        # editVirtualStateButton.set_sensitive(False)
        # buttonBox.add(editVirtualStateButton)

        # self._addVirtualStateButton = addVirtualStateButton = \
        #     Gtk.Button.new_from_icon_name("list-add", Gtk.IconSize.BUTTON)
        # addVirtualStateButton.set_sensitive(False)
        # addVirtualStateButton.connect("clicked",
        #                               self._addVirtualStateButtonClicked)
        # buttonBox.add(addVirtualStateButton)

        # self._removeVirtualStateButton = removeVirtualStateButton = \
        #     Gtk.Button.new_from_icon_name("list-remove", Gtk.IconSize.BUTTON)
        # removeVirtualStateButton.set_sensitive(False)
        # removeVirtualStateButton.connect("clicked",
        #                                  self._removeVirtualStateButtonClicked)
        # buttonBox.add(removeVirtualStateButton)

        # vbox.pack_start(buttonBox, False, False, 4)

        # virtualStates = self._virtualStates = Gtk.ListStore(object, str, str)
        # self._partialVirtualStates = {}

        # scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        # self._virtualStatesView = view = Gtk.TreeView.new_with_model(virtualStates)
        # view.get_selection().connect("changed", self._virtualStateSelected)

        # displayNameRenderer = Gtk.CellRendererText.new()
        # displayNameRenderer.props.editable = True
        # displayNameRenderer.connect("edited", self._virtualStateDisplayNameEdited)
        # displayNameColumn = Gtk.TreeViewColumn(title = _("State"),
        #                                        cell_renderer = displayNameRenderer,
        #                                        text = 1)
        # displayNameColumn.set_resizable(True)
        # view.append_column(displayNameColumn)

        # constraintRenderer = Gtk.CellRendererText.new()
        # constraintRenderer.props.editable = False
        # constraintColumn = Gtk.TreeViewColumn(title = _("Constraints"),
        #                                       cell_renderer =
        #                                       constraintRenderer,
        #                                       text = 2)
        # view.append_column(constraintColumn)

        # scrolledWindow.add(view)

        # vbox.pack_start(scrolledWindow, True, True, 5)

        # vbox.set_vexpand(True)

        # vcPaned.add2(vbox)

        # vcPaned.set_position(200)

        # label = Gtk.Label(_("_Virtual controls"))
        # label.set_use_underline(True)

        # notebook.append_page(vcPaned, label)

        # paned.pack2(notebook, False, False)

        # paned.set_wide_handle(True)
        # paned.set_position(900)

        # self.add(paned)

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        identityWidget = self._identityWidget = IdentityWidget(self)
        vbox.pack_start(identityWidget, False, False, 0)

        # paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        # alignment = Gtk.Entry()
        # alignment.set_valign(Gtk.Align.FILL)
        # paned.pack1(alignment, True, False)
        # alignment = Gtk.Entry()
        # alignment.set_valign(Gtk.Align.FILL)
        # paned.pack2(alignment, True, False)
        # vbox.pack_start(paned, True, True, 0)

        self.add(vbox)

        gui.addProfilesEditor(joystickType, self)

        self.set_titlebar(headerBar)

        profileList.setup()
        if profiles.iter_n_children(None)>0:
            self._profileSelector.set_active(0)

        self.show_all()

        # window = self._imageFixed.get_window()
        # window.set_events(window.get_events() |
        #                   Gdk.EventMask.BUTTON_PRESS_MASK |
        #                   Gdk.EventMask.BUTTON_RELEASE_MASK |
        #                   Gdk.EventMask.POINTER_MOTION_MASK |
        #                   Gdk.EventMask.SCROLL_MASK |
        #                   Gdk.EventMask.SMOOTH_SCROLL_MASK)

        # joystickType.connect("save-failed", self._saveFailed)

        #if hasProfile:
        #    self._profileSelector.set_active(0)

    @property
    def joystickType(self):
        """Get the joystick type this editor window belongs to."""
        return self._joystickType

    @property
    def activeProfile(self):
        """Get the active profile."""
        i = self._profileSelector.get_active_iter()
        if i is not None:
            return self._profiles.get_value(i, 1)

    def copyVersion(self, version):
        """Copy the given version into the current profile being edited."""
        if self.activeProfile is not None:
            self._identityWidget.setVersion(version)

    def copyPhys(self, phys):
        """Copy the given physical location into the current profile being edited."""
        if self.activeProfile is not None:
            self._identityWidget.setPhys(phys)

    def copyUniq(self, uniq):
        """Copy the given unique identifier into the current profile being edited."""
        if self.activeProfile is not None:
            self._identityWidget.setUniq(uniq)

    def _profileAdded(self, profileList, profile, name, index):
        """Called when a profile is added."""
        self._profiles.insert(index, (name, profile))

    def _profileRenamed(self, profileList, profile, name, oldIndex, index):
        """Called when a profile is renamed."""
        i = self._profiles.iter_nth_child(None, oldIndex)
        self._profiles.set_value(i, 0, name)
        if oldIndex!=index:
            if oldIndex<index:
                index += 1
            i = self._profiles.iter_nth_child(None, oldIndex)
            j = self._profiles.iter_nth_child(None, index)

            self._profiles.move_before(i, j)

    def _profileRemoved(self, profileList, profile, index):
        """Called when a profile is removed."""
        i = self._profiles.iter_nth_child(None, index)

        activeIter = None
        if profile is self.activeProfile:
            activeIter = self._profiles.iter_next(i)
            if activeIter is None:
                activeIter = self._profiles.iter_previous(i)

        self._profiles.remove(i)

        if activeIter is not None:
            self._profileSelector.set_active_iter(activeIter)

    def _profileSelectionChanged(self, comboBox):
        """Called when the profile selection has changed."""
        self._activeIndex = self._profileSelector.get_active()
        self._changingProfile = True
        i = self._profileSelector.get_active_iter()
        if i is None:
            self._editProfileNameButton.set_sensitive(False)
            self._removeProfileButton.set_sensitive(False)
            self._copyProfileButton.set_sensitive(False)
            self._gui.editingProfile(self._joystickType, None)
            self._identityWidget.clear()
        else:
            profile = self._profiles.get_value(i, 1)
            self._editProfileNameButton.set_sensitive(profile.userDefined)
            self._removeProfileButton.set_sensitive(profile.userDefined)
            self._copyProfileButton.set_sensitive(True)
            self._gui.editingProfile(self._joystickType, profile)
            self._identityWidget.setFrom(profile.identity)
        self._changingProfile = False

    def _findProfileIter(self, profile):
        """Find the iterator in the profile selector for the given profile."""
        profiles = self._profiles
        i = profiles.get_iter_first()
        while i is not None:
            p = profiles.get_value(i, 1)
            if p is profile:
                return i
            i = profiles.iter_next(i)

    def _findProfileNameIter(self,  name):
        """Find the iterator in the profile selector for the given profile name."""
        profiles = self._profiles
        i = profiles.get_iter_first()
        while i is not None:
            n = profiles.get_value(i, 0)
            if n==name:
                return i
            i = profiles.iter_next(i)

    def _editProfileName(self, button):
        """Called when the current profile's name should be edited."""
        i = self._profileSelector.get_active_iter()

        profile = self._profiles.get_value(i, 1)

        dialog = ProfileNameDialog(self, _("Edit profile name"), profile = profile)
        dialog.show()

        response = dialog.run()

        newName = dialog.name
        newFileName = dialog.fileName

        dialog.destroy()

        if response==Gtk.ResponseType.OK and \
           (newName!=profile.name or newFileName!=profile.fileName):
            updateResult = self._joystickType.updateProfileNames(profile,
                                                                 newName,
                                                                 newFileName)
            assert updateResult is not False

    def _doAddProfile(self, fromProfile = None):
        """Add a new profile.

        The new profile is either empty or is a copy of the given one."""
        dialog = ProfileNameDialog(self,
                                   _("New profile") if fromProfile is None
                                   else _("Copy profile"),
                                   initialName = None if fromProfile is None
                                   else (_("Copy of ") + fromProfile.name))
        dialog.show()

        response = dialog.run()

        name = dialog.name
        fileName = dialog.fileName

        dialog.destroy()
        if response==Gtk.ResponseType.OK:
            newProfile = self._joystickType.addProfile(name, fileName,
                                                       self._identity,
                                                       cloneFrom = fromProfile)
            assert newProfile is not None

            i = self._findProfileIter(newProfile)
            self._profileSelector.set_active_iter(i)

    def _addProfile(self, button):
        """Called when a new profile is to be added."""
        self._doAddProfile()

    def _removeProfile(self, button):
        """Called when the current profile should be removed."""
        i = self._profileSelector.get_active_iter()

        profileName = self._profiles.get_value(i, 0)

        if yesNoDialog(self,
                       _("Are you sure to remove profile '{0}'?").format(profileName)):

            profile = self._profiles.get_value(i, 1)
            self._joystickType.deleteProfile(profile)

    def _copyProfile(self, button):
        """Called when the current profile should be copied into a new one."""
        i = self._profileSelector.get_active_iter()

        profile = self._profiles.get_value(i, 1)

        self._doAddProfile(fromProfile = profile)

    def _windowStateChanged(self, window, event):
        """Called when the window's state has changed.

        If the window became focused, the monitoring of the joysticks of its
        type is started. If the window lost the focus, the monitoring is
        stopped."""
        if (event.changed_mask&Gdk.WindowState.FOCUSED)!=0:
            self._focused = (event.new_window_state&Gdk.WindowState.FOCUSED)!=0
            self._updateJoystickMonitoring()

    def _updateJoystickMonitoring(self):
        """Update the monitoring of the joysticks based on the current focus
        state."""
        if self._focused:
            if not self._monitoringJoystick:
                if self._gui.startMonitorJoysticksFor(self._joystickType):
                    self._monitoringJoystick = True
                    # for state in self._gui.getJoystickStatesFor(self._joystickType):
                    #     for keyData in state[0]:
                    #         code = keyData[0]
                    #         value = keyData[1]
                    #         if value>0:
                    #             self._keys.set_value(self._getKeyIterForCode(code),
                    #                                  3, True)

        else:
            if self._monitoringJoystick and \
               not self._forceMonitoringJoystick:
                if self._gui.stopMonitorJoysticksFor(self._joystickType):
                    self._monitoringJoystick = False
                    # for (timeoutID, _step) in self._axisHighlightTimeouts.values():
                    #     GLib.source_remove(timeoutID)
                    # self._axisHighlightTimeouts = {}

                    # self._clearHighlights(self._keys)
                    # self._clearHighlights(self._axes)

        # self._setupHotspotHighlights()

    def _versionChanged(self, entry, value):
        """Called when the version of the profile being edited has changed."""
        if not self._changingProfile:
            profile = self.activeProfile
            if profile is not None:
                profile.identity.inputID.version = value
                self._joystickType.updateProfileIdentity(profile)

    def _physChanged(self, entry, value):
        """Called when the physical location of the profile being edited has changed."""
        if not self._changingProfile:
            profile = self.activeProfile
            if profile is not None:
                profile.identity.phys = value
                self._joystickType.updateProfileIdentity(profile)

    def _uniqChanged(self, entry, value):
        """Called when the unique identifier of the profile being edited has changed."""
        if not self._changingProfile:
            profile = self.activeProfile
            if profile is not None:
                profile.identity.uniq = value
                self._joystickType.updateProfileIdentity(profile)
