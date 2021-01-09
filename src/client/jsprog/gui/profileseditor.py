# Joystick profiles editor window

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from .vceditor import VirtualControlEditor, NewVirtualControlDialog

from jsprog.profile import Profile, ShiftLevel
from jsprog.parser import SingleValueConstraint, Control, VirtualState
from jsprog.device import DisplayVirtualState
from jsprog.action import Action, SimpleAction
from .joystick import ProfileList, findCodeForGdkKey
from jsprog.joystick import Key

import traceback
import math

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
                                 profilesEditorWindow.versionChanged)
        self.pack_start(versionEntry, False, False, 0)

        separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 8)

        physEntry = self._physEntry = \
            IdentityWidget.Entry(_("_Physical location:"),
                                 ValueEntry,
                                 _("When matching the profile for automatic loading, this value, if not empty, will be used as an extra condition."),
                                 profilesEditorWindow.physChanged)
        self.pack_start(physEntry, False, False, 0)

        separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 8)

        uniqEntry = self._uniqEntry = \
            IdentityWidget.Entry(_("_Unique ID:"),
                                 ValueEntry,
                                 _("When matching the profile for automatic loading, this value, if not empty, will be used as an extra condition."),
                                 profilesEditorWindow.uniqChanged)
        self.pack_start(uniqEntry, False, False, 0)

        separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 8)

        autoLoadButton = self._autoLoadButton = \
            Gtk.CheckButton.new_with_label(_("_Auto-load profile"))
        autoLoadButton.set_use_underline(True)
        autoLoadButton.set_tooltip_text(_("If selected, the profile will be "
                                          "a candidate to be "
                                          "loaded automatically when a matching "
                                          "joystick is connected. If any of "
                                          "the version, the physical location "
                                          "or the unique identifier is given, "
                                          "the more specific the match will "
                                          "be. If the unique identifiers match "
                                          "that trumps everything."))
        autoLoadButton.connect("clicked", profilesEditorWindow.autoLoadClicked)
        self.pack_start(autoLoadButton, False, False, 0)

        self.set_sensitive(False)

    def clear(self):
        """Clear the contents of and disable the identity widget."""
        self._versionEntry.clear()
        self._physEntry.clear()
        self._uniqEntry.clear()
        self.set_sensitive(False)

    def setFrom(self, identity, autoLoad):
        """Set the contents of the entry fields from the given identity and
        enable this widget."""
        self._versionEntry.set(identity.inputID.version)
        self._physEntry.set(identity.phys)
        if identity.uniq:
            self._uniqEntry.set(identity.uniq)
        else:
            self._uniqEntry.set("")
        self._autoLoadButton.set_active(autoLoad)
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

class ShiftStatesWidget(Gtk.DrawingArea, Gtk.Scrollable):
    """The widget displaying the shift states in a hierarchical manner."""
    # GObject property: 'vscroll_policy'
    vscroll_policy = GObject.property(type=Gtk.ScrollablePolicy,
                                      default=Gtk.ScrollablePolicy.MINIMUM)

    # GObject property: 'vadjustment'
    vadjustment = GObject.property(type=Gtk.Adjustment)

    # GObject property: 'hscroll_policy'
    hscroll_policy = GObject.property(type=Gtk.ScrollablePolicy,
                                      default=Gtk.ScrollablePolicy.MINIMUM)

    # The default label for a shift state
    DEFAULT_STATE_LABEL = _("Default")

    # The gap between columns. It includes a column separator and some space on
    # both sides
    COLUMN_GAP = 11

    # The gap between levels, which includes some space above and below the
    # labels as well as the separator
    LEVEL_GAP = 17

    class Level(object):
        """Information about a shift level."""
        # The gap between rows of a constraint
        ROW_GAP = 3
        def __init__(self, shiftStatesWidget, joystickType, profile, shiftLevel, pangoLayout):
            """Construct the level from the given shift level object of the
            profile."""
            self._shiftStatesWidget = shiftStatesWidget

            self.numStates = 0
            self.columnWidth = 0
            self.labels = []

            self.numRows = 1
            self.rowHeight = 0

            if shiftLevel is None:
                self._addStateLabels(pangoLayout, [ShiftStatesWidget.DEFAULT_STATE_LABEL])
            else:
                for state in shiftLevel.states:
                    stateLabels = \
                        ShiftStatesWidget.getShiftStateLabels(joystickType,
                                                              profile,
                                                              state)
                    self._addStateLabels(pangoLayout, stateLabels)

        @property
        def width(self):
            """Get the total width needed for the level.

            Note, that if this is not the topmost level, it may need to be
            displayed more than once. This property is the width for a single
            instance."""
            return self.numStates * self.columnWidth + \
                (self.numStates - 1) * ShiftStatesWidget.COLUMN_GAP

        @width.setter
        def width(self, w):
            """Set the width, i.e. the column width so that the level is so
            wide as given."""

            self.columnWidth = \
                (w - (self.numStates - 1) * ShiftStatesWidget.COLUMN_GAP)/ \
                self.numStates

        @property
        def height(self):
            """Get the total height needed for the level considering also any
            buttons to the left."""
            return max(self._shiftStatesWidget._profileWidget.topWidget.minButtonHeight,
                       self.minHeight)

        @property
        def minHeight(self):
            """Get the minimal height of the widget."""
            return self.numRows * self.rowHeight + (self.numRows - 1) * self.ROW_GAP

        def getSeparatorCoordinates(self, x, stretch):
            """Get the coordinates for the separators when starting to render
            the level at the given X-coordinate."""
            coordinates = []

            columnWidth = self.columnWidth * stretch
            for stateLabels in self.labels:
                if stateLabels is not self.labels[-1]:
                    lineX = round(x + columnWidth + (ShiftStatesWidget.COLUMN_GAP-1)/2)
                    coordinates.append(lineX)
                x += columnWidth + ShiftStatesWidget.COLUMN_GAP

            return coordinates

        def draw(self, cr, pangoLayout, styleContext, x, y0, topY, bottomY, stretch):
            """Draw the level with the given context and layout."""
            columnWidth = self.columnWidth * stretch
            for stateLabels in self.labels:
                y = y0
                for row in stateLabels:
                    pangoLayout.set_text(row)
                    (_ink, logical) = pangoLayout.get_extents()
                    width = (logical.x + logical.width) / Pango.SCALE
                    xOffset = (columnWidth - width)/2
                    Gtk.render_layout(styleContext, cr,
                                      x + xOffset, y, pangoLayout)
                    y += self.rowHeight + self.ROW_GAP
                if stateLabels is not self.labels[-1]:
                    lineX = round(x + columnWidth +
                                  (ShiftStatesWidget.COLUMN_GAP-1)/2)
                    separatorDrawer.drawVertical(cr, lineX, topY, bottomY - topY)
                x += columnWidth + ShiftStatesWidget.COLUMN_GAP

        def _addStateLabels(self, pangoLayout, stateLabels):
            """Add the given state labels to the level and update information
            accordingly."""
            self.numStates += 1

            self.numRows = max(self.numRows, len(stateLabels))
            self.labels.append(stateLabels)

            for label in stateLabels:
                pangoLayout.set_text(label)
                (_ink, logical) = pangoLayout.get_extents()

                width = (logical.x + logical.width) / Pango.SCALE
                height = (logical.y + logical.height) / Pango.SCALE

                self.columnWidth = max(self.columnWidth, width)
                self.rowHeight = max(self.rowHeight, height)
            self.columnWidth = max(ProfileWidget.MIN_COLUMN_WIDTH, self.columnWidth)

    @staticmethod
    def getConstraintValueText(profile, constraint):
        """Get the text for the value of the given constraint."""
        control = constraint.control

        if control.isKey:
            return _("released") if constraint.value==0 else _("pressed")
        elif isinstance(constraint, SingleValueConstraint):
            value = constraint.value
            if control.isVirtual:
                vc = profile.findVirtualControlByCode(control.code)
                if vc is not None:
                    state = vc.getState(value)
                    if isinstance(state, DisplayVirtualState):
                        value = state.displayName
            return str(value)
        else:
            return "%%d..%d" % (constraint.fromValue, constraint.toValue)

    @staticmethod
    def getConstraintText(joystickType, profile, constraint):
        """Get the text for the given constraint."""
        return joystickType.getControlDisplayName(constraint.control, profile) + ": " + \
            ShiftStatesWidget.getConstraintValueText(profile, constraint)

    @staticmethod
    def getShiftStateLabels(joystickType, profile, state):
        """Get the labels for the given shift state.

        An array is returned with each element being a textual descriptor of a
        constraint in the state. If there are no constraints, a single default
        label is returned."""
        labels = []
        for constraint in state.constraints:
            labels.append(ShiftStatesWidget.getConstraintText(joystickType,
                                                              profile, constraint))

        if len(labels)==0:
            labels.append(ShiftStatesWidget.DEFAULT_STATE_LABEL)

        return labels

    def __init__(self, profileWidget):
        super().__init__()

        self._hadjustment = None

        self._profileWidget = profileWidget

        self._levels = []
        self.shiftStateSequences = []
        self.minWidth = 0
        self.minHeight = 0
        self._columnSeparatorCoordinates = []
        self._currentStretch = 0.0
        self.minColumnWidth = 50

        self._layout = Pango.Layout(self.get_pango_context())

        self.connect("size-allocate", self._resized)
        self.set_hexpand(True)

    @GObject.Property(type=Gtk.Adjustment)
    def hadjustment(self):
        """Get the hadjustment property."""
        return self._hadjustment

    @hadjustment.setter
    def hadjustment(self, adjustment):
        """Set the hadjustment property."""
        self._hadjustment = adjustment
        adjustment.connect("value-changed", self._adjustmentValueChanged)

    @property
    def numColumns(self):
        """Get the number of columns."""
        return len(self._columnSeparatorCoordinates) + 1

    @property
    def stretch(self):
        """Get the current horizontal stretch of the widget."""
        allocation = self.get_allocation()
        return max(1.0, allocation.width / self.minWidth)

    @property
    def levels(self):
        """Return an iterator over the levels."""
        return iter(self._levels)

    @property
    def minLevelHeight(self):
        """Get the height of the smallest level."""
        height = 0
        for level in self._levels:
            height = level.height if height==0 else min(height, level.height)
        return height

    def getColumnSeparatorCoordinates(self, stretch):
        """Get an iterator over the column separator coordinates for the given
        stretch."""
        self._recalculateColumnSeparatorCoordinates(stretch)
        return iter(self._columnSeparatorCoordinates)

    def profileChanged(self):
        """Called when the profile is changed."""

        profilesEditorWindow = self._profileWidget.profilesEditorWindow
        profile = profilesEditorWindow.activeProfile
        joystickType = profilesEditorWindow.joystickType

        self._levels = []
        self.shiftStateSequences = []
        self.minHeight = 0
        self.minWidth = 0
        self._columnSeparatorCoordinates = []
        self._currentStretch = 0.0

        if profile is None:
            return

        if profile.numShiftLevels>0:
            previousLevel = None

            shiftStateSequences = []
            for i in range(0, profile.numShiftLevels):
                shiftLevel = profile.getShiftLevel(i)
                level = ShiftStatesWidget.Level(self, joystickType, profile,
                                                shiftLevel, self._layout)
                self.minHeight += level.height
                self._levels.append(level)
                previousLevel = level
                self.minColumnWidth = level.columnWidth
                numStates = level.numStates
                if shiftStateSequences:
                    newSSS = []
                    for seq in shiftStateSequences:
                        for i in range(0, numStates):
                            newSSS.append(seq + [i])
                    shiftStateSequences = newSSS
                else:
                    for i in range(0, numStates):
                        shiftStateSequences.append([i])

            self.shiftStateSequences = shiftStateSequences

            previousLevel = None
            for level in reversed(self._levels):
                if previousLevel is not None:
                    level.columnWidth = max(level.columnWidth, previousLevel.width)
                previousLevel = level

            previousLevel = None
            for level in self._levels:
                if previousLevel is not None:
                    if previousLevel.columnWidth > level.width:
                        level.width = previousLevel.columnWidth
                previousLevel = level

            self.minWidth = self._levels[0].width + self.COLUMN_GAP - 1
            self.minHeight += profile.numShiftLevels * self.LEVEL_GAP
        else:
            self.shiftStateSequences = [[]]
            self.minWidth = ProfileWidget.MIN_COLUMN_WIDTH

        self._recalculateColumnSeparatorCoordinates(self.stretch)

        self.queue_resize()

    def getShiftStateIndexForX(self, x):
        """Get the shift state index for the given X-coordinate."""
        columnSeparatorCoordinates = \
            self.getColumnSeparatorCoordinates(self.stretch)
        previousCoordinate = 0
        for (index, coordinate) in enumerate(columnSeparatorCoordinates):
            if x>previousCoordinate and x<coordinate:
                return index
            elif x<=coordinate:
                break
            else:
                previousCoordinate = coordinate

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self, *args):
        """Get the preferred width of the widget."""
        return (0, 0)

    def do_get_preferred_height(self, *args):
        """Get the preferred height of the widget."""
        return (self.minHeight, self.minHeight)

    def do_draw(self, cr):
        """Draw the widget."""
        if not self._levels:
            return

        allocation = self.get_allocation()
        stretch = self.stretch
        adjustmentValue = int(self._hadjustment.get_value())

        styleContext = self.get_style_context()

        Gtk.render_background(styleContext, cr, 0, 0, allocation.width, allocation.height)

        separatorDrawer.drawHorizontal(cr, -adjustmentValue, 0, self.minWidth * stretch)

        y = self.LEVEL_GAP / 2 - 1
        numRepeats = 1
        for level in self._levels:
            x = -adjustmentValue + (self.COLUMN_GAP - 1) / 2
            topY = y - (self.LEVEL_GAP/2 - 1)
            if level is not self._levels[-1]:
                bottomY = y + level.height + self.LEVEL_GAP/2 - 1
                separatorDrawer.drawHorizontal(cr, 0, bottomY, allocation.width)

            yOffset = (level.height - level.minHeight) / 2
            for i in range(0, numRepeats):
                level.draw(cr, self._layout, styleContext, x, y + yOffset,
                           topY, allocation.height, stretch)
                x += level.width * stretch + self.COLUMN_GAP

            numRepeats *= len(level.labels)
            y += level.height + self.LEVEL_GAP

        separatorDrawer.drawVertical(cr, 0, 0, allocation.height)
        separatorDrawer.drawVertical(cr, allocation.width - 1, 0, allocation.height)

        return True

    def _resized(self, _widget, allocation):
        """Called when the widget is resized.

        The column separator coordinates are recalculated."""
        if not self._levels:
            return

        self._recalculateColumnSeparatorCoordinates(self.stretch)

    def _recalculateColumnSeparatorCoordinates(self, stretch):
        """Recalculate the column separator coordinates."""

        if stretch==self._currentStretch:
            return self._columnSeparatorCoordinates

        coordinates = []

        numRepeats = 1
        for level in self._levels:
            x = (self.COLUMN_GAP - 1) / 2

            numLevelColumns = len(level.labels)
            for i in range(0, numRepeats):
                levelCoordinates = level.getSeparatorCoordinates(x, stretch)
                coordinates = coordinates[:i*numLevelColumns] + \
                    levelCoordinates + coordinates[i*numLevelColumns:]
                x += level.width * stretch + self.COLUMN_GAP

            numRepeats *= numLevelColumns

        coordinates.append(int(self.minWidth*stretch-1))

        self._columnSeparatorCoordinates = coordinates
        self._currentStretch = stretch

        return coordinates

    def _adjustmentValueChanged(self, *args):
        """Called when the adjustment value of the horizontal scrollbar of the
        action widget has changed."""
        self.queue_draw()

#-------------------------------------------------------------------------------

class ControlsWidget(Gtk.DrawingArea, Gtk.Scrollable):
    """The widget for the controls."""
    # GObject property: 'vscroll_policy'
    vscroll_policy = GObject.property(type=Gtk.ScrollablePolicy,
                                      default=Gtk.ScrollablePolicy.MINIMUM)

    # GObject property: 'hscroll_policy'
    hscroll_policy = GObject.property(type=Gtk.ScrollablePolicy,
                                      default=Gtk.ScrollablePolicy.MINIMUM)

    # GObject property: 'hadjustment'
    hadjustment = GObject.property(type=Gtk.Adjustment)

    # The margin to the left of a label
    LABEL_LEFT_MARGIN = 4

    # The margen to the right of a control label
    LABEL_RIGHT_MARGIN = 12

    # The gap between a control and its state
    CONTROL_STATE_GAP = 16

    # The gap between controls. It includes a row separator and some space on
    # both sides
    CONTROL_GAP = 29

    # The indentation of a separator between control states
    CONTROL_STATE_INDENT = 40

    def __init__(self, profileWidget):
        """Construct the widget for the given profile widget."""
        super().__init__()

        self._vadjustment = None
        self._profileWidget = profileWidget

        self._layout = layout = Pango.Layout(self.get_pango_context())

        self._rowSeparatorCoordinates = []
        self._currentStretch = 0.0

        joystickType = profileWidget.profilesEditorWindow.joystickType

        self._minWidth = 0
        self._minLabelHeight = 0

        self._joystickControlStates = []
        for key in joystickType.keys:
            self._joystickControlStates.append((key, None))

        for axis in joystickType.axes:
            self._joystickControlStates.append((axis, None))

        self._profileControlStates = []

        self._recalculateSizes()

        self.set_vexpand(True)

        self.connect("size-allocate", self._resized)

        self.show_all()

    @GObject.Property(type=Gtk.Adjustment)
    def vadjustment(self):
        """Get the vadjustment property."""
        return self._vadjustment

    @vadjustment.setter
    def vadjustment(self, adjustment):
        """Set the vadjustment property."""
        self._vadjustment = adjustment
        adjustment.connect("value-changed", self._adjustmentValueChanged)

    @property
    def minControlHeight(self):
        """Get the minimal height of a control."""
        return self._minLabelHeight + ControlsWidget.CONTROL_GAP

    @property
    def minHeight(self):
        """Get the minimal height of the widget."""
        return self.numControlStates*self.minControlHeight - 1

    @property
    def numControlStates(self):
        """Get the number of controls."""
        return len(self._joystickControlStates) + \
            len(self._profileControlStates)

    @property
    def controlStates(self):
        """Get an iterator over the controls."""
        for s in self._joystickControlStates:
            yield s
        for s in self._profileControlStates:
            yield s

    @property
    def stretch(self):
        """Get the current vertical tretch of the widget."""
        allocation = self.get_allocation()
        return max(1.0, allocation.height / self.minHeight)

    def getControlState(self, index):
        """Get the control state at the given index."""
        return self._joystickControlStates[index] \
            if index<len(self._joystickControlStates) \
            else self._profileControlStates[index-len(self._joystickControlStates)]

    def getControlStateIndexForY(self, y):
        """Get the index of the control state that is displayed at the given
        y-coordinate."""
        rowHeight = (self._minLabelHeight + ControlsWidget.CONTROL_GAP) * self.stretch

        return int(y / rowHeight)

    def profileChanged(self):
        """Called when the profile has changed."""
        profilesEditorWindow = self._profileWidget.profilesEditorWindow
        profile = profilesEditorWindow.activeProfile

        vcNames = set()
        self._profileControlStates = []
        for vc in profile.allVirtualControls:
            vcNames.add(vc.name)
            for state in vc.states:
                self._profileControlStates.append((vc, state))

        self._recalculateSizes()

        self.queue_resize()

    def getRowSeparatorCoordinates(self, stretch):
        """Get an iterator over the row separator coordinates for the given
        stretch."""
        self._recalculateRowSeparatorCoordinates(stretch)
        return iter(self._rowSeparatorCoordinates)

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self, *args):
        return (self._minWidth, self._minWidth)

    def do_get_preferred_height(self, *args):
        return (0, 0)

    def do_draw(self, cr):
        """Draw the widget."""

        allocation = self.get_allocation()
        stretch = self.stretch
        adjustmentValue = int(self._vadjustment.get_value())

        styleContext = self.get_style_context()

        Gtk.render_background(styleContext, cr, 0, 0, allocation.width, allocation.height)

        separatorDrawer.drawHorizontal(cr, 0, 0, allocation.width)

        minRowHeight = self._minLabelHeight + ControlsWidget.CONTROL_GAP
        rowHeight = minRowHeight * stretch

        y = -adjustmentValue

        pangoLayout = self._layout
        previousControl = None
        for (control, state) in self.controlStates:
            yOffset = None
            if control is not previousControl:
               (_width, height) = getTextSizes(pangoLayout,
                                               control.name
                                               if control.displayName is None
                                               else control.displayName)
               yOffset = (rowHeight - height) / 2
               Gtk.render_layout(styleContext, cr, self.LABEL_LEFT_MARGIN,
                                 y + yOffset, pangoLayout)

            if state is not None:
                (width, height) = getTextSizes(pangoLayout,
                                               control.value
                                               if state.displayName is None
                                               else state.displayName)
                if yOffset is None:
                    yOffset = (rowHeight - height) / 2
                Gtk.render_layout(styleContext, cr,
                                  allocation.width - width - self.LABEL_RIGHT_MARGIN,
                                  y + yOffset, pangoLayout)

            if control is previousControl and state is not None:
                separatorDrawer.drawHorizontal(cr, self.CONTROL_STATE_INDENT,
                                               y,
                                               allocation.width - self.CONTROL_STATE_INDENT)
            elif previousControl is not None:
                separatorDrawer.drawHorizontal(cr, 0, y, allocation.width)

            previousControl = control

            y += rowHeight

        separatorDrawer.drawHorizontal(cr, 0, allocation.height - 1, allocation.width)
        separatorDrawer.drawVertical(cr, 0, 0, allocation.height)

        return 0

    def _resized(self, _widget, allocation):
        """Called when the widget is resized.

        The row separator coordinates are recalculated."""
        self._recalculateRowSeparatorCoordinates(self.stretch)

    def _recalculateSizes(self):
        """Recalculate the sizes based on the current control set."""
        layout = self._layout

        self._minWidth = 0
        self._minLabelHeight = 0

        for (control, state) in self.controlStates:
            (width, height) = getTextSizes(layout, control.name if
                                           control.displayName is None
                                           else control.displayName)

            if state is not None:
                (w, h) = getTextSizes(layout, state.value if
                                      state.displayName is None
                                      else state.displayName)

                height = max(height, h)
                width += w + self.CONTROL_STATE_GAP

            self._minWidth = max(self._minWidth, width)
            self._minLabelHeight = max(self._minLabelHeight, height)

        self._minWidth += self.LABEL_LEFT_MARGIN
        self._minWidth += self.LABEL_RIGHT_MARGIN

    def _recalculateRowSeparatorCoordinates(self, stretch):
        """Recalculate the row separator coordinates."""

        if stretch==self._currentStretch:
            return self._rowSeparatorCoordinates

        coordinates = []

        minRowHeight = self._minLabelHeight + ControlsWidget.CONTROL_GAP
        rowHeight = minRowHeight * stretch

        y = 0
        for _control in self.controlStates:
            coordinates.append(y + rowHeight)
            y += rowHeight

        self._rowSeparatorCoordinates = coordinates
        self._currentStretch = stretch

        return coordinates

    def _adjustmentValueChanged(self, *args):
        """Called when the adjustment value of the horizontal scrollbar of the
        action widget has changed."""
        self.queue_draw()

#-------------------------------------------------------------------------------

class KeyDrawer(object):
    """Suppport for drawing keyboard keys."""
    # The margin on the sides of the key's text
    TEXT_HORIZONTAL_MARGIN = 8

    # The margin above and below the key's text
    TEXT_VERTICAL_MARGIN = 4

    # The radius of the inner corner of a key
    KEY_INNER_CORNER_RADIUS = 6

    # The distance between the inner and outer outlines of the key
    KEY_INNER_OUTER_GAP = 6

    @staticmethod
    def draw(cr, styleContext, pangoLayout, text, x, y, height):
        """Draw a key with the given text at the given coordinates with the
        given height.

        The width will be returned."""
        pangoLayout.set_text(text)

        (_ink, logical) = pangoLayout.get_extents()
        textWidth = (logical.x + logical.width) / Pango.SCALE
        textHeight = (logical.y + logical.height) / Pango.SCALE

        totalHeight = textHeight + \
            2 * KeyDrawer.TEXT_VERTICAL_MARGIN + \
            2 * KeyDrawer.KEY_INNER_OUTER_GAP
        totalWidth = textWidth + \
            2 * KeyDrawer.TEXT_HORIZONTAL_MARGIN + \
            2 * KeyDrawer.KEY_INNER_OUTER_GAP

        scale = height / totalHeight

        cr.save()

        cr.scale(scale, scale)

        x /= scale
        y /= scale

        innerRadius = KeyDrawer.KEY_INNER_CORNER_RADIUS
        innerOuterGap = KeyDrawer.KEY_INNER_OUTER_GAP
        outerRadius = innerRadius * 1.5 # + innerOuterGap

        cr.set_line_width(1.0)

        cr.arc(x + outerRadius, y + outerRadius, outerRadius,
               math.pi, 3 * math.pi / 2)
        cr.line_to(x + totalWidth - outerRadius, y)
        cr.arc(x + totalWidth - outerRadius, y + outerRadius, outerRadius,
               3 * math.pi / 2, 0)
        cr.line_to(x + totalWidth, y + totalHeight - outerRadius)
        cr.arc(x + totalWidth - outerRadius, y + totalHeight -  outerRadius,
               outerRadius, 0, math.pi / 2)
        cr.line_to(x + outerRadius, y + totalHeight)
        cr.arc(x + outerRadius, y + totalHeight -  outerRadius,
               outerRadius, math.pi/2, math.pi)
        cr.close_path()

        cr.stroke()


        cr.arc(x + innerOuterGap + innerRadius,
               y + innerOuterGap + innerRadius, innerRadius,
               math.pi, 3 * math.pi / 2)
        cr.line_to(x + totalWidth - innerOuterGap - innerRadius, y + innerOuterGap)
        cr.arc(x + totalWidth - innerOuterGap - innerRadius,
               y + innerOuterGap + innerRadius,
               innerRadius,
               3 * math.pi / 2, 0)
        cr.line_to(x + totalWidth - innerOuterGap,
                   y + totalHeight - innerOuterGap - innerRadius)
        cr.arc(x + totalWidth - innerOuterGap - innerRadius,
               y + totalHeight - innerOuterGap - innerRadius,
               innerRadius, 0, math.pi / 2)
        cr.line_to(x + innerOuterGap + innerRadius,
                   y + totalHeight - innerOuterGap)
        cr.arc(x + innerOuterGap + innerRadius,
               y + totalHeight - innerOuterGap - innerRadius,
               innerRadius, math.pi/2, math.pi)
        cr.close_path()

        cr.stroke()

        Gtk.render_layout(styleContext, cr,
                          x + innerOuterGap +
                          KeyDrawer.TEXT_HORIZONTAL_MARGIN,
                          y + innerOuterGap +
                          KeyDrawer.TEXT_VERTICAL_MARGIN,
                          pangoLayout)
        cr.stroke()

        cr.restore()

        return totalWidth * scale

#-------------------------------------------------------------------------------

class KeyCombinationEntry(Gtk.EventBox):
    """A widget to allow entering a key combination."""
    # The margin around the text
    TEXT_MARGIN = 4

    def __init__(self, dialog, keyCombination = None, autoEdit = False):
        super().__init__()

        self._dialog = dialog

        self._keyCombination = \
            SimpleAction.KeyCombination(0) if keyCombination is None \
            else keyCombination

        self._autoEdit = autoEdit

        self._pangoLayout = Pango.Layout(self.get_pango_context())

        self._placeHolderPangoLayout = self._pangoLayout.copy()
        attrList = Pango.AttrList.new()

        (found, color) = entryStyle.styleContext.lookup_color("placeholder_text_color")
        if not found:
            color = Gdk.RGBA(0.5, 0.5, 0.5, 1.0)

        attr = Pango.attr_foreground_new(color.red * 65535,
                                         color.green * 65535,
                                         color.blue * 65535)
        attrList.insert(attr)

        self._placeHolderPangoLayout.set_attributes(attrList)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("button-release-event", self._buttonReleaseEvent)

        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.add_events(Gdk.EventMask.KEY_RELEASE_MASK)
        self.connect_after("key-press-event", self._keyboardEvent)
        self.connect_after("key-release-event", self._keyboardEvent)

        self.set_can_focus(True)

        self._editing = False
        self._savedKeyCombination = None

        self.connect("focus-in-event", self._focusIn)

    @property
    def keyCombination(self):
        """Get the key combination."""
        return self._keyCombination

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self, *args):
        """Get the preferred width of the widget."""
        return (0, 0)

    def do_get_preferred_height(self, *args):
        """Get the preferred height of the widget."""
        self._pangoLayout.set_text("Ctrl + A")
        (_ink, logical) = self._pangoLayout.get_extents()
        height = (logical.y + logical.height) / Pango.SCALE

        height += KeyCombinationEntry.TEXT_MARGIN * 2

        return (height, height)

    def do_draw(self, cr):
        """Draw the widget."""
        styleContext = entryStyle.styleContext

        allocation = self.get_allocation()

        Gtk.render_background(styleContext, cr,
                              0, 0, allocation.width, allocation.height)
        if self.has_focus():
            Gtk.render_focus(styleContext, cr, 0, 0, allocation.width,
                             allocation.height)

        text = SimpleActionEditor.keyCombination2Str(self.keyCombination)

        if text:
            pangoLayout = self._pangoLayout
        else:
            pangoLayout = self._placeHolderPangoLayout
            text = "Enter a key combination or click to cancel" \
                if self._editing else "Click to enter a key combination"

        pangoLayout.set_text(text)
        Gtk.render_layout(styleContext, cr,
                          KeyCombinationEntry.TEXT_MARGIN,
                          KeyCombinationEntry.TEXT_MARGIN,
                          pangoLayout)

    def _buttonReleaseEvent(self, _widget, event):
        """Called when a mouse button is released."""
        if event.button==1:
            if self._editing:
                self._endEdit(True)
            else:
                self._startEdit()

            self.queue_draw()

    def _keyboardEvent(self, _widget, event):
        """Called when a keyboard event occurs."""
        if self._editing:
            press = event.type==Gdk.EventType.KEY_PRESS
            keyCombination = self._keyCombination

            keyMap = Gdk.Keymap.get_for_display(self.get_display())

            (result, keyval, _group, _level, _consumedModifiers) = \
                keyMap.translate_keyboard_state(event.hardware_keycode, 0, 0)
            if not result:
                print("KeyCombinationEntry._keyboardEvent: could not translate  to keyval: hardware_keycode=%d, group=%d, keyval=%d, is_modifier=%d, state=%d" %
                      (event.hardware_keycode, event.group, event.keyval, event.is_modifier, event.state))
                keyval = event.keyval

            code = findCodeForGdkKey(keyval)
            if code is not None:
                name = Key.getNameFor(code)
                if name=="KEY_LEFTSHIFT":
                    keyCombination.leftShift = press
                elif name=="KEY_RIGHTSHIFT":
                    keyCombination.rightShift = press
                elif name=="KEY_LEFTCTRL":
                    keyCombination.leftControl = press
                elif name=="KEY_RIGHTCTRL":
                    keyCombination.rightControl = press
                elif name=="KEY_LEFTALT":
                    keyCombination.leftAlt = press
                elif name=="KEY_RIGHTALT":
                    keyCombination.rightAlt = press
                elif name=="KEY_LEFTMETA":
                    keyCombination.leftSuper = press
                elif name=="KEY_RIGHTMETA":
                    keyCombination.rightSuper = press
                elif press:
                    if keyCombination.code==0:
                        keyCombination.code = code
                        self._endEdit(False)
                else:
                    if keyCombination.code==code:
                        keyCombination.code = 0
            else:
                print("KeyCombinationEntry._keyboardEvent: unhandled key value:", keyval)

            self.queue_draw()
            return True

    def _startEdit(self):
        """Start editing, i.e. reading the key combination."""
        if self._editing:
            return

        window = self.get_window()
        seat = window.get_display().get_default_seat()
        result = seat.grab(window,
                           Gdk.SeatCapabilities.KEYBOARD,
                           False,
                           None,
                           None,
                           None, None)

        if result==Gdk.GrabStatus.SUCCESS:
            print("KeyCombinationEntry._startEdit: grab succeeded")
            self._savedKeyCombination = self._keyCombination.clone()
            self._keyCombination.reset()

            self._dialog.disableHeader()

            self._editing = True
            self._autoEdit = False
            self.emit("editing-started")
        else:
            print("KeyCombinationEntry._startEdit: failed to grab keyboard:", result)

    def _endEdit(self, cancelled):
        """Finish editing."""
        if cancelled:
            self._keyCombination = self._savedKeyCombination

        self.get_display().get_default_seat().ungrab()
        self._editing = False
        self._dialog.enableHeader()

        self.emit("editing-done", cancelled, self._keyCombination)

    def _focusIn(self, *args):
        """Called when the widget gains focus.

        Editing is started if the widget is auto-edit."""
        if self._autoEdit:
            self._startEdit()

#-------------------------------------------------------------------------------

GObject.signal_new("editing-started", KeyCombinationEntry,
                   GObject.SignalFlags.RUN_FIRST, None, ())

GObject.signal_new("editing-done", KeyCombinationEntry,
                   GObject.SignalFlags.RUN_FIRST, None, (bool, object))

#-------------------------------------------------------------------------------

class KeyCombinationDialog(Gtk.Dialog):
    """A dialog to enter a key combination."""
    _instructions0 = _("Click in the field below to enter a new key combination.")

    def __init__(self, title):
        """Construct the dialog."""
        super().__init__(use_header_bar = True)
        self.set_title(title)

        self._cancelButton = self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self._addButton = button = self.add_button(Gtk.STOCK_ADD, Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        button.set_sensitive(False)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        self._label = label = Gtk.Label.new(KeyCombinationDialog._instructions0)
        label.set_line_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        contentArea.pack_start(label, False, False, 4)

        self._entry = entry = KeyCombinationEntry(self, autoEdit = True)
        entry.connect("editing-started", self._entryEditingStarted)
        entry.connect("editing-done", self._entryEditingDone)
        entry.set_valign(Gtk.Align.CENTER)
        contentArea.pack_start(entry, True, False, 4)

        self.show_all()

    @property
    def keyCombination(self):
        """Get the key combination."""
        return self._entry.keyCombination

    def disableHeader(self):
        """Disable the header to facilitate the entering of a key
        combination."""
        self._cancelButton.set_visible(False)
        self._addButton.set_visible(False)
        self.set_default_response(Gtk.ResponseType.NONE)

    def enableHeader(self):
        """Enable the header to facilitate the entering of a key
        combination."""
        self._cancelButton.set_visible(True)
        self._addButton.set_visible(True)
        self.set_default_response(Gtk.ResponseType.OK)

    def _entryEditingStarted(self, entry):
        """Called when the editing has started."""
        self._label.set_text(_("Press the key combination to be added. Click in the entry field below to cancel."))

    def _entryEditingDone(self, entry, cancelled, keyCombination):
        """Called when the editing is done."""
        if cancelled and keyCombination.code==0:
            self.response(Gtk.ResponseType.CANCEL)
            return

        self._label.set_text(KeyCombinationDialog._instructions0)
        self._addButton.set_sensitive(keyCombination.code!=0)

#-------------------------------------------------------------------------------

class SimpleActionEditor(Gtk.VBox):
    """A widget to edit a simple action."""
    @staticmethod
    def keyCombination2Str(keyCombination):
        """Convert the given key combination into a string."""
        s = ""

        if keyCombination.leftSuper:
            s += "Super + "
        if keyCombination.rightSuper:
            s += "Right Super + "
        if keyCombination.leftControl:
            s += "Left Ctrl + "
        if keyCombination.rightControl:
            s += "Right Ctrl + "
        if keyCombination.leftAlt:
            s += "Left Alt + "
        if keyCombination.rightAlt:
            s += "Right Alt + "
        if keyCombination.leftShift:
            s += "Left Shift + "
        if keyCombination.rightShift:
            s += "Right Shift + "

        if keyCombination.code!=0:
            s += Key.getDisplayNameFor(keyCombination.code)

        return s

    def __init__(self, window, edit = False):
        """Construct the widget for the given action."""
        super().__init__()

        self._window = window

        if edit:
            buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
            buttonBox.set_layout(Gtk.ButtonBoxStyle.END)

            self._addButton = addButton = Gtk.Button.new_from_icon_name("list-add-symbolic",
                                                                    Gtk.IconSize.BUTTON)
            addButton.set_tooltip_text(_("Append a new key combination"))
            addButton.connect("clicked", self._addClicked)
            buttonBox.add(addButton)

            removeButton = self._removeButton = \
                Gtk.Button.new_from_icon_name("list-remove-symbolic",
                                              Gtk.IconSize.BUTTON)
            removeButton.set_sensitive(False)
            removeButton.set_tooltip_text(_("Remove the currently selected key combination"))
            removeButton.connect("clicked", self._removeClicked)
            buttonBox.add(removeButton)

            self.pack_start(buttonBox, False, False, 4)

        self._keyCombinations = keyCombinations = Gtk.ListStore(object, str)

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        self._keyCombinationsView = view = \
            Gtk.TreeView.new_with_model(keyCombinations)
        view.get_selection().connect("changed", self._keyCombinationSelected)

        keyCombinationRenderer = Gtk.CellRendererText.new()
        keyCombinationColumn = Gtk.TreeViewColumn(title =
                                                  _("Key combinations"),
                                                  cell_renderer =
                                                  keyCombinationRenderer,
                                                  text = 1)
        view.append_column(keyCombinationColumn)

        scrolledWindow.add(view)

        self.pack_start(scrolledWindow, True, True, 4)

        repeatBox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)

        self._repeatCheckButton = repeatCheckButton = \
            Gtk.CheckButton.new_with_mnemonic(_("R_epeat the key combinations"))
        repeatCheckButton.set_tooltip_text(
            _("When selected, the key combination(s) will be repeated "
              "as long as the control is in the appropriate state (e.g. "
              "a button is pressed)."))
        repeatCheckButton.connect("clicked", self._repeatToggled)

        repeatBox.pack_start(repeatCheckButton, False, False, 3)

        label = Gtk.Label.new("Interval:")
        repeatBox.pack_start(label, False, False, 3)

        self._repeatIntervalEntry = repeatIntervalEntry = \
            IntegerEntry(zeroPadded = False)
        repeatIntervalEntry.set_tooltip_text(
            _("If the key combinations are to be repeated as long as the "
              "control is active, there should be a delay between the "
              "repetitions and its length is determined by the contents "
              "of this field. The value is in milliseconds"))
        repeatIntervalEntry.connect("value-changed", self._repeatDelayChanged)

        repeatBox.pack_start(repeatIntervalEntry, False, False, 0)

        label = Gtk.Label.new("ms")
        repeatBox.pack_start(label, False, False, 0)

        self.pack_start(repeatBox, False, False, 0)

    @property
    def action(self):
        """Get the action being edited."""
        repeatDelay = None
        if self._repeatCheckButton.get_active():
            repeatDelay = self._repeatIntervalEntry.value

        action = SimpleAction(repeatDelay = repeatDelay)

        keyCombinations = self._keyCombinations
        i = keyCombinations.get_iter_first()
        while i is not None:
            action.appendKeyCombination(keyCombinations.get_value(i, 0))
            i = keyCombinations.iter_next(i)

        return action

    @action.setter
    def action(self, action):
        """Set the contents of the widget from the given action."""
        self._keyCombinations.clear()
        self._repeatCheckButton.set_active(False)
        self._repeatIntervalEntry.set_sensitive(False)
        self._repeatIntervalEntry.value = None

        if action is not None and action.type==Action.TYPE_SIMPLE:
            for keyCombination in action.keyCombinations:
                s = SimpleActionEditor.keyCombination2Str(keyCombination)
                self._keyCombinations.append([keyCombination.clone(), s])
            if action.repeatDelay is not None:
                self._repeatCheckButton.set_active(True)
                self._repeatIntervalEntry.set_sensitive(True)
                self._repeatIntervalEntry.value = action.repeatDelay

    @property
    def valid(self):
        """Determine if the editor contains a valid action.

        It is valid if there is at least one key combination and the repeat is
        either disabled or has a positive delay."""
        repeatInterval = self._repeatIntervalEntry.value
        return self._keyCombinations.iter_n_children(None)>0 and \
            (not self._repeatCheckButton.get_active() or
             (repeatInterval is not None and repeatInterval>0))

    def _keyCombinationSelected(self, selection):
        """Handle the change in the selected key combination."""
        (_model, i) = selection.get_selected()

        self._removeButton.set_sensitive(i is not None)

    def _addClicked(self, button):
        """Called when the 'Add' button is clicked."""
        dialog = KeyCombinationDialog(_("Add key combination"))

        response = dialog.run()
        keyCombination = dialog.keyCombination

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            s = SimpleActionEditor.keyCombination2Str(keyCombination)
            self._keyCombinations.append([keyCombination, s])
            self.emit("modified", self.valid)

    def _removeClicked(self, button):
        """Called when the 'Remove' button is clicked."""
        if yesNoDialog(self._window,
                       _("Are you sure to remove the selected key combination?")):
            (_model, i) = self._keyCombinationsView.get_selection().get_selected()
            self._keyCombinations.remove(i)
            self.emit("modified", self.valid)

    def _repeatToggled(self, button):
        """Called when the 'Repeat' button is toggled."""
        self._repeatIntervalEntry.set_sensitive(self._repeatCheckButton.get_active())
        self.emit("modified", self.valid)

    def _repeatDelayChanged(self, _entry, _value):
        """Called when the repeat delay is changed."""
        self.emit("modified", self.valid)

GObject.signal_new("modified", SimpleActionEditor,
                   GObject.SignalFlags.RUN_FIRST, None, (bool,))

#-------------------------------------------------------------------------------

class ActionWidget(Gtk.Box):
    """The widget to display or edit an action."""
    def __init__(self, window, edit = False, action = None):
        super().__init__()
        self.set_property("orientation", Gtk.Orientation.VERTICAL)

        self.set_margin_start(8)
        self.set_margin_end(8)

        self._typeBox = typeBox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        typeBox.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label.new("Type:")
        typeBox.pack_start(label, False, False, 4)

        self._simpleButton = simpleButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("S_imple"))
        simpleButton.connect("toggled", self._typeChanged)
        typeBox.pack_start(simpleButton, False, False, 4)

        self._advancedButton = advancedButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("_Advanced"))
        advancedButton.join_group(simpleButton)
        advancedButton.connect("toggled", self._typeChanged)
        typeBox.pack_start(advancedButton, False, False, 4)

        self._mouseMoveButton = mouseMoveButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("_Mouse move"))
        mouseMoveButton.join_group(simpleButton)
        mouseMoveButton.connect("toggled", self._typeChanged)
        typeBox.pack_start(mouseMoveButton, False, False, 4)

        self._scriptButton = scriptButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("Sc_ript"))
        scriptButton.join_group(simpleButton)
        scriptButton.connect("toggled", self._typeChanged)
        typeBox.pack_start(scriptButton, False, False, 4)

        self.pack_start(typeBox, False, False, 5)

        self._stack = stack = Gtk.Stack.new()

        self._simpleEditor = simpleEditor = \
            SimpleActionEditor(window, edit = edit)
        simpleEditor.connect("modified", self._modified)
        stack.add_named(simpleEditor, "simple")

        self._advancedEditor = advancedEditor = Gtk.Entry.new()
        stack.add_named(advancedEditor, "advanced")

        self._mouseMoveEditor = mouseMoveEditor = Gtk.Entry.new()
        stack.add_named(mouseMoveEditor, "mouseMove")

        self._scriptEditor = scriptEditor = Gtk.Entry.new()
        stack.add_named(scriptEditor, "script")

        self.pack_start(stack, True, True, 5)

        self.action = action

    @property
    def action(self):
        """Get the action appropriate for the currently selected editor."""
        if self._simpleButton.get_active():
            return self._simpleEditor.action
        elif self._advancedButton.get_active():
            return None
        elif self._mouseMoveButton.get_active():
            return None
        elif self._scriptButton.get_active():
            return None

    @action.setter
    def action(self, action):
        """Setup the display for the given action."""
        isSimple = action is None or action.type in [Action.TYPE_SIMPLE,
                                                     Action.TYPE_NOP]
        self._simpleButton.set_active(isSimple)
        self._advancedButton.set_active(
            action is not None and action.type==Action.TYPE_ADVANCED)
        self._mouseMoveButton.set_active(
            action is not None and action.type==Action.TYPE_MOUSE_MOVE)
        self._scriptButton.set_active(
            action is not None and action.type==Action.TYPE_SCRIPT)
        if isSimple:
            self._simpleEditor.action = action
        elif action.type==Action.TYPE_ADVANCED:
            pass
        elif action.type==Action.TYPE_MOUSE_MOVE:
            pass
        elif action.type==Action.TYPE_SCRIPT:
            pass

    def _typeChanged(self, button):
        """Called when the type selector has changed."""
        if button.get_active():
            if button is self._simpleButton:
                self._stack.set_visible_child(self._simpleEditor)
            elif button is self._advancedButton:
                self._stack.set_visible_child(self._advancedEditor)
            elif button is self._mouseMoveButton:
                self._stack.set_visible_child(self._mouseMoveEditor)
            elif button is self._scriptButton:
                self._stack.set_visible_child(self._scriptEditor)

    def _modified(self, editor, canSave):
        """Called when the action is modified."""
        self.emit("modified", canSave)

GObject.signal_new("modified", ActionWidget,
                   GObject.SignalFlags.RUN_FIRST, None, (bool,))

#-------------------------------------------------------------------------------

class ActionEditor(Gtk.Dialog):
    """An action editor dialog."""
    # Response code: clear the action
    RESPONSE_CLEAR = 1

    def __init__(self, action):
        """Construct the action editor."""
        super().__init__(use_header_bar = True)

        self.set_title(_("Edit action"))

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        button = self._saveButton = self.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        button.set_tooltip_text(_("Save the modifications to the action."))
        button.set_sensitive(False)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

        button = self._clearButton = self.add_button(Gtk.STOCK_CLEAR,
                                                     ActionEditor.RESPONSE_CLEAR)
        button.set_tooltip_text(_("Clear the action."))
        button.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        button.set_visible(False)

        contentArea = self.get_content_area()

        actionWidget = self._actionWidget = ActionWidget(self, edit = True)
        actionWidget.connect("modified", self._modified)
        contentArea.pack_start(actionWidget, True, True, 0)

        self.set_size_request(-1, 400)

        self.show_all()

        self.action = action

    @property
    def action(self):
        """Get the action appropriate for the currently selected editor."""
        return self._actionWidget.action

    @action.setter
    def action(self, action):
        """Setup the window from the given action."""
        self._clearButton.set_visible(
            action is not None and action.type!=Action.TYPE_NOP)
        self._actionWidget.action = action
        self._saveButton.set_sensitive(False)

    def _modified(self, actionWidget, canSave):
        """Called when the action is modified."""
        self._saveButton.set_sensitive(canSave)

#-------------------------------------------------------------------------------

class ActionsWidget(Gtk.DrawingArea):
    """The widget displaying the matrix of actions where the rows are the
    controls and the columns are the various shift state combinations."""

    def __init__(self, profileWidget, shiftStates, controls):
        super().__init__()

        self._profileWidget = profileWidget
        self._shiftStates = shiftStates
        self._controls = controls

        self.connect("size-allocate", self._resized)

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect("motion-notify-event", self._motionEvent)

        self.add_events(Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("leave-notify-event", self._leaveEvent)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("button-release-event", self._buttonReleaseEvent)

        self._styleContext = self.get_style_context()

        self._highlightedShiftStateIndex = None
        self._highlightedControlStateIndex = None

    def profileChanged(self):
        """Called when the profile is changed.

        It is called after the shift state widget, so its pre-calculated
        values are available."""
        self.queue_resize()

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self, *args):
        """Get the preferred width of the widget."""
        width = self._shiftStates.minWidth
        return (width, width)

    def do_get_preferred_height(self, *args):
        """Get the preferred height of the widget."""
        height = self._controls.minHeight
        return (height, height)

    def do_draw(self, cr):
        """Draw the widget."""

        allocation = self.get_allocation()

        Gtk.render_background(self._styleContext, cr,
                              0, 0, allocation.width, allocation.height)

        separatorDrawer.drawHorizontal(cr, 0, 0, allocation.width)
        separatorDrawer.drawVertical(cr, 0, 0, allocation.height)

        rowStretch = self._controls.stretch
        for y in self._controls.getRowSeparatorCoordinates(rowStretch):
            separatorDrawer.drawHorizontal(cr, 0, y, allocation.width)

        columnStretch = self._shiftStates.stretch
        for x in self._shiftStates.getColumnSeparatorCoordinates(columnStretch):
            separatorDrawer.drawVertical(cr, x, 0, allocation.height)

        separatorDrawer.drawHorizontal(cr, 0, allocation.height-1, allocation.width)

        layout = Pango.Layout(self.get_pango_context())
        y = 0
        profile = self._profileWidget.profilesEditorWindow.activeProfile
        for (controlStateIndex, (yEnd, (control, state))) in \
            enumerate(zip(self._controls.getRowSeparatorCoordinates(rowStretch),
                          self._controls.controlStates)):
            x = 0
            for (shiftStateIndex, (xEnd, shiftStateSequence)) in \
                enumerate(zip(self._shiftStates.
                              getColumnSeparatorCoordinates(columnStretch),
                              self._shiftStates.shiftStateSequences)):
                self._drawAction(cr, shiftStateIndex, controlStateIndex,
                                 x + 1, y + 1, xEnd, yEnd,
                                 control, shiftStateSequence, state)
                x = xEnd

            y = yEnd

    def _resized(self, _widget, allocation):
        """Called when the widget is resized."""
        self.queue_draw()

    def _drawAction(self, cr, shiftStateIndex, controlStateIndex,
                    x, y, xEnd, yEnd,
                    control, shiftStateSequence, state):
        """Draw the action of the given control for the given shift index
        into the rectangle given by the coordinates"""
        highlighted = \
            self._highlightedShiftStateIndex==shiftStateIndex and \
            self._highlightedControlStateIndex==controlStateIndex

        styleContext = highlightStyle.styleContext if highlighted else self._styleContext

        cr.save()
        cr.move_to(x, y)
        cr.new_path()
        cr.line_to(xEnd, y)
        cr.line_to(xEnd, yEnd)
        cr.line_to(x, yEnd)
        cr.line_to(x, y)
        cr.clip()

        Gtk.render_background(styleContext, cr,
                              x - 16, y - 16, xEnd + 32 - x, yEnd + 32 - y)

        layout = Pango.Layout(self.get_pango_context())

        action = self._findAction(control, state, shiftStateSequence)

        if action is None:
            layout.set_text("-----")
        else:
            if isinstance(action, Action):
                if action.type==Action.TYPE_NOP:
                    layout.set_text("-----")
                elif action.type==Action.TYPE_SIMPLE:
                    s = ""
                    for keyCombination in action.keyCombinations:
                        if s:
                            s += ", "
                        s += SimpleActionEditor.keyCombination2Str(keyCombination)
                    layout.set_text(s)
                else:
                    layout.set_text("<" + Action.getTypeNameFor(action.type) + ">")
            else:
                layout.set_text("???????")

        (_ink, logical) = layout.get_extents()
        layoutWidth = (logical.x + logical.width) / Pango.SCALE
        layoutHeight = (logical.y + logical.height) / Pango.SCALE

        width = xEnd - x
        height = yEnd - y

        xOffset = (width - layoutWidth)/2
        yOffset = (height - layoutHeight)/2

        Gtk.render_layout(styleContext, cr, x + xOffset, y + yOffset,
                          layout)

        cr.restore()

    def _motionEvent(self, _widget, event):
        """Called for a mouse movement event."""
        shiftStateIndex = self._shiftStates.getShiftStateIndexForX(event.x)
        controlStateIndex = self._controls.getControlStateIndexForY(event.y)
        if shiftStateIndex!=self._highlightedShiftStateIndex or \
           controlStateIndex!=self._highlightedControlStateIndex:
            self._highlightedShiftStateIndex = shiftStateIndex
            self._highlightedControlStateIndex = controlStateIndex
            self.queue_draw()

    def _leaveEvent(self, _widget, _event):
        """Called for an event signalling that the pointer has left the
        widget."""
        self._highlightedShiftStateIndex = -1
        self._highlightedControlStateIndex = -1
        self.queue_draw()

    def _buttonReleaseEvent(self, _widget, event):
        """Called for an event signalling that a mouse button has been
        released."""
        if event.button==1:
            shiftStateIndex = self._shiftStates.getShiftStateIndexForX(event.x)
            controlStateIndex = self._controls.getControlStateIndexForY(event.y)

            (action, control, state, shiftStateSequence) = \
                self._findActionForIndexes(shiftStateIndex, controlStateIndex)

            dialog = ActionEditor(action)
            newAction = None
            while True:
                response = dialog.run()

                if response==ActionEditor.RESPONSE_CLEAR:
                    if yesNoDialog(dialog,
                                   _("Are you sure to clear the action?")):
                        break
                elif response==Gtk.ResponseType.OK:
                    newAction = dialog.action
                    break
                else:
                    break

            dialog.destroy()

            if response==Gtk.ResponseType.OK or \
               response==ActionEditor.RESPONSE_CLEAR:
                profilesEditorWindow = self._profileWidget.profilesEditorWindow
                joystickType  = profilesEditorWindow.joystickType
                if joystickType.setAction(profilesEditorWindow.activeProfile,
                                          control, state,
                                          shiftStateSequence, newAction):
                    self.queue_draw()

    def _findActionForIndexes(self, shiftStateIndex, controlStateIndex):
        """Find the action for the given shift and control state indexes.

        The control, its state (if any) and the shift state sequence are also
        returned a tuple following the action."""
        shiftStateSequence = self._shiftStates.shiftStateSequences[shiftStateIndex]
        (control, state) = self._controls.getControlState(controlStateIndex)

        return (self._findAction(control, state, shiftStateSequence),
                control, state, shiftStateSequence)

    def _findAction(self, control, state, shiftStateSequence):
        """Find the action for the given control, state and shift state
        sequence."""
        profile = self._profileWidget.profilesEditorWindow.activeProfile
        ctrl = Control.fromJoystickControl(control)
        controlProfile = profile.findControlProfile(ctrl)
        if controlProfile is None:
            return None

        handlerTree = controlProfile.handlerTree if state is None else \
            controlProfile.findHandlerTree(state.value)
        if handlerTree is None:
            return None

        for shiftState in shiftStateSequence:
            handlerTree = handlerTree.findChild(shiftState)
            if handlerTree is None:
                return None

        action = None
        if handlerTree.numChildren==1:
            for action in handlerTree.children:
                pass

        return action

#-------------------------------------------------------------------------------

class ButtonsWidget(Gtk.Fixed):
    """The buttons in the upper left corner to manipulate the shift
    states."""
    # The gap between the buttons
    BUTTON_GAP = 8

    # The total (top and bottom) margin of a button
    BUTTON_MARGIN = 6

    def __init__(self, profileWidget):
        super().__init__()
        self._profileWidget = profileWidget

        self.connect("size-allocate", self._resized)

        self._levelButtonRows = []
        self._maxButtonHeight = \
            ShiftStatesWidget.LEVEL_GAP - \
            ButtonsWidget.BUTTON_MARGIN

    @property
    def maxButtonHeight(self):
        """Get the maximal button height."""
        return self._maxButtonHeight

    def profileChanged(self):
        """Called when the profile has changed."""
        profilesEditorWindow = self._profileWidget.profilesEditorWindow
        profile = profilesEditorWindow.activeProfile

        numShiftLevels = profile.numShiftLevels
        if numShiftLevels>len(self._levelButtonRows):
            while len(self._levelButtonRows)<numShiftLevels:
                addButton = Gtk.Button.new_from_icon_name("list-add",
                                                          Gtk.IconSize.BUTTON)
                addButton.connect("clicked", self._addShiftLevel)
                addButton.set_tooltip_text(_("Insert a new shift level after this one."))
                addButton.show()
                self.put(addButton, 0, 0)

                removeButton = Gtk.Button.new_from_icon_name("list-remove",
                                                          Gtk.IconSize.BUTTON)
                removeButton.connect("clicked", self._removeShiftLevel)
                removeButton.set_tooltip_text(_("Remove this shift level."))
                removeButton.show()
                self.put(removeButton, 0, 0)

                editButton = Gtk.Button.new_from_icon_name(Gtk.STOCK_EDIT,
                                                           Gtk.IconSize.BUTTON)
                editButton.connect("clicked", self._editShiftLevel)
                editButton.set_tooltip_text(_("Edit this shift level."))
                editButton.show()
                self.put(editButton, 0, 0)

                self._levelButtonRows.append((addButton, removeButton, editButton))
        elif numShiftLevels<len(self._levelButtonRows):
            diff = len(self._levelButtonRows) - numShiftLevels

            for levelButtonRow in self._levelButtonRows[-diff:]:
                for button in levelButtonRow:
                    self.remove(button)

            del self._levelButtonRows[-diff:]

        shiftStates = self._profileWidget.shiftStates

        self._maxButtonHeight = shiftStates.minLevelHeight + \
            ShiftStatesWidget.LEVEL_GAP - \
            ButtonsWidget.BUTTON_MARGIN

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self, *args):
        """Get the preferred width of the widget."""
        return self._profileWidget.controls.get_preferred_width()

    def do_get_preferred_height(self, *args):
        """Get the preferred height of the widget."""
        (minHeight, preferredHeight) = \
            self._profileWidget.shiftStates.get_preferred_height()

        if self._levelButtonRows:
            for button in self._levelButtonRows[0]:
                (minSize, preferredSize) =  button.get_preferred_size()
                minHeight = max(minHeight, minSize.height)
                preferredHeight = max(preferredHeight, preferredSize.height)

        return (minHeight, preferredHeight)

    def _resized(self, _widget, allocation):
        """Called when the widget is resized.

        The buttons will be moved accordingly."""
        shiftStates = self._profileWidget.shiftStates

        y = allocation.y
        for (levelButtonRow, level) in zip(self._levelButtonRows,
                                           shiftStates.levels):

            levelHeight = level.height + ShiftStatesWidget.LEVEL_GAP

            x = allocation.width + allocation.x - ButtonsWidget.BUTTON_GAP
            for button in levelButtonRow:
                (minSize, preferredSize) = button.get_preferred_size()

                x -= preferredSize.width
                height = min(self._maxButtonHeight, preferredSize.height)

                r = Gdk.Rectangle()
                r.x = x
                r.y = y + (levelHeight - height) / 2
                r.width = preferredSize.width
                r.height = height
                button.size_allocate(r)
                self.move(button, r.x, r.y)

                x -= ButtonsWidget.BUTTON_GAP

            y += levelHeight

    def _addShiftLevel(self, button):
        """Called when a shift level is to be added to the profile."""
        for (index, (addButton, _removeButton, _editButton)) in \
            enumerate(self._levelButtonRows):
            if button is addButton:
                self._profileWidget.insertShiftLevel(index+1)

    def _editShiftLevel(self, button):
        """Called when a shift level of the profile is to be edited."""
        for (index, (_addButton, _removeButton, editButton)) in \
            enumerate(self._levelButtonRows):
            if button is editButton:
                self._profileWidget.editShiftLevel(index)

    def _removeShiftLevel(self, button):
        """Called when a shift level is to be removed from the profile."""
        for (index, (_addButton, removeButton, _editButton)) in \
            enumerate(self._levelButtonRows):
            if button is removeButton:
                self._profileWidget.removeShiftLevel(index)

#-------------------------------------------------------------------------------

class TopWidget(Gtk.Fixed):
    """The widget at the top of the profile widget."""
    def __init__(self, profileWidget):
        super().__init__()
        self._profileWidget = profileWidget

        self.connect("size-allocate", self._resized)

        self._addButton = addButton = \
            Gtk.Button.new_from_icon_name("list-add",
                                          Gtk.IconSize.BUTTON)
        addButton.connect("clicked", self._addShiftLevel)
        addButton.set_tooltip_text(_("Add a new top shift level."))
        addButton.show()
        self.put(addButton, 0, 0)

        self._minButtonHeight = self._addButton.get_preferred_size()[0].height

    @property
    def minButtonHeight(self):
        """Get the minimal height for a button."""
        return self._minButtonHeight

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self, *args):
        """Get the preferred width of the widget."""
        allocation = self._profileWidget.get_allocation()
        return (allocation.width, allocation.width)

    def do_get_preferred_height(self, *args):
        """Get the preferred height of the widget."""
        (minSize, preferredSize) = self._addButton.get_preferred_size()
        return(minSize.height + 1 +  ButtonsWidget.BUTTON_GAP/2,
               preferredSize.height + 1 +  ShiftStatesWidget.LEVEL_GAP/2)

    def profileChanged(self):
        """Called when the profile has changed."""
        self.queue_resize()

    def _resized(self, _widget, allocation):
        """Called when we are resized."""
        buttons = self._profileWidget.buttons

        x = buttons.get_allocation().width + allocation.x - ButtonsWidget.BUTTON_GAP
        y = allocation.y

        (buttonMinSize, buttonPreferredSize) = self._addButton.get_preferred_size()
        height = min(allocation.height, buttonPreferredSize.height)

        width = buttonPreferredSize.width

        r = Gdk.Rectangle()
        r.x = x - width
        r.y = y
        r.width = width
        r.height = height
        self._addButton.size_allocate(r)
        self.move(self._addButton, r.x, r.y)

    def _addShiftLevel(self, button):
        """Called when a shift level is to be added to the profile at the top level."""
        self._profileWidget.insertShiftLevel(0)

#-------------------------------------------------------------------------------

class ProfileWidget(Gtk.Grid):
    """The widget containing the scrollable table of the controls and
    their actions."""

    # The minimal column width
    MIN_COLUMN_WIDTH = 50

    def __init__(self, profilesEditorWindow):
        super().__init__()

        self._profilesEditorWindow = profilesEditorWindow

        self._topWidget = topWidget = TopWidget(self)
        self.attach(topWidget, 0, 0, 2, 1)

        self._buttons = buttons = ButtonsWidget(self)
        self.attach(buttons, 0, 1, 1, 1)

        self._shiftStates = shiftStates =  ShiftStatesWidget(self)
        self.attach(shiftStates, 1, 1, 1, 1)

        self._controls = controls = ControlsWidget(self)
        self.attach(controls, 0, 2, 1, 1)

        self._actions = actions = \
            ActionsWidget(self, self._shiftStates, self._controls)

        self._horizontalScrolledWindow = Gtk.ScrolledWindow.new(None, None)
        self._horizontalScrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC,
                                                  Gtk.PolicyType.AUTOMATIC)
        self._horizontalScrolledWindow.add(actions)
        self._horizontalScrolledWindow.set_hexpand(True)
        self._horizontalScrolledWindow.set_vexpand(True)

        self.attach(self._horizontalScrolledWindow, 1, 2, 1, 1)

        shiftStates.set_hadjustment(self._horizontalScrolledWindow.get_hadjustment())
        controls.set_vadjustment(self._horizontalScrolledWindow.get_vadjustment())

        self.set_hexpand(True)
        self.set_vexpand(True)

    @property
    def profilesEditorWindow(self):
        """Get the profiles editor window this widget belongs to."""
        return self._profilesEditorWindow

    @property
    def topWidget(self):
        """Get the widget at the top of the profile editor."""
        return self._topWidget

    @property
    def shiftStates(self):
        """Get the widget containing the shift states."""
        return self._shiftStates

    @property
    def controls(self):
        """Get the controls widget."""
        return self._controls

    @property
    def buttons(self):
        """Get the widget with the buttons."""
        return self._buttons

    def profileChanged(self):
        """Called when the selected profile has changed."""
        self._shiftStates.profileChanged()
        self._controls.profileChanged()
        self._actions.profileChanged()
        self._buttons.profileChanged()
        self._topWidget.profileChanged()
        self.queue_resize()

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self, *args):
        """Get the minimal and preferred widths of the widget."""
        (controlsMinWidth, controlsPreferredWidth) = \
            self._controls.get_preferred_width()
        return (controlsMinWidth + min(self._shiftStates.minWidth,
                                       self._shiftStates.minColumnWidth),
                controlsPreferredWidth + self._shiftStates.minWidth)

    def do_get_preferred_height(self, *args):
        (topMinSize, topPreferreSize) = \
            self._topWidget.get_preferred_size()
        controlsMinHeight = self._controls.minControlHeight
        controlsPreferredHeight = self._controls.minHeight
        (shiftStatesMinHeight, shiftStatesPreferredHeight) = \
            self._shiftStates.get_preferred_height()
        return (controlsMinHeight + shiftStatesMinHeight + topMinSize.height,
                controlsPreferredHeight + shiftStatesPreferredHeight +
                topPreferreSize.height)

    def insertShiftLevel(self, beforeIndex):
        """Insert a shift level into the current profile before the one with
        the given index."""
        self._profilesEditorWindow.insertShiftLevel(beforeIndex)

    def editShiftLevel(self, index):
        """Edit the shift level of the current profile with the given index."""
        self._profilesEditorWindow.editShiftLevel(index)

    def removeShiftLevel(self, index):
        """Remove the shift level with the given index from the current profile."""
        self._profilesEditorWindow.removeShiftLevel(index)


#-------------------------------------------------------------------------------

class ShiftLevelEditor(Gtk.Dialog):
    """A dialog displayed when a shift level is added or edited."""
    # Response code: delete the shift level
    RESPONSE_DELETE = 1

    def __init__(self, title, joystickType, shiftLevel, profile, edit = False):
        """Construct the dialog."""
        super().__init__(use_header_bar = True)

        self.set_title(title)

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        button = self.add_button(Gtk.STOCK_SAVE if edit else Gtk.STOCK_ADD,
                                 Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

        if edit:
            button = self.add_button(Gtk.STOCK_DELETE, ShiftLevelEditor.RESPONSE_DELETE)
            button.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        vcEditor = VirtualControlEditor(joystickType, self,
                                        forShiftLevel =  True,
                                        profile = profile)

        contentArea.pack_start(vcEditor, True, True, 5)

        vcEditor.setVirtualControl(shiftLevel)

        self.set_size_request(-1, 400)

        self.show_all()

#-------------------------------------------------------------------------------

class RemoveShiftLevelDialog(Gtk.Dialog):
    """A dialog to confirm that a shift level should be removed and the actions
    for which state of it should be kept."""
    def __init__(self, joystickType, profile, index):
        """Construct the dialog."""
        super().__init__(use_header_bar = True)
        self.set_title(_("Remove shift level"))

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self._removeButton = button = self.add_button(Gtk.STOCK_REMOVE, Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        label = Gtk.Label.new(_("If you are sure to remove the shift level,\nselect the state below for which the actions should be kept:"))
        label.set_justify(Gtk.Justification.CENTER)
        contentArea.pack_start(label, False, False, 4)

        self._virtualStates = virtualStates = Gtk.ListStore(int, str)

        shiftLevel = profile.getShiftLevel(index)
        for (index, state) in enumerate(shiftLevel.states):
            virtualStates.append([index,
                                  VirtualControlEditor.
                                  getStateConstraintText(joystickType, profile, state)])

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        self._virtualStatesView = view = Gtk.TreeView.new_with_model(virtualStates)

        constraintRenderer = Gtk.CellRendererText.new()
        constraintRenderer.props.editable = False
        constraintColumn = Gtk.TreeViewColumn(title = _("State constraints"),
                                              cell_renderer =
                                              constraintRenderer,
                                              text = 1)
        view.append_column(constraintColumn)

        scrolledWindow.add(view)
        contentArea.pack_start(scrolledWindow, True, True, 10)

        self.set_size_request(-1, 400)

        self.show_all()

    @property
    def keepStateIndex(self):
        """Get the index of the selected state to keep."""
        (_model, i) = self._virtualStatesView.get_selection().get_selected()
        return self._virtualStates.get_value(i, 0)

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

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        alignment = Gtk.Entry()
        alignment.set_valign(Gtk.Align.FILL)
        paned.pack1(alignment, True, True)

        self._profileWidget = profileWidget = ProfileWidget(self)
        #profileWidget.set_vexpand(True)
        #profileWidget.set_hexpand(True)

        # hadjustment = scrolledWindow.get_hadjustment()
        # print("hadjustment", hadjustment.get_lower(),
        #       hadjustment.get_page_increment(),
        #       hadjustment.get_page_size(),
        #       hadjustment.get_step_increment(),
        #       hadjustment.get_minimum_increment(),
        #       hadjustment.get_upper())
        # profileWidget.set_hadjustment(hadjustment)

        # vadjustment = scrolledWindow.get_vadjustment()
        # profileWidget.set_vadjustment(vadjustment)

        # alignment = Gtk.Entry()
        # alignment.set_valign(Gtk.Align.FILL)
        profileWidget.set_margin_start(8)
        profileWidget.set_margin_end(8)
        profileWidget.set_margin_top(8)
        profileWidget.set_margin_bottom(8)
        paned.pack2(profileWidget, True, False)

        vbox.pack_start(paned, True, True, 0)

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

    def insertShiftLevel(self, beforeIndex):
        """Insert a shift level into the current profile before the one with
        the given index."""
        dialog = NewVirtualControlDialog(self._joystickType, 0,
                                         _("Add shift level"), forShiftLevel =
                                         True)
        response = dialog.run()
        (baseControlType, baseControlCode) = dialog.baseControl

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            shiftLevel = ShiftLevel()
            shiftLevel.addStatesFromControl(baseControlType, baseControlCode,
                                            lambda: VirtualState(),
                                            self._joystickType,
                                            self.activeProfile)

            dialog = ShiftLevelEditor(_("Add shift level"), self._joystickType,
                                      shiftLevel, self.activeProfile)
            response = dialog.run()

            dialog.destroy()

            if response==Gtk.ResponseType.OK:
                if self._joystickType.insertShiftLevel(self.activeProfile,
                                                       beforeIndex, shiftLevel):
                    self._profileSelectionChanged(None)

    def editShiftLevel(self, index):
        """Edit the shift level with the given index of the current
        profile."""
        shiftLevel = self.activeProfile.getShiftLevel(index)
        modifiedShiftLevel = shiftLevel.clone()

        dialog = ShiftLevelEditor(_("Edit shift level"), self._joystickType,
                                  modifiedShiftLevel, self.activeProfile, edit = True)

        response = None
        while True:
            response = dialog.run()

            if response==ShiftLevelEditor.RESPONSE_DELETE:
                if self.removeShiftLevel(index):
                    break
            else:
                break

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            (hasDifference, removedStates, addedStates, existingStates) = \
                modifiedShiftLevel.getDifferenceFrom(shiftLevel)
            if hasDifference:
                if self._joystickType.modifyShiftLevel(self.activeProfile,
                                                       index, modifiedShiftLevel,
                                                       removedStates,
                                                       addedStates,
                                                       existingStates):
                    self._profileSelectionChanged(None)

    def removeShiftLevel(self, index):
        """Remove the shift level with the given index from the current
        profile."""
        dialog = RemoveShiftLevelDialog(self._joystickType,
                                        self.activeProfile,
                                        index)

        response = dialog.run()
        keepStateIndex = dialog.keepStateIndex

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            if self._joystickType.removeShiftLevel(self.activeProfile,
                                                   index, keepStateIndex):
                self._profileSelectionChanged(None)
                return True

        return False

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
            self._identityWidget.setFrom(profile.identity, profile.autoLoad)
        self._profileWidget.profileChanged()
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

    def versionChanged(self, entry, value):
        """Called when the version of the profile being edited has changed."""
        if not self._changingProfile:
            profile = self.activeProfile
            if profile is not None:
                profile.identity.inputID.version = value
                self._joystickType.updateProfileIdentity(profile)

    def physChanged(self, entry, value):
        """Called when the physical location of the profile being edited has changed."""
        if not self._changingProfile:
            profile = self.activeProfile
            if profile is not None:
                profile.identity.phys = value
                self._joystickType.updateProfileIdentity(profile)

    def uniqChanged(self, entry, value):
        """Called when the unique identifier of the profile being edited has changed."""
        if not self._changingProfile:
            profile = self.activeProfile
            if profile is not None:
                profile.identity.uniq = value
                self._joystickType.updateProfileIdentity(profile)

    def autoLoadClicked(self, button):
        """Called when the auto-load button is clicked."""
        if not self._changingProfile:
            profile = self.activeProfile
            if profile is not None:
                autoLoad = button.get_active()
                if autoLoad!=profile.autoLoad:
                    profile.autoLoad = autoLoad
                    self._joystickType.updateProfileIdentity(profile)
