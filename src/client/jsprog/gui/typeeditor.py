# Joystick type editor window

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from jsprog.device import View, Hotspot
import jsprog.device
from jsprog.joystick import Key, Axis

import shutil
import math

#-------------------------------------------------------------------------------

## @package jsprog.gui.typeeditor
#
# The window to edit a joystick type, i.e. to give human-readable names to
# the buttons and axes, to provide a joystick image with hotspots as well as
# icons for various purposes and to edit the virtual controls.

#-------------------------------------------------------------------------------

class PaddedImage(Gtk.Fixed):
    """A fixed widget containing an image that has a margins around it."""
    def __init__(self):
        super().__init__()

        self._leftMargin = 0
        self._rightMargin = 0
        self._topMargin = 0
        self._bottomMargin = 0
        self._imageXOffset = 0
        self._imageYOffset = 0
        self._preparedImageXOffset = 0
        self._preparedImageYOffset = 0

        self._image = Gtk.Image()
        self._preparedPixbuf = None

        self.put(self._image, 0, 0)

        self.connect("size-allocate", self._resized)

    @property
    def requestedWidth(self):
        """Get the requested width of the image. If there is a prepard pixbuf,
        it is used, otherwise the currently set one."""
        requestedWidth = self._leftMargin + self._rightMargin
        pixbuf = self._image.get_pixbuf() if self._preparedPixbuf is None \
                 else self._preparedPixbuf
        if pixbuf is not None:
            requestedWidth += pixbuf.get_width()
        return requestedWidth

    @property
    def requestedHeight(self):
        """Get the requested height of the image.  If there is a prepard pixbuf,
        it is used, otherwise the currently set one."""
        requestedHeight = self._topMargin + self._bottomMargin
        pixbuf = self._image.get_pixbuf() if self._preparedPixbuf is None \
                 else self._preparedPixbuf
        if pixbuf is not None:
            requestedHeight += pixbuf.get_height()
        return requestedHeight

    @property
    def pixbufXOffset(self):
        """Get the X offset of the image's pixbuf."""
        return self._preparedImageXOffset

    @property
    def pixbufYOffset(self):
        """Get the Y offset of the image's pixbuf."""
        return self._preparedImageYOffset

    def clearImage(self):
        """Clear the underlying image."""
        self._image.clear()
        self.setMargins(0, 0, 0, 0)

    def preparePixbuf(self, pixbuf):
        """Prepare the given pixbuf to be displayed by the image.

        It will not be set immediately, but a resize is requested, which will
        recalculate the new offsets. Then, when the size has been allocated,
        call finalizePixbuf() to actually update it."""
        if pixbuf is not self._preparedPixbuf:
            self._preparedPixbuf = pixbuf
            self.queue_resize_no_redraw()

    def finalizePixbuf(self):
        """Finalize the prepared pixbuf."""
        if self._preparedPixbuf is not None:
            self._image.set_from_pixbuf(self._preparedPixbuf)
            self._preparedPixbuf = None
        if self._imageXOffset != self._preparedImageXOffset or \
           self._imageYOffset != self._preparedImageYOffset:
            self._imageXOffset = self._preparedImageXOffset
            self._imageYOffset = self._preparedImageYOffset
            self.move(self._image, self._imageXOffset, self._imageYOffset)

    def setMargins(self, leftMargin, rightMargin, topMargin, bottomMargin):
        """Set the margins"""
        self._leftMargin = leftMargin
        self._rightMargin = rightMargin
        self._topMargin = topMargin
        self._bottomMargin = bottomMargin

        self.queue_resize_no_redraw()

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self):
        """Get the preferred width.

        Both the minimum and the requested widths are equal to the requested
        width."""
        requestedWidth = self.requestedWidth
        return (requestedWidth, requestedWidth)

    def do_get_preferred_height(self):
        """Get the preferred height.

        Both the minimum and the requested heights are equal to the requested
        height."""
        requestedHeight = self.requestedHeight
        return (requestedHeight, requestedHeight)

    def _resized(self, _widget, allocation):
        """Called when we have been resized.

        The X- and Y-offsets of the image are recalculated based on the
        allocated with and stored as prepared offsets. finalizePixbuf() makes
        them current."""
        allocatedWidth = allocation.width
        imageXOffset = \
            self._leftMargin + (allocatedWidth - self.requestedWidth) / 2

        allocatedHeight = allocation.height
        imageYOffset = \
            self._topMargin + (allocatedHeight - self.requestedHeight) / 2

        self._preparedImageXOffset = imageXOffset
        self._preparedImageYOffset = imageYOffset

#-------------------------------------------------------------------------------

class LabelHotspot(Gtk.DrawingArea):
    """A drawing area to draw the label of a hotspot."""

    def __init__(self, typeEditor, model):
        """"Construct the label."""
        super().__init__()

        self._typeEditor = typeEditor
        self._model = model

        self._imageX = model.x
        self._imageY = model.y
        self._magnification = 1.0

        self._pangoContext = self.get_pango_context()

        self._layout = layout = Pango.Layout(self._pangoContext)
        self._font = typeEditor.gui.graphicsFontDescription.copy()

        self._highlighted = False
        self._selected = False

        self.updateLabel()

    @property
    def model(self):
        """Get the model displayed by this hotspot widget."""
        return self._model

    @property
    def imageX(self):
        """Get the X-coordinate of the widget relative to the displayed image."""
        return self._imageX

    @property
    def imageY(self):
        """Get the Y-coordinate of the widget relative to the displayed image."""
        return self._imageY

    @property
    def width(self):
        """Get the width of the hotspot widget."""
        return round((self._layoutWidth + 2*self._bgMargin + 6) *
                     self._magnification) + 2

    @property
    def height(self):
        """Get the height of the hotspot widget."""
        return round((self._layoutHeight + 2*self._bgMargin + 6) *
                     self._magnification) + 2

    @property
    def imageBoundingBox(self):
        """Get the bounding box of the hotspot relative to the image in image
        coordinates."""
        x0 = self._model.x - self._layoutWidth/2 - self._bgMargin - 3
        x1 = self._model.x + self._layoutWidth/2 + self._bgMargin + 3
        y0 = self._model.y - self._layoutHeight/2 - self._bgMargin - 3
        y1 = self._model.y + self._layoutHeight/2 + self._bgMargin + 3

        return ((x0, y0), (x1, y1))

    def cloneHotspot(self):
        """Clone the model hotspot for editing.

        The new hotspot will replace the current one. A tuple is returned
        consisting of the old and the new hotspot."""
        model = self._model
        self._model = model.clone()

        return (model, self._model)

    def restoreHotspot(self, model):
        """Restore the given hotspot model."""
        self._model = model
        self.updateLabel()

    def updateLabel(self):
        """Update the label and the font size from the model."""
        label = self._typeEditor.joystickType.getHotspotLabel(self._model)
        self._layout.set_text(label, len(label))

        self._bgMargin = max(3, self._model.fontSize * 4 / 10)
        self._bgCornerRadius = max(2, self._bgMargin * 4 / 5)

        self._font.set_size(self._model.fontSize * Pango.SCALE)
        self._font.set_weight(Pango.Weight.NORMAL)
        self._layout.set_font_description(self._font)

        (_ink, logical) = self._layout.get_extents()

        self._layoutWidth = logical.width / Pango.SCALE
        self._layoutHeight = logical.height / Pango.SCALE

        return self.updateImageCoordinates()

    def highlight(self):
        """Highlight the hotspot."""
        if not self._highlighted:
            self._highlighted = True
            self.queue_draw()

    def unhighlight(self):
        """Remove the highlight from the hotspot."""
        if self._highlighted:
            self._highlighted = False
            self.queue_draw()

    def select(self):
        """Make the widget selected."""
        if not self._selected:
            self._selected = True
            self.queue_draw()

    def deselect(self):
        """Clear the selected status of the widget."""
        if self._selected:
            self._selected = False
            self.queue_draw()

    def isWithin(self, x, y):
        """Determine if the given image coordinates are within the hotspot's
        drawn area.

        The coordinates are relative to the widget."""
        return x>=self._boundingBox[0] and x < self._boundingBox[2] and \
            y>=self._boundingBox[1] and y < self._boundingBox[3]

    def setMagnification(self, magnification):
        """Set the magnification. It also recalculates the image-relative
        coordinates and returns them as a pair."""
        self._magnification = magnification
        self._imageX = round((self._model.x - self._layoutWidth/2 - self._bgMargin - 3) * magnification) - 1
        self._imageY = round((self._model.y - self._layoutHeight/2 - self._bgMargin - 3) * magnification) - 1

        dx = (self._model.x - self._layoutWidth/2) * magnification - self._imageX
        dy = (self._model.y - self._layoutHeight/2) * magnification - self._imageY

        dx /= magnification
        dy /= magnification

        x0 = (dx - self._bgMargin) * magnification
        y0 = (dy - self._bgMargin) * magnification
        width = (self._layoutWidth + 2 * self._bgMargin) * magnification
        height = (self._layoutHeight + 2 * self._bgMargin) * magnification

        self._boundingBox = (x0, y0, x0 + width, y0 + height)

        self.queue_resize()

        return (self._imageX, self._imageY)

    def getModelCoordinatesFor(self, imageX, imageY):
        """Get the hotspot model coordinates for the given displayed
        image-relative ones."""
        x = round((imageX + 1) / self._magnification + self._layoutWidth / 2 +
                  self._bgMargin + 3)
        y = round((imageY + 1) / self._magnification + self._layoutHeight / 2 +
                  self._bgMargin + 3)

        return (x, y)

    def updateImageCoordinates(self):
        """Update the image coordinates from the model."""
        return self.setMagnification(self._magnification)

    def do_draw(self, cr):
        """Draw the dot."""
        dx = (self._model.x - self._layoutWidth/2) * self._magnification - self._imageX
        dy = (self._model.y - self._layoutHeight/2) * self._magnification - self._imageY

        dx /= self._magnification
        dy /= self._magnification

        cr.set_line_width(0.1)
        cr.scale(self._magnification, self._magnification)

        if self._model.bgColor[3]>0.0:
            bgColor = self._model.highlightBGColor if self._highlighted else \
                self._model.bgColor
            cr.set_source_rgba(*bgColor)

            cornerOverhead = self._bgMargin - self._bgCornerRadius

            cr.arc(dx - cornerOverhead, dy - cornerOverhead,
                   self._bgCornerRadius, math.pi, 3 * math.pi / 2)

            cr.rel_line_to(self._layoutWidth + 2 * cornerOverhead, 0.0)

            cr.arc(dx + self._layoutWidth + cornerOverhead, dy - cornerOverhead,
                   self._bgCornerRadius, 3 * math.pi / 2, 0.0)

            cr.rel_line_to(0.0, self._layoutHeight + 2 * cornerOverhead)

            cr.arc(dx + self._layoutWidth + cornerOverhead,
                   dy + self._layoutHeight + cornerOverhead,
                   self._bgCornerRadius, 0.0, math.pi / 2)

            cr.rel_line_to(-(self._layoutWidth + 2 * cornerOverhead), 0.0)

            cr.arc(dx + - cornerOverhead,
                   dy + self._layoutHeight + cornerOverhead,
                   self._bgCornerRadius, math.pi / 2, math.pi)

            cr.close_path()

            cr.fill()

        color = self._model.highlightColor if self._highlighted else \
            self._model.color
        cr.set_source_rgba(*color)

        cr.move_to(dx, dy)
        PangoCairo.layout_path(cr, self._layout)
        cr.stroke_preserve()

        cr.fill()

        if self._selected:
            cr.set_line_width(3.0)
            cr.set_source_rgba(*self._model.selectColor)
            cr.arc(dx - cornerOverhead, dy - cornerOverhead,
                   self._bgCornerRadius + 2, math.pi, 3 * math.pi / 2)

            cr.rel_line_to(self._layoutWidth + 2 * cornerOverhead+2.0, 0.0)

            cr.arc(dx + self._layoutWidth + cornerOverhead, dy - cornerOverhead,
                   self._bgCornerRadius + 2, 3 * math.pi / 2, 0.0)

            cr.rel_line_to(0.0, self._layoutHeight + 2 * cornerOverhead + 2)

            cr.arc(dx + self._layoutWidth + cornerOverhead,
                   dy + self._layoutHeight + cornerOverhead,
                   self._bgCornerRadius + 2, 0.0, math.pi / 2)

            cr.rel_line_to(-(self._layoutWidth + 2 * cornerOverhead + 2), 0.0)

            cr.arc(dx + - cornerOverhead,
                   dy + self._layoutHeight + cornerOverhead,
                   self._bgCornerRadius + 2, math.pi / 2, math.pi)

            cr.close_path()

            cr.stroke()

        return True

    def do_get_request_mode(self):
        """Get the request mode, which is width for height"""
        return Gtk.SizeRequestMode.WIDTH_FOR_HEIGHT

    def do_get_preferred_width(self):
        """Get the preferred width.

        The minimum and the preferred values are both the magnified diameter
        plus 2 to account for the subpixel shifting."""
        width = self.width
        return (width, width)

    def do_get_preferred_height(self):
        """Get the preferred width.

        The minimum and the preferred values are both the magnified diameter
        plus 2 to account for the subpixel shifting."""
        height = self.height
        self.queue_draw()
        return (height, height)

#-------------------------------------------------------------------------------

class HotspotEditor(Gtk.Dialog):
    """An editor dialog for a new or existing hotspot."""
    # Response type: delete the hotspot
    RESPONSE_DELETE = 1

    @staticmethod
    def rgba2color(rgba):
        """Convert the given RGBA color to a color tuple."""
        return (rgba.red, rgba.green, rgba.blue, rgba.alpha)

    def __init__(self, typeEditor, title, hotspotWidget, edit = False):
        """Construct the editor for the given hotspot widget."""
        super().__init__(use_header_bar = True)

        self._typeEditor = typeEditor
        self._hotspotWidget = hotspotWidget

        hotspot = hotspotWidget.model

        self.set_title(title)

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        button = self.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

        if edit:
            button = self.add_button(Gtk.STOCK_DELETE, HotspotEditor.RESPONSE_DELETE)
            button.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)

        contentArea = self.get_content_area()
        contentArea.set_margin_start(8)
        contentArea.set_margin_end(8)

        grid = self._grid = Gtk.Grid.new()
        grid.set_column_spacing(16)
        grid.set_row_spacing(8)

        label = Gtk.Label(_("Co_ntrol:"))
        label.set_use_underline(True)
        label.props.halign = Gtk.Align.START
        grid.attach(label, 0, 0, 1, 1)

        self._controls = controls = Gtk.ListStore(str, str, int, int)
        index = 0
        activeIndex = 0
        joystickType = typeEditor.joystickType
        for key in joystickType.keys:
            controls.append([key.name, key.displayName,
                             Hotspot.CONTROL_TYPE_KEY, key.code])
            if hotspot.controlType==Hotspot.CONTROL_TYPE_KEY and \
               hotspot.controlCode==key.code:
                activeIndex = index
            index += 1
        for axis in joystickType.axes:
            controls.append([axis.name, axis.displayName,
                             Hotspot.CONTROL_TYPE_AXIS, axis.code])
            if hotspot.controlType==Hotspot.CONTROL_TYPE_AXIS and \
               hotspot.controlCode==axis.code:
                activeIndex = index
            index += 1

        controlSelector = self._controlSelector = \
            Gtk.ComboBox.new_with_model(controls)
        controlSelector.connect("changed", self._controlChanged)

        displayNameRenderer = Gtk.CellRendererText.new()
        controlSelector.pack_start(displayNameRenderer, True)
        controlSelector.add_attribute(displayNameRenderer, "text", 1)

        nameRenderer = Gtk.CellRendererText.new()
        controlSelector.pack_start(nameRenderer, True)
        controlSelector.add_attribute(nameRenderer, "text", 0)

        controlSelector.set_active(activeIndex)
        label.set_mnemonic_widget(controlSelector)

        grid.attach(controlSelector, 1, 0, 1, 1)

        label = Gtk.Label(_("_Font:"))
        label.set_use_underline(True)
        label.props.halign = Gtk.Align.START
        grid.attach(label, 0, 1, 1, 1)

        gui = typeEditor.gui
        button = self._fontButton = Gtk.FontButton()
        fontDescription = gui.graphicsFontDescription.copy()
        fontDescription.set_size(hotspot.fontSize * Pango.SCALE)
        button.set_font_desc(fontDescription)
        button.set_filter_func(self._fontFilter, gui)
        button.connect("font-set", self._fontSet)

        label.set_mnemonic_widget(button)
        grid.attach(button, 1, 1, 1, 1)

        colorGrid = self._colorGrid = Gtk.Grid()
        colorGrid.set_column_homogeneous(True)
        colorGrid.set_row_spacing(4)
        colorGrid.set_column_spacing(8)
        colorGrid.set_margin_end(8)
        colorGrid.set_margin_bottom(8)

        label = Gtk.Label(_("Text"))
        label.props.halign = Gtk.Align.CENTER
        colorGrid.attach(label, 1, 0, 1, 1)

        label = Gtk.Label(_("Background"))
        label.props.halign = Gtk.Align.CENTER
        colorGrid.attach(label, 2, 0, 1, 1)

        self._normalColorButton = normalColorButton = \
            Gtk.RadioButton.new_with_label(None, _("Normal"))
        colorGrid.attach(normalColorButton, 0, 1, 1, 1)
        normalColorButton.connect("toggled", self._colorSetChanged)

        self._highlightedColorButton = highlightedColorButton = \
            Gtk.RadioButton.new_with_label_from_widget(normalColorButton,
                                                       _("Highlighted"))
        highlightedColorButton.connect("toggled", self._colorSetChanged)
        colorGrid.attach(highlightedColorButton, 0, 2, 1, 1)

        colorButton = self._colorButton = Gtk.ColorButton()
        colorButton.set_use_alpha(True)
        colorButton.set_rgba(Gdk.RGBA(*hotspot.color))
        colorButton.connect("color-set", self._colorChanged)
        colorGrid.attach(colorButton, 1, 1, 1, 1)

        bgColorButton = self._bgColorButton = Gtk.ColorButton()
        bgColorButton.set_use_alpha(True)
        bgColorButton.set_rgba(Gdk.RGBA(*hotspot.bgColor))
        bgColorButton.connect("color-set", self._colorChanged)
        colorGrid.attach(bgColorButton, 2, 1, 1, 1)

        highlightColorButton = self._highlightColorButton = Gtk.ColorButton()
        highlightColorButton.set_use_alpha(True)
        highlightColorButton.set_rgba(Gdk.RGBA(*hotspot.highlightColor))
        highlightColorButton.connect("color-set", self._colorChanged)
        colorGrid.attach(highlightColorButton, 1, 2, 1, 1)

        highlightBGColorButton = self._highlightBGColorButton = Gtk.ColorButton()
        highlightBGColorButton.set_use_alpha(True)
        highlightBGColorButton.set_rgba(Gdk.RGBA(*hotspot.highlightBGColor))
        highlightBGColorButton.connect("color-set", self._colorChanged)
        colorGrid.attach(highlightBGColorButton, 2, 2, 1, 1)

        colorGrid.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL),
                         0, 3, 3, 1)

        label = Gtk.Label(_("Selection color"))
        colorGrid.attach(label, 0, 4, 1, 1)

        selectColorButton = self._selectColorButton = Gtk.ColorButton()
        selectColorButton.set_use_alpha(True)
        selectColorButton.set_rgba(Gdk.RGBA(*hotspot.selectColor))
        selectColorButton.connect("color-set", self._colorChanged)
        colorGrid.attach(selectColorButton, 1, 4, 1, 1)


        colorFrame = self._colorFrame = Gtk.Frame.new(_("Colors"))
        colorFrame.add(colorGrid)

        grid.attach(colorFrame, 0, 2, 2, 1)

        contentArea.pack_start(grid, True, True, 8)

        actionArea = self.get_action_area()
        actionArea.set_margin_top(16)
        actionArea.set_margin_bottom(4)

        self.show_all()

    def _fontFilter(self, fontFamily, fontFace, gui):
        return fontFace.describe().equal(gui.graphicsFontDescription)

    def _controlChanged(self, controlSelector):
        """Called when a different control has been selected."""
        i = controlSelector.get_active_iter()
        if i is not None:
            hotspot = self._hotspotWidget.model
            hotspot.controlType = self._controls.get_value(i, 2)
            hotspot.controlCode = self._controls.get_value(i, 3)
            (x, y) = self._hotspotWidget.updateLabel()
            self._typeEditor._imageFixed.move(self._hotspotWidget,
                                              self._typeEditor._pixbufXOffset + x,
                                              self._typeEditor._pixbufYOffset + y)


    def _fontSet(self, fontButton):
        """Called when a font has been selected."""
        hotspot = self._hotspotWidget.model
        hotspot.fontSize = fontButton.get_font_size() / Pango.SCALE
        (x, y) = self._hotspotWidget.updateLabel()
        self._typeEditor._imageFixed.move(self._hotspotWidget,
                                          self._typeEditor._pixbufXOffset + x,
                                          self._typeEditor._pixbufYOffset + y)

    def _colorSetChanged(self, button):
        """Called when the color set selection has changed."""
        if button.get_active():
            if button is self._normalColorButton:
                self._hotspotWidget.unhighlight()
            else:
                self._hotspotWidget.highlight()

    def _colorChanged(self, button):
        """Called when one of the colours has changed."""
        color = button.get_rgba()
        hotspot = self._hotspotWidget.model
        redraw = False
        if button is self._colorButton:
            hotspot.color = HotspotEditor.rgba2color(color)
            redraw = self._normalColorButton.get_active()
        elif button is self._bgColorButton:
            hotspot.bgColor = HotspotEditor.rgba2color(color)
            redraw = self._normalColorButton.get_active()
        elif button is self._highlightColorButton:
            hotspot.highlightColor = HotspotEditor.rgba2color(color)
            redraw = self._highlightedColorButton.get_active()
        elif button is self._highlightBGColorButton:
            hotspot.highlightBGColor = HotspotEditor.rgba2color(color)
            redraw = self._highlightedColorButton.get_active()
        elif button is self._selectColorButton:
            hotspot.selectColor = HotspotEditor.rgba2color(color)
            redraw = True

        if redraw:
            self._hotspotWidget.queue_draw()

#-------------------------------------------------------------------------------

class TypeEditorWindow(Gtk.ApplicationWindow):
    """The type editor window."""
    def __init__(self, gui, joystickType, *args, **kwargs):
        """Construct the window."""
        super().__init__(*args, **kwargs)

        self._gui = gui
        self._joystickType = joystickType

        self._views = Gtk.ListStore(str, GdkPixbuf.Pixbuf, object)
        hasView = False
        for view in joystickType.views:
            hasView = True
            self._views.append([view.name,
                                self._findViewImage(view.imageFileName),
                                view])

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

        self._viewSelector = Gtk.ComboBox.new_with_model(self._views)
        viewNameRenderer = self._viewNameRenderer = Gtk.CellRendererText.new()
        self._viewSelector.pack_start(viewNameRenderer, True)
        self._viewSelector.add_attribute(viewNameRenderer, "text", 0)
        self._viewSelector.connect("changed", self._viewChanged)
        self._viewSelector.set_size_request(150, -1)

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

        self._magnification = 1.0

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        self._imageOverlay = imageOverlay = Gtk.Overlay()

        self._image = PaddedImage()
        self._image.connect("size-allocate", self._imageResized)

        imageOverlay.add(self._image)
        imageOverlay.connect("button-press-event",
                             self._overlayButtonEvent);
        imageOverlay.connect("button-release-event",
                             self._overlayButtonEvent);
        imageOverlay.connect("motion-notify-event",
                             self._overlayMotionEvent);
        imageOverlay.connect("scroll-event",
                             self._overlayScrollEvent);

        self._imageFixed = Gtk.Fixed()
        imageOverlay.add_overlay(self._imageFixed)

        self._hotspotWidgets = []
        self._draggedHotspot = None
        self._mouseHighlightedHotspotWidget = None

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)
        scrolledWindow.add(imageOverlay)

        paned.pack1(scrolledWindow, True, True)

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        (keysFrame, self._keysView) = \
            self._createControlListView(_("Buttons"), self._keys)
        vbox.pack_start(keysFrame, True, True, 4)

        (axesFrame, self._axesView) = \
            self._createControlListView(_("Axes"), self._axes)
        vbox.pack_start(axesFrame, True, True, 4)

        vbox.set_margin_left(8)

        paned.pack2(vbox, False, False)

        paned.set_wide_handle(True)
        paned.set_position(900)

        self.add(paned)

        gui.addTypeEditor(joystickType, self)

        self.set_titlebar(headerBar)

        self.show_all()

        window = self._imageFixed.get_window()
        window.set_events(window.get_events() |
                          Gdk.EventMask.BUTTON_PRESS_MASK |
                          Gdk.EventMask.BUTTON_RELEASE_MASK |
                          Gdk.EventMask.POINTER_MOTION_MASK |
                          Gdk.EventMask.SCROLL_MASK |
                          Gdk.EventMask.SMOOTH_SCROLL_MASK)

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
        i = self._viewSelector.get_active_iter()
        return None if i is None else self._views.get_value(i, 2)


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
        code = model[path][0]
        if model is self._keys:
            self._joystickType.setKeyDisplayName(code, text)
            self._updateHotspotLabel(Hotspot.CONTROL_TYPE_KEY, code)
        else:
            self._joystickType.setAxisDisplayName(code, text)
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

    def _viewChanged(self, comboBox):
        """Called when the view has changed."""
        for hotspotObject in self._hotspotWidgets:
            self._imageFixed.remove(hotspotObject)
        self._hotspotWidgets = []

        view = self._view
        if view is not None:
            i = self._viewSelector.get_active_iter()
            pixbuf = self._views.get_value(i, 1)
            self._image.preparePixbuf(pixbuf)

            for hotspot in view.hotspots:
                if hotspot.type==Hotspot.TYPE_LABEL:
                    h = LabelHotspot(self, hotspot)
                    self._hotspotWidgets.append(h)
                    self._imageFixed.put(h, hotspot.x, hotspot.y)
            self._imageFixed.show_all()
        else:
            self._image.clearImage()

        self._resizeImage()

    def _updateHotspotPositions(self):
        """Update the hotspot positions ."""
        if self._view is None:
            return

        self._pixbufXOffset = pixbufXOffset = self._image.pixbufXOffset
        self._pixbufYOffset = pixbufYOffset = self._image.pixbufYOffset

        for hotspotObject in self._hotspotWidgets:
            (x, y) = hotspotObject.setMagnification(self._magnification)
            self._imageFixed.move(hotspotObject,
                                  pixbufXOffset + x, pixbufYOffset + y)

    def _resizeImage(self):
        """Calculate a new requested size for the image, and if different from
        the current one, request a resize of the image."""
        i = self._viewSelector.get_active_iter()
        if i is None:
            return

        pixbuf = self._views.get_value(i, 1)

        pixbufWidth = pixbuf.get_width()
        pixbufHeight = pixbuf.get_height()

        minX = 0
        maxX = pixbufWidth - 1
        minY = 0
        maxY = pixbufHeight - 1

        for hotspotWidget in self._hotspotWidgets:
            ((x0, y0), (x1, y1)) = hotspotWidget.imageBoundingBox
            minX = min(minX, x0)
            maxX = max(maxX, x1)
            minY = min(minY, y0)
            maxY = max(maxY, y1)

        magnification = self._magnification

        self._image.setMargins((100 - minX) * magnification,
                               (maxX + 100 - pixbufWidth) * magnification,
                               (100 - minY) * magnification,
                               (maxY + 100 - pixbufHeight) * magnification)

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

        numViews = self._views.iter_n_children(None)
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

        view = self._joystickType.newView(viewName,  imageFileName)
        self._views.append([view.name,
                            self._findViewImage(imageFileName),
                            view])

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

    def _findViewImage(self, imageFileName):
        """Search for the image file with the given name in the possible data
        directories.

        Return the Pixbuf for the image, if found, None otherwise."""
        for (directoryPath, _type) in self._joystickType.deviceDirectories:
            imagePath = os.path.join(directoryPath, imageFileName)
            if os.path.isfile(imagePath):
                try:
                    return GdkPixbuf.Pixbuf.new_from_file(imagePath)
                except Exception as e:
                    print("Failed to image from '%s'" % (imagePath,))

    def _editViewName(self, button):
        """Called when the current view's name should be edited."""
        i = self._viewSelector.get_active_iter()

        origViewName = self._views.get_value(i, 0)
        view = self._views.get_value(i, 2)

        viewName = self._queryViewName(viewName = origViewName, view = view)
        if viewName:
            self._joystickType.changeViewName(origViewName, viewName)
            self._views.set_value(i, 0, viewName)

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
        i = self._viewSelector.get_active_iter()

        viewName = self._views.get_value(i, 0)

        if yesNoDialog(self,
                       _("Are you sure to remove view '{0}'?").format(viewName)):
            toActivate = self._views.iter_next(i)
            if toActivate is None:
                toActivate = self._views.iter_previous(i)

            if toActivate is None:
                self._editViewNameButton.set_sensitive(False)
                self._removeViewButton.set_sensitive(False)
            else:
                self._viewSelector.set_active_iter(toActivate)

            view = self._views.get_value(i, 2)
            self._joystickType.deleteView(viewName)
            self._views.remove(i)

    def _imageResized(self, image, rectangle):
        """Called when the image is resized.

        It enqueues a call to _redrawImage(), as such operations cannot be
        called from this event handler.
        """
        GLib.idle_add(self._redrawImage, None)

    def _redrawImage(self, *args):
        """Redraw the image by finalizing the pixbuf and updating the hotspot
        positions."""
        self._image.finalizePixbuf()
        self._updateHotspotPositions()

    def _findHotspotWidgetAt(self, widget, eventX, eventY):
        """Find the hotspot for the given event coordinates."""
        for hotspotWidget in self._hotspotWidgets:
            (x, y) = widget.translate_coordinates(hotspotWidget, eventX, eventY)
            if hotspotWidget.isWithin(x, y):
                return hotspotWidget

    def _overlayButtonEvent(self, overlay, event):
        """Handle mouse button press and release events."""
        if event.button==1:
            if event.type==Gdk.EventType.BUTTON_RELEASE:
                if self._draggedHotspot is None:
                    self._createHotspot(event.x, event.y)
                elif self._draggedHotspot[5]:
                        hotspot = self._draggedHotspot[0]
                        (x, y) = hotspot.getModelCoordinatesFor(self._draggedHotspot[3],
                                                                self._draggedHotspot[4])
                        self._joystickType.updateViewHotspotCoordinates(hotspot.model,
                                                                        x, y)
                        (x, y) = hotspot.updateImageCoordinates()
                        self._imageFixed.move(hotspot,
                                              self._pixbufXOffset + x,
                                              self._pixbufYOffset + y)
                        self._resizeImage()
                else:
                    hotspotWidget = self._findHotspotWidgetAt(overlay, event.x, event.y)
                    if hotspotWidget is not None:
                        self._editHotspot(hotspotWidget)

                self._draggedHotspot = None
            else:
                hotspotWidget = self._findHotspotWidgetAt(overlay, event.x, event.y)
                if hotspotWidget is not None:
                    self._draggedHotspot = [hotspotWidget, event.x, event.y,
                                            hotspotWidget.imageX,
                                            hotspotWidget.imageY,
                                            False]

    def _overlayMotionEvent(self, overlay, event):
        """Handle mouse motion events in the image."""
        if self._draggedHotspot is None:
            hotspotWidget = self._findHotspotWidgetAt(overlay, event.x, event.y)
            if self._mouseHighlightedHotspotWidget is not hotspotWidget:
                if self._mouseHighlightedHotspotWidget is not None:
                    self._mouseHighlightedHotspotWidget.unhighlight()

                self._mouseHighlightedHotspotWidget = hotspotWidget
                if hotspotWidget is not None:
                    hotspotWidget.highlight()
        else:
            hotspotWidget = self._draggedHotspot[0]
            x = round(hotspotWidget.imageX + event.x - self._draggedHotspot[1])
            y = round(hotspotWidget.imageY + event.y - self._draggedHotspot[2])

            self._imageFixed.move(hotspotWidget,
                                  self._pixbufXOffset + x,
                                  self._pixbufYOffset + y)
            self._draggedHotspot[3] = x
            self._draggedHotspot[4] = y
            self._draggedHotspot[5] = True

    def _overlayScrollEvent(self, overlay, event):
        """Called when a scroll event is received.

        When the Control key is pressed, and the scroll direction is up or
        down, the image will be zoomed in or out."""
        i = self._viewSelector.get_active_iter()
        if event.state==Gdk.ModifierType.CONTROL_MASK and i is not None:
            delta = 0.0
            if event.direction==Gdk.ScrollDirection.UP:
                delta = 1.0
            elif event.direction==Gdk.ScrollDirection.DOWN:
                delta = -1.0
            elif event.direction==Gdk.ScrollDirection.SMOOTH:
                delta = -event.delta_y

            if delta!=0.0 and (delta<0.0 or self._magnification<1.0):
                self._magnification += self._magnification * delta / 10.0
                self._magnification = min(self._magnification, 1.0)

                pixbuf = self._views.get_value(i, 1)
                if abs(self._magnification-1)<1e-2:
                    self._magnification = 1.0
                else:
                    origWidth = pixbuf.get_width()
                    width = round(origWidth * self._magnification)
                    self._magnification = width / origWidth
                    pixbuf = pixbuf.scale_simple(width,
                                                 round(pixbuf.get_height() *
                                                       self._magnification),
                                                 GdkPixbuf.InterpType.BILINEAR)

                self._image.preparePixbuf(pixbuf)
                self._resizeImage()

            return True
        else:
            return False

    def _createHotspot(self, eventX, eventY):
        """Create a hotspot at the given mouse event coordinates."""
        x = round((eventX - self._pixbufXOffset) / self._magnification)
        y = round((eventY - self._pixbufYOffset) / self._magnification)

        view = self._view
        lastHotspot = view.lastHotspot

        controlType = None
        controlCode = None
        if lastHotspot is None:
            fontSize = 12

            color = highlightColor = (1.0, 1.0, 1.0, 1.0)
            bgColor = (0.2, 0.4, 0.64, 0.75)
            highlightBGColor = (0.45, 0.62, 0.81, 0.8)
            selectColor = (0.91, 0.33, 0.13, 1.0)
        else:
            afterPrevious = False
            if lastHotspot.controlType == Hotspot.CONTROL_TYPE_KEY:
                for key in self._joystickType.iterKeys:
                    if afterPrevious:
                        controlType = Hotspot.CONTROL_TYPE_KEY
                        controlCode = key.code
                        afterPrevious = False
                        break
                    elif key.code==lastHotspot.controlCode:
                        afterPrevious = True

            if controlType is None:
                for axis in self._joystickType.iterAxes:
                    if afterPrevious:
                        controlType = Hotspot.CONTROL_TYPE_AXIS
                        controlCode = axis.code
                        afterPrevious = False
                        break
                    elif axis.code==lastHotspot.controlCode:
                        afterPrevious = True

            fontSize = lastHotspot.fontSize

            color = lastHotspot.color
            bgColor = lastHotspot.bgColor
            highlightColor = lastHotspot.highlightColor
            highlightBGColor = lastHotspot.highlightBGColor
            selectColor = lastHotspot.selectColor

        if controlType is None:
            firstKey = self._joystickType.firstKey
            if firstKey is None:
                controlType = Hotspot.CONTROL_TYPE_AXIS
                controlCode = self._joystickType.firstAxis.code
            else:
                controlType = Hotspot.CONTROL_TYPE_KEY
                controlCode = firstKey.code

        hotspot = jsprog.device.LabelHotspot(x, y,
                                             controlType = controlType,
                                             controlCode = controlCode,
                                             fontSize = 12,
                                             color = color,
                                             bgColor = bgColor,
                                             highlightColor = highlightColor,
                                             highlightBGColor =
                                             highlightBGColor,
                                             selectColor = selectColor)

        hotspotWidget = LabelHotspot(self, hotspot)
        hotspotWidget.select()
        hotspotWidget.show()
        self._hotspotWidgets.append(hotspotWidget)
        (x, y) = hotspotWidget.setMagnification(self._magnification)
        self._imageFixed.put(hotspotWidget,
                             self._pixbufXOffset + x, self._pixbufYOffset + y)

        dialog = HotspotEditor(self, ("Create hotspot"), hotspotWidget)

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response==Gtk.ResponseType.OK:
            self._joystickType.addViewHotspot(view, hotspot)
            hotspotWidget.unhighlight()
            hotspotWidget.deselect()
            self._resizeImage()
        else:
            self._imageFixed.remove(hotspotWidget)
            del self._hotspotWidgets[-1]

    def _editHotspot(self, hotspotWidget):
        """Edit the given hotspot."""
        hotspotWidget.unhighlight()
        hotspotWidget.select()

        (origHotspot, newHotspot) = hotspotWidget.cloneHotspot()

        dialog = HotspotEditor(self, ("Edit hotspot"), hotspotWidget,
                               edit = True)

        dialog.show_all()
        while True:
            response = dialog.run()

            if response==Gtk.ResponseType.OK:
                hotspotWidget.deselect()
                hotspotWidget.unhighlight()
                self._joystickType.modifyViewHotspot(self._view,
                                                     origHotspot, newHotspot)
                self._resizeImage()
                break
            elif response==HotspotEditor.RESPONSE_DELETE:
                if yesNoDialog(self, _("Are you sure to delete the hotspot?")):
                    self._joystickType.removeViewHotspot(self._view, origHotspot)
                    self._imageFixed.remove(hotspotWidget)
                    self._hotspotWidgets.remove(hotspotWidget)
                    self._resizeImage()
                    break
            else:
                hotspotWidget.deselect()
                hotspotWidget.unhighlight()
                hotspotWidget.restoreHotspot(origHotspot)
                break

        dialog.destroy()

    def _updateHotspotLabel(self, controlType, controlCode):
        """Update the label of the hotspot with the given control type and
        code."""
        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.model
            if hotspot.controlType==controlType and \
               hotspot.controlCode==controlCode:
                (x, y) = hotspotWidget.updateLabel()
                self._imageFixed.move(hotspotWidget,
                                      self._pixbufXOffset + x,
                                      self._pixbufYOffset + y)
                self._resizeImage()
