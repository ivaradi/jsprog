# Virtual Control editor widget

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from jsprog.device import DisplayVirtualState
from jsprog.parser import Control, ControlConstraint
from jsprog.parser import SingleValueConstraint, ValueRangeConstraint

#-------------------------------------------------------------------------------

class ValueRangeCellEditable(Gtk.EventBox, Gtk.CellEditable):
    """The editor for a cell containing a value range."""
    editing_canceled = GObject.property(type=bool, default=False)

    def __init__(self, joystickType, constraint):
        """Construct the editor."""
        super().__init__()

        control = constraint.control

        if isinstance(constraint, SingleValueConstraint):
            fromValue = toValue = constraint.value
        else:
            fromValue = constraint.fromValue
            toValue = constraint.toValue

        axis = joystickType.findAxis(control.code)
        if axis is None:
            minValue = fromValue
            maxValue = toValue
        else:
            minValue = axis.minimum
            maxValue = axis.maximum

        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
        self.add(box)

        adjustment = self._fromAdjustment = \
            Gtk.Adjustment.new(fromValue, minValue, toValue, 1, 10, 0)
        adjustment.connect("value-changed", self._adjustmentChanged)
        button = Gtk.SpinButton.new(adjustment, 1, 0)
        box.pack_start(button, True, True, 0)

        box.pack_start(Gtk.Label.new(".."), False, False, 0)

        adjustment = self._toAdjustment = \
            Gtk.Adjustment.new(toValue, fromValue, maxValue, 1, 10, 0)
        adjustment.connect("value-changed", self._adjustmentChanged)
        button = Gtk.SpinButton.new(adjustment, 1, 0)
        box.pack_start(button, True, True, 0)

        self.connect("key-release-event", self._keyEvent)

    @property
    def fromValue(self):
        """Get the lower limit of the vaqlue."""
        return int(self._fromAdjustment.get_value())

    @property
    def toValue(self):
        """Get the upper limit of the value."""
        return int(self._toAdjustment.get_value())

    def do_start_editing(self, event):
        """Called at the beginning when editing starts.

        Key release events are enabled so that we can catch the Escape key."""
        window = self.get_window()
        window.set_events(window.get_events() | Gdk.EventMask.KEY_RELEASE_MASK)

    def _adjustmentChanged(self, adjustment):
        """Called when the value of one of the adjustment's have changed.

        The limits of the other adjustment will be changed accordingly."""
        if adjustment is self._fromAdjustment:
            self._toAdjustment.set_lower(adjustment.get_value())
        elif adjustment is self._toAdjustment:
            self._fromAdjustment.set_upper(adjustment.get_value())

    def _keyEvent(self, editable, event):
        """Called when a key event has been received.

        If it concerns the Escape key, it is signalled that editing is done and
        the widget should be removed."""
        keyName = Gdk.keyval_name(event.keyval)
        if keyName =="Escape":
            self.editing_done()
            self.remove_widget()
            return True

        return False

#-------------------------------------------------------------------------------

class CellRendererConstraintValue(Gtk.CellRenderer):
    """A cell renderer for a constraint value.

    In case of a key, it is a switch. In case of an axis it consists of two
    spinners side-by-side."""
    constraint = GObject.property(type=object, default=None)

    def __init__(self, joystickType, viewWidget):
        super().__init__()
        self._joystickType = joystickType
        self._viewWidget = viewWidget

        self._keyWidget = None
        self._axisWidget = None

        self._editedConstraint = None
        self._editedPath = None

    def do_activate(self, event, widget, path, background_area, cell_area,
                    flags):
        """Called when the cell's widget is a toggle button and the mouse is
        clicked in the cell area."""
        control = self.constraint.control
        if control.isKey:
            self.emit("value-toggled", path)
        return True

    # def do_set_property(self, pspec, value):
    #     print("do_set_property", self, pspec, value)
    #     setattr(self, pspec.name, value)

    # def do_get_property(self, pspec):
    #     print("do_get_property", self, pspec)
    #     return getattr(self, pspec.name)

    def do_get_preferred_height(self, widget):
        """Called when the parent queries the preferred height."""
        self._ensureWidgets()
        return max(self._keyWidget.get_preferred_height(),
                   self._axisWidget.get_preferred_height())

    def do_get_preferred_height_for_width(self, widget, width):
        """Called when the parent queries the preferred height for the given
        width."""
        self._ensureWidgets()
        return max(self._keyWidget.get_preferred_height_for_width(width),
                   self._axisWidget.get_preferred_height_for_width(width))

    def do_get_preferred_width(self, widget):
        """Called when the parent queries the preferred width."""
        self._ensureWidgets()
        return max(self._keyWidget.get_preferred_width(),
                   self._axisWidget.get_preferred_width())

    def do_get_preferred_width_for_height(self, widget, height):
        """Called when the parent queries the preferred width for the given height."""
        self._ensureWidgets()
        return max(self._keyWidget.get_preferred_width_for_height(height),
                   self._axisWidget.get_preferred_width_for_height(height))

    def do_get_request_mode(self):
        """Called when the parent queries the preferred size computation method."""
        return Gtk.SizeRequestMode.WIDTH_FOR_HEIGHT

    def do_get_size(self, widget, cell_area):
        """Get the width and height needed to render the cell."""
        self._ensureWidgets()

        return (0, 0,
                self.do_get_preferred_width(widget),
                self.do_get_preferred_height(widget))

    def do_render(self, cr, widget, background_area, cell_area, flags):
        """Render the cell.

        Depending on the control type, it is either rendered as a toggle button
        for keys or as a label for the axes."""
        self._ensureWidgets()

        constraint = self.constraint
        if constraint is self._editedConstraint:
            return

        control = constraint.control
        widget = None

        if control.isKey:
            widget = self._keyWidget
            widget.set_label(_("pressed") if self.constraint.value!=0
                             else _("released"))
        elif control.isAxis:
            widget = self._axisWidget
            if isinstance(constraint, SingleValueConstraint):
                widget.set_label("%d" % (constraint.value,))
            else:
                widget.set_label("%d..%d" % (constraint.fromValue,
                                             constraint.toValue))

        if widget is not None:
            # The width is shifted to a very invisible area to avoid catching
            # any events
            area = Gdk.Rectangle()
            area.x = -1000
            area.y = -1000
            area.width = cell_area.width
            area.height = cell_area.height
            widget.size_allocate(area)

            widget.map()
            cr.save()
            cr.translate(cell_area.x, cell_area.y)

            widget.draw(cr)

            cr.restore()
            widget.unmap()

        return True

    def do_editing_canceled(self):
        """Called when the editing of a value range has been cancelled."""
        self._editedConstraint = None

    def do_editing_started(self, editable, path):
        """Called when the editing of a value range has been started."""
        self._editedConstraint = self.constraint
        editable.show_all()

    def do_start_editing(self, event, widget, path, background_area, cell_area,
                         flags):
        """Called when the editing of a value range is started.

        A ValueRangeCellEditable object is created and returned."""
        constraint = self.constraint
        control = self.constraint.control
        if control.isAxis:
            editable =  ValueRangeCellEditable(self._joystickType, constraint)
            editable.connect("editing-done", self._editingDone)
            self._editedPath = path
            return editable

    def _ensureWidgets(self):
        """Create the display widgets if they do not exist yet."""
        if self._keyWidget is None:
            keyWidget = self._keyWidget = Gtk.ToggleButton.new()
            keyWidget.set_label("XXXXXXXXXXXXXXX")
            keyWidget.set_parent(self._viewWidget)
            keyWidget.show()

        if self._axisWidget is None:
            axisWidget = self._axisWidget = Gtk.Label.new()
            axisWidget.set_label("XXXXXXXXXXXXXXXXXXXX")
            axisWidget.set_parent(self._viewWidget)
            axisWidget.show()

    def _editingDone(self, editable):
        """Called when the current editing operation is finished."""
        self._editedConstraint = None
        self.emit("value-range-edited",
                  self._editedPath, editable.fromValue, editable.toValue)

#-------------------------------------------------------------------------------

GObject.signal_new("value-toggled", CellRendererConstraintValue,
                   GObject.SignalFlags.RUN_FIRST, None, (str,))

GObject.signal_new("value-range-edited", CellRendererConstraintValue,
                   GObject.SignalFlags.RUN_FIRST, None, (str, int, int))

#-------------------------------------------------------------------------------

class VirtualStateEditor(Gtk.Dialog):
    """A dialog to edit a virtual state."""
    @staticmethod
    def compareConstraints(model, a, b, userData):
        """Function to compare the constraints for default sorting."""
        ca = model.get_value(a, 0)
        cb = model.get_value(b, 0)

        return ca.__cmp__(cb)

    def __init__(self, joystickType, virtualControl, virtualState,
                 okButtonLabel):
        super().__init__(use_header_bar = True)
        self.set_title(_("Virtual State"))
        self.set_default_size(400, 300)

        self._joystickType = joystickType
        self._virtualControl = virtualControl
        self._virtualState = virtualState

        self.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)

        self._applyButton = button = self.add_button(okButtonLabel, Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)
        contentArea.set_hexpand(True)
        contentArea.set_vexpand(True)

        grid = self._grid = Gtk.Grid.new()
        grid.set_column_spacing(16)
        grid.set_row_spacing(8)
        grid.set_hexpand(True)
        grid.set_vexpand(True)

        row = 0

        label = Gtk.Label(_("_Display name:"))
        label.set_use_underline(True)
        label.props.halign = Gtk.Align.START
        grid.attach(label, 0, row, 1, 1)

        self._displayNameEntry = displayNameEntry = Gtk.Entry()
        displayNameEntry.set_text(virtualState.displayName)
        displayNameEntry.connect("changed", self._displayNameChanged)
        grid.attach(displayNameEntry, 1, row, 1, 1)
        label.set_mnemonic_widget(displayNameEntry)

        row +=1

        grid.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL),
                    0, row, 2, 1)
        row += 1

        buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        buttonBox.set_layout(Gtk.ButtonBoxStyle.END)

        addButton = self._addButton = \
            Gtk.Button.new_from_icon_name("list-add-symbolic",
                                          Gtk.IconSize.BUTTON)
        addButton.connect("clicked", self._addClicked)
        buttonBox.add(addButton)

        removeButton = self._removeButton = \
            Gtk.Button.new_from_icon_name("list-remove-symbolic",
                                          Gtk.IconSize.BUTTON)
        removeButton.set_sensitive(False)
        removeButton.connect("clicked", self._removeClicked)
        buttonBox.add(removeButton)

        grid.attach(buttonBox, 0, row, 2, 1)
        row += 1

        # FIXME: this is very similar to the code in HotspotEditor and NewVirtualControlDialog
        self._controls = controls = Gtk.ListStore(str, str, int, int)
        index = 0
        activeIndex = 0
        for key in joystickType.keys:
            controls.append([key.name, key.displayName,
                             Control.TYPE_KEY, key.code])
        for axis in joystickType.axes:
            controls.append([axis.name, axis.displayName,
                             Control.TYPE_AXIS, axis.code])

        self._constraints = constraints = Gtk.ListStore(object, str, int)
        constraints.set_default_sort_func(VirtualStateEditor.compareConstraints)
        constraints.set_sort_column_id(Gtk.TREE_SORTABLE_DEFAULT_SORT_COLUMN_ID,
                                       Gtk.SortType.ASCENDING)
        for constraint in virtualState.constraints:
            control = constraint.control
            displayName = joystickType.getControlDisplayName(control)

            constraints.append([constraint, displayName,
                                Gtk.CellRendererMode.ACTIVATABLE
                                if control.isKey else
                                Gtk.CellRendererMode.EDITABLE])

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        scrolledWindow.set_hexpand(True)
        scrolledWindow.set_vexpand(True)

        self._constraintsView = constraintsView = \
            Gtk.TreeView.new_with_model(constraints)
        #controlSelector.connect("changed", self._controlChanged)

        controlRenderer = Gtk.CellRendererCombo.new()
        controlRenderer.props.model = controls
        controlRenderer.props.text_column = 1
        controlRenderer.props.editable = True
        controlRenderer.props.has_entry = False
        controlRenderer.connect("changed", self._controlChanged)
        controlColumn = Gtk.TreeViewColumn(title = _("Control"),
                                           cell_renderer = controlRenderer,
                                           text = 1)
        controlColumn.set_resizable(True)
        controlColumn.set_expand(True)
        constraintsView.append_column(controlColumn)

        valueRenderer = CellRendererConstraintValue(self._joystickType, constraintsView)
        valueRenderer.connect("value-toggled", self._constraintValueToggled)
        valueRenderer.connect("value-range-edited", self._constraintValueRangeEdited)
        valueColumn = Gtk.TreeViewColumn(title = _("Value(s)"),
                                         cell_renderer = valueRenderer,
                                         constraint = 0,
                                         mode = 2)
        valueColumn.set_resizable(True)
        valueColumn.set_alignment(0.5)
        valueColumn.set_expand(True)
        constraintsView.append_column(valueColumn)

        constraintsView.get_selection().connect("changed", self._selectionChanged)

        scrolledWindow.add(constraintsView)

        grid.attach(scrolledWindow, 0, row, 2, 1)
        row += 1

        contentArea.pack_start(grid, True, True, 8)

        self._updateButtons()

        self.show_all()

    @property
    def displayName(self):
        """Get the currently set display name."""
        return self._displayNameEntry.get_text()

    @property
    def constraints(self):
        """Get an iterator over the edited constraints in the state."""
        constraints = self._constraints
        i = constraints.get_iter_first()
        while i is not None:
            yield constraints.get_value(i, 0)
            i = constraints.iter_next(i)

    def _displayNameChanged(self, entry):
        """Called when the display name has changed."""
        self._updateButtons()

    def _controlChanged(self, cellRenderer, cellPath, valueIter):
        """Called when a control cell has been edited."""
        i = self._constraints.get_iter(cellPath)

        constraint = self._constraints.get_value(i, 0)
        control = constraint.control

        newDisplayName = self._controls.get_value(valueIter, 1)
        newControl = Control(self._controls.get_value(valueIter, 2),
                             self._controls.get_value(valueIter, 3))

        if newControl.type==Control.TYPE_KEY:
            if control.type==Control.TYPE_KEY:
                value = constraint.value
            else:
                value = 0

            newConstraint = SingleValueConstraint(newControl, value)
        else:
            if control.type==Control.TYPE_KEY or \
               isinstance(constraint, SingleValueConstraint):
                fromValue = toValue = constraint.value
            else:
                fromValue = constraint.fromValue
                toValue = constraint.toValue

            axis = self._joystickType.findAxis(newControl.code)
            fromValue = max(axis.minimum, fromValue,
                            min(axis.maximum, fromValue))
            toValue = min(axis.maximum, toValue,
                          max(axis.minimum, toValue))
            if fromValue==toValue:
                newConstraint = SingleValueConstraint(newControl, fromValue)
            else:
                newConstraint = ValueRangeConstraint(newControl, fromValue, toValue)

        self._constraints.set(i, [0, 1, 2],
                              [newConstraint, newDisplayName,
                               Gtk.CellRendererMode.ACTIVATABLE
                               if newControl.isKey else
                               Gtk.CellRendererMode.EDITABLE])

    def _constraintValueToggled(self, cellRenderer, cellPath):
        """Called when a constraint related to a key is toggled."""
        i = self._constraints.get_iter(cellPath)
        constraint = self._constraints.get_value(i, 0)
        constraint = SingleValueConstraint(constraint.control,
                                           1 if constraint.value==0 else 0)
        self._constraints.set(i, [0], [constraint])

    def _constraintValueRangeEdited(self, cellRenderer, cellPath, fromValue, toValue):
        """Called when a value range related to an axis is toggled."""
        i = self._constraints.get_iter(cellPath)
        constraint = self._constraints.get_value(i, 0)

        if fromValue==toValue:
            constraint = SingleValueConstraint(constraint.control, fromValue)
        else:
            constraint = ValueRangeConstraint(constraint.control,
                                              fromValue, toValue)

        self._constraints.set(i, [0], [constraint])

    def _selectionChanged(self, selection):
        """Called when the selection of the virtual controls has changed."""
        (_model, i) = selection.get_selected()

        self._removeButton.set_sensitive(i is not None and
                                         self._constraints.iter_n_children(None)>1)

    def _addClicked(self, button):
        """Called when the Add button is clicked.

        The 'next' control is added with an constraint: for keys it is a single
        value constraint with a value of 0 (released), for axes it is a value
        range with the full range of the axis."""
        joystickType = self._joystickType

        numControls = len(joystickType.keys) + len(joystickType.axes)

        numConstraints = self._constraints.iter_n_children(None)
        if numConstraints>=numControls:
            return

        controls = set()
        lastControlType = None
        lastControlCode = None

        i = self._constraints.get_iter_first()
        while i is not None:
            constraint = self._constraints.get_value(i, 0)
            control = constraint.control

            controls.add(control)

            lastControlType = control.type
            lastControlCode= control.code

            i = self._constraints.iter_next(i)

        while True:
            (controlType, controlCode) = \
                joystickType.getNextControl(lastControlType, lastControlCode)

            control = Control(controlType, controlCode)
            if control not in controls:
                break

            lastControlType = controlType
            lastControlCode = controlCode

        constraint = None
        if controlType==Control.TYPE_KEY:
            constraint = SingleValueConstraint(control, 0)
        else:
            axis = joystickType.findAxis(controlCode)
            constraint = ValueRangeConstraint(control, axis.minimum,
                                              axis.maximum)

        displayName = joystickType.getControlDisplayName(control)
        self._constraints.append([constraint, displayName,
                                  Gtk.CellRendererMode.ACTIVATABLE
                                  if control.isKey else
                                  Gtk.CellRendererMode.EDITABLE])

        self._updateButtons()

    def _removeClicked(self, button):
        """Called when the Remove button is clicked."""
        (_model, i) = self._constraintsView.get_selection().get_selected()
        if i is not None:
            constraints = self._constraints
            constraints.remove(i)
            self._updateButtons()

    def _updateButtons(self):
        """Update the senstivity of some buttons."""
        displayName = self.displayName
        vs = self._virtualControl.findStateByDisplayName(displayName)
        self._applyButton.set_sensitive(displayName and
                                        (vs is None or vs is self._virtualState) and
                                        self._constraints.iter_n_children(None)>0)


#-------------------------------------------------------------------------------

class VirtualControlEditor(Gtk.Box):
    """An editor for a virtual control (or shift level).

    It displays buttons to edit, add and remove virtual states and the
    virtual states themselves and allows the editing of the virtual states."""
    def __init__(self, joystickType, window):
        """Construct the editor."""
        super().__init__()
        self.set_property("orientation", Gtk.Orientation.VERTICAL)

        self._joystickType = joystickType
        self._window = window

        buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        buttonBox.set_layout(Gtk.ButtonBoxStyle.END)

        self._editVirtualStateButton = editVirtualStateButton = \
            Gtk.Button.new_from_icon_name(Gtk.STOCK_EDIT, Gtk.IconSize.BUTTON)
        editVirtualStateButton.connect("clicked",
                                       self._editVirtualStateButtonClicked)
        editVirtualStateButton.set_sensitive(False)
        buttonBox.add(editVirtualStateButton)

        self._addVirtualStateButton = addVirtualStateButton = \
            Gtk.Button.new_from_icon_name("list-add", Gtk.IconSize.BUTTON)
        addVirtualStateButton.set_sensitive(False)
        addVirtualStateButton.connect("clicked",
                                      self._addVirtualStateButtonClicked)
        buttonBox.add(addVirtualStateButton)

        self._removeVirtualStateButton = removeVirtualStateButton = \
            Gtk.Button.new_from_icon_name("list-remove", Gtk.IconSize.BUTTON)
        removeVirtualStateButton.set_sensitive(False)
        removeVirtualStateButton.connect("clicked",
                                         self._removeVirtualStateButtonClicked)
        buttonBox.add(removeVirtualStateButton)

        self.pack_start(buttonBox, False, False, 4)

        virtualStates = self._virtualStates = Gtk.ListStore(object, str, str)

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        self._virtualStatesView = view = Gtk.TreeView.new_with_model(virtualStates)
        view.get_selection().connect("changed", self._virtualStateSelected)

        displayNameRenderer = Gtk.CellRendererText.new()
        displayNameRenderer.props.editable = True
        displayNameRenderer.connect("edited", self._virtualStateDisplayNameEdited)
        displayNameColumn = Gtk.TreeViewColumn(title = _("State"),
                                               cell_renderer = displayNameRenderer,
                                               text = 1)
        displayNameColumn.set_resizable(True)
        view.append_column(displayNameColumn)

        constraintRenderer = Gtk.CellRendererText.new()
        constraintRenderer.props.editable = False
        constraintColumn = Gtk.TreeViewColumn(title = _("Constraints"),
                                              cell_renderer =
                                              constraintRenderer,
                                              text = 2)
        view.append_column(constraintColumn)

        scrolledWindow.add(view)

        self.pack_start(scrolledWindow, True, True, 5)

        self._virtualControl = None

    def setVirtualControl(self, virtualControl):
        """Set the virtual control to be edited to the given one."""
        self._virtualStates.clear()

        self._virtualControl = virtualControl

        self._addVirtualStateButton.set_sensitive(virtualControl is not None)

        if virtualControl is not None:
            for state in virtualControl.states:
                self._virtualStates.append([state, state.displayName,
                                            self._getStateConstraintText(state)])


    def _addVirtualStateButtonClicked(self, button):
        virtualControl = self._virtualControl

        number = self._virtualStates.iter_n_children(None)+1
        while True:
            displayName = "State " + str(number)
            if virtualControl.findStateByDisplayName(displayName) is None:
                break
            number += 1

        state = DisplayVirtualState(displayName)

        dialog = VirtualStateEditor(self._joystickType, virtualControl, state, _("_Add"))

        response = dialog.run()

        if response==Gtk.ResponseType.OK:
            state.displayName = dialog.displayName
            for constraint in dialog.constraints:
                state.addConstraint(constraint)

            if self._joystickType.newVirtualState(virtualControl, state):
                self._virtualStates.append([state, state.displayName,
                                            self._getStateConstraintText(state)])

        dialog.destroy()

    def _removeVirtualStateButtonClicked(self, button):
        """Called when the button to remove a constraint has been clicked."""
        if yesNoDialog(self._window,
                       _("Are you sure to remove the selected virtual state?")):
            (_model, i) = self._virtualStatesView.get_selection().get_selected()
            virtualState = self._virtualStates.get_value(i, 0)

            self._joystickType.deleteVirtualState(self._virtualControl,
                                                  virtualState)
            self._virtualStates.remove(i)

    def _editVirtualStateButtonClicked(self, button):
        """Called when a virtual state is to be edited."""
        virtualControl = self._virtualControl
        virtualState = self._getSelectedVirtualState()

        dialog = VirtualStateEditor(self._joystickType, virtualControl, virtualState,
                                    _("_Apply"))

        response = dialog.run()
        if response==Gtk.ResponseType.OK:
            self._joystickType.setVirtualStateDisplayName(virtualControl,
                                                          virtualState,
                                                          dialog.displayName)

            constraints = [c for c in dialog.constraints]
            self._joystickType.setVirtualStateConstraints(virtualControl,
                                                          virtualState,
                                                          constraints)

            (_model, i) = self._virtualStatesView.get_selection().get_selected()
            self._virtualStates.set(
                i, [1, 2], [virtualState.displayName,
                            self._getStateConstraintText(virtualState)])

        dialog.destroy()


    def _getConstraintText(self, constraint):
        """Get the textual description of the given constraint."""
        control = constraint.control

        displayName = self._joystickType.getControlDisplayName(control)

        text = displayName + ": "
        if constraint.type==ControlConstraint.TYPE_SINGLE_VALUE:
            if control.isKey:
                text += _("pressed") if constraint.value else _("released")
            else:
                text += str(constraint.value)
        elif constraint.type==ControlConstraint.TYPE_VALUE_RANGE:
            text += str(constraint.fromValue) + ".." + str(constraint.toValue)
        else:
            text += "?unknown?"

        return text

    def _getStateConstraintText(self, state):
        """Get a textual description of the constraints of the given state."""
        return ", ".join([self._getConstraintText(c) for c in state.constraints])

    def _virtualStateDisplayNameEdited(self, renderer, path, newName):
        """Called when the display name of a virtual state has been edited."""
        i = self._virtualStates.get_iter(path)
        virtualState = self._virtualStates.get_value(i, 0)
        if newName != virtualState.displayName:
            if self._joystickType.setVirtualStateDisplayName(self._virtualControl,
                                                             virtualState,
                                                             newName):
                self._virtualStates.set_value(i, 1, newName)

    def _virtualStateSelected(self, selection):
        """Handle the change in the selected virtual state."""
        (_model, i) = selection.get_selected()

        self._editVirtualStateButton.set_sensitive(i is not None)

        if i is None:
            self._removeVirtualStateButton.set_sensitive(False)
        else:
            self._removeVirtualStateButton.set_sensitive(
                self._virtualStates.iter_n_children(None)>2)

    def _getSelectedVirtualState(self):
        """Get the currently selected virtual state."""
        (_model, i) = self._virtualStatesView.get_selection().get_selected()

        return None if i is None else self._virtualStates.get_value(i, 0)

#-------------------------------------------------------------------------------
