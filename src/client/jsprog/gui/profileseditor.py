# Joystick profiles editor window

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from .vceditor import VirtualControlEditor, NewVirtualControlDialog
from .vceditor import VirtualControlSetEditor
from .jsview import JSViewer

from jsprog.profile import Profile, ShiftLevel
from jsprog.parser import SingleValueConstraint, Control, VirtualState
from jsprog.device import DisplayVirtualState
from jsprog.action import Action, NOPAction, SimpleAction, ValueRangeAction
from jsprog.action import MouseMoveCommand, MouseMove, AdvancedAction
from jsprog.action import KeyPressCommand, KeyReleaseCommand, DelayCommand
from jsprog.action import ScriptAction
from .joystick import ProfileList, findCodeForGdkKey
from jsprog.joystick import Key, Axis

import traceback
import math
import sys

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
            IdentityWidget.Entry(_("Ve_rsion:"),
                                 lambda : IntegerEntry(maxWidth=4, base = 16),
                                 _("When matching the profile for automatic loading, this value, if not empty, will be used as an extra condition. The value should be hexadecimal."),
                                 profilesEditorWindow.versionChanged)
        self.pack_start(versionEntry, False, False, 0)

        separator = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.pack_start(separator, False, False, 8)

        physEntry = self._physEntry = \
            IdentityWidget.Entry(_("Ph_ysical location:"),
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
            Gtk.CheckButton.new_with_label(_("Auto-_load profile"))
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

            self.updateStateLabels(joystickType, profile, shiftLevel, pangoLayout)

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

        def updateStateLabels(self, joystickType, profile, shiftLevel, pangoLayout):
            """Update the state labels."""
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
                nextX = x + columnWidth + ShiftStatesWidget.COLUMN_GAP
                if isInClip(cr, x, topY, nextX-1, bottomY):
                    y = y0
                    for row in stateLabels:
                        yEnd = y + self.rowHeight

                        cr.save()
                        cr.move_to(x, y)
                        cr.new_path()
                        cr.line_to(x + columnWidth, y)
                        cr.line_to(x + columnWidth, yEnd)
                        cr.line_to(x, yEnd)
                        cr.line_to(x, y)
                        cr.clip()

                        pangoLayout.set_text(row)
                        (_ink, logical) = pangoLayout.get_extents()
                        width = (logical.x + logical.width) / Pango.SCALE

                        (x1, y1, x2, y2) = cr.clip_extents()
                        clipWidth = x2 + 1 - x1
                        if width<=clipWidth:
                            renderX = x1 + (clipWidth - width) / 2
                        else:
                            renderX = x2 - width

                        Gtk.render_layout(styleContext, cr,
                                          renderX, y, pangoLayout)

                        cr.restore()
                        y = yEnd + self.ROW_GAP
                    if stateLabels is not self.labels[-1]:
                        lineX = round(x + columnWidth +
                                      (ShiftStatesWidget.COLUMN_GAP-1)/2)
                        separatorDrawer.drawVertical(cr, lineX, topY, bottomY - topY)

                x = nextX

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
            return "%d..%d" % (constraint.fromValue, constraint.toValue)

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
        return 1.0 if self.minWidth==0 else max(1.0, allocation.width / self.minWidth)

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

            self._finalizeLevels(profile)
        else:
            self.shiftStateSequences = [[]]
            self.minWidth = ProfileWidget.MIN_COLUMN_WIDTH

        self._recalculateColumnSeparatorCoordinates(self.stretch)

        self.queue_resize()

    def updateStateLabels(self):
        """Update the state labels."""
        profilesEditorWindow = self._profileWidget.profilesEditorWindow
        profile = profilesEditorWindow.activeProfile

        if profile is not None:
            self.minHeight = 0
            joystickType = profilesEditorWindow.joystickType
            for i in range(0, profile.numShiftLevels):
                shiftLevel = profile.getShiftLevel(i)
                self._levels[i].updateStateLabels(joystickType, profile,
                                                  shiftLevel, self._layout)

            self._finalizeLevels(profile)

            self._currentStretch = 0.0
            self._recalculateColumnSeparatorCoordinates(self.stretch)

        self.queue_resize()

    def getShiftStateIndexForX(self, x):
        """Get the shift state index for the given X-coordinate."""
        columnSeparatorCoordinates = \
            self.getColumnSeparatorCoordinates(self.stretch)
        previousCoordinate = 0
        for (index, coordinate) in enumerate(columnSeparatorCoordinates):
            if x>previousCoordinate and x<coordinate:
                return (index, x - previousCoordinate, coordinate - previousCoordinate)
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

    def _finalizeLevels(self, profile):
        """Finalize the shift levels."""
        previousLevel = None
        for level in reversed(self._levels):
            if previousLevel is not None:
                level.columnWidth = max(level.columnWidth, previousLevel.width)
            previousLevel = level

        self.minHeight = 0

        previousLevel = None
        for level in self._levels:
            self.minHeight += level.height
            if previousLevel is not None:
                if previousLevel.columnWidth > level.width:
                    level.width = previousLevel.columnWidth
            previousLevel = level


        self.minWidth = self._levels[0].width + self.COLUMN_GAP - 1
        self.minHeight += profile.numShiftLevels * self.LEVEL_GAP

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
        self._highlightedControls = {}

        self._recalculateSizes()

        self.set_vexpand(True)

        self.connect("size-allocate", self._resized)

        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self.connect("scroll-event", self._scrollEvent)

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

        return (int(y / rowHeight), y % rowHeight, rowHeight)

    def profileChanged(self):
        """Called when the profile has changed."""
        profilesEditorWindow = self._profileWidget.profilesEditorWindow
        profile = profilesEditorWindow.activeProfile
        if profile is None:
            return

        vcNames = set()
        self._profileControlStates = []
        for vc in profile.allVirtualControls:
            vcNames.add(vc.name)
            for state in vc.states:
                self._profileControlStates.append((vc, state))

        self.updateControlNames()

    def updateControlNames(self):
        """Update the control names."""
        self._recalculateSizes()

        self._currentStretch = 0.0
        self._recalculateRowSeparatorCoordinates(self.stretch)

        self.queue_resize()

    def getRowSeparatorCoordinates(self, stretch):
        """Get an iterator over the row separator coordinates for the given
        stretch."""
        self._recalculateRowSeparatorCoordinates(stretch)
        return iter(self._rowSeparatorCoordinates)

    def keyPressed(self, code):
        """Called when the key with the given code has been pressed."""
        self._showControl(Control(Control.TYPE_KEY, code))

    def axisChanged(self, code, value):
        """Called when the value of the axis with the given code has changed."""
        self._showControl(Control(Control.TYPE_AXIS, code))

    def setKeyHighlight(self, code, value):
        """Set the highlighing of the key with the given code."""
        control = Control(Control.TYPE_KEY, code)
        if value>0:
            self._highlightedControls[control] = value
        else:
            if control in self._highlightedControls:
                del self._highlightedControls[control]

        self.queue_draw()

    def setAxisHighlight(self, code, value):
        """Stop highlighting the axis with the given code."""
        control = Control(Control.TYPE_AXIS, code)
        if value>0:
            self._highlightedControls[control] = value
        else:
            if control in self._highlightedControls:
                del self._highlightedControls[control]

        self.queue_draw()

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

        profilesEditorWindow = self._profileWidget.profilesEditorWindow
        joystickType = profilesEditorWindow.joystickType
        profile = profilesEditorWindow.activeProfile

        pangoLayout = self._layout
        previousControl = None
        for (control, state) in self.controlStates:
            if isInClip(cr, 0, y, allocation.width-1, y + rowHeight):
                yOffset = None
                c = Control.fromJoystickControl(control)
                if c in self._highlightedControls:
                    cr.save()
                    cr.rectangle(0, y, allocation.width, rowHeight)

                    highlight = self._highlightedControls[c]
                    alpha = 0.5 * highlight / 100
                    cr.set_source_rgba(0.0, 0.5, 0.8, alpha)

                    cr.fill()
                    cr.restore()

                if control is not previousControl:
                    displayName = joystickType.getControlDisplayName(control,
                                                                     profile = profile)
                    (_width, height) = getTextSizes(pangoLayout, displayName)
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

    def _showControl(self, control):
        """Make sure that the row of the given control is visible."""
        stretch = self.stretch
        adjustmentValue = int(self._vadjustment.get_value())

        minRowHeight = self._minLabelHeight + ControlsWidget.CONTROL_GAP
        rowHeight = minRowHeight * stretch

        fromIndex = -1
        toIndex = -1
        for (index, (jsc, _state)) in enumerate(self.controlStates):
            c = Control.fromJoystickControl(jsc)
            if c==control:
                if fromIndex<0:
                    fromIndex = index
                toIndex = index

        yStart = fromIndex * rowHeight
        yEnd = (toIndex + 1) * rowHeight

        allocation = self.get_allocation()

        y0 = int(self._vadjustment.get_value())
        y1 = y0 + allocation.height

        if yStart<y0:
            self._vadjustment.set_value(yStart)
        elif yEnd>y1:
            self._vadjustment.set_value(max(0, yEnd - allocation.height))

    def _resized(self, _widget, allocation):
        """Called when the widget is resized.

        The row separator coordinates are recalculated."""
        self._recalculateRowSeparatorCoordinates(self.stretch)

    def _recalculateSizes(self):
        """Recalculate the sizes based on the current control set."""
        layout = self._layout

        self._minWidth = 0
        self._minLabelHeight = 0

        profilesEditorWindow = self._profileWidget.profilesEditorWindow
        joystickType = profilesEditorWindow.joystickType
        profile = profilesEditorWindow.activeProfile

        for (control, state) in self.controlStates:
            displayName = joystickType.getControlDisplayName(control,
                                                             profile = profile)
            (width, height) = getTextSizes(layout, displayName)

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

    def _scrollEvent(self, _widget, event):
        """Called when scrolling occurs."""
        if self._vadjustment is not None:
            vadjustment = self._vadjustment
            value = vadjustment.get_value()
            increment = vadjustment.get_step_increment()
            if event.direction==Gdk.ScrollDirection.DOWN:
                upper = vadjustment.get_upper()
                value = min(value + increment, upper)
                vadjustment.set_value(value)
            elif event.direction==Gdk.ScrollDirection.UP:
                lower = vadjustment.get_lower()
                value = max(value - increment, lower)
                vadjustment.set_value(value)

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

    def __init__(self, dialog, keyCombination = None, autoEdit = False,
                 handleModifiers = True):
        super().__init__()

        self._dialog = dialog

        self._keyCombination = \
            SimpleAction.KeyCombination(0) if keyCombination is None \
            else keyCombination

        self._autoEdit = autoEdit
        self._handleModifiers = handleModifiers

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
                if self._handleModifiers:
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
    _instructions1 = _("Click in the field below to enter a new key.")

    def __init__(self, title, subtitle = None, handleModifiers = True, edit = False):
        """Construct the dialog."""
        super().__init__(use_header_bar = True)
        self.set_title(title)

        if subtitle:
            self.get_header_bar().set_subtitle(subtitle)

        self._handleModifiers = handleModifiers

        self._cancelButton = self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self._addButton = button = \
            self.add_button(Gtk.STOCK_SAVE if edit else Gtk.STOCK_ADD, Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        button.set_sensitive(False)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        instructions = \
            KeyCombinationDialog._instructions0 if handleModifiers else \
            KeyCombinationDialog._instructions1
        self._label = label = Gtk.Label.new(instructions)
        label.set_line_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        contentArea.pack_start(label, False, False, 4)

        self._entry = entry = KeyCombinationEntry(self, autoEdit = True,
                                                  handleModifiers = handleModifiers)
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
        what = _("key combination") if self._handleModifiers else _("key")
        self._label.set_text(_("Press the %s to be added. "
                               "Click in the entry field below to cancel.") % (what,))

    def _entryEditingDone(self, entry, cancelled, keyCombination):
        """Called when the editing is done."""
        if cancelled and keyCombination.code==0:
            self.response(Gtk.ResponseType.CANCEL)
            return

        instructions = \
            KeyCombinationDialog._instructions0 if self._handleModifiers else \
            KeyCombinationDialog._instructions1
        self._label.set_text(instructions)
        self._addButton.set_sensitive(keyCombination.code!=0)

#-------------------------------------------------------------------------------

class RepeatDelayEditor(Gtk.Box):
    """An editor for the repeat delay."""
    def __init__(self, buttonTitle, buttonTooltip, intervalTooltip):
        """Construct the editor."""
        super().__init__(Gtk.Orientation.HORIZONTAL, 4)

        self._repeatCheckButton = repeatCheckButton =\
            Gtk.CheckButton.new_with_mnemonic(buttonTitle)
        repeatCheckButton.set_tooltip_text(buttonTooltip)
        repeatCheckButton.connect("clicked", self._repeatToggled)

        self.pack_start(repeatCheckButton, False, False, 4)

        label = Gtk.Label.new_with_mnemonic(_("Interva_l:"))
        self.pack_start(label, False, False, 4)

        self._repeatIntervalEntry = repeatIntervalEntry = \
            IntegerEntry(zeroPadded = False)
        repeatIntervalEntry.set_tooltip_text(intervalTooltip)
        repeatIntervalEntry.connect("value-changed", self._repeatDelayChanged)
        label.set_mnemonic_widget(repeatIntervalEntry)

        self.pack_start(repeatIntervalEntry, False, False, 0)

        label = Gtk.Label.new(_("ms"))
        self.pack_start(label, False, False, 0)

    @property
    def repeatDelay(self):
        """Get the value of the configured repeat delay."""
        return self._repeatIntervalEntry.value \
            if self._repeatCheckButton.get_active() else None

    @repeatDelay.setter
    def repeatDelay(self, repeatDelay):
        """Set the repeat delay from the given value."""
        valid =  repeatDelay is not None and repeatDelay>0

        self._repeatCheckButton.set_active(valid)
        self._repeatIntervalEntry.set_sensitive(valid)

        self._repeatIntervalEntry.value = repeatDelay

    @property
    def valid(self):
        """Determine if the widget contains a valid value."""
        repeatInterval = self._repeatIntervalEntry.value
        return not self._repeatCheckButton.get_active() or \
            (repeatInterval is not None and repeatInterval>0)

    @property
    def repeatEnabled(self):
        """Indicate if repetition itself has been enabled."""
        return self._repeatCheckButton.get_active()

    def _repeatToggled(self, button):
        """Called when the 'Repeat' button is toggled."""
        self._repeatIntervalEntry.set_sensitive(self._repeatCheckButton.get_active())
        self.emit("modified")

    def _repeatDelayChanged(self, _entry, _value):
        """Called when the repeat delay is changed."""
        self.emit("modified")

GObject.signal_new("modified", RepeatDelayEditor,
                   GObject.SignalFlags.RUN_FIRST, None, [])

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

    def __init__(self, window, edit = False, subtitle = None):
        """Construct the widget for the given action."""
        super().__init__()

        self._window = window
        self._subtitle = subtitle

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

        self._repeatDelayEditor = repeatDelayEditor = \
            RepeatDelayEditor(
                _("R_epeat the key combinations"),
                _("When selected, the key combination(s) will be repeated "
                  "as long as the control is in the appropriate state (e.g. "
                  "a button is pressed)."),
                _("If the key combinations are to be repeated as long as the "
                  "control is active, there should be a delay between the "
                  "repetitions and its length is determined by the contents "
                  "of this field. The value is in milliseconds"))

        repeatDelayEditor.connect("modified", self._repeatDelayModified)

        repeatDelayEditor.set_halign(Gtk.Align.CENTER)
        repeatDelayEditor.set_valign(Gtk.Align.END)

        self.pack_start(repeatDelayEditor, False, False, 4)

    @property
    def action(self):
        """Get the action being edited."""
        keyCombinations = self._keyCombinations
        if keyCombinations.iter_n_children(None)==0:
            return NOPAction()

        action = SimpleAction(repeatDelay = self._repeatDelayEditor.repeatDelay)

        i = keyCombinations.get_iter_first()
        while i is not None:
            action.appendKeyCombination(keyCombinations.get_value(i, 0))
            i = keyCombinations.iter_next(i)

        return action

    @action.setter
    def action(self, action):
        """Set the contents of the widget from the given action."""
        self._keyCombinations.clear()

        if action is not None and action.type==Action.TYPE_SIMPLE:
            for keyCombination in action.keyCombinations:
                s = SimpleActionEditor.keyCombination2Str(keyCombination)
                self._keyCombinations.append([keyCombination.clone(), s])

            self._repeatDelayEditor.repeatDelay = action.repeatDelay
        else:
            self._repeatDelayEditor.repeatDelay = None

    @property
    def valid(self):
        """Determine if the editor contains a valid action.

        It is valid if there is at least one key combination and the repeat is
        either disabled or has a positive delay."""
        return self._keyCombinations.iter_n_children(None)>0 and \
            self._repeatDelayEditor.valid

    def _keyCombinationSelected(self, selection):
        """Handle the change in the selected key combination."""
        (_model, i) = selection.get_selected()

        self._removeButton.set_sensitive(i is not None)

    def _addClicked(self, button):
        """Called when the 'Add' button is clicked."""
        dialog = KeyCombinationDialog(_("Add key combination"),
                                      subtitle = self._subtitle)

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

    def _repeatDelayModified(self, repeatDelayEditor):
        """Called when the repeat delay has been modified"""
        self.emit("modified", self.valid)

GObject.signal_new("modified", SimpleActionEditor,
                   GObject.SignalFlags.RUN_FIRST, None, (bool,))

#-------------------------------------------------------------------------------

class MouseMoveCommandWidget(Gtk.Box):
    """A widget to edit a mouse move command."""
    def __init__(self):
        """Construct the widget."""
        super().__init__()
        self.set_property("orientation", Gtk.Orientation.VERTICAL)

        directionBox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)

        label = Gtk.Label.new(_("Direction:"))
        directionBox.pack_start(label, False, False, 0)

        self._horizontalButton = horizontalButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("_Horizontal"))
        horizontalButton.set_tooltip_text(
            _("If selected, the action will produce a horizontal "
              "mouse pointer movement."))
        horizontalButton.connect("toggled", self._modified)
        directionBox.pack_start(horizontalButton, False, False, 0)

        self._verticalButton = verticalButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("_Vertical"))
        verticalButton.join_group(horizontalButton)
        verticalButton.set_tooltip_text(
            _("If selected, the action will produce a vertical "
              "mouse pointer movement."))
        verticalButton.connect("toggled", self._modified)
        directionBox.pack_start(verticalButton, False, False, 0)

        self._wheelButton = wheelButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("_Wheel"))
        wheelButton.join_group(horizontalButton)
        wheelButton.set_tooltip_text(
            _("If selected, the action will produce a mouse "
              "wheel movement."))
        wheelButton.connect("toggled", self._modified)
        directionBox.pack_start(wheelButton, False, False, 0)

        directionBox.set_halign(Gtk.Align.CENTER)

        self.pack_start(directionBox, False, False, 4)

        grid = Gtk.Grid.new()

        grid.set_column_spacing(8)
        grid.set_row_spacing(2)

        row = 0

        label = Gtk.Label.new_with_mnemonic(_("Ad_justment:"))
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)

        self._adjust = adjust = \
            Gtk.Adjustment.new(0.0, -sys.float_info.max, sys.float_info.max,
                               0.1, 1.0, 10.0)
        adjust.connect("value-changed", self._modified)
        self._adjustButton = adjustButton = Gtk.SpinButton.new(adjust, 2.0, 2)
        adjustButton.set_tooltip_text(
            _("This adjusment value will be subtracted from the "
              "value of the control to produce adjustedValue"))
        label.set_mnemonic_widget(adjustButton)
        grid.attach(adjustButton, 1, row, 1, 1)

        row += 1

        factorTooltipText = \
            _("The distance the mouse pointer is to be moved or the wheel spun "
              "is determined from adjustedValue as follows: "
              "A + B*adjustedValue + C*adjustedValue^2")

        label = Gtk.Label.new_with_mnemonic(_("_A:"))
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)

        self._a = a = \
            Gtk.Adjustment.new(0.0, -sys.float_info.max, sys.float_info.max,
                               0.1, 1.0, 10.0)
        a.connect("value-changed", self._modified)
        self._aButton = aButton = Gtk.SpinButton.new(a, 2.0, 2)
        aButton.set_tooltip_text(factorTooltipText)
        label.set_mnemonic_widget(aButton)
        grid.attach(aButton, 1, row, 1, 1)

        row += 1

        label = Gtk.Label.new_with_mnemonic(_("_B:"))
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)

        self._b = b = \
            Gtk.Adjustment.new(0.0, -sys.float_info.max, sys.float_info.max,
                               0.1, 1.0, 10.0)
        b.connect("value-changed", self._modified)
        self._bButton = bButton = Gtk.SpinButton.new(b, 2.0, 2)
        bButton.set_tooltip_text(factorTooltipText)
        label.set_mnemonic_widget(bButton)
        grid.attach(bButton, 1, row, 1, 1)

        row += 1

        label = Gtk.Label.new_with_mnemonic(_("_C:"))
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)

        self._c = c = \
            Gtk.Adjustment.new(0.0, -sys.float_info.max, sys.float_info.max,
                               0.1, 1.0, 10.0)
        c.connect("value-changed", self._modified)
        self._cButton = cButton = Gtk.SpinButton.new(c, 2.0, 2)
        cButton.set_tooltip_text(factorTooltipText)
        label.set_mnemonic_widget(cButton)
        grid.attach(cButton, 1, row, 1, 1)

        grid.set_halign(Gtk.Align.CENTER)
        grid.set_valign(Gtk.Align.CENTER)

        self.pack_start(grid, True, False, 4)

    @property
    def valid(self):
        """Determine if the editor contains a valid action.

        It is valid if there is at least one key combination and the repeat is
        either disabled or has a positive delay."""
        return (abs(self._a.get_value())>1e-3 or abs(self._b.get_value())>1e-3 or
                abs(self._c.get_value())>1e-3)

    @property
    def command(self):
        """Get the MouseMoveCommand with the values currently set in the widget."""
        if self._horizontalButton.get_active():
            direction = MouseMoveCommand.DIRECTION_HORIZONTAL
        elif self._verticalButton.get_active():
            direction = MouseMoveCommand.DIRECTION_VERTICAL
        else:
            direction = MouseMoveCommand.DIRECTION_WHEEL

        adjust = self._adjust.get_value()
        a = self._a.get_value()
        b = self._b.get_value()
        c = self._c.get_value()

        return MouseMoveCommand(direction, a = a, b = b, c = c,
                                adjust = adjust)

    @command.setter
    def command(self, command):
        """Setup the widget from the command."""
        if command is None:
            self._horizontalButton.set_active(True)
            self._verticalButton.set_active(False)
            self._wheelButton.set_active(False)
            self._adjust.set_value(0.0)
            self._a.set_value(0.0)
            self._b.set_value(0.0)
            self._c.set_value(0.0)
        else:
            direction = command.direction
            self._horizontalButton.set_active(
                direction!=MouseMoveCommand.DIRECTION_VERTICAL and
                direction!=MouseMoveCommand.DIRECTION_WHEEL)
            self._verticalButton.set_active(direction==MouseMoveCommand.DIRECTION_VERTICAL)
            self._wheelButton.set_active(direction==MouseMoveCommand.DIRECTION_WHEEL)

            self._adjust.set_value(command.adjust)
            self._a.set_value(command.a)
            self._b.set_value(command.b)
            self._c.set_value(command.c)

    def _modified(self, *args):
        """Called when something is modified."""
        self.emit("modified", self.valid)

GObject.signal_new("modified", MouseMoveCommandWidget,
                   GObject.SignalFlags.RUN_FIRST, None, (bool,))

#-------------------------------------------------------------------------------

class MouseMoveEditor(MouseMoveCommandWidget):
    """An editor widget for a mouse move action."""
    def __init__(self, window, edit = False):
        """Construct the widget for the given action."""
        super().__init__()

        self._window = window

        self._repeatDelayEditor = repeatDelayEditor = \
            RepeatDelayEditor(
                _("R_epeat the mouse movement"),
                _("When selected, the mouse movement will be repeated "
                  "as long as the control is in the appropriate state (e.g. "
                  "the axis is deflected)."),
                _("If the mouse movement is to be repeated as long as the "
                  "control is active, there should be a delay between the "
                  "repetitions and its length is determined by the contents "
                  "of this field. The value is in milliseconds."))
        repeatDelayEditor.connect("modified", self._modified)

        repeatDelayEditor.set_halign(Gtk.Align.CENTER)
        repeatDelayEditor.set_valign(Gtk.Align.END)
        self.pack_start(repeatDelayEditor, False, False, 4)

        self.action = None

    @property
    def valid(self):
        """Determine if the editor contains a valid action.

        It is valid if there is at least one key combination and the repeat is
        either disabled or has a positive delay."""
        return self._repeatDelayEditor.valid and super().valid

    @property
    def action(self):
        """Get the action being edited."""
        if self._horizontalButton.get_active():
            direction = MouseMoveCommand.DIRECTION_HORIZONTAL
        elif self._verticalButton.get_active():
            direction = MouseMoveCommand.DIRECTION_VERTICAL
        else:
            direction = MouseMoveCommand.DIRECTION_WHEEL

        adjust = self._adjust.get_value()
        a = self._a.get_value()
        b = self._b.get_value()
        c = self._c.get_value()

        return MouseMove(direction, a = a, b = b, c = c, adjust = adjust,
                         repeatDelay = self._repeatDelayEditor.repeatDelay)

    @action.setter
    def action(self, action):
        """Set the contents of the widget from the given action."""
        if action is not None and action.type==Action.TYPE_MOUSE_MOVE:
            self.command = action.command
        else:
            self.command = None

        self._repeatDelayEditor.repeatDelay = \
            None if action is None else action.repeatDelay

#-------------------------------------------------------------------------------

class MouseMoveCommandDialog(Gtk.Dialog):
    """A dialog to edit/add a mouse move command."""
    def __init__(self, title, edit = True, subtitle = None):
        """Construct the dialog."""
        super().__init__(use_header_bar = True)
        self.set_title(title)

        if subtitle:
            self.get_header_bar().set_subtitle(subtitle)

        self.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)

        self._addButton = button = \
            self.add_button(_("_Save") if edit else _("_Add"), Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        button.set_sensitive(False)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        self._commandWidget = commandWidget = MouseMoveCommandWidget()
        commandWidget.connect("modified", self._modified)
        contentArea.pack_start(commandWidget, True, True, 0)

        self.show_all()

    @property
    def command(self):
        """Get the command being edited."""
        return self._commandWidget.command

    @command.setter
    def command(self, command):
        """Get the command being edited."""
        self._commandWidget.command = command

    def _modified(self, *args):
        """Called when the command is modified."""
        self._addButton.set_sensitive(self._commandWidget.valid)

#-------------------------------------------------------------------------------

class DelayCommandDialog(Gtk.Dialog):
    """A dialog to enter a delay value."""
    def __init__(self, title, edit = True, subtitle = None):
        """Construct the dialog."""
        super().__init__(use_header_bar = True)
        self.set_title(title)

        if subtitle:
            self.get_header_bar().set_subtitle(subtitle)

        self.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)

        self._addButton = button = \
            self.add_button(_("_Save") if edit else _("_Add"), Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        button.set_sensitive(True)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        entryBox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)

        label = Gtk.Label.new_with_mnemonic(_("_Delay:"))
        entryBox.pack_start(label, False, False, 4)

        self._length = length = \
            Gtk.Adjustment.new(0, 1, 10000000000000000000000,
                               1, 10, 100)
        self._lengthButton = lengthButton = Gtk.SpinButton.new(length, 2, 0)
        lengthButton.set_alignment(1.0)
        entryBox.pack_start(lengthButton, True, True, 4)

        label = Gtk.Label.new_with_mnemonic(_("ms"))
        entryBox.pack_start(label, False, False, 4)

        contentArea.pack_start(entryBox, False, False, 0)

        self.show_all()

    @property
    def command(self):
        """Get the command for the delay value entered into the widget."""
        return DelayCommand(int(self._length.get_value()))

    @command.setter
    def command(self, command):
        """Get the command for the delay value entered into the widget."""
        if command is None:
            self._length.set_value(10)
        else:
            self._length.set_value(command.length)

#-------------------------------------------------------------------------------

class ActionCommandRenderer(Gtk.CellRenderer):
    """Render an advanced action command."""
    command = GObject.property(type=object, default=None)

    def __init__(self, pangoLayout):
        """Construct the renderer."""
        super().__init__()

        self._pangoLayout = pangoLayout

    def do_render(self, cr, widget, background_area, cell_area, flags):
        """Render the command."""
        styleContext = widget.get_style_context()
        pangoLayout = self._pangoLayout

        command = self.command
        if isinstance(command, KeyPressCommand):
            text = _("Press %s") % (Key.getDisplayNameFor(command.code),)
        elif isinstance(command, KeyReleaseCommand):
            text = _("Release %s") % (Key.getDisplayNameFor(command.code),)
        elif isinstance(command, MouseMoveCommand):
            text = _("Mouse ")
            if command.direction==MouseMoveCommand.DIRECTION_HORIZONTAL:
                text += _("horizontal")
            elif command.direction==MouseMoveCommand.DIRECTION_VERTICAL:
                text += _("vertical")
            elif command.direction==MouseMoveCommand.DIRECTION_WHEEL:
                text += _("wheel")

            parameters = ActionsWidget.getMouseMoveParametersString(command)
            if parameters:
                text += ": " + parameters
        elif isinstance(command, DelayCommand):
            text = _("Delay %d ms") % (command.length,)

        pangoLayout.set_text(text)
        Gtk.render_layout(styleContext, cr, cell_area.x, cell_area.y, pangoLayout)

#-------------------------------------------------------------------------------

class ActionCommandsEditor(Gtk.Box):
    """An editor for a sequence of commands in an advanced action."""
    def __init__(self, window, edit = True, subtitle = None):
        """Construct the widget."""
        super().__init__()
        self.set_property("orientation", Gtk.Orientation.VERTICAL)

        self._window = window
        self._edit = edit
        self._subtitle = subtitle

        if edit:
            buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)

            self._keyPressButton = keyPressButton = \
                Gtk.Button.new_with_mnemonic(_("_Key press"))
            keyPressButton.set_tooltip_text(_("Add a new key press command"))
            keyPressButton.connect("clicked", self._addKeyPress)
            buttonBox.pack_start(keyPressButton, False, False, 0)
            buttonBox.set_child_non_homogeneous(keyPressButton, True)

            self._keyReleaseButton = keyReleaseButton = \
                Gtk.Button.new_with_mnemonic(_("Ke_y release"))
            keyReleaseButton.set_tooltip_text(_("Add a new key release command"))
            keyReleaseButton.connect("clicked", self._addKeyRelease)
            buttonBox.pack_start(keyReleaseButton, False, False, 0)
            buttonBox.set_child_non_homogeneous(keyReleaseButton, True)

            self._mouseMoveButton = mouseMoveButton = \
                Gtk.Button.new_with_mnemonic(_("Mouse m_ove"))
            mouseMoveButton.set_tooltip_text(_("Add a new mouse move command"))
            mouseMoveButton.connect("clicked", self._addMouseMove)
            buttonBox.pack_start(mouseMoveButton, False, False, 0)
            buttonBox.set_child_non_homogeneous(mouseMoveButton, True)

            self._delayButton = delayButton = \
                Gtk.Button.new_with_mnemonic(_("_Delay"))
            delayButton.set_tooltip_text(_("Add a new delay command"))
            delayButton.connect("clicked", self._addDelay)
            buttonBox.pack_start(delayButton, False, False, 0)
            buttonBox.set_child_non_homogeneous(delayButton, True)

            self._editButton = editButton = \
                Gtk.Button.new_from_icon_name("gtk-edit", Gtk.IconSize.BUTTON)
            editButton.set_tooltip_text(_("Edit the selected command"))
            editButton.set_sensitive(False)
            editButton.connect("clicked", self._editCommand)
            buttonBox.pack_start(editButton, False, False, 0)
            buttonBox.set_child_non_homogeneous(editButton, True)

            self._moveUpButton = moveUpButton = \
                Gtk.Button.new_from_icon_name("go-up", Gtk.IconSize.BUTTON)
            moveUpButton.set_tooltip_text(_("Move up the selected command"))
            moveUpButton.set_sensitive(False)
            moveUpButton.connect("clicked", self._moveUp)
            buttonBox.pack_start(moveUpButton, False, False, 0)
            buttonBox.set_child_non_homogeneous(moveUpButton, True)

            self._moveDownButton = moveDownButton = \
                Gtk.Button.new_from_icon_name("go-down", Gtk.IconSize.BUTTON)
            moveDownButton.set_tooltip_text(_("Move down the selected command"))
            moveDownButton.set_sensitive(False)
            moveDownButton.connect("clicked", self._moveDown)
            buttonBox.pack_start(moveDownButton, False, False, 0)
            buttonBox.set_child_non_homogeneous(moveDownButton, True)

            self._removeButton = removeButton = \
                Gtk.Button.new_from_icon_name("list-remove", Gtk.IconSize.BUTTON)
            removeButton.set_tooltip_text(_("Delete the selected command"))
            removeButton.set_sensitive(False)
            removeButton.connect("clicked", self._removeCommand)
            buttonBox.pack_start(removeButton, False, False, 0)
            buttonBox.set_child_non_homogeneous(removeButton, True)

            buttonBox.set_halign(Gtk.Align.END)

            self.pack_start(buttonBox, False, False, 4)

        self._commands = commands = Gtk.ListStore.new([object])

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)

        self._commandsView = commandsView = \
            Gtk.TreeView.new_with_model(commands)
        pangoLayout = Pango.Layout(commandsView.get_pango_context())
        commandRenderer = ActionCommandRenderer(pangoLayout)
        commandColumn = Gtk.TreeViewColumn(title = _("Commands"),
                                           cell_renderer = commandRenderer,
                                           command = 0)
        commandsView.append_column(commandColumn)
        selection = commandsView.get_selection()
        selection.connect("changed", self._commandSelected)
        selection.unselect_all()

        scrolledWindow.add(commandsView)

        self.pack_start(scrolledWindow, True, True, 4)

    @property
    def commands(self):
        """Get the list of commands edited in this widget."""
        commands = []

        cmds = self._commands
        i = cmds.get_iter_first()
        while i is not None:
            commands.append(cmds.get_value(i, 0))
            i = cmds.iter_next(i)

        return commands

    @commands.setter
    def commands(self, commands):
        """Set the list of commands to be edited in this widget."""
        cmds = self._commands

        cmds.clear()
        for command in commands:
            cmds.append([command])

        self._commandsView.get_selection().unselect_all()

    @property
    def empty(self):
        """Determine if the list of commands is empty."""
        return self._commands.iter_n_children(None)==0

    @property
    def _currentCommand(self):
        """Get the currently selected command."""
        i = self._commandsView.get_selection().get_selected()[1]
        return None if i is None else self._commands.get_value(i, 0)

    def _addKeyPress(self, button):
        """Called when the button to add a key press has been clicked."""
        dialog = KeyCombinationDialog(_("Add a key press"),
                                      subtitle = self._subtitle,
                                      handleModifiers = False)
        response = dialog.run()
        keyCombination = dialog.keyCombination

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            self._commands.append([KeyPressCommand(keyCombination.code)])
            self._modified()

    def _addKeyRelease(self, button):
        """Called when the button to add a key release has been clicked."""
        dialog = KeyCombinationDialog(_("Add a key release"),
                                      subtitle = self._subtitle,
                                      handleModifiers = False)
        response = dialog.run()
        keyCombination = dialog.keyCombination

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            self._commands.append([KeyReleaseCommand(keyCombination.code)])
            self._modified()

    def _addMouseMove(self, button):
        """Called when the button to add a mouse move has been clicked."""
        dialog = MouseMoveCommandDialog(_("Add a mouse move"),
                                        edit = False,
                                        subtitle = self._subtitle)
        dialog.command = None

        response = dialog.run()
        command = dialog.command

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            self._commands.append([command])
            self._modified()

    def _addDelay(self, button):
        """Called when the button to add a delay has been clicked."""
        dialog = DelayCommandDialog(_("Add a delay"),
                                    edit = False,
                                    subtitle = self._subtitle)
        dialog.command = None

        response = dialog.run()
        command = dialog.command

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            self._commands.append([command])
            self._modified()

    def _commandSelected(self, selection):
        """Called when the command selection has changed."""
        i = self._commandsView.get_selection().get_selected()[1]
        self._editButton.set_sensitive(i is not None)
        self._removeButton.set_sensitive(i is not None)

        if i is None:
            self._moveUpButton.set_sensitive(False)
            self._moveDownButton.set_sensitive(False)
        else:
            path = self._commands.get_path(i)
            firstPath = self._commands.get_path(self._commands.get_iter_first())
            self._moveUpButton.set_sensitive(path != firstPath)

            numCommands = self._commands.iter_n_children(None)
            lastPath = self._commands.get_path(
                self._commands.iter_nth_child(None, numCommands-1))
            self._moveDownButton.set_sensitive(path != lastPath)

    def _editCommand(self, button):
        """Called when the button to edit the current command is clicked."""
        i = self._commandsView.get_selection().get_selected()[1]
        if i is None:
            return

        command = self._commands.get_value(i, 0)

        if isinstance(command, KeyPressCommand) or \
           isinstance(command, KeyReleaseCommand):
            keyPress = isinstance(command, KeyPressCommand)
            dialog = KeyCombinationDialog(_("Edit the key press") if keyPress
                                          else _("Edit the key release"),
                                          subtitle = self._subtitle,
                                          handleModifiers = False,
                                          edit = True)
            response = dialog.run()
            keyCombination = dialog.keyCombination

            dialog.destroy()

            if response==Gtk.ResponseType.OK:
                self._commands.set_value(i, 0,
                                         (KeyPressCommand if keyPress
                                          else KeyReleaseCommand)(keyCombination.code))
                self._modified()
        elif isinstance(command, MouseMoveCommand):
            dialog = MouseMoveCommandDialog(_("Edit the mouse move"),
                                            edit = True,
                                            subtitle = self._subtitle)
            dialog.command = command

            response = dialog.run()
            command = dialog.command

            dialog.destroy()

            if response==Gtk.ResponseType.OK:
                self._commands.set_value(i, 0, command)
                self._modified()
        elif isinstance(command, DelayCommand):
            dialog = DelayCommandDialog(_("Edit the delay"),
                                        edit = True,
                                        subtitle = self._subtitle)
            dialog.command = command

            response = dialog.run()
            command = dialog.command

            dialog.destroy()

            if response==Gtk.ResponseType.OK:
                self._commands.set_value(i, 0, command)
                self._modified()

    def _moveUp(self, button):
        """Called when the button to move the current command up has been
        pressed."""
        i = self._commandsView.get_selection().get_selected()[1]
        j = self._commands.iter_previous(i)
        self._commands.move_before(i, j)
        self._commandSelected(None)
        self._modified()

    def _moveDown(self, button):
        """Called when the button to move the current command down has been
        pressed."""
        i = self._commandsView.get_selection().get_selected()[1]
        j = self._commands.iter_next(i)
        self._commands.move_after(i, j)
        self._commandSelected(None)
        self._modified()

    def _removeCommand(self, button):
        """Called when the button to remmove the current command has been
        pressed."""
        if yesNoDialog(self._window,
                       _("Are you sure to remove the selected command?")):
            i = self._commandsView.get_selection().get_selected()[1]
            self._commands.remove(i)

    def _modified(self):
        """Emit a modified signal."""
        self.emit("modified")

GObject.signal_new("modified", ActionCommandsEditor,
                   GObject.SignalFlags.RUN_FIRST, None, [])

#-------------------------------------------------------------------------------

class AdvancedActionEditor(Gtk.Box):
    """Editor for an advanced action."""
    def __init__(self, window, edit = True, subtitle = None):
        """Construct the widget."""
        super().__init__()
        self.set_property("orientation", Gtk.Orientation.VERTICAL)

        self._window = window
        self._subtitle = subtitle

        self._notebook = notebook = Gtk.Notebook.new()

        self._enterCommandsEditor = enterCommandsEditor = \
            ActionCommandsEditor(window, edit = edit, subtitle = subtitle)
        enterCommandsEditor.connect("modified", self._modified)
        label = Gtk.Label.new_with_mnemonic(_("Ente_r"))
        notebook.append_page(enterCommandsEditor, label)

        self._repeatCommandsEditor = repeatCommandsEditor = \
            ActionCommandsEditor(window, edit = edit, subtitle = subtitle)
        repeatCommandsEditor.connect("modified", self._modified)
        self._repeatCommandsCheckButton = repeatCommandsCheckButton = \
            Gtk.CheckButton.new_with_mnemonic(_("Re_peat"))
        self._repeatCommandsCheckButton.connect("clicked",
                                                self._repeatCommandsCheckButtonClicked)
        self._handlingRepeatCommandsCheckButton = False
        repeatCommandsCheckButton.set_tooltip_text(
            _("Check to enable a separate set of repeat commands. "
              "If they are enabled, they will be repeated while the "
              "control is active. Otherwise the enter commands will."))
        notebook.append_page(repeatCommandsEditor, repeatCommandsCheckButton)

        self._leaveCommandsEditor = leaveCommandsEditor = \
            ActionCommandsEditor(window, edit = edit, subtitle = subtitle)
        leaveCommandsEditor.connect("modified", self._modified)
        label = Gtk.Label.new_with_mnemonic(_("Le_ave"))
        notebook.append_page(leaveCommandsEditor, label)

        self.pack_start(notebook, True, True, 4)

        self._repeatDelayEditor = repeatDelayEditor = \
            RepeatDelayEditor(
                _("R_epeat the commands"),
                _("When selected, the commands will be repeated "
                  "as long as the control is in the appropriate state (e.g. "
                  "the axis is deflected). If the separate sequence of "
                  "repeat commands is enabled, those commands will be "
                  "repeated. Otherwise the entry commands will."),
                _("If the commands are to be repeated as long as the "
                  "control is active, there should be a delay between the "
                  "repetitions and its length is determined by the contents "
                  "of this field. The value is in milliseconds."))
        repeatDelayEditor.connect("modified", self._repeatDelayModified)

        repeatDelayEditor.set_halign(Gtk.Align.CENTER)
        repeatDelayEditor.set_valign(Gtk.Align.END)
        self.pack_start(repeatDelayEditor, False, False, 4)

        repeatCommandsEditor.hide()

    @property
    def valid(self):
        """Determine if the contents of this editor are valid."""
        if not self._repeatDelayEditor.valid:
            return False

        repeatDelay = self._repeatDelayEditor.repeatDelay
        hasRepeatCommands = repeatDelay is not None and \
            self._repeatCommandsCheckButton.get_active() and \
            not self._repeatCommandsEditor.empty
        return (repeatDelay is None and
                (not self._enterCommandsEditor.empty or
                 not self._leaveCommandsEditor.empty) and
                not hasRepeatCommands) or \
                (repeatDelay is not None and
                 (not self._enterCommandsEditor.empty or hasRepeatCommands)) and \
                (repeatDelay is None or
                 not self._repeatCommandsCheckButton.get_active() or
                 not self._repeatCommandsEditor.empty)

    @property
    def action(self):
        """Get the action being edited in this editor."""
        repeatDelay = self._repeatDelayEditor.repeatDelay
        action = AdvancedAction(repeatDelay = repeatDelay)

        action.setSection(AdvancedAction.SECTION_ENTER)
        for command in self._enterCommandsEditor.commands:
            action.appendCommand(command)

        if repeatDelay is not None and self._repeatCommandsCheckButton.get_active():
            action.setSection(AdvancedAction.SECTION_REPEAT)
            for command in self._repeatCommandsEditor.commands:
                action.appendCommand(command)

        action.setSection(AdvancedAction.SECTION_LEAVE)
        for command in self._leaveCommandsEditor.commands:
            action.appendCommand(command)

        action.clearSection()

        return action

    @action.setter
    def action(self, action):
        """Set the given action for editing."""
        repeatDelay = action.repeatDelay
        self._repeatDelayEditor.repeatDelay = repeatDelay
        if repeatDelay is None:
            self._repeatCommandsEditor.hide()
        else:
            self._repeatCommandsEditor.show()
        self._handlingRepeatCommandsCheckButton = True
        self._repeatCommandsCheckButton.set_active(action.hasRepeatCommands)
        self._handlingRepeatCommandsCheckButton = False

        self._enterCommandsEditor.commands = \
            [command.clone() for command in action.enterCommands]
        self._repeatCommandsEditor.commands = \
            [command.clone() for command in action.repeatCommands]
        self._leaveCommandsEditor.commands = \
            [command.clone() for command in action.leaveCommands]

        self._notebook.set_current_page(0)

    @property
    def numViews(self):
        """Get the number of views."""
        return 3 if self._repeatDelayEditor.repeatEnabled else 2

    def prepare(self):
        """Prepare the editor for showing."""
        repeatDelay = self._repeatDelayEditor.repeatDelay
        if repeatDelay is None:
            self._repeatCommandsEditor.hide()
        else:
            self._repeatCommandsEditor.show()

    def showView(self, index):
        """Show the view with the given index."""
        self._notebook.set_current_page(
            (1 if self._repeatDelayEditor.repeatEnabled else 2)
            if index==1 else index)

    def _repeatDelayModified(self, widget):
        """Called when the repeat delay has been modified."""
        if self._repeatDelayEditor.repeatEnabled:
            self._repeatCommandsEditor.show()
        else:
            self._repeatCommandsEditor.hide()
        self._modified(widget)

    def _repeatCommandsCheckButtonClicked(self, button):
        """Called when the repeat commands check button is clicked."""
        if not self._handlingRepeatCommandsCheckButton:
            self._handlingRepeatCommandsCheckButton = True
            if self._notebook.get_current_page()!=1:
                button.set_active(not button.get_active())
                self._notebook.set_current_page(1)
            self._modified(button)
            self._handlingRepeatCommandsCheckButton = False

    def _modified(self, widget):
        """Called when something has been modified."""
        self.emit("modified", self.valid)

GObject.signal_new("modified", AdvancedActionEditor,
                   GObject.SignalFlags.RUN_FIRST, None, (bool,))

#-------------------------------------------------------------------------------

class ScriptActionEditor(Gtk.Box):
    """Editor for a script action."""
    _luaToolTip = _(
        "JSProg can be compiled with various versions of the Lua "
        "interpreter. (As of this writing versions 5.2, 5.3 and 5.4 "
        "are supported.) It is likely, that your version is compiled "
        "with the latest one available for your distribution, thus "
        "you may use the language features present only in that "
        "particular version. However, if you want to make your "
        "profile generally useful, you may want to refrain from "
        "using those features, so that people with a lower Lua "
        "version may be able to use your profile. "
        "\n\n"
        "No modules are available in the execution environment, but "
        "JSProg provides several global constants and functions "
        "that can be used in Lua script snippets."
        "\n\n"
        "The constants provided are the codes of the controls, i.e. "
        "keys and axes. The names of the constants (as any symbols "
        "provided by JSProg) start with 'jsprog_' and followed by "
        "the identifier of the control as defined in "
        "linux/input-event-codes.h."
        "\n\n"
        "The following global functions are provided:"
        "\n\n"
        "* jsprog_iskeypressed(code): return a boolean indicating if the key "
        "with the given code is pressed."
        "\n\n"
        "* jsprog_getabs(code): get the value of the absolute axis with the "
        "given code."
        "\n\n"
        "* jsprog_getabsmin(code), jsprog_getabsmax(code): get the minimum/"
        "maximum value of the absolute axis with the given code."
        "\n\n"
        "* jsprog_presskey(code), jsprog_releasekey(code): emit an input "
        "event indicating that the key with the given code has been pressed/"
        "released."
        "\n\n"
        "* jsprog_moverel(code, distance): emit an input "
        "event indicating that the relative control with the given code "
        "has been moved by the given distance."
        "\n\n"
        "* jsprog_startthread(function): start a Lua thread (coroutine) executing "
        "the given function and return that thread."
        "\n\n"
        "* jsprog_delay(delay[, cancellable]): delay the execution for the "
        "given amount of time in milliseconds (int). cancellable is a "
        "boolean indicating of the delay may be cancelled by a call to "
        "jsprog_canceldelay()."
        "\n\n"
        "* jsprog_canceldelay(thread): if the given thread is in a "
        "cancellable delay, cancel that delay."
        "\n\n"
        "* jsprog_jointhread(thread): join the given Lua thread and wait for "
        "it exiting.")


    def __init__(self, window, edit = True, subtitle = None):
        """Construct the widget."""
        super().__init__()
        self.set_property("orientation", Gtk.Orientation.VERTICAL)

        self._window = window
        self._subtitle = subtitle

        self._notebook = notebook = Gtk.Notebook.new()

        self._enterCommandsView = enterCommandsView = \
            Gtk.TextView.new()
        self._enterCommands = enterCommands = enterCommandsView.get_buffer()
        enterCommands.connect("changed", self._modified)
        enterCommandsView.set_tooltip_text(ScriptActionEditor._luaToolTip)
        label = Gtk.Label.new_with_mnemonic(_("Ente_r"))
        notebook.append_page(enterCommandsView, label)

        self._leaveCommandsView = leaveCommandsView = \
            Gtk.TextView.new()
        self._leaveCommands = leaveCommands = leaveCommandsView.get_buffer()
        leaveCommands.connect("changed", self._modified)
        leaveCommandsView.set_tooltip_text(ScriptActionEditor._luaToolTip)
        label = Gtk.Label.new_with_mnemonic(_("Le_ave"))
        notebook.append_page(leaveCommandsView, label)

        self.pack_start(notebook, True, True, 4)

        self._settingUp = False

    @property
    def valid(self):
        """Determine if the editor contains valid data."""
        return self._enterCommands.get_char_count()>0 or \
            self._leaveCommands.get_char_count()>0

    @property
    def action(self):
        """Get the action being edited in this editor."""
        action = ScriptAction()

        for (section, textBuffer) in [(ScriptAction.SECTION_ENTER,
                                       self._enterCommands),
                                      (ScriptAction.SECTION_LEAVE,
                                       self._leaveCommands)]:
            (start, end) = textBuffer.get_bounds()
            text = textBuffer.get_text(start, end, True)
            action.setSection(section)
            for line in text.splitlines():
                action.appendLine(line)
        action.clearSection()

        return action

    @action.setter
    def action(self, action):
        """Set the given action for editing."""
        self._settingUp = True
        self._enterCommands.set_text("\n".join(action.enterLines))
        self._leaveCommands.set_text("\n".join(action.leaveLines))

        self._notebook.set_current_page(0)
        self._settingUp = False

    @property
    def numViews(self):
        """Get the number of views."""
        return 2

    def showView(self, index):
        """Show the view with the given index."""
        self._notebook.set_current_page(index)

    def _modified(self, textBuffer):
        """Called when something has been modified."""
        if not self._settingUp:
            self.emit("modified", self.valid)

GObject.signal_new("modified", ScriptActionEditor,
                   GObject.SignalFlags.RUN_FIRST, None, (bool,))

#-------------------------------------------------------------------------------

class ValueRangeWidget(Gtk.EventBox):
    """A widget to edit a value range."""
    # The radius of the slider
    SLIDER_RADIUS = 10

    # The length of mark
    MARK_LENGTH = 4

    # The gap of the value above or below the slider
    VALUE_GAP = 4

    # The gap of the lower and upper limit values next to the slider
    LIMIT_VALUE_GAP = 4

    # The width of the trough
    TROUGH_WIDTH = 4

    # The minimal width for the value part
    MIN_VALUE_WIDTH = 100

    def __init__(self, editable = True):
        """Construct the value range widget."""
        super().__init__()

        self._editable = editable

        styleContext = self.get_style_context()

        self._troughStyleContext = getStyleContextFor("scale.horizontal", "trough")
        self._troughStyleContext.set_parent(styleContext)

        self._highlightStyleContext = getStyleContextFor("scale.horizontal", "highlight")
        self._highlightStyleContext.set_parent(styleContext)

        self._sliderStyleContext =  getStyleContextFor("scale.horizontal", "slider")
        self._sliderStyleContext.set_parent(styleContext)

        self._valueStyleContext = getStyleContextFor("scale.horizontal", "value")
        self._valueStyleContext.set_parent(styleContext)

        self._markStyleContext = getStyleContextFor("scale.horizontal", "mark")
        self._markStyleContext.set_parent(styleContext)

        self._resizedOnce = False
        self._fromSliderPrelit = False
        self._toSliderPrelit = False
        self._dragging = False
        self._draggingToSlider = False
        self._lastDragX = None

        self._pangoLayout = pangoLayout = Pango.Layout(self.get_pango_context())
        pangoLayout.set_text("0123456789")
        (_ink, logical) = pangoLayout.get_extents()
        self._valueHeight = (logical.y + logical.height) / Pango.SCALE

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect("motion-notify-event", self._motionEvent)

        self.add_events(Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("leave-notify-event", self._leaveEvent)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self._buttonPressEvent)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("button-release-event", self._buttonReleaseEvent)

        self.connect("size-allocate", self._resized)

        self.set_can_focus(True)
        self.set_hexpand(True)

    @property
    def _minHeight(self):
        """Get the minimal height of the widget."""
        minHeight = 2*ValueRangeWidget.SLIDER_RADIUS + \
            ValueRangeWidget.VALUE_GAP + self._valueHeight
        if self._editable:
            minHeight += ValueRangeWidget.MARK_LENGTH + self._valueHeight
        return minHeight

    @property
    def fromValue(self):
        """Get the current starting value of the range being editor."""
        return self._fromValue

    @property
    def toValue(self):
        """Get the current ending value of the range being editor."""
        return self._toValue

    def setTotalRange(self, minValue, maxValue):
        """Set the total range."""
        self._minValue = minValue
        self._maxValue = maxValue
        self._totalRangeSize = self._maxValue - self._minValue

        pangoLayout = self._pangoLayout

        pangoLayout.set_text(str(self._minValue))
        (_ink, logical) = pangoLayout.get_extents()
        self._minValueWidth = (logical.x + logical.width) / Pango.SCALE

        pangoLayout.set_text(str(self._maxValue))
        (_ink, logical) = pangoLayout.get_extents()
        self._maxValueWidth = (logical.x + logical.width) / Pango.SCALE

        self._valueWidth = max(self._minValueWidth, self._maxValueWidth)

    def setValueRange(self, fromValue, toValue, valueRanges = []):
        """Set the value range."""
        self._fromValue = fromValue
        self._toValue = toValue

        otherRanges = []

        previousT = -1
        for (f, t) in [(f, t) for (f, t) in valueRanges
                       if f!=fromValue or t!=toValue]:
            if len(otherRanges)==0 or f>(previousT+1):
                otherRanges.append((f, t))
            else:
                otherRanges[-1] = (otherRanges[-1][0], t)
            previousT = t

        self._otherRanges = otherRanges

        self._recalculateValuesData()

    def setParentStyleContext(self, styleContext):
        """Set the parent style context."""
        self.get_style_context().set_parent(styleContext)

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self, *args):
        """Get the preferred width of the widget."""

        valueWidth = self._maxValue - self._minValue
        extraWidth = self._minValueWidth + \
            max(ValueRangeWidget.SLIDER_RADIUS,
                self._valueWidth / 2) + \
            self._maxValueWidth + 2*ValueRangeWidget.LIMIT_VALUE_GAP

        return (max(valueWidth, ValueRangeWidget.MIN_VALUE_WIDTH)  + extraWidth,
                max(valueWidth * (2 if self._editable else 1),
                    ValueRangeWidget.MIN_VALUE_WIDTH) + extraWidth)

    def do_get_preferred_height(self, *args):
        """Get the preferred height of the widget."""

        minHeight = self._minHeight

        return (minHeight, minHeight)

    def do_draw(self, cr):
        """Draw the widget."""
        allocation = self.get_allocation()

        styleContext = self.get_style_context()

        Gtk.render_background(styleContext, cr, 0, 0, allocation.width, allocation.height)

        self._renderTrough(styleContext, cr)

        self._renderHighlight(styleContext, cr)

        self._renderLimitValues(styleContext, cr)

        self._renderSliders(styleContext, cr)

        if self._editable:
            self._renderMarks(styleContext, cr)

    def _renderTrough(self, styleContext, cr):
        """Render the trough."""
        sc = self._troughStyleContext
        sc.set_state(styleContext.get_state())

        Gtk.render_background(sc, cr,
                              self._troughX, self._troughY,
                              self._troughWidth, self._troughHeight)
        Gtk.render_frame(sc, cr,
                         self._troughX, self._troughY,
                         self._troughWidth, self._troughHeight)

        sc.set_state(Gtk.StateFlags.INSENSITIVE)
        for (x, width) in self._otherRangeRenderData:
            Gtk.render_background(sc, cr, x,
                                  self._troughY, width, self._troughHeight)
            Gtk.render_frame(sc, cr, x, self._troughY, width, self._troughHeight)

    def _renderHighlight(self, styleContext, cr):
        """Render the highlighted area."""
        sc = self._highlightStyleContext
        sc.set_state(styleContext.get_state())

        x = self._fromValueX
        width = self._toValueX - x
        Gtk.render_background(sc, cr, x, self._troughY, width, self._troughHeight)
        Gtk.render_frame(sc, cr, x, self._troughY, width, self._troughHeight)

    def _renderLimitValues(self, styleContext, cr):
        """Render the minimum and maximum values."""
        sc = self._valueStyleContext
        sc.set_state(styleContext.get_state())

        pangoLayout = self._pangoLayout
        pangoLayout.set_text(str(self._minValue))

        (_ink, logical) = pangoLayout.get_extents()
        textHeight = (logical.y + logical.height) / Pango.SCALE
        y = self._middleY - textHeight/2

        Gtk.render_layout(sc, cr, 0, y, pangoLayout)

        pangoLayout.set_text(str(self._maxValue))

        x = self._getValueX(self._maxValue) + \
            ValueRangeWidget.SLIDER_RADIUS + ValueRangeWidget.LIMIT_VALUE_GAP

        Gtk.render_layout(sc, cr, x, y, pangoLayout)

    def _renderSliders(self, styleContext, cr):
        """Render the sliders."""
        self._renderSlider(styleContext, cr, not self._draggingToSlider)
        self._renderSlider(styleContext, cr, self._draggingToSlider)

    def _renderSlider(self, styleContext, cr, toSlider):
        """Render one of the sliders."""
        sc = self._sliderStyleContext
        sc.set_state(styleContext.get_state())

        if self._dragging and toSlider==self._draggingToSlider:
            sc.set_state(styleContext.get_state()|Gtk.StateFlags.ACTIVE)
        elif (toSlider and self._toSliderPrelit) or \
             (not toSlider and self._fromSliderPrelit):
            sc.set_state(styleContext.get_state()|Gtk.StateFlags.PRELIGHT)

        valueX = self._toValueX if toSlider else self._fromValueX
        middleY = self._middleY

        r = ValueRangeWidget.SLIDER_RADIUS
        x = valueX - r
        y = middleY - r

        Gtk.render_background(sc, cr, x, y, 2*r, 2*r)
        Gtk.render_slider(sc, cr, x, y, 2*r, 2*r, Gtk.Orientation.HORIZONTAL)

        if not toSlider and self._toValue==self._fromValue:
            return

        sc = self._valueStyleContext
        sc.set_state(styleContext.get_state())

        pangoLayout = self._pangoLayout
        pangoLayout.set_text(str(self._toValue if toSlider else self._fromValue))

        (_ink, logical) = pangoLayout.get_extents()
        textWidth = (logical.x + logical.width) / Pango.SCALE

        x = valueX - textWidth / 2
        if self._toValue!=self._fromValue:
            valueMiddleX = (self._fromValueX + self._toValueX) / 2
            x = max(x, valueMiddleX + 3) if toSlider \
                else min(x, valueMiddleX - 3 - textWidth)
        y = middleY - r - ValueRangeWidget.VALUE_GAP - self._valueHeight

        Gtk.render_layout(sc, cr, x, y, pangoLayout)

    def _renderMarks(self, styleContext, cr):
        """Render the marks."""
        sc = self._markStyleContext
        sc.set_state(styleContext.get_state())

        sc1 = self._valueStyleContext
        pangoLayout = self._pangoLayout

        y0 = self._middleY + self.SLIDER_RADIUS
        y1 = y0 + ValueRangeWidget.MARK_LENGTH
        for (x, value) in self._marks:
            Gtk.render_line(sc, cr, x, y0, x, y1)

            pangoLayout.set_text(str(value))
            (_ink, logical) = pangoLayout.get_extents()
            width = (logical.x + logical.width) / Pango.SCALE

            Gtk.render_layout(sc1, cr, x - width/2, y1, pangoLayout)

    def _resized(self, widget, allocation):
        """Called when the widget has been resized."""
        r = ValueRangeWidget.SLIDER_RADIUS

        verticalMargin = max(0, (allocation.height - self._minHeight)/2)
        self._middleY = middleY = verticalMargin + self._valueHeight + \
            ValueRangeWidget.VALUE_GAP + r

        tw = ValueRangeWidget.TROUGH_WIDTH

        limitValueGap = ValueRangeWidget.LIMIT_VALUE_GAP
        self._startOffset = \
            max(self._minValueWidth + limitValueGap + r, self._valueWidth / 2)
        self._endOffset = \
            max(self._maxValueWidth + limitValueGap + r, self._valueWidth / 2)
        self._troughWidth = allocation.width - self._startOffset - self._endOffset

        self._troughX = self._startOffset
        self._troughY = middleY - tw / 2
        self._troughHeight = tw

        self._otherRangeRenderData = []
        for (f, t) in self._otherRanges:
            x = self._getValueX(f)
            self._otherRangeRenderData.append((x, self._getValueX(t) - x))

        valueXInterval = self._troughWidth / self._totalRangeSize

        candidateMarkInterval = None
        multiplier = 1
        while candidateMarkInterval is None:
            for n in [1, 2, 5]:
                markInterval = n*multiplier
                markXInterval = markInterval * valueXInterval
                if markXInterval>=(self._valueWidth + ValueRangeWidget.VALUE_GAP):
                    candidateMarkInterval = markInterval
                    break
            multiplier *= 10

        self._marks = []
        value = self._minValue + markInterval
        while value<(self._maxValue - markInterval / 2):
            self._marks.append((self._getValueX(value), value))
            value += markInterval

        self._resizedOnce = True

        self._recalculateValuesData()

    def _recalculateValuesData(self):
        """Recalculate the coordinates of the from and to values."""
        if self._resizedOnce:
            self._fromValueX = self._getValueX(self._fromValue)
            self._toValueX = self._getValueX(self._toValue)

    def _getValueX(self, value):
        """Get the X-coordinate of the given value."""
        return self._startOffset + \
            (value - self._minValue) * self._troughWidth / \
            self._totalRangeSize

    def _getXValue(self, x):
        """Get value corresponding to the given X-coordinate."""
        return round(self._minValue + (x - self._startOffset) *
                     self._totalRangeSize / self._troughWidth)

    def _isMouseInSlider(self, valueX, mouseX, mouseY):
        """Determine if the slider centered at the given value X-coordinate
        contains the given mouse coordinates."""
        dx = mouseX - valueX
        dy = mouseY - self._middleY
        return math.sqrt(dx*dx + dy*dy)<=ValueRangeWidget.SLIDER_RADIUS

    def _motionEvent(self, _widget, event):
        """Called for a mouse movement event."""
        if self._dragging:
            self._setupDragging(event.x)
            self.queue_draw()
        else:
            needDraw = False

            prelit = self._isMouseInSlider(self._fromValueX, event.x, event.y)
            if prelit!=self._fromSliderPrelit:
                self._fromSliderPrelit = prelit
                needDraw = True

            prelit = self._isMouseInSlider(self._toValueX, event.x, event.y)
            if prelit!=self._toSliderPrelit:
                self._toSliderPrelit = prelit
                needDraw = True

            if needDraw:
                self.queue_draw()

    def _leaveEvent(self, _widget, _event):
        """Called for an event signalling that the pointer has left the
        widget."""
        if self._fromSliderPrelit or self._toSliderPrelit:
            self._fromSliderPrelit = self._toSliderPrelit = False
            self.queue_draw()

    def _buttonPressEvent(self, _widget, event):
        """Called for an event signalling that a mouse button has been
        pressed."""
        if event.button == Gdk.BUTTON_PRIMARY:
            self._fromSliderPrelit = self._toSliderPrelit = False
            self._setupDragging(event.x)
            self._dragging = True
            self.queue_draw()

    def _buttonReleaseEvent(self, _widget, event):
        """Called for an event signalling that a mouse button has been
        released."""
        if event.button == Gdk.BUTTON_PRIMARY:
            self._dragging = False
            self._lastDragX = None
            self._fromSliderPrelit = self._isMouseInSlider(self._fromValueX, event.x, event.y)
            self._toSliderPrelit = self._isMouseInSlider(self._toValueX, event.x, event.y)
            self.queue_draw()

    def _setupDragging(self, x):
        """Setup the dragging status and the values for the given X-coordinate."""
        value = min(self._maxValue, max(self._minValue, self._getXValue(x)))

        if self._lastDragX is not None:
            nearestMarkValue = None
            nearestMarkX = None
            for (markX, markValue) in self._marks:
                if nearestMarkValue is None:
                    nearestMarkValue = markValue
                    nearestMarkX = markX
                elif abs(markValue-value)<abs(nearestMarkValue-value):
                    nearestMarkValue = markValue
                    nearestMarkX = markX

            if x>self._lastDragX:
                if x>nearestMarkX and (x-nearestMarkX)<5:
                    value = nearestMarkValue
            else:
                if x<nearestMarkX and (nearestMarkX-x)<5:
                    value = nearestMarkValue

        self._lastDragX = x

        previousRange = None
        valueRange = None
        nextRange = None
        for (f, t) in self._otherRanges:
            if t<value:
                previousRange = (f, t)
            elif value>=f and value<=t:
                valueRange = (f, t)
            elif value<f and nextRange is None:
                nextRange = (f, t)

        if self._dragging:
            if self._draggingToSlider:
                fromValueX = self._getValueX(self._fromValue)
                if x>=(fromValueX - 10):
                    value = max(self._fromValue, value)
                else:
                    self._draggingToSlider = False
            else:
                toValueX = self._getValueX(self._toValue)
                if x<=(toValueX + 10):
                    value = min(value, self._toValue)
                else:
                    self._draggingToSlider = True

        if value>self._toValue:
            if valueRange is None:
                self._toValue = min(value, self._maxValue)
                if previousRange is not None and self._fromValue<previousRange[1]:
                    self._fromValue = previousRange[1] + 1
            else:
                self._toValue = min(value, valueRange[0] - 1)
            self._draggingToSlider = True
        elif value<self._fromValue:
            if valueRange is None:
                self._fromValue = max(value, self._minValue)
                if nextRange is not None and self._toValue>nextRange[0]:
                    self._toValue = nextRange[0] - 1
            else:
                self._fromValue = max(value, valueRange[1] + 1)
            self._draggingToSlider = False
        elif self._dragging:
            if self._draggingToSlider:
                self._toValue = value
            else:
                self._fromValue = value
        else:
            fromDiff = value - self._fromValue
            toDiff = self._toValue - value

            if fromDiff<=toDiff:
                self._fromValue = value
                self._draggingToSlider = False
            else:
                self._toValue = value
                self._draggingToSlider = True

        self._recalculateValuesData()

#-------------------------------------------------------------------------------

class ValueRangeEditor(Gtk.Dialog):
    """A dialog to edit a value range."""
    def __init__(self, title, axis, fromValue, toValue, valueRanges,
                 subtitle = None):
        super().__init__(use_header_bar = True)
        self.set_title(title)

        if subtitle:
            self.get_header_bar().set_subtitle(subtitle)

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self._saveButton = saveButton = self.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        saveButton.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        self._valueRangeWidget = valueRangeWidget = ValueRangeWidget()
        valueRangeWidget.setTotalRange(axis.minimum, axis.maximum)
        valueRangeWidget.setValueRange(fromValue, toValue, valueRanges)

        contentArea.pack_start(valueRangeWidget, True, True, 8)

        #scale = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, None)
        #scale.set_range(0, 255)
        #scale.set_value(100)
        #scale.add_mark(10, Gtk.PositionType.BOTTOM, "10")

        #contentArea.pack_start(scale, False, False, 0)

        self.show_all()

    @property
    def fromValue(self):
        """Get the current starting value of the range."""
        return self._valueRangeWidget.fromValue

    @property
    def toValue(self):
        """Get the current ending value of the range."""
        return self._valueRangeWidget.toValue

#-------------------------------------------------------------------------------

class CellRendererValueRange(Gtk.CellRenderer):
    """A cell renderer for a value range."""
    fromValue = GObject.property(type=int, default=None)
    toValue = GObject.property(type=int, default=None)

    def __init__(self, actionWidget):
        super().__init__()

        self._actionWidget = actionWidget
        self._valueRangeWidget = ValueRangeWidget(editable = False)
        self._valueRangeWidget.show()

    def setControl(self, control):
        """Set the control."""
        self._control = control
        self._valueRangeWidget.setTotalRange(control.minimum,
                                             control.maximum)

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return self._valueRangeWidget.do_get_request_mode()

    def do_get_preferred_width(self, *args):
        """Get the preferred width of the widget."""
        return self._valueRangeWidget.do_get_preferred_width(*args)

    def do_get_preferred_height(self, *args):
        """Get the preferred height of the widget."""
        return self._valueRangeWidget.do_get_preferred_height(*args)

    def do_render(self, cr, widget, background_area, cell_area, flags):
        """Render the cell.

        Depending on the control type, it is either rendered as a toggle button
        for keys or as a label for the axes."""

        self._valueRangeWidget.setParentStyleContext(widget.get_style_context())
        self._valueRangeWidget.setValueRange(self.fromValue, self.toValue)
        self._valueRangeWidget.size_allocate(cell_area)

        self._valueRangeWidget.do_draw(cr)

#-------------------------------------------------------------------------------

class ActionWidget(Gtk.Box):
    """The widget to display or edit an action."""
    def __init__(self, window, edit = False, subtitle = None):
        super().__init__()

        self._control = None
        self._action = None
        self._window = window
        self._edit = edit
        self._subtitle = subtitle

        self.set_property("orientation", Gtk.Orientation.VERTICAL)

        self.set_margin_start(8)
        self.set_margin_end(8)

        self._valueRangeBox = valueRangeBox = \
            Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

        label = Gtk.Label.new_with_mnemonic(_("Ran_ge:"))
        valueRangeBox.pack_start(label, False, False, 2)

        self._unusedRanges = []
        self._valueRanges = []
        self._valueRangesStore = valueRangesStore = Gtk.ListStore(int, int)

        self._valueRangeSelector = valueRangeSelector = \
            Gtk.ComboBox.new_with_model(valueRangesStore)
        self._valueRangeRenderer = renderer = CellRendererValueRange(self)
        renderer.props.mode = Gtk.CellRendererMode.EDITABLE
        valueRangeSelector.pack_start(renderer, True)
        valueRangeSelector.add_attribute(renderer, "fromValue", 0)
        valueRangeSelector.add_attribute(renderer, "toValue", 1)
        valueRangeSelector.connect("changed", self._valueRangeSelectionChanged)
        valueRangeSelector.set_tooltip_text(
            _("The value range of the axis which the action belongs to."))
        label.set_mnemonic_widget(valueRangeSelector)

        valueRangeBox.pack_start(valueRangeSelector, True, True, 2)

        if edit:
            self._editValueRangeButton = editValueRangeButton = \
                Gtk.Button.new_from_icon_name("gtk-edit", Gtk.IconSize.BUTTON)
            editValueRangeButton.set_tooltip_text(_("Edit the current value range"))
            editValueRangeButton.set_sensitive(True)
            editValueRangeButton.connect("clicked", self._editValueRange)

            valueRangeBox.pack_start(editValueRangeButton, False, False, 2)

            self._addValueRangeButton = addValueRangeButton = \
                Gtk.Button.new_from_icon_name("list-add", Gtk.IconSize.BUTTON)
            addValueRangeButton.set_tooltip_text(_("Add a new value range"))
            addValueRangeButton.set_sensitive(False)
            addValueRangeButton.connect("clicked", self._addValueRange)

            valueRangeBox.pack_start(addValueRangeButton, False, False, 2)

            self._removeValueRangeButton = removeValueRangeButton = \
                Gtk.Button.new_from_icon_name("list-remove", Gtk.IconSize.BUTTON)
            removeValueRangeButton.set_tooltip_text(
                _("Remove the selected value range. If this is the only range, "
                  "it will be expanded to cover the whole range of the axis."))
            removeValueRangeButton.set_sensitive(False)
            removeValueRangeButton.connect("clicked", self._removeValueRange)

            valueRangeBox.pack_start(removeValueRangeButton, False, False, 2)

        self.pack_start(valueRangeBox, False, False, 4)

        nameBox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

        label = Gtk.Label.new("Name:")
        nameBox.pack_start(label, False, False, 4)

        self._nameEntry = nameEntry = Gtk.Entry.new()
        nameEntry.set_tooltip_text(
            _("Enter the name of the action. It is not necessary to have "
              "a name for an action, but if it does, it is displayed in the "
              "action table for easier identification."))
        nameEntry.connect("changed", self._nameChanged)

        nameBox.pack_start(nameEntry, True, True, 4)

        self.pack_start(nameBox, False, False, 5)

        self._typeBox = typeBox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        typeBox.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label.new("Type:")
        typeBox.pack_start(label, False, False, 4)

        self._simpleButton = simpleButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("S_imple"))
        simpleButton.connect("toggled", self._typeChanged)
        simpleButton.set_tooltip_text(
            _("Select this to have a simple action."
              "\n\n"
              "A simple action is a series of key combinations. You can add "
              "and remove key combinations using the buttons below."))
        typeBox.pack_start(simpleButton, False, False, 4)

        self._mouseMoveButton = mouseMoveButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("_Mouse move"))
        mouseMoveButton.join_group(simpleButton)
        mouseMoveButton.connect("toggled", self._typeChanged)
        mouseMoveButton.set_tooltip_text(
            _("Select this to have a mouse move action."
              "\n\n"
              "A mouse move action produces a horizontal or vertical movement "
              "of the mouse pointer or a movement of the mouse wheel."
              "\n\n"
              "The amount of the movement (or speed of it in case of "
              "repetition being enabled) produced depends on the value "
              "of the control, hence it is most useful with axes. "
              "For the formula of how much movement is produced, see "
              "the tooltips of the values below."))
        typeBox.pack_start(mouseMoveButton, False, False, 4)

        self._advancedButton = advancedButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("Adva_nced"))
        advancedButton.join_group(simpleButton)
        advancedButton.connect("toggled", self._typeChanged)
        advancedButton.set_tooltip_text(
            _("Select this to have an advanced action."
              "\n\n"
              "An advanced action is a sequence of more elementary commands, "
              "key presses, releases, mouse movements and/or delays. Also, "
              "separate command sequences can be defined to be executed "
              "when the control enters the state the advanced action "
              "belongs to, and when that state is left. "
              "Repetition can be enabled here as well, and a separate command "
              "sequence can be given for the repeats. If no such command "
              "sequence is given, the entry sequence will be repeated."))
        typeBox.pack_start(advancedButton, False, False, 4)

        self._scriptButton = scriptButton = \
            Gtk.RadioButton.new_with_mnemonic(None, _("Scrip_t"))
        scriptButton.join_group(simpleButton)
        scriptButton.connect("toggled", self._typeChanged)
        scriptButton.set_tooltip_text(
            _("Select this to have a script action."
              "\n\n"
              "A script action consists of two Lua scripts to be executed when "
              "the control enters the state the action belongs to and when "
              "that state is left. The code entered is placed into a function "
              "with no arguments or return value. See more information about "
              "the Lua execution environment in the tooltips of the script "
              "entry fields below."))

        typeBox.pack_start(scriptButton, False, False, 4)

        self.pack_start(typeBox, False, False, 5)

        frame = Gtk.Frame.new(None)

        self._stack = stack = Gtk.Stack.new()

        self._simpleEditor = simpleEditor = \
            SimpleActionEditor(window, edit = edit, subtitle = subtitle)
        simpleEditor.connect("modified", self._modified)
        simpleEditor.set_vexpand(True)
        simpleEditor.set_valign(Gtk.Align.FILL)
        stack.add_named(simpleEditor, "simple")

        self._advancedEditor = advancedEditor = \
            AdvancedActionEditor(window, edit = edit, subtitle = subtitle)
        advancedEditor.connect("modified", self._modified)
        advancedEditor.set_vexpand(True)
        advancedEditor.set_valign(Gtk.Align.FILL)
        stack.add_named(advancedEditor, "advanced")

        self._mouseMoveEditor = mouseMoveEditor = \
            MouseMoveEditor(window, edit = edit)
        mouseMoveEditor.connect("modified", self._modified)
        mouseMoveEditor.set_vexpand(True)
        mouseMoveEditor.set_valign(Gtk.Align.FILL)
        stack.add_named(mouseMoveEditor, "mouseMove")

        self._scriptEditor = scriptEditor = \
            ScriptActionEditor(window, edit=edit, subtitle = subtitle)
        scriptEditor.connect("modified", self._modified)
        scriptEditor.set_vexpand(True)
        scriptEditor.set_valign(Gtk.Align.FILL)
        stack.add_named(scriptEditor, "script")

        stack.set_vexpand(True)
        stack.set_valign(Gtk.Align.FILL)

        frame.add(stack)

        self.pack_start(frame, True, True, 5)

        self._lastValueRangeSelection = None

    @property
    def singleAction(self):
        """Get the single action being edited."""
        action = None
        if self._simpleButton.get_active():
            action = self._simpleEditor.action
        elif self._advancedButton.get_active():
            action = self._advancedEditor.action
        elif self._mouseMoveButton.get_active():
            action = self._mouseMoveEditor.action
        elif self._scriptButton.get_active():
            action = self._scriptEditor.action

        if action is not None:
            name = self._nameEntry.get_text()
            if name:
                action.displayName = name

        return action

    @property
    def action(self):
        """Get the action being edited."""
        if self._action is None or self._action.type!=Action.TYPE_VALUE_RANGE:
            return self.singleAction
        else:
            self._saveCurrentAction()
            return self._action

    @property
    def control(self):
        """Get the control whose action is being edited."""
        return self._control

    @property
    def controlAction(self):
        """Get the control and the action to be displayed/edited."""
        return (self._control, self.action)

    @controlAction.setter
    def controlAction(self, controlAction):
        """Set the control and the action to display/edit."""
        (control, action) = controlAction
        self._control = control
        self._action = action

        if isinstance(control, Axis):
            self._valueRangeRenderer.setControl(control)

            self._lastValueRangeSelection = None

            self._valueRanges = []
            self._valueRangesStore.clear()

            if action is None or action.type!=Action.TYPE_VALUE_RANGE:
                self._valueRanges.append((control.minimum, control.maximum))
                self._valueRangesStore.append([control.minimum, control.maximum])
            else:
                for (fromValue, toValue, action) in action._actions:
                    self._valueRanges.append((fromValue, toValue))
                    self._valueRangesStore.append([fromValue, toValue])
            self._valueRangeSelector.set_active(0)
            self._valueRangeBox.show()
        else:
            self._valueRangeBox.hide()

            self._valueRanges = []
            self._valueRangesStore.clear()

            self._displaySingleAction(action)

        self._updateUnusedRanges()

    @property
    def numValueRanges(self):
        """Get the number of the value ranges."""
        return len(self._valueRanges)

    @property
    def numActionViews(self):
        """Get the number of the views for the current action."""
        if self._advancedButton.get_active():
            return self._advancedEditor.numViews
        elif self._scriptButton.get_active():
            return self._scriptEditor.numViews
        else:
            return 1

    def showValueRange(self, index):
        """Show the value range with the given index."""
        self._valueRangeSelector.set_active(index)

    def showActionView(self, index):
        """Show the view of the action with the given index."""
        if self._advancedButton.get_active():
            return self._advancedEditor.showView(index)
        elif self._scriptButton.get_active():
            return self._scriptEditor.showView(index)
        else:
            return 1

    def _displaySingleAction(self, action):
        """Display the given (non-value range) action."""
        if action is not None and action.displayName:
            self._nameEntry.set_text(action.displayName)
        else:
            self._nameEntry.set_text("")

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
            self._advancedEditor.action = action
        elif action.type==Action.TYPE_MOUSE_MOVE:
            self._mouseMoveEditor.action = action
        elif action.type==Action.TYPE_SCRIPT:
            self._scriptEditor.action = action

    def _typeChanged(self, button):
        """Called when the type selector has changed."""
        if button.get_active():
            if button is self._simpleButton:
                self._stack.set_visible_child(self._simpleEditor)
            elif button is self._advancedButton:
                self._advancedEditor.prepare()
                self._stack.set_visible_child(self._advancedEditor)
            elif button is self._mouseMoveButton:
                self._stack.set_visible_child(self._mouseMoveEditor)
            elif button is self._scriptButton:
                self._stack.set_visible_child(self._scriptEditor)

    def _modified(self, editor, canSave):
        """Called when the action is modified."""
        self.emit("modified", canSave)

    def _valueRangeSelectionChanged(self, comboBox):
        """Called when a different value range has been selected."""
        if not isinstance(self._control, Axis):
            return

        self._saveCurrentAction()

        i = self._valueRangeSelector.get_active_iter()
        if i is None:
            self._displaySingleAction(None)
        elif self._action is None or self._action.type!=Action.TYPE_VALUE_RANGE:
            self._displaySingleAction(self._action)
        else:
            fromValue = self._valueRangesStore.get_value(i, 0)
            toValue = self._valueRangesStore.get_value(i, 1)
            action = self._action.findAction(fromValue, toValue)
            self._displaySingleAction(action)

        self._lastValueRangeSelection = i

    def _updateUnusedRanges(self):
        """Update the unused ranges."""
        unusedRanges = []

        control = self._control
        if control is not None and isinstance(control, Axis):
            previousToValue = control.minimum - 1
            for (fromValue, toValue) in self._valueRanges:
                if fromValue>(previousToValue+1):
                    unusedRanges.append((previousToValue + 1, fromValue - 1))
                previousToValue = toValue

            maximum = control.maximum
            if maximum>(previousToValue+1):
                unusedRanges.append((previousToValue + 1, maximum))

            if self._edit:
                self._removeValueRangeButton.set_sensitive(
                    len(self._valueRanges)>1 or
                    self._valueRanges[0][0]!=control.minimum or
                    self._valueRanges[0][1]!=control.maximum)

        self._unusedRanges = unusedRanges

        if self._edit:
            self._addValueRangeButton.set_sensitive(len(unusedRanges)>0)

    def _saveCurrentAction(self):
        """Save the current action."""
        if self._lastValueRangeSelection is not None:
            if self._action is None or \
               self._action.type!=Action.TYPE_VALUE_RANGE:
                self._action = self.singleAction
            else:
                fromValue = self._valueRangesStore.get_value(self._lastValueRangeSelection, 0)
                toValue = self._valueRangesStore.get_value(self._lastValueRangeSelection, 1)
                self._action.setAction(fromValue, toValue, self.singleAction)

    def _editValueRange(self, button):
        """Called when the button to edit a value range is called."""
        axis = self._control
        action = self._action
        activeIter = self._valueRangeSelector.get_active_iter()
        if action is None or action.type!=Action.TYPE_VALUE_RANGE:
            fromValue = axis.minimum
            toValue = axis.maximum
        else:
            fromValue = self._valueRangesStore.get_value(activeIter, 0)
            toValue = self._valueRangesStore.get_value(activeIter, 1)

        dialog = ValueRangeEditor(_("Edit value range"),
                                  self._control, fromValue, toValue,
                                  self._valueRanges,
                                  subtitle = self._subtitle)
        dialog.set_transient_for(self._window)

        response = dialog.run()

        newFromValue = dialog.fromValue
        newToValue = dialog.toValue

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            if newFromValue!=fromValue or newToValue!=toValue:
                if action is None or action.type!=Action.TYPE_VALUE_RANGE:
                    self._action = ValueRangeAction()
                    if action is None:
                        action = NOPAction()
                    self._action.addAction(newFromValue, newToValue, action)
                elif newFromValue==axis.minimum and newToValue==axis.maximum:
                    assert(self._action.numActions==1)
                    for (f, t, action) in self._action.actions:
                        self._action = action
                        break
                    if self._action.type==Action.TYPE_NOP:
                        self._action = None
                else:
                    self._action.changeRange(fromValue, toValue,
                                             newFromValue, newToValue)

                self._valueRanges = [(newFromValue, newToValue) if
                                     f==fromValue and t==toValue else
                                     (f, t) for (f, t) in self._valueRanges]
                self._valueRangesStore.set_value(activeIter, 0, newFromValue)
                self._valueRangesStore.set_value(activeIter, 1, newToValue)
                self._updateUnusedRanges()
                self.emit("modified", True)

    def _addValueRange(self, button):
        """Called when a value range is to be added."""
        unusedRanges = self._unusedRanges
        if len(unusedRanges)==0:
            return

        dialog = ValueRangeEditor(_("Add value range"),
                                  self._control,
                                  unusedRanges[0][0], unusedRanges[0][1],
                                  self._valueRanges,
                                  subtitle = self._subtitle)
        dialog.set_transient_for(self._window)

        response = dialog.run()

        fromValue = dialog.fromValue
        toValue = dialog.toValue

        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            action = self._action
            assert(action.type==Action.TYPE_VALUE_RANGE)
            action.addAction(fromValue, toValue, NOPAction())

            targetIndex = len(self._valueRanges)
            previousT = self._control.minimum - 1
            for (index, (f, t)) in enumerate(self._valueRanges):
                if fromValue>previousT and toValue<f:
                    targetIndex = index
                    break

                previousT = t

            self._valueRanges.insert(targetIndex, (fromValue, toValue))
            i = self._valueRangesStore.insert(targetIndex,
                                              [fromValue, toValue])
            self._valueRangeSelector.set_active_iter(i)
            self._updateUnusedRanges()
            self.emit("modified", True)

    def _removeValueRange(self, button):
        """Called when a value range is to be removed."""
        valueRanges = self._valueRanges
        if len(valueRanges)==1:
            text = _("Are you sure to expand the range to cover the full range of the axis?")
        else:
            text = _("Are you sure to remove the selected value range?")

        if yesNoDialog(self._window, text):
            activeIter = self._valueRangeSelector.get_active_iter()
            if len(valueRanges)==1:
                axis = self._control
                if self._action is not None and self._action.type==Action.TYPE_VALUE_RANGE:
                    valueRanges[0] = (axis.minimum, axis.maximum)
                    self._valueRangesStore.set_value(activeIter, 0, axis.minimum)
                    self._valueRangesStore.set_value(activeIter, 1, axis.maximum)
                    for (f, t, action) in self._action.actions:
                        self._action = action
                        break
                else:
                    assert(valueRanges[0][0]==axis.minimum)
                    assert(valueRanges[0][1]==axis.maximum)
            else:
                assert(self._action.type==Action.TYPE_VALUE_RANGE)

                activeIndex = self._valueRangeSelector.get_active()

                newIter = self._valueRangesStore.iter_next(activeIter)
                if newIter is None:
                    newIter = self._valueRangesStore.iter_previous(activeIter)
                self._lastValueRangeSelection = None

                self._action.removeAction(valueRanges[activeIndex][0],
                                          valueRanges[activeIndex][1])
                self._valueRangesStore.remove(activeIter)
                del valueRanges[activeIndex]

                self._valueRangeSelector.set_active_iter(newIter)

            self._updateUnusedRanges()
            self.emit("modified", True)

    def _nameChanged(self, entry):
        """Called when the name has changed."""
        self.emit("modified", True)

GObject.signal_new("modified", ActionWidget,
                   GObject.SignalFlags.RUN_FIRST, None, (bool,))

#-------------------------------------------------------------------------------

class ActionEditor(Gtk.Dialog):
    """An action editor dialog."""
    # Response code: clear the action
    RESPONSE_CLEAR = 1

    def __init__(self, joystickType, profile, action, control, state, shiftStateSequence):
        """Construct the action editor."""
        super().__init__(use_header_bar = True)

        self.set_title(_("Edit action"))

        subtitle = control.displayName
        if state is not None:
            subtitle += ": " + state.displayName

        if shiftStateSequence:
            shiftStateText = ""

            for (index, value) in enumerate(shiftStateSequence):
                shiftLevel = profile.getShiftLevel(index)
                shiftState = shiftLevel.getState(value)
                if not shiftState.isDefault:
                    labels = ShiftStatesWidget.getShiftStateLabels(joystickType,
                                                                   profile,
                                                                   shiftState)
                    text = ", ".join(labels)

                    shiftStateText += ", " if shiftStateText else ""
                    shiftStateText += text

            if shiftStateText:
                subtitle += " (" + shiftStateText + ")"

        self.get_header_bar().set_subtitle(subtitle)

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

        actionWidget = self._actionWidget = ActionWidget(self, edit = True,
                                                         subtitle = subtitle)
        actionWidget.connect("modified", self._modified)
        contentArea.pack_start(actionWidget, True, True, 0)

        self.set_size_request(-1, 400)

        self.show_all()

        self.controlAction = (control, action)

    @property
    def action(self):
        """Get the action in the the currently selected editor."""
        return self._actionWidget.action

    @property
    def controlAction(self):
        """Get the control and the action appropriate for the currently
        selected editor."""
        return self._actionWidget.controlAction

    @controlAction.setter
    def controlAction(self, controlAction):
        """Setup the window from the given action."""
        (_control, action) = controlAction

        self._clearButton.set_visible(
            action is not None and action.type!=Action.TYPE_NOP)
        self._actionWidget.controlAction = controlAction
        self._saveButton.set_sensitive(False)

    def _modified(self, actionWidget, canSave):
        """Called when the action is modified."""
        self._saveButton.set_sensitive(canSave)

#-------------------------------------------------------------------------------

class ActionTooltipWindow(Gtk.Window):
    """A tooltip window for the actions widget displaying an action widget in
    non-editing mode."""
    def __init__(self, actionsWidget):
        super().__init__()

        self.set_attached_to(actionsWidget)
        self.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)
        self.set_decorated(False)

        actionWidget = self._actionWidget = ActionWidget(self, edit = False)
        actionWidget.show_all()
        self.add(actionWidget)

        self.set_size_request(-1, 250)

    def setControlAction(self, controlAction):
        """Set the action."""
        self._actionWidget.controlAction = controlAction

    def setRangeIndex(self, numerator, denominator):
        """Set the index of the value range to be shown using the given
        numerator and denominator."""
        actionWidget = self._actionWidget
        index = int(numerator * actionWidget.numValueRanges // denominator)
        actionWidget.showValueRange(index)

    def setActionViewIndex(self, numerator, denominator):
        """Set the index of the action view to be shown using the given
        numerator and denominator."""
        actionWidget = self._actionWidget
        index = int(numerator * actionWidget.numActionViews // denominator)
        actionWidget.showActionView(index)

#-------------------------------------------------------------------------------

class ActionsWidget(Gtk.DrawingArea):
    """The widget displaying the matrix of actions where the rows are the
    controls and the columns are the various shift state combinations."""
    @staticmethod
    def getMouseMoveParametersString(command):
        """Get the parameters of the given mouse move command as a string."""
        parameters = ""

        for (name, value) in [(_("adjust"), command.adjust),
                              (_("a"), command.a),
                              (_("b"), command.b),
                              (_("c"), command.c)]:
            if abs(value)>1e-3:
                if parameters:
                    parameters += ", "
                parameters += "%s=%.02f" % (name, value)

        return parameters

    @staticmethod
    def getActionDisplayString(action):
        """Get a string representation of the given action."""
        if action is None:
            return "-----"
        elif isinstance(action, Action):
            if action.displayName:
                return action.displayName
            elif action.type==Action.TYPE_NOP:
                return "-----"
            elif action.type==Action.TYPE_SIMPLE:
                s = ""
                for keyCombination in action.keyCombinations:
                    if s:
                        s += ", "
                    s += SimpleActionEditor.keyCombination2Str(keyCombination)
                return s
            elif action.type==Action.TYPE_ADVANCED:
                return "<Advanced>"
            elif action.type==Action.TYPE_MOUSE_MOVE:
                return "<Mouse>"
            elif action.type==Action.TYPE_SCRIPT:
                return "<Script>"
            elif action.type==Action.TYPE_VALUE_RANGE:
                return "<Range>"
            else:
                return "<" + Action.getTypeNameFor(action.type) + ">"
        else:
            return "???????"

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

        self._highlightedShiftStateIndex = None
        self._highlightedControlStateIndex = None

        self._pangoLayout = layout = Pango.Layout(self.get_pango_context())
        layout.set_alignment(Pango.Alignment.CENTER)

        self._tooltipWindow = ActionTooltipWindow(self)
        self.set_tooltip_window(self._tooltipWindow)
        self.connect("query-tooltip", self._queryTooltip)
        self._profile = None

    def profileChanged(self):
        """Called when the profile is changed.

        It is called after the shift state widget, so its pre-calculated
        values are available."""
        self._profile = self._profileWidget.profilesEditorWindow.activeProfile
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

        Gtk.render_background(buttonStyle.styleContext, cr,
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
        if not isInClip(cr, x, y, xEnd, yEnd):
            return

        highlighted = \
            self._highlightedShiftStateIndex==shiftStateIndex and \
            self._highlightedControlStateIndex==controlStateIndex

        styleContext = \
            highlightStyle.styleContext if highlighted else buttonStyle.styleContext

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


        action = self._findAction(control, state, shiftStateSequence)

        displayString = ActionsWidget.getActionDisplayString(action)

        layout = self._pangoLayout
        layout.set_text(displayString)
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
        if not self.get_sensitive():
            return

        (shiftStateIndex, xOffset, width) = \
            self._shiftStates.getShiftStateIndexForX(event.x)
        (controlStateIndex, yOffset, height) = \
            self._controls.getControlStateIndexForY(event.y)
        if shiftStateIndex!=self._highlightedShiftStateIndex or \
           controlStateIndex!=self._highlightedControlStateIndex:
            self._highlightedShiftStateIndex = shiftStateIndex
            self._highlightedControlStateIndex = controlStateIndex
            self.queue_draw()

            (action, control, _state, _shiftStateSequence) = \
                self._findActionForIndexes(shiftStateIndex, controlStateIndex)

            self._tooltipWindow.setControlAction((control, action))

        self._tooltipWindow.setRangeIndex(yOffset, height)
        self._tooltipWindow.setActionViewIndex(xOffset, width)

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
            (shiftStateIndex, _xOffset, _width) = \
                self._shiftStates.getShiftStateIndexForX(event.x)
            (controlStateIndex, _yOffset, _height) = \
                self._controls.getControlStateIndexForY(event.y)

            (action, control, state, shiftStateSequence) = \
                self._findActionForIndexes(shiftStateIndex, controlStateIndex)

            profilesEditorWindow = self._profileWidget.profilesEditorWindow
            joystickType  = profilesEditorWindow.joystickType
            profile = profilesEditorWindow.activeProfile

            dialog = ActionEditor(joystickType, profile, action, control,
                                  state, shiftStateSequence)
            dialog.set_transient_for(profilesEditorWindow)

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
                if joystickType.setAction(profile, control, state,
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
        stateValue = 0 if state is None else state.value
        return profile.findAction(control, stateValue, shiftStateSequence)

    def _queryTooltip(self, _widget, _x, _y, _keyboardMode, _tooltip):
        """Called when a tooltip is about to be shown."""
        return self._profile is not None

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
        if profile is None:
            return

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

class LuaEditor(Gtk.Dialog):
    """An editor for the Lua prologue or epilogue code snippets."""
    # Response code: clear the code
    RESPONSE_CLEAR = 1

    def __init__(self, title, codeLines):
        """Construct the editor."""
        super().__init__(use_header_bar = True)
        self.set_title(title)

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self._saveButton = button = self.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        button.set_sensitive(False)

        self._clearButton = button = self.add_button(Gtk.STOCK_CLEAR,
                                                     LuaEditor.RESPONSE_CLEAR)
        button.set_tooltip_text(_("Clear the code."))
        button.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)

        contentArea = self.get_content_area()

        scrolledWindow = Gtk.ScrolledWindow.new()

        self._codeView = codeView = Gtk.TextView.new()
        self._code = code = codeView.get_buffer()
        code.set_text("\n".join(codeLines))
        code.connect("changed", self._modified)
        codeView.set_tooltip_text(ScriptActionEditor._luaToolTip)
        scrolledWindow.add(codeView)

        contentArea.pack_start(scrolledWindow, True, True, 4)

        self.set_size_request(-1, 400)
        self.show_all()

        self._clearButton.set_visible(codeLines)

    @property
    def codeLines(self):
        """Get the lines of code."""
        code = self._code
        (start, end) = code.get_bounds()

        return code.get_text(start, end, True).splitlines()

    def _modified(self, buffer):
        """Called when the code is modified."""
        self._saveButton.set_sensitive(True)

#-------------------------------------------------------------------------------

class TopWidget(Gtk.Fixed):
    """The widget at the top of the profile widget."""
    _generalLuaExplanation = _(
        "The profile is eventually turned into a Lua script that is "
        "downloaded to the daemon and gets called whenever the state "
        "of a control of the joystick changes. The script starts with "
        "a prologue containing some definitions needed for the control "
        "change event handlers. It is possible to append further code to the "
        "end of this generated prologue. "
        "The prologue is followed by the function definitions for the event "
        "handlers. These are usually quite simple, calling the functions in "
        "the prologue. The function definitions may be followed by a "
        "user-defined epilogue.")

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

        self._buttonBox = buttonBox = \
            Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)

        self._editPrologueButton = editPrologueButton = \
            Gtk.Button.new_with_mnemonic(_("Lua _prologue"))
        editPrologueButton.set_tooltip_text(
            _("Edit the Lua prologue code snippet.") +
            "\n\n" +
            TopWidget._generalLuaExplanation +
            "\n\n" +
            _("It is possible to define actions that are Lua scripts. Such "
              "scripts may need some global variables or other initialization "
              "that may go into the prologue part. The code is appended to the "
              "end of the prologue generated from the profile. "
              "It is followed by the function definitions for the "
              "control change events."))
        editPrologueButton.connect("clicked", self._editPrologue)
        buttonBox.pack_start(editPrologueButton, False, False, 4)

        self._editEpilogueButton = editEpilogueButton = \
            Gtk.Button.new_with_mnemonic(_("Lua _epilogue"))
        editEpilogueButton.set_tooltip_text(
            _("Edit the Lua epilogue code snippet.") +
            "\n\n" +
            TopWidget._generalLuaExplanation +
            "\n\n" +
            _("The epilogue is appended after the generated Lua code, "
              "to allow for further initialization or definitions "
              "that need to come after the rest."))
        editEpilogueButton.connect("clicked", self._editEpilogue)
        buttonBox.pack_start(editEpilogueButton, False, False, 4)

        buttonBox.set_halign(Gtk.Align.END)

        self.put(buttonBox, 0, 0)

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

        allocationWidth = allocation.width

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

        r.x = x
        r.y = y
        r.width = allocationWidth - x
        r.height = height
        self._buttonBox.size_allocate(r)
        self.move(self._buttonBox, r.x, r.y)

    def _addShiftLevel(self, button):
        """Called when a shift level is to be added to the profile at the top level."""
        self._profileWidget.insertShiftLevel(0)

    def _editPrologue(self, button):
        """Called when the button to edit the prologue is clicked."""
        self._edit(True)

    def _editEpilogue(self, button):
        """Called when the button to edit the epilogue is clicked."""
        self._edit(False)

    def _edit(self, prologue):
        """Edit the prologue or the epilogue."""
        profilesEditorWindow = self._profileWidget.profilesEditorWindow
        profile = profilesEditorWindow.activeProfile
        joystickType = profilesEditorWindow.joystickType

        dialog = LuaEditor(_("Lua prologue") if prologue else _("Lua epilogue"),
                           profile.prologue if prologue else profile.epilogue)

        codeLines = []
        while True:
            response = dialog.run()

            if response==LuaEditor.RESPONSE_CLEAR:
                if yesNoDialog(dialog,
                               _("Are you sure to clear the prologue?")
                               if prologue else
                               _("Are you sure to clear the epilogue?")):
                    break
            elif response==Gtk.ResponseType.OK:
                codeLines = dialog.codeLines
                break
            else:
                break

        dialog.destroy()

        if response==Gtk.ResponseType.OK or \
           response==LuaEditor.RESPONSE_CLEAR:
            if prologue:
                joystickType.setPrologue(profile, codeLines)
            else:
                joystickType.setEpilogue(profile, codeLines)

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

        joystickType = profilesEditorWindow.joystickType
        joystickType.connect("key-display-name-changed",
                             self._controlDisplayNameChanged)
        joystickType.connect("axis-display-name-changed",
                             self._controlDisplayNameChanged)
        joystickType.connect("virtualControl-added",
                             self._virtualControlsChanged)
        joystickType.connect("virtualControl-display-name-changed",
                             self._controlDisplayNameChanged)
        joystickType.connect("virtualControl-removed",
                             self._virtualControlsChanged)
        joystickType.connect("virtualState-added",
                             self._virtualControlsChanged)
        joystickType.connect("virtualState-moved-forward",
                             self._virtualControlsChanged)
        joystickType.connect("virtualState-moved-backward",
                             self._virtualControlsChanged)
        joystickType.connect("virtualState-display-name-changed",
                             self._controlDisplayNameChanged)
        joystickType.connect("virtualState-removed",
                             self._virtualControlsChanged)
        joystickType.connect("profile-virtualControl-added",
                             self._virtualControlsChanged)
        joystickType.connect("profile-virtualControl-display-name-changed",
                             self._controlDisplayNameChanged)
        joystickType.connect("profile-virtualState-added",
                             self._virtualControlsChanged)
        joystickType.connect("profile-virtualState-display-name-changed",
                             self._controlDisplayNameChanged)
        joystickType.connect("profile-virtualState-moved-forward",
                             self._virtualControlsChanged)
        joystickType.connect("profile-virtualState-moved-backward",
                             self._virtualControlsChanged)
        joystickType.connect("profile-virtualState-removed",
                             self._virtualControlsChanged)
        joystickType.connect("profile-virtualControl-removed",
                             self._virtualControlsChanged)

        self.connect("size-allocate", self._resized)

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

    def keyPressed(self, code):
        """Called when the key with the given code has been pressed."""
        self._controls.keyPressed(code)

    def keyReleased(self, code):
        """Called when the key with the given code has been released."""
        pass

    def axisChanged(self, code, value):
        """Called when the value of the axis with the given code has changed."""
        self._controls.axisChanged(code, value)

    def setKeyHighlight(self, code, value):
        """Set the highlighing of the key with the given code."""
        self._controls.setKeyHighlight(code, value)

    def setAxisHighlight(self, code, value):
        """Stop highlighting the axis with the given code."""
        self._controls.setAxisHighlight(code, value)

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

    def _controlDisplayNameChanged(self, *args):
        """Called when the display name of a control has changed."""
        self._shiftStates.updateStateLabels()
        self._controls.updateControlNames()
        self.queue_resize()

    def _virtualControlsChanged(self, *args):
        """Called when a virtual control or a state thereof has been added or
        removed."""
        self._controls.profileChanged()
        self._actions.queue_resize()
        self.queue_resize()

    def _resized(self, w, a):
        """Called when the widge is resized."""
        self._topWidget.queue_resize()

#-------------------------------------------------------------------------------

class ShiftLevelEditor(Gtk.Dialog):
    """A dialog displayed when a shift level is added or edited."""
    # Response code: delete the shift level
    RESPONSE_DELETE = 1

    def __init__(self, title, joystickType, shiftLevel, shiftLevelIndex,
                 profile, edit = False):
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
                                        forShiftLevel =  True)
        vcEditor.setProfile(profile)

        contentArea.pack_start(vcEditor, True, True, 5)

        vcEditor.setShiftLevel(shiftLevel, shiftLevelIndex)

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

        profileLabel = Gtk.Label.new_with_mnemonic(_("Pr_ofile:"))
        headerBar.pack_start(profileLabel)

        self._profileSelector = Gtk.ComboBox.new_with_model(self._profiles)
        profileNameRenderer = self._profileNameRenderer = Gtk.CellRendererText.new()
        self._profileSelector.pack_start(profileNameRenderer, True)
        self._profileSelector.add_attribute(profileNameRenderer, "text", 0)
        self._profileSelector.connect("changed", self._profileSelectionChanged)
        self._profileSelector.set_size_request(200, -1)
        self._profileSelector.set_tooltip_text(
            _("You can select the profile to be edited."
              "\n\n"
              "Several profiles can be defined for each joystick type. A "
              "profile determines what actions must be executed when one "
              "or more controls of the joystick is operated."
              "\n\n"
              "Typically different profiles are meant for different games "
              "or applications."))
        profileLabel.set_mnemonic_widget(self._profileSelector)

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

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        identityWidget = self._identityWidget = IdentityWidget(self)
        vbox.pack_start(identityWidget, False, False, 4)

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        self._jsViewer = jsViewer = JSViewer(gui, joystickType, self)
        hasView = jsViewer.hasView

        jsVBox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        jsViewBox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

        label = Gtk.Label.new_with_mnemonic(_("Vie_w:"))
        jsViewBox.pack_start(label, False, False, 4)

        self._viewSelector = Gtk.ComboBox.new_with_model(jsViewer.views)
        viewNameRenderer = self._viewNameRenderer = Gtk.CellRendererText.new()
        self._viewSelector.pack_start(viewNameRenderer, True)
        self._viewSelector.add_attribute(viewNameRenderer, "text", 0)
        self._viewSelector.connect("changed", self._jsViewer.viewChanged)
        self._viewSelector.set_size_request(150, -1)
        self._viewSelector.set_tooltip_text(
            _("Select the view of the joystick to show below."))
        label.set_mnemonic_widget(self._viewSelector)

        jsViewer.setCallbacks(self._viewSelector.get_active_iter,
                              activateViewFn = self._activateView,
                              joystickEventListener = self)

        jsViewBox.pack_start(self._viewSelector, True, True, 4)

        jsVBox.pack_start(jsViewBox, False, False, 0)

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        scrolledWindow.add(jsViewer)

        jsVBox.pack_start(scrolledWindow, True, True, 2)

        paned.pack1(jsVBox, True, True)

        self._notebook = notebook = Gtk.Notebook.new()
        notebook.set_sensitive(False)

        self._profileWidget = profileWidget = ProfileWidget(self)
        profileWidget.set_margin_start(8)
        profileWidget.set_margin_end(8)
        profileWidget.set_margin_top(8)
        profileWidget.set_margin_bottom(8)

        label = Gtk.Label.new_with_mnemonic(_("_Actions"))
        label.set_tooltip_text(
            _("This tab displays the table of the actions the operation of "
              "each control should evoke."
              "\n\n"
              "The left side of the table shows the controls of the "
              "joystick, including the virtual ones defined for the "
              "joystick type or the profile."
              "\n\n"
              "The cells of the table display the names of the actions "
              "defined for the controls, if any. Click in any of the "
              "action fields to create an action or to edit an existing "
              "one. An action always belongs to a state or state change. "
              "In case of buttons, an action belongs to the pressed state "
              "of the button, i.e. the action is executed when the button is "
              "pressed. In case of axes, the actions are invoked when "
              "the axis is deflected or moved, i.e. when its value or state "
              "changes. In case of virtual controls the actions are invoked "
              "when the virtual control enters the state the action belongs "
              "to."
              "\n\n"
              "Some action types allow the definition of some 'leave' activity, "
              "which is executed when the state the action belongs to is "
              "left. In case of buttons it means the releasing of the button. "
              "In case of axes it means a change in the value, i.e. when "
              "an axis is moved and its value changes, the leave activity "
              "for the old value is executed followed by the action for the new "
              "value, if any."
              "\n\n"
              "One can also define one or more shift levels. A shift "
              "level is a set of virtual states, that can be used to "
              "achieve different behaviour for the controls depending "
              "on the states of certain other controls. One of the simplest "
              "examples is to define a button as the 'shift' button on "
              "your joystick, so that if that button is pressed, "
              "some or all controls execute actions different from "
              "those executed when that button is not pressed. But an "
              "arbitrary number of states can be defined with different "
              "combinations of button, axis and/or virtual control states."
              "\n\n"
              "There can also be several shift levels to be able to "
              "combine those. For example, some joysticks have a mode "
              "selector button or wheel, and the different modes could be "
              "used for different games, plus a shift button to alter "
              "the behaviour of the other controls."
              "\n\n"
              "If there are one or more shift levels, the table contains "
              "columns for each combinaton of the shift level states, "
              "thus a different action can be specified for each such "
              "combination."))
        notebook.append_page(profileWidget, label)

        self._virtualControlSetEditor = virtualControlSetEditor = \
            VirtualControlSetEditor(self, joystickType, forProfile = True)
        virtualControlSetEditor.set_position(200)

        label = Gtk.Label.new_with_mnemonic(_("_Virtual controls"))
        label.set_tooltip_text(
            _("This tab displays any virtual controls defined "
              "in the current profile. These virtual controls "
              "are available besides the ones defined for the "
              "joystick type.") + VirtualControlSetEditor.tabTooltip)
        notebook.append_page(virtualControlSetEditor, label)

        if gui.debug:
            label = Gtk.Label.new_with_mnemonic(_("_Daemon XML"))

            self._daemonXMLWindow = daemonXMLWindow = Gtk.ScrolledWindow.new(None, None)

            self._daemonXMLView = daemonXMLView = Gtk.TextView.new()
            daemonXMLView.set_editable(False)
            daemonXMLWindow.add(daemonXMLView)

            notebook.append_page(daemonXMLWindow, label)

            notebook.connect("switch_page", self._pageSwitched)

        paned.pack2(notebook, True, False)

        paned.set_wide_handle(True)
        paned.set_position(900)

        vbox.pack_start(paned, True, True, 0)

        self.add(vbox)

        gui.addProfilesEditor(joystickType, self)

        self.set_titlebar(headerBar)

        profileList.setup()
        if profiles.iter_n_children(None)>0:
            self._profileSelector.set_active(0)

        self.show_all()

        jsViewer.setupWindowEvents()

        if hasView:
            self._viewSelector.set_active(0)

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
                                         _("Add shift level"),
                                         forShiftLevel = True,
                                         profile = self.activeProfile)
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
                                      shiftLevel, -1, self.activeProfile)
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
                                  modifiedShiftLevel, index,
                                  self.activeProfile,
                                  edit = True)

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

    def keyPressed(self, code):
        """Called when the key with the given code has been pressed."""
        self._profileWidget.keyPressed(code)

    def keyReleased(self, code):
        """Called when the key with the given code has been released."""
        self._profileWidget.keyReleased(code)

    def axisChanged(self, code, value):
        """Called when the value of the axis with the given code has changed."""
        self._profileWidget.axisChanged(code, value)

    def setKeyHighlight(self, code, value):
        """Set the highlighing of the key with the given code."""
        self._profileWidget.setKeyHighlight(code, value)

    def setAxisHighlight(self, code, value):
        """Stop highlighting the axis with the given code."""
        self._profileWidget.setAxisHighlight(code, value)

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
            self._virtualControlSetEditor.setProfile(None)
            self._notebook.set_sensitive(False)
        else:
            profile = self._profiles.get_value(i, 1)
            self._editProfileNameButton.set_sensitive(profile.userDefined)
            self._removeProfileButton.set_sensitive(profile.userDefined)
            self._copyProfileButton.set_sensitive(True)
            self._gui.editingProfile(self._joystickType, profile)
            self._identityWidget.setFrom(profile.identity, profile.autoLoad)
            self._virtualControlSetEditor.setProfile(profile)
            self._notebook.set_sensitive(True)
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
            self._jsViewer.startMonitorJoysticks()
        else:
            self._jsViewer.stopMonitorJoysticks()

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

    def _activateView(self, i):
        """Activate the view with the given iterator."""
        self._viewSelector.set_active_iter(i)

    def _pageSwitched(self, notebook, widget, pageNum):
        """Called when the notebook page has switched."""
        if widget is self._daemonXMLWindow:
            profile = self.activeProfile
            document = profile.getDaemonXMLDocument()
            self._daemonXMLView.get_buffer().set_text(
                document.toprettyxml())
