# Joystick viewer widget

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from jsprog.device import Hotspot

import math

#-------------------------------------------------------------------------------

DisplayDotInfo = namedtuple("DisplayDotInfo", "xc yc radius")

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

class HotspotWidget(Gtk.DrawingArea):
    """A widget to draw a hotspot."""

    # The width of the selection border
    SELECTION_BORDER_WIDTH = 3

    # The minimal background margin
    MIN_BG_MARGIN = 3

    # The minimal background corner radius
    MIN_BG_CORNER_RADIUS = 2

    @staticmethod
    def getColorBetween(color0, color100, percentage):
        """Get the color between the given colors corresponding to the given
        percentage."""
        (red0, green0, blue0, alpha0) = color0
        (red100, green100, blue100, alpha100) = color100

        return (red0 + (red100 - red0) * percentage / 100,
                green0 + (green100 - green0) * percentage / 100,
                blue0 + (blue100 - blue0) * percentage / 100,
                alpha0 + (alpha100 - alpha0) * percentage / 100)

    def __init__(self, typeEditor, hotspot):
        """"Construct the hotspot widget for the given hotspot."""
        super().__init__()

        self._typeEditor = typeEditor
        self._hotspot = hotspot

        self._imageX = hotspot.x
        self._imageY = hotspot.y
        self._magnification = 1.0

        self._pangoContext = self.get_pango_context()

        self._layout = layout = Pango.Layout(self._pangoContext)
        self._font = typeEditor.gui.graphicsFontDescription.copy()

        self._highlightPercentage = 0
        self._highlightNegated = False
        self._highlightForced = False
        self._highlightInhibited = False
        self._selected = False

        self.updateLabel()

    @property
    def hotspot(self):
        """Get the hotspot displayed by this hotspot widget."""
        return self._hotspot

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
        box = self._imageBoundingBox
        return round((box.x1 - box.x0)*self._magnification) + 2

    @property
    def height(self):
        """Get the height of the hotspot widget."""
        box = self._imageBoundingBox
        return round((box.y1 - box.y0)*self._magnification) + 2

    @property
    def labelBoundingBox(self):
        """Get the bounding box of the label in image coordinates."""
        hotspot = self._hotspot

        return BoundingBox(hotspot.x - self._layoutWidth/2 - self._bgMargin,
                           hotspot.y - self._layoutHeight/2 - self._bgMargin,
                           hotspot.x + self._layoutWidth/2 + self._bgMargin,
                           hotspot.y + self._layoutHeight/2 + self._bgMargin)

    @property
    def dotBoundingBox(self):
        """Get the bounding box of the dot in image coordinates.

        If there is no dot, None is returned."""
        dot = self._hotspot.dot

        if dot is not None:
            return BoundingBox(dot.x - dot.radius, dot.y - dot.radius,
                               dot.x + dot.radius, dot.y + dot.radius)

    @property
    def imageBoundingBox(self):
        """Get the bounding box of the hotspot relative to the image in image
        coordinates."""
        return self._imageBoundingBox

    @property
    def _effectiveHighlightPercentage(self):
        """Get the effective highlight percentage according to the current
        state."""
        highlightPercentage = 0

        if self._highlightForced:
            highlightPercentage = 100
        elif self._highlightInhibited:
            highlightPercentage = 0
        else:
            highlightPercentage = self._highlightPercentage
            if self._highlightNegated:
                highlightPercentage = 100 - highlightPercentage

        return highlightPercentage

    def cloneHotspot(self):
        """Clone the hotspot for editing.

        The new hotspot will replace the current one. A tuple is returned
        consisting of the old and the new hotspot."""
        hotspot = self._hotspot
        self._hotspot = hotspot.clone()

        return (hotspot, self._hotspot)

    def restoreHotspot(self, hotspot):
        """Restore the given hotspot."""
        self._hotspot = hotspot
        self.updateLabel()

    def updateLabel(self):
        """Update the label and the font size from the hotspot."""
        hotspot = self._hotspot

        label = self._typeEditor.joystickType.getHotspotLabel(hotspot)
        self._layout.set_text(label, len(label))

        self._bgMargin = max(HotspotWidget.MIN_BG_MARGIN,
                             hotspot.fontSize * 4 / 10)
        self._bgCornerRadius = max(HotspotWidget.MIN_BG_CORNER_RADIUS,
                                   self._bgMargin * 4 / 5)

        self._font.set_size(hotspot.fontSize * Pango.SCALE)
        self._font.set_weight(Pango.Weight.NORMAL)
        self._layout.set_font_description(self._font)

        (_ink, logical) = self._layout.get_extents()

        self._layoutWidth = logical.width / Pango.SCALE
        self._layoutHeight = logical.height / Pango.SCALE

        self._recalculateImageBoundingBox()

        return self.updateImageCoordinates()

    def highlight(self, percentage = 100):
        """Highlight the hotspot."""
        if self._highlightPercentage != percentage:
            self._highlightPercentage = percentage
            self.queue_draw()

    def unhighlight(self):
        """Remove the highlight from the hotspot."""
        self.highlight(percentage=0)

    def negateHighlight(self):
        """Negate the highlight of the hotspot."""
        if not self._highlightNegated:
            self._highlightNegated = True
            self.queue_draw()

    def unnegateHighlight(self):
        """Remove the negation the highlight of the hotspot."""
        if self._highlightNegated:
            self._highlightNegated = False
            self.queue_draw()

    def forceHighlight(self):
        """Make the highlight of the hotspot forced."""
        if not self._highlightForced:
            self._highlightForced = True
            self._highlightInhibited = False
            self.queue_draw()

    def clearForceHighlight(self):
        """Clear the forcing of the highlight."""
        if self._highlightForced:
            self._highlightForced = False
            self.queue_draw()

    def inhibitHighlight(self):
        """Inhibit the highlight of the hotspot."""
        if not self._highlightInhibited:
            self._highlightForced = False
            self._highlightInhibited = True
            self.queue_draw()

    def clearInhibitHighlight(self):
        """Clear the inhibiting of the highlight."""
        if self._highlightInhibited:
            self._highlightInhibited = False
            self.queue_draw()

    def invertHighlight(self):
        """Invert the highlight of the hotspot."""
        if not self._highlightInverted:
            self._highlightInverted = True
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
        return \
            x >= self._displayBoundingBox.x0 and \
            x <= self._displayBoundingBox.x1 and \
            y >= self._displayBoundingBox.y0 and \
            y <= self._displayBoundingBox.y1

    def isWithinDot(self, x, y):
        """Determine if the given image coordinates are within the dot's drawn
        area, if there is a dot."""
        displayDotInfo = self._displayDotInfo

        if displayDotInfo is None:
            return False
        else:
            dx = x - displayDotInfo.xc
            dy = y - displayDotInfo.yc
            return math.sqrt(dx*dx + dy*dy)<=displayDotInfo.radius

    def setMagnification(self, magnification):
        """Set the magnification. It also recalculates the image-relative
        coordinates and returns them as a pair."""
        self._magnification = magnification

        boundingBox = self._imageBoundingBox

        self._imageX = round(boundingBox.x0 * magnification) - 1
        self._imageY = round(boundingBox.y0 * magnification) - 1

        labelBoundingBox = self.labelBoundingBox

        self._displayBoundingBox = \
            BoundingBox(labelBoundingBox.x0 * magnification - self._imageX,
                        labelBoundingBox.y0 * magnification - self._imageY,
                        labelBoundingBox.x1 * magnification - self._imageX,
                        labelBoundingBox.y1 * magnification - self._imageY)

        dot = self._hotspot.dot

        if dot is None:
            self._displayDotInfo = None
        else:
            self._displayDotInfo = \
                DisplayDotInfo(dot.x * self._magnification - self._imageX,
                               dot.y * self._magnification - self._imageY,
                               dot.radius * self._magnification)

        self.queue_resize()

        return (self._imageX, self._imageY)

    def updateImageCoordinates(self):
        """Update the image coordinates from the hotspot."""
        self._recalculateImageBoundingBox()
        return self.setMagnification(self._magnification)

    def do_draw(self, cr):
        """Draw the hotspot."""
        cr.push_group()

        cr.save()
        self._drawLine(cr)
        cr.restore()

        cr.save()
        self._drawLabel(cr)
        cr.restore()

        cr.save()
        self._drawDot(cr)
        cr.restore()

        cr.pop_group_to_source()
        cr.paint()

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

    def _recalculateImageBoundingBox(self):
        """Recalculate the image-relative bounding box."""
        boundingBox = self.labelBoundingBox
        boundingBox.extend(HotspotWidget.SELECTION_BORDER_WIDTH)

        boundingBox.merge(self.dotBoundingBox)

        self._imageBoundingBox = boundingBox

    def _drawLine(self, cr):
        """Draw the line of the hotspot, if it has a dot."""
        hotspot = self._hotspot

        dot = hotspot.dot
        if dot is None:
            return

        (labelX, labelY) = self._img2widget(hotspot.x, hotspot.y)
        (dotX, dotY) = self._img2widget(dot.x, dot.y)

        cr.set_line_width(dot.lineWidth)
        cr.scale(self._magnification, self._magnification)

        color = HotspotWidget.getColorBetween(dot.lineColor,
                                              dot.lineHighlightColor,
                                              self._effectiveHighlightPercentage)
        cr.set_source_rgba(*color)

        # FIXME: These two calls here prevent certain artifacts when the
        # widgets of one or more hotspots overlap. Perhaps a bug in Cairo?
        cr.arc(dotX, dotY, dot.radius, 0.0, 2*math.pi)
        cr.fill()

        cr.move_to(labelX, labelY)
        cr.line_to(dotX, dotY)
        cr.stroke()

    def _drawLabelOutline(self, cr, dx, dy,
                          expandLinear = 0.0, expandFactorial = 1.0):
        """Draw the label's outline with the given linear and/or factorial
        expansions."""
        cornerOverhead = (self._bgMargin - self._bgCornerRadius) * expandFactorial
        cornerRadius = (self._bgCornerRadius + expandLinear) * expandFactorial

        cr.arc(dx - cornerOverhead, dy - cornerOverhead,
               cornerRadius, math.pi, 3 * math.pi / 2)

        cr.rel_line_to(self._layoutWidth + 2 * cornerOverhead, 0.0)

        cr.arc(dx + self._layoutWidth + cornerOverhead, dy - cornerOverhead,
               cornerRadius, 3 * math.pi / 2, 0.0)

        cr.rel_line_to(0.0, self._layoutHeight + 2 * cornerOverhead)

        cr.arc(dx + self._layoutWidth + cornerOverhead,
               dy + self._layoutHeight + cornerOverhead,
               cornerRadius, 0.0, math.pi / 2)

        cr.rel_line_to(-(self._layoutWidth + 2 * cornerOverhead), 0.0)

        cr.arc(dx + - cornerOverhead,
               dy + self._layoutHeight + cornerOverhead,
               cornerRadius, math.pi / 2, math.pi)

        cr.close_path()

    def _drawLabel(self, cr):
        """Draw the label of the hotspot."""
        hotspot = self._hotspot

        (dx, dy) = self._img2widget(hotspot.x - self._layoutWidth/2,
                                    hotspot.y - self._layoutHeight/2)

        cr.set_line_width(0.1)
        cr.scale(self._magnification, self._magnification)

        if hotspot.dot is not None:
            cr.save()
            cr.set_operator(cairo.Operator.CLEAR)
            self._drawLabelOutline(cr, dx, dy,
                                   expandLinear = 2 if self._selected else 0,
                                   expandFactorial =
                                   1.4 if self._selected else 1.3)
            cr.fill()

            cr.restore()

        highlightPercentage = self._effectiveHighlightPercentage

        if hotspot.bgColor[3]>0.0:
            bgColor = HotspotWidget.getColorBetween(hotspot.bgColor,
                                                    hotspot.highlightBGColor,
                                                    highlightPercentage)
            cr.set_source_rgba(*bgColor)

            self._drawLabelOutline(cr, dx, dy)

            cr.fill()

        color = HotspotWidget.getColorBetween(hotspot.color,
                                              hotspot.highlightColor,
                                              highlightPercentage)
        cr.set_source_rgba(*color)

        cr.move_to(dx, dy)
        PangoCairo.layout_path(cr, self._layout)
        cr.stroke_preserve()

        cr.fill()

        if self._selected:
            cr.set_line_width(HotspotWidget.SELECTION_BORDER_WIDTH)
            cr.set_source_rgba(*hotspot.selectColor)

            self._drawLabelOutline(cr, dx, dy, expandLinear = 2)

            cr.stroke()

    def _drawDot(self, cr):
        """Draw the dot of the hotspot if any, including the line connecting
        the label and the dot."""
        dot = self._hotspot.dot
        if dot is None:
            return

        (dx, dy) = self._img2widget(dot.x, dot.y)

        cr.scale(self._magnification, self._magnification)

        cr.set_operator(cairo.Operator.CLEAR)
        cr.arc(dx, dy, dot.radius * 1.3, 0.0, 2*math.pi)
        cr.fill()

        color = HotspotWidget.getColorBetween(dot.color,
                                             dot.highlightColor,
                                             self._effectiveHighlightPercentage)

        cr.set_source_rgba(*color)
        cr.set_operator(cairo.Operator.OVER)

        cr.arc(dx, dy, dot.radius, 0.0, 2*math.pi)

        cr.fill()

    def _img2widget(self, x, y):
        """Convert the given image-relative coordinates to widget-relative ones
        that are not magnified."""
        return ((x * self._magnification - self._imageX) /
                self._magnification,
                (y * self._magnification - self._imageY) /
                self._magnification)


#-------------------------------------------------------------------------------

class HotspotEditor(Gtk.Dialog):
    """An editor dialog for a new or existing hotspot."""
    # Response type: delete the hotspot
    RESPONSE_DELETE = 1

    @staticmethod
    def rgba2color(rgba):
        """Convert the given RGBA color to a color tuple."""
        return (rgba.red, rgba.green, rgba.blue, rgba.alpha)

    def __init__(self, jsViewer, title, hotspotWidget, edit = False):
        """Construct the editor for the given hotspot widget."""
        super().__init__(use_header_bar = True)

        self._jsViewer = jsViewer
        self._hotspotWidget = hotspotWidget
        hotspot = hotspotWidget.hotspot

        self._dot = hotspot.dot

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
        joystickType = jsViewer.joystickType
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

        gui = jsViewer.gui
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

        label = Gtk.Label(_("S_election color"))
        label.set_use_underline(True)
        colorGrid.attach(label, 0, 4, 1, 1)

        selectColorButton = self._selectColorButton = Gtk.ColorButton()
        selectColorButton.set_use_alpha(True)
        selectColorButton.set_rgba(Gdk.RGBA(*hotspot.selectColor))
        selectColorButton.connect("color-set", self._colorChanged)
        colorGrid.attach(selectColorButton, 1, 4, 1, 1)
        label.set_mnemonic_widget(selectColorButton)

        colorFrame = self._colorFrame = Gtk.Frame.new(_("Colors"))
        colorFrame.add(colorGrid)

        grid.attach(colorFrame, 0, 2, 2, 1)

        dotGrid = self._dotGrid = Gtk.Grid()

        dotGrid.set_column_homogeneous(True)
        dotGrid.set_row_spacing(4)
        dotGrid.set_column_spacing(8)
        dotGrid.set_margin_end(8)
        dotGrid.set_margin_bottom(8)

        dot = hotspot.dot

        line = 0

        label = Gtk.Label(_("Dot _radius:"))
        label.set_use_underline(True)
        dotGrid.attach(label, 0, line, 1, 1)

        value = dot.radius if dot else 5
        adjustment = Gtk.Adjustment(value, 0.5, 15.0, 0.1, 1.0, 0.0)
        dotRadius = self._dotRadius = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL,
                                                    adjustment)
        dotRadius.set_value(value)
        dotRadius.connect("value-changed", self._dotRadiusChanged)
        dotGrid.attach(dotRadius, 1, line, 2, 1)
        label.set_mnemonic_widget(dotRadius)

        line += 1

        label = Gtk.Label(_("_Line width:"))
        label.set_use_underline(True)
        dotGrid.attach(label, 0, line, 1, 1)

        value = dot.lineWidth if dot else 3
        adjustment = Gtk.Adjustment(value, 0.5, 15.0, 0.1, 1.0, 0.0)
        lineWidth = self._lineWidth = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL,
                                                    adjustment)
        lineWidth.set_value(value)
        lineWidth.connect("value-changed", self._lineWidthChanged)
        dotGrid.attach(lineWidth, 1, line, 2, 1)
        label.set_mnemonic_widget(lineWidth)

        line += 1

        label = Gtk.Label(_("Dot"))
        label.props.halign = Gtk.Align.CENTER
        dotGrid.attach(label, 1, line, 1, 1)

        label = Gtk.Label(_("Line"))
        label.props.halign = Gtk.Align.CENTER
        dotGrid.attach(label, 2, line, 1, 1)

        line += 1

        self._normalDotColorButton = normalDotColorButton = \
            Gtk.RadioButton.new_with_label(None, _("Normal"))
        dotGrid.attach(normalDotColorButton, 0, line, 1, 1)
        normalDotColorButton.connect("toggled", self._dotColorSetChanged)

        self._highlightedDotColorButton = highlightedDotColorButton = \
            Gtk.RadioButton.new_with_label_from_widget(normalDotColorButton,
                                                       _("Highlighted"))
        highlightedDotColorButton.connect("toggled", self._dotColorSetChanged)
        dotGrid.attach(highlightedDotColorButton, 0, line + 1, 1, 1)

        dotColorButton = self._dotColorButton = Gtk.ColorButton()
        dotColorButton.set_use_alpha(True)
        dotColorButton.connect("color-set", self._colorChanged)
        dotGrid.attach(dotColorButton, 1, line, 1, 1)

        lineColorButton = self._lineColorButton = Gtk.ColorButton()
        lineColorButton.set_use_alpha(True)
        lineColorButton.connect("color-set", self._colorChanged)
        dotGrid.attach(lineColorButton, 2, line, 1, 1)

        highlightDotColorButton = self._highlightDotColorButton = Gtk.ColorButton()
        highlightDotColorButton.set_use_alpha(True)
        highlightDotColorButton.connect("color-set", self._colorChanged)
        dotGrid.attach(highlightDotColorButton, 1, line+1, 1, 1)

        highlightLineColorButton = self._highlightLineColorButton = Gtk.ColorButton()
        highlightLineColorButton.set_use_alpha(True)
        highlightLineColorButton.connect("color-set", self._colorChanged)
        dotGrid.attach(highlightLineColorButton, 2, line + 1, 1, 1)

        self._setDotColorButtonColors()

        line += 2

        dotFrame = self._dotFrame = Gtk.Frame.new()
        self._dotEnabled = Gtk.CheckButton(_("Sh_ow dot"))
        self._dotEnabled.set_use_underline(True)
        dotFrame.set_label_widget(self._dotEnabled)
        self._dotEnabled.set_active(hotspot.dot is not None)
        self._dotEnabled.connect("toggled", self._dotEnabledToggled)
        self._updateDotWidgets()
        dotFrame.add(dotGrid)

        grid.attach(dotFrame, 0, 3, 2, 1)

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
            hotspot = self._hotspotWidget.hotspot
            hotspot.controlType = self._controls.get_value(i, 2)
            hotspot.controlCode = self._controls.get_value(i, 3)
            self._jsViewer._updateHotspotWidget(
                self._hotspotWidget,
                self._hotspotWidget.updateLabel())

    def _fontSet(self, fontButton):
        """Called when a font has been selected."""
        hotspot = self._hotspotWidget.hotspot
        hotspot.fontSize = fontButton.get_font_size() / Pango.SCALE
        self._jsViewer._updateHotspotWidget(self._hotspotWidget,
                                              self._hotspotWidget.updateLabel())

    def _colorSetChanged(self, button):
        """Called when the color set selection has changed."""
        if button.get_active():
            if button is self._normalColorButton:
                self._normalDotColorButton.set_active(True)
                self._hotspotWidget.inhibitHighlight()
            else:
                self._highlightedDotColorButton.set_active(True)
                self._hotspotWidget.forceHighlight()

    def _dotColorSetChanged(self, button):
        """Called when the dot color set selection has changed."""
        if button.get_active():
            if button is self._normalDotColorButton:
                if not self._normalColorButton.get_active():
                    self._normalColorButton.set_active(True)
            else:
                if not self._highlightedColorButton.get_active():
                    self._highlightedColorButton.set_active(True)

    def _colorChanged(self, button):
        """Called when one of the colours has changed."""
        color = button.get_rgba()
        hotspot = self._hotspotWidget.hotspot
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
        elif button is self._dotColorButton:
            hotspot.dot.color = HotspotEditor.rgba2color(color)
            redraw = self._normalColorButton.get_active()
        elif button is self._lineColorButton:
            hotspot.dot.lineColor = HotspotEditor.rgba2color(color)
            redraw = self._normalColorButton.get_active()
        elif button is self._highlightDotColorButton:
            hotspot.dot.highlightColor = HotspotEditor.rgba2color(color)
            redraw = self._highlightedColorButton.get_active()
        elif button is self._highlightLineColorButton:
            hotspot.dot.lineHighlightColor = HotspotEditor.rgba2color(color)
            redraw = self._highlightedColorButton.get_active()

        if redraw:
            self._hotspotWidget.queue_draw()

    def _updateDotWidgets(self):
        """Update the sensitivity of the widgets controlling the parameters of
        the dot."""
        enabled = self._dotEnabled.get_active()
        self._normalDotColorButton.set_sensitive(enabled)
        self._highlightedDotColorButton.set_sensitive(enabled)

        self._dotColorButton.set_sensitive(enabled)
        self._lineColorButton.set_sensitive(enabled)
        self._highlightDotColorButton.set_sensitive(enabled)
        self._highlightLineColorButton.set_sensitive(enabled)

    def _dotEnabledToggled(self, button):
        """Called when the dot-enabled button is toggled."""
        self._updateDotWidgets()
        hotspot = self._hotspotWidget.hotspot
        if self._dotEnabled.get_active():
            assert hotspot.dot is None
            if self._dot is None:
                hotspot.addDot(hotspot.x + 30, hotspot.y + 30,
                               radius = 5,
                               color = hotspot.bgColor,
                               highlightColor = hotspot.highlightBGColor,
                               lineWidth = 2,
                               lineColor = hotspot.color,
                               lineHighlightColor = hotspot.highlightColor)
                self._dot = dot = hotspot.dot
                self._setDotColorButtonColors()
            else:
                hotspot.dot = self._dot
        else:
            hotspot.dot = None

        self._jsViewer._updateHotspotWidget(self._hotspotWidget)

    def _setDotColorButtonColors(self):
        """Set the colours of the dot color buttons from the hotspot."""
        hotspot = self._hotspotWidget.hotspot
        dot = hotspot.dot
        self._dotColorButton.set_rgba(
            Gdk.RGBA(*(dot.color if dot else hotspot.bgColor)))

        self._lineColorButton.set_rgba(
            Gdk.RGBA(*(dot.lineColor if dot else hotspot.color)))

        self._highlightDotColorButton.set_rgba(
            Gdk.RGBA(*(dot.highlightColor if dot
                       else hotspot.highlightBGColor)))

        self._highlightLineColorButton.set_rgba(
            Gdk.RGBA(*(dot.lineHighlightColor if dot
                       else hotspot.highlightColor)))

    def _dotRadiusChanged(self, widget):
        """Called when the dot radius has been changed."""
        self._dot.radius = widget.get_value()
        self._jsViewer._updateHotspotWidget(self._hotspotWidget)

    def _lineWidthChanged(self, widget):
        """Called when the line width has been changed."""
        self._dot.lineWidth = widget.get_value()
        self._jsViewer._updateHotspotWidget(self._hotspotWidget)

#-------------------------------------------------------------------------------

class JSViewer(Gtk.Overlay):
    """A viewer and editor for a joystick view."""
    class DraggedHotspot(object):
        """A representation of a dragged hotspot."""
        def __init__(self, widget, eventX0, eventY0, x0, y0, moved, withinDot):
            self.widget = widget
            self.eventX0 = eventX0
            self.eventY0 = eventY0
            self.x0 = x0
            self.y0 = y0
            self.moved = moved
            self.withinDot = withinDot

    def __init__(self, gui, joystickType, window, editable = False):
        """Construct the viewer."""
        super().__init__()

        self._gui = gui
        self._joystickType = joystickType
        self._window = window
        self._editable = editable

        self._monitoringJoystick = False
        self._forceMonitoringJoystick = False
        self._axisHighlightTimeouts = {}
        self._highlightedKeys = set()
        self._highlightedAxes = set()

        self._views = Gtk.ListStore(str, GdkPixbuf.Pixbuf, object)
        for view in joystickType.views:
            self._views.append([view.name,
                                self._findViewImage(view.imageFileName),
                                view])

        self._viewIterQueryFn = None
        self._getSelectedControlsFn = None
        self._joystickEventListener = None
        self._activateViewFn = None

        self._magnification = 1.0

        self._image = PaddedImage()
        self._image.connect("size-allocate", self._imageResized)

        self.add(self._image)
        if self._editable:
            self.connect("button-press-event",
                         self._overlayButtonEvent);
            self.connect("button-release-event",
                         self._overlayButtonEvent);
        self.connect("motion-notify-event",
                     self._overlayMotionEvent);
        self.connect("scroll-event",
                     self._overlayScrollEvent);

        self._imageFixed = Gtk.Fixed()
        self.add_overlay(self._imageFixed)

        self._hotspotWidgets = []
        self._draggedHotspot = None
        self._mouseHighlightedHotspotWidget = None

        self._emittingSignal = False


        joystickType.connect("key-display-name-changed",
                             self._keyDisplayNameChanged)
        joystickType.connect("axis-display-name-changed",
                             self._axisDisplayNameChanged)

        joystickType.connect("view-added", self._viewAdded)
        joystickType.connect("view-name-changed", self._viewNameChanged)
        joystickType.connect("hotspot-moved", self._hotspotMoved)
        joystickType.connect("hotspot-modified", self._hotspotModified)
        joystickType.connect("hotspot-added", self._hotspotAdded)
        joystickType.connect("hotspot-removed", self._hotspotRemoved)
        joystickType.connect("view-removed", self._viewRemoved)

    @property
    def gui(self):
        """Get the GUI object."""
        return self._gui

    @property
    def joystickType(self):
        """Get the joystick type."""
        return self._joystickType

    @property
    def numViews(self):
        """Determine the number of views."""
        return self._views.iter_n_children(None)

    @property
    def hasView(self):
        """Determine if there are any views."""
        return self.numViews>0

    @property
    def views(self):
        """Get the list store with the views."""
        return self._views

    @property
    def _viewIter(self):
        """Get the iterator of the currently selected view."""
        return None if self._viewIterQueryFn is None else self._viewIterQueryFn()

    @property
    def view(self):
        """Get the currently selected view."""
        i = self._viewIter
        return None if i is None else self._views.get_value(i, 2)

    @property
    def viewName(self):
        """Get the name of the virew currently selected."""
        i = self._viewIter
        return None if i is None else self._views.get_value(i, 0)

    @viewName.setter
    def viewName(self, viewName):
        """Set the name of the current view."""
        i = self._viewIter
        if i is not None:
            origViewName = self._views.get_value(i, 0)
            self._callEmitter(self._joystickType.changeViewName,
                              origViewName, viewName)
            self._views.set_value(i, 0, viewName)

        return viewName

    @property
    def _selectedControls(self):
        """Get the list of the selected controls."""
        return [] if self._getSelectedControlsFn is None else self._getSelectedControlsFn()

    def setCallbacks(self, viewIterQueryFn,
                     getSelectedControlsFn = None,
                     joystickEventListener = None,
                     activateViewFn = None):
        """Set the various callback functions."""
        self._viewIterQueryFn = viewIterQueryFn
        self._getSelectedControlsFn = getSelectedControlsFn
        self._joystickEventListener = joystickEventListener
        self._activateViewFn = activateViewFn

    def setupWindowEvents(self):
        """Setup the window events for the fixed image."""
        window = self._imageFixed.get_window()

        events = \
            Gdk.EventMask.POINTER_MOTION_MASK | \
            Gdk.EventMask.SCROLL_MASK | \
            Gdk.EventMask.SMOOTH_SCROLL_MASK

        if self._editable:
            events |= \
                Gdk.EventMask.BUTTON_PRESS_MASK | \
                Gdk.EventMask.BUTTON_RELEASE_MASK

        window.set_events(window.get_events() | events)

    def addView(self, viewName, imageFileName):
        """Add a view with the given name and image file name."""
        view = self._callEmitter(self._joystickType.newView,
                                 viewName,  imageFileName)
        self._views.append([view.name,
                            self._findViewImage(imageFileName),
                            view])

    def viewChanged(self, *args):
        """Called when the view has changed."""
        for hotspotWidget in self._hotspotWidgets:
            self._imageFixed.remove(hotspotWidget)
        self._hotspotWidgets = []

        view = self.view
        if view is not None:
            i = self._viewIter
            pixbuf = self._views.get_value(i, 1)
            self._image.preparePixbuf(pixbuf)

            for hotspot in view.hotspots:
                h = HotspotWidget(self, hotspot)
                self._hotspotWidgets.append(h)
                self._imageFixed.put(h, hotspot.x, hotspot.y)
            self._imageFixed.show_all()
        else:
            self._image.clearImage()

        self.updateHotspotSelection()
        self.setupHotspotHighlights()

        self._resizeImage()

    def updateHotspotSelection(self):
        """Update the hotspot selection."""
        selectedControls = self._selectedControls

        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.hotspot
            if (hotspot.controlType, hotspot.controlCode) in \
               selectedControls:
                hotspotWidget.select()
            else:
                hotspotWidget.deselect()

    def setAxisHotspotHighlight(self, code, percentage):
        """Highlight the hotspot(s) of the axis with the given code."""
        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.hotspot
            if hotspot.controlType == Hotspot.CONTROL_TYPE_AXIS and \
               hotspot.controlCode == code:
                hotspotWidget.highlight(percentage = percentage)

    def setupHotspotHighlights(self):
        """Setup the hotspot highlights."""
        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.hotspot
            if hotspot.controlType == Hotspot.CONTROL_TYPE_KEY:
                if hotspot.controlCode in self._highlightedKeys:
                    hotspotWidget.highlight()
                else:
                    hotspotWidget.unhighlight()
            else:
                if hotspot.controlCode in self._highlightedAxes:
                    percentage = 100 - 20 * self._axisHighlightTimeouts[hotspot.controlCode][1]
                    hotspotWidget.highlight(percentage = percentage)
                else:
                    hotspotWidget.unhighlight()

    def removeCurrentView(self):
        """Remove the current view.

        Returns the iterator of the view to activate. If the current view is
        not the last one, the iterator of the next view is returned. Otherwise
        the iterator of the previous one is returned, or None if no views remain."""
        i = self._viewIter
        if i is None:
            return None

        toActivate = self._views.iter_next(i)
        if toActivate is None:
            toActivate = self._views.iter_previous(i)

        self._callEmitter(self._joystickType.deleteView, self._views.get_value(i, 0))
        self._views.remove(i)

        return toActivate

    def startMonitorJoysticks(self):
        """Start monitoring the joysticks, if not already started."""
        if not self._monitoringJoystick and \
           self._gui.startMonitorJoysticksFor(self._joystickType, self):

            self._monitoringJoystick = True
            for state in self._gui.getJoystickStatesFor(self._joystickType):
                for keyData in state[0]:
                    code = keyData[0]
                    value = keyData[1]
                    if value>0:
                        self._highlightedKeys.add(code)
                        if self._joystickEventListener is not None:
                            self._joystickEventListener.setKeyHighlight(code, 100)

            self.setupHotspotHighlights()
            return True
        else:
            return False

    def stopMonitorJoysticks(self):
        """Stop monitoring the joysticks, if it is being monitored."""
        if self._monitoringJoystick and \
           self._gui.stopMonitorJoysticksFor(self._joystickType, self):
            self._monitoringJoystick = False
            for (timeoutID, _step) in self._axisHighlightTimeouts.values():
                GLib.source_remove(timeoutID)
            self._axisHighlightTimeouts = {}

            listener = self._joystickEventListener
            if listener is not None:
                for code in self._highlightedKeys:
                    listener.setKeyHighlight(code, 0)
                for code in self._highlightedAxes:
                    listener.setAxisHighlight(code, 0)

            self._highlightedKeys.clear()
            self._highlightedAxes.clear()

            self.setupHotspotHighlights()

            return True
        else:
            return False

    def keyPressed(self, code):
        """Called when a key has been pressed on a joystick whose type is
        handled by this widget."""
        if not self._monitoringJoystick:
            return

        self._setKeyHotspotHighlight(code, True)

        if self._joystickEventListener is not None:
            self._joystickEventListener.keyPressed(code)
            self._joystickEventListener.setKeyHighlight(code, 100)

    def keyReleased(self, code):
        """Called when a key has been released on a joystick whose type is
        handled by this editor window."""
        if not self._monitoringJoystick:
            return

        self._setKeyHotspotHighlight(code, False)

        if self._joystickEventListener is not None:
            self._joystickEventListener.keyReleased(code)
            self._joystickEventListener.setKeyHighlight(code, 0)

    def axisChanged(self, code, value):
        """Called when the value of an axis had changed on a joystick whose
        type is handled by this editor window."""
        if not self._monitoringJoystick:
            return

        if code in self._axisHighlightTimeouts:
            GLib.source_remove(self._axisHighlightTimeouts[code][0])
        try:
            self._axisHighlightTimeouts[code] = \
                (GLib.timeout_add(75, self._handleAxisHighlightTimeout, code),
                 0)
        except Exception as e:
            print(e)

        self.setAxisHotspotHighlight(code, 100)

        if self._joystickEventListener is not None:
            self._joystickEventListener.setAxisHighlight(code, 100)
            self._joystickEventListener.axisChanged(code, value)

    def _setKeyHotspotHighlight(self, code, enabled):
        """Enable or disable the highlight of the hotspot(s) for the key with
        the given code."""
        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.hotspot
            if hotspot.controlType == Hotspot.CONTROL_TYPE_KEY and \
               hotspot.controlCode == code:
                hotspotWidget.highlight(percentage = 100 if enabled else 0)

    def _clearHotspotSelection(self):
        """Clear the selection of all selected hotspots."""
        for hotspotWidget in self._hotspotWidgets:
            hotspotWidget.deselect()

    def _updateHotspotWidget(self, hotspotWidget, coords = None):
        """Update the given hotspot widget."""
        if coords is None:
            coords = hotspotWidget.updateImageCoordinates()
        (x, y) = coords
        self._imageFixed.move(hotspotWidget,
                              self._pixbufXOffset + x,
                              self._pixbufYOffset + y)

    def _updateHotspotPositions(self):
        """Update the hotspot positions ."""
        if self.view is None:
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
        i = self._viewIter
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
            box = hotspotWidget.imageBoundingBox
            minX = min(minX, box.x0)
            maxX = max(maxX, box.x1)
            minY = min(minY, box.y0)
            maxY = max(maxY, box.y1)

        magnification = self._magnification

        self._image.setMargins((100 - minX) * magnification,
                               (maxX + 100 - pixbufWidth) * magnification,
                               (100 - minY) * magnification,
                               (maxY + 100 - pixbufHeight) * magnification)

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

    def _findHotspotWidget(self, hotspot):
        """Find the hotspot widget for the given hotspot."""
        for hotspotWidget in self._hotspotWidgets:
            if hotspotWidget.hotspot is hotspot:
                return hotspotWidget

    def _findHotspotWidgetAt(self, widget, eventX, eventY):
        """Find the hotspot for the given event coordinates.

        A tuple is returned consisting of:
        - the hotspot widget, or None if no widget was found, and
        - a boolean indicating if the coordinates are within the dot of the
        widget
        """
        for hotspotWidget in self._hotspotWidgets:
            (x, y) = widget.translate_coordinates(hotspotWidget, eventX, eventY)
            within = hotspotWidget.isWithin(x, y)
            withinDot = hotspotWidget.isWithinDot(x, y)
            if within or withinDot:
                return (hotspotWidget, withinDot and not within)
        return (None, False)

    def _overlayButtonEvent(self, overlay, event):
        """Handle mouse button press and release events."""
        if self.view is None:
            return

        if event.button==1:
            if event.type==Gdk.EventType.BUTTON_RELEASE:
                if self._draggedHotspot is None:
                    self._createHotspot(event.x, event.y)
                elif self._draggedHotspot.moved:
                    self._updateDraggedHotspot(event, finalize = True)
                else:
                    (hotspotWidget, _withinDot) = \
                        self._findHotspotWidgetAt(overlay, event.x, event.y)
                    if hotspotWidget is not None:
                        self._editHotspot(hotspotWidget)

                self._draggedHotspot = None
            else:
                (hotspotWidget, withinDot) = \
                    self._findHotspotWidgetAt(overlay, event.x, event.y)
                if hotspotWidget is not None:
                    hotspot = hotspotWidget.hotspot
                    x = hotspot.dot.x if withinDot else hotspot.x
                    y = hotspot.dot.y if withinDot else hotspot.y
                    self._draggedHotspot = \
                        JSViewer.DraggedHotspot(hotspotWidget,
                                                event.x, event.y,
                                                x, y, False, withinDot)

    def _overlayMotionEvent(self, overlay, event):
        """Handle mouse motion events in the image."""
        if self.view is None:
            return

        if self._draggedHotspot is None:
            (hotspotWidget, _isWithinDot) = \
                self._findHotspotWidgetAt(overlay, event.x, event.y)
            if self._mouseHighlightedHotspotWidget is not hotspotWidget:
                if self._mouseHighlightedHotspotWidget is not None:
                    self._mouseHighlightedHotspotWidget.unnegateHighlight()

                self._mouseHighlightedHotspotWidget = hotspotWidget
                if hotspotWidget is not None:
                    hotspotWidget.negateHighlight()
        else:
            self._updateDraggedHotspot(event)

    def _updateDraggedHotspot(self, event, finalize = False):
        """Update the dragged hotspot with the coordinates from the given
        event.

        If finalize is True, the data is saved permanently and dragging
        ends."""
        hotspotWidget = self._draggedHotspot.widget

        dx = (event.x - self._draggedHotspot.eventX0) / self._magnification
        dy = (event.y - self._draggedHotspot.eventY0) / self._magnification

        x = self._draggedHotspot.x0 + dx
        y = self._draggedHotspot.y0 + dy

        hotspot = hotspotWidget.hotspot
        if self._draggedHotspot.withinDot:
            if finalize:
                self._callEmitter(self._joystickType.updateViewHotspotDotCoordinates,
                                  self.view, hotspot, x, y)
            else:
                hotspot.dot.x = x
                hotspot.dot.y = y
        else:
            if finalize:
                self._callEmitter(self._joystickType.updateViewHotspotCoordinates,
                                  self.view, hotspot, x, y)
            else:
                hotspot.x = x
                hotspot.y = y

        (x, y) = hotspotWidget.updateImageCoordinates()
        self._imageFixed.move(hotspotWidget,
                              self._pixbufXOffset + x,
                              self._pixbufYOffset + y)

        if finalize:
            self._resizeImage()
        else:
            self._draggedHotspot.moved = True

    def _overlayScrollEvent(self, overlay, event):
        """Called when a scroll event is received.

        When the Control key is pressed, and the scroll direction is up or
        down, the image will be zoomed in or out."""
        i = self._viewIter
        if event.state==Gdk.ModifierType.CONTROL_MASK and i is not None:
            delta = 0.0
            if event.direction==Gdk.ScrollDirection.UP:
                delta = 1.0
            elif event.direction==Gdk.ScrollDirection.DOWN:
                delta = -1.0
            elif event.direction==Gdk.ScrollDirection.SMOOTH:
                delta = -event.delta_y

            if delta!=0.0 and (delta<0.0 or self._magnification<1.0):
                self._magnification += self._magnification * delta / 100.0
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

    def _createHotspot(self, eventX, eventY):
        """Create a hotspot at the given mouse event coordinates."""
        x = round((eventX - self._pixbufXOffset) / self._magnification)
        y = round((eventY - self._pixbufYOffset) / self._magnification)

        view = self.view
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

        hotspot = Hotspot(x, y,
                          controlType = controlType, controlCode = controlCode,
                          fontSize = 12,
                          color = color, bgColor = bgColor,
                          highlightColor = highlightColor,
                          highlightBGColor = highlightBGColor,
                          selectColor = selectColor)

        self._clearHotspotSelection()

        hotspotWidget = HotspotWidget(self, hotspot)
        hotspotWidget.inhibitHighlight()
        hotspotWidget.select()
        hotspotWidget.show()
        self._hotspotWidgets.append(hotspotWidget)
        (x, y) = hotspotWidget.setMagnification(self._magnification)
        self._imageFixed.put(hotspotWidget,
                             self._pixbufXOffset + x, self._pixbufYOffset + y)

        dialog = HotspotEditor(self, ("Create hotspot"), hotspotWidget)

        self._forceMonitoringJoystick = True
        self._updateJoystickMonitoring()

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        self._forceMonitoringJoystick = False
        self._updateJoystickMonitoring()

        if response==Gtk.ResponseType.OK:
            self._callEmitter(self._joystickType.addViewHotspot,
                              view, hotspot)
            hotspotWidget.clearForceHighlight()
            hotspotWidget.clearInhibitHighlight()
            hotspotWidget.unnegateHighlight()
            self._resizeImage()
        else:
            self._imageFixed.remove(hotspotWidget)
            del self._hotspotWidgets[-1]

        self.updateHotspotSelection()
        self.setupHotspotHighlights()

    def _editHotspot(self, hotspotWidget):
        """Edit the given hotspot."""
        self._clearHotspotSelection()

        hotspotWidget.inhibitHighlight()
        hotspotWidget.select()

        (origHotspot, newHotspot) = hotspotWidget.cloneHotspot()

        dialog = HotspotEditor(self, ("Edit hotspot"), hotspotWidget,
                               edit = True)

        self._forceMonitoringJoystick = True
        self._updateJoystickMonitoring()

        dialog.show_all()
        while True:
            response = dialog.run()

            if response==Gtk.ResponseType.OK:
                hotspotWidget.clearForceHighlight()
                hotspotWidget.clearInhibitHighlight()
                hotspotWidget.unnegateHighlight()
                self._callEmitter(self._joystickType.modifyViewHotspot,
                                  self.view, origHotspot, newHotspot)
                self._resizeImage()
                break
            elif response==HotspotEditor.RESPONSE_DELETE:
                if yesNoDialog(self._window, _("Are you sure to delete the hotspot?")):
                    self._callEmitter(self._joystickType.removeViewHotspot,
                                      self.view, origHotspot)
                    self._imageFixed.remove(hotspotWidget)
                    self._hotspotWidgets.remove(hotspotWidget)
                    self._resizeImage()
                    break
            else:
                hotspotWidget.deselect()
                hotspotWidget.clearForceHighlight()
                hotspotWidget.clearInhibitHighlight()
                hotspotWidget.unnegateHighlight()
                hotspotWidget.restoreHotspot(origHotspot)
                break

        dialog.destroy()

        self._forceMonitoringJoystick = False
        self._updateJoystickMonitoring()

        self.updateHotspotSelection()
        self.setupHotspotHighlights()

    def _updateHotspotLabel(self, controlType, controlCode):
        """Update the label of the hotspot with the given control type and
        code."""
        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.hotspot
            if hotspot.controlType==controlType and \
               hotspot.controlCode==controlCode:
                (x, y) = hotspotWidget.updateLabel()
                self._imageFixed.move(hotspotWidget,
                                      self._pixbufXOffset + x,
                                      self._pixbufYOffset + y)
                self._resizeImage()

    def _getSelectedControls(self):
        """Get the list of the selected controls.

        This default implementation returns an empty list."""
        return []

    def _updateJoystickMonitoring(self):
        pass

    def _handleAxisHighlightTimeout(self, code):
        """Handle the timeout of an axis highlight."""
        (timeoutID, step) = self._axisHighlightTimeouts[code]

        if step>=5:
            del self._axisHighlightTimeouts[code]
            if self._joystickEventListener is not None:
                self._joystickEventListener.setAxisHighlight(code, 0)
            return GLib.SOURCE_REMOVE
        else:
            value = 80 - step * 20
            self.setAxisHotspotHighlight(code, value)
            if self._joystickEventListener is not None:
                self._joystickEventListener.setAxisHighlight(code, value)
            self._axisHighlightTimeouts[code] = (timeoutID, step + 1)
            return GLib.SOURCE_CONTINUE

    def _callEmitter(self, fn, *args):
        """Call the given function with the given arguments assuming that a
        signal will be emitted."""
        self._emittingSignal = True
        result = fn(*args)
        self._emittingSignal = False
        return result

    def _keyDisplayNameChanged(self, joystickType, code, displayName):
        """Called when the display name of a key has changed."""
        self._updateHotspotLabel(Hotspot.CONTROL_TYPE_KEY, code)

    def _axisDisplayNameChanged(self, joystickType, code, displayName):
        """Called when the display name of an axis has changed."""
        self._updateHotspotLabel(Hotspot.CONTROL_TYPE_AXIS, code)

    def _viewAdded(self, joystickType, viewName):
        """Called when a view with the given name has been added."""
        if not self._emittingSignal:
            view = joystickType.findView(viewName)
            self._views.append([view.name,
                                self._findViewImage(view.imageFileName),
                                view])

    def _viewNameChanged(self, joystickType, origViewName, newViewName):
        """Called when the view with the given name has been renamed."""
        if not self._emittingSignal:
            i = self._views.get_iter_first()
            while i is not None:
                if self._views.get_value(i, 0)==origViewName:
                    self._views.set_value(i, 0, newViewName)
                    break
                i = self._views.iter_next(i)

    def _hotspotMoved(self, joystickType, view, hotspot):
        """Called when a hotspot is moved."""
        if not self._emittingSignal and view is self.view:
            hotspotWidget = self._findHotspotWidget(hotspot)
            if hotspotWidget is not None:
                (x, y) = hotspotWidget.updateImageCoordinates()
                self._imageFixed.move(hotspotWidget,
                                      self._pixbufXOffset + x,
                                      self._pixbufYOffset + y)

                self._resizeImage()
                self.updateHotspotSelection()
                self.setupHotspotHighlights()

    def _hotspotModified(self, joystickType, view, origHotspot, newHotspot):
        """Called when a hotspot is modified."""
        if not self._emittingSignal and view is self.view:
            hotspotWidget = self._findHotspotWidget(origHotspot)
            if hotspotWidget is not None:
                hotspotWidget.restoreHotspot(newHotspot)

                self._resizeImage()
                self.updateHotspotSelection()
                self.setupHotspotHighlights()

    def _hotspotAdded(self, joystickType, view, hotspot):
        """Called when a hotspot has been added."""
        if not self._emittingSignal and view is self.view:
            hotspotWidget = HotspotWidget(self, hotspot)
            hotspotWidget.show()
            self._hotspotWidgets.append(hotspotWidget)
            (x, y) = hotspotWidget.setMagnification(self._magnification)
            self._imageFixed.put(hotspotWidget,
                                 self._pixbufXOffset + x, self._pixbufYOffset + y)

            self._resizeImage()
            self.updateHotspotSelection()
            self.setupHotspotHighlights()

    def _hotspotRemoved(self, joystickType, view, hotspot):
        """Called when a hotspot has been removed."""
        if not self._emittingSignal and view is self.view:
            hotspotWidget = self._findHotspotWidget(hotspot)
            if hotspotWidget is not None:
                self._imageFixed.remove(hotspotWidget)
                self._hotspotWidgets.remove(hotspotWidget)

                self._resizeImage()
                self.updateHotspotSelection()
                self.setupHotspotHighlights()

    def _viewRemoved(self, joystickType, viewName):
        """Called when a view with the given name has been removed."""
        if not self._emittingSignal:
            i = self._views.get_iter_first()
            prevI = None
            while i is not None:
                nextI = self._views.iter_next(i)
                if self._views.get_value(i, 0)==viewName:
                    viewCurrent = self._views.get_value(i, 2) is self.view
                    if viewCurrent and self._activateViewFn is not None:
                        self._activateViewFn(prevI if nextI is None else nextI)
                    self._views.remove(i)
                    break
                prevI = i
                i = nextI
