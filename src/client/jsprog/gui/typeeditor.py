# Joystick type editor window

#-------------------------------------------------------------------------------

from .common import *
from .common import _

from jsprog.device import View, Hotspot, DisplayVirtualState
import jsprog.device
from jsprog.joystick import Key, Axis
from jsprog.parser import Control, VirtualControl, ControlConstraint
from jsprog.parser import checkVirtualControlName
from jsprog.parser import SingleValueConstraint, ValueRangeConstraint

import shutil
import math

#-------------------------------------------------------------------------------

## @package jsprog.gui.typeeditor
#
# The window to edit a joystick type, i.e. to give human-readable names to
# the buttons and axes, to provide a joystick image with hotspots as well as
# icons for various purposes and to edit the virtual controls.

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

    def __init__(self, typeEditor, title, hotspotWidget, edit = False):
        """Construct the editor for the given hotspot widget."""
        super().__init__(use_header_bar = True)

        self._typeEditor = typeEditor
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
            self._typeEditor._updateHotspotWidget(
                self._hotspotWidget,
                self._hotspotWidget.updateLabel())

    def _fontSet(self, fontButton):
        """Called when a font has been selected."""
        hotspot = self._hotspotWidget.hotspot
        hotspot.fontSize = fontButton.get_font_size() / Pango.SCALE
        self._typeEditor._updateHotspotWidget(self._hotspotWidget,
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

        self._typeEditor._updateHotspotWidget(self._hotspotWidget)

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
        self._typeEditor._updateHotspotWidget(self._hotspotWidget)

    def _lineWidthChanged(self, widget):
        """Called when the line width has been changed."""
        self._dot.lineWidth = widget.get_value()
        self._typeEditor._updateHotspotWidget(self._hotspotWidget)

#-------------------------------------------------------------------------------

class NewVirtualControlDialog(Gtk.Dialog):
    """Dialog displayed when a new virtual control is to be added to a
    joystick."""
    def __init__(self, typeEditor, title):
        super().__init__(use_header_bar = True)
        self.set_title(title)

        index = typeEditor._virtualControls.iter_n_children(None)
        joystickType = typeEditor.joystickType

        name = None
        displayName = None
        while True:
            name = "VC" + str(index)
            displayName = "Virtual Control " + str(index)

            if joystickType.findVirtualControl(name) is None and \
               joystickType.findVirtualControlByDisplayName(displayName) is None:
                break

            index += 1

        self._typeEditor = typeEditor

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self._saveButton = button = self.add_button(Gtk.STOCK_ADD, Gtk.ResponseType.OK)
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
        nameEntry.set_text(name)
        nameEntry.connect("changed", self._nameChanged)
        grid.attach(nameEntry, 1, 0, 1, 1)
        label.set_mnemonic_widget(nameEntry)

        label = Gtk.Label(_("_Display name:"))
        label.set_use_underline(True)
        label.props.halign = Gtk.Align.START
        grid.attach(label, 0, 1, 1, 1)

        self._displayNameEntry = displayNameEntry = Gtk.Entry()
        displayNameEntry.set_text(displayName)
        displayNameEntry.connect("changed", self._displayNameChanged)
        grid.attach(displayNameEntry, 1, 1, 1, 1)
        label.set_mnemonic_widget(displayNameEntry)

        label = Gtk.Label(_("_Base control:"))
        label.set_use_underline(True)
        label.props.halign = Gtk.Align.START
        grid.attach(label, 0, 3, 1, 1)

        # FIXME: this is very similar to the code in HotspotEditor
        self._controls = controls = Gtk.ListStore(str, str, int, int)
        index = 0
        activeIndex = 0
        for key in joystickType.keys:
            controls.append([key.name, key.displayName,
                             Control.TYPE_KEY, key.code])
            index += 1
        for axis in joystickType.axes:
            controls.append([axis.name, axis.displayName,
                             Control.TYPE_AXIS, axis.code])
            index += 1

        controlSelector = self._controlSelector = \
            Gtk.ComboBox.new_with_model(controls)
        #controlSelector.connect("changed", self._controlChanged)

        displayNameRenderer = Gtk.CellRendererText.new()
        controlSelector.pack_start(displayNameRenderer, True)
        controlSelector.add_attribute(displayNameRenderer, "text", 1)

        nameRenderer = Gtk.CellRendererText.new()
        controlSelector.pack_start(nameRenderer, True)
        controlSelector.add_attribute(nameRenderer, "text", 0)

        controlSelector.set_active(activeIndex)
        label.set_mnemonic_widget(controlSelector)

        grid.attach(controlSelector, 1, 3, 1, 1)

        contentArea.pack_start(grid, True, True, 8)

        self.show_all()

    @property
    def name(self):
        """Get the name entered by the user."""
        return self._nameEntry.get_text()

    @property
    def displayName(self):
        """Get the display name entered by the user."""
        return self._displayNameEntry.get_text()

    @property
    def baseControl(self):
        """Get a tuple containing the control type and code for the selected
        base control."""
        i = self._controlSelector.get_active_iter()
        return (self._controls.get_value(i, 2),
                self._controls.get_value(i, 3))

    def _nameChanged(self, nameEntry):
        """Called when the name has changed."""
        self._updateSaveButton()

    def _displayNameChanged(self, displayNameEntry):
        """Called when the name has changed."""
        self._updateSaveButton()

    def _updateSaveButton(self):
        """Update the state of the Save button based on the names."""
        joystickType = self._typeEditor.joystickType

        name = self.name

        self._saveButton.set_sensitive(
            checkVirtualControlName(name) and
            joystickType.findVirtualControl(name) is None and
            joystickType.findVirtualControlByDisplayName(self.displayName) is None)

#-------------------------------------------------------------------------------

class ValueRangeCellEditable(Gtk.EventBox, Gtk.CellEditable):
    """The editor for a cell containing a value range."""
    editing_canceled = GObject.property(type=bool, default=False)

    def __init__(self, typeEditor, constraint):
        """Construct the editor."""
        super().__init__()

        control = constraint.control
        joystickType = typeEditor.joystickType

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

    def __init__(self, typeEditor, viewWidget):
        super().__init__()
        self._typeEditor = typeEditor
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
            editable =  ValueRangeCellEditable(self._typeEditor, constraint)
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

    def __init__(self, typeEditor, virtualControl, virtualState,
                 okButtonLabel):
        super().__init__(use_header_bar = True)
        self.set_title(_("Virtual State"))
        self.set_default_size(400, 300)

        self._typeEditor = typeEditor
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

        joystickType = typeEditor.joystickType

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

        valueRenderer = CellRendererConstraintValue(self._typeEditor, constraintsView)
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

            axis = self._typeEditor.joystickType.findAxis(newControl.code)
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
        joystickType = self._typeEditor.joystickType

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

class TypeEditorWindow(Gtk.ApplicationWindow):
    """The type editor window."""
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

    def __init__(self, gui, joystickType, *args, **kwargs):
        """Construct the window."""
        super().__init__(*args, **kwargs)

        self._gui = gui
        self._joystickType = joystickType
        self._monitoringJoystick = False
        self._forceMonitoringJoystick = False
        self._focused = False

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

        notebook = Gtk.Notebook.new()
        label = Gtk.Label(_("_Physical controls"))
        label.set_use_underline(True)
        notebook.append_page(vbox, label)

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        buttonBox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        buttonBox.set_layout(Gtk.ButtonBoxStyle.END)

        addVirtualControlButton = Gtk.Button.new_from_icon_name("list-add",
                                                    Gtk.IconSize.BUTTON)
        addVirtualControlButton.connect("clicked",
                                        self._addVirtualControlButtonClicked)
        buttonBox.add(addVirtualControlButton)

        self._removeVirtualControlButton = removeVirtualControlButton = \
            Gtk.Button.new_from_icon_name("list-remove",
                                          Gtk.IconSize.BUTTON)
        removeVirtualControlButton.set_sensitive(False)
        removeVirtualControlButton.connect("clicked",
                                           self._removeVirtualControlButtonClicked)
        buttonBox.add(removeVirtualControlButton)

        vbox.pack_start(buttonBox, False, False, 4)

        virtualControls = self._virtualControls = Gtk.ListStore(object,
                                                                str, str)
        for virtualControl in joystickType.virtualControls:
            displayName = virtualControl.displayName
            if not displayName:
                displayName = virtualControl.name
            virtualControls.append([virtualControl,
                                    virtualControl.name, displayName])

        scrolledWindow = Gtk.ScrolledWindow.new(None, None)

        self._virtualControlsView = view = Gtk.TreeView.new_with_model(virtualControls)

        nameRenderer = Gtk.CellRendererText.new()
        nameRenderer.props.editable = True
        nameRenderer.connect("edited", self._virtualControlNameEdited)
        nameColumn = Gtk.TreeViewColumn(title = _("Name"),
                                        cell_renderer = nameRenderer,
                                        text = 1)
        nameColumn.set_resizable(True)
        view.append_column(nameColumn)

        displayNameRenderer = Gtk.CellRendererText.new()
        displayNameRenderer.props.editable = True
        displayNameRenderer.connect("edited", self._virtualControlDisplayNameEdited)
        displayNameColumn = Gtk.TreeViewColumn(title = _("Display name"),
                                               cell_renderer =
                                               displayNameRenderer,
                                               text = 2)
        view.append_column(displayNameColumn)
        view.get_selection().connect("changed", self._virtualControlSelected)

        scrolledWindow.add(view)

        vbox.pack_start(scrolledWindow, False, False, 0)

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

        vbox.pack_start(buttonBox, False, False, 4)

        virtualStates = self._virtualStates = Gtk.ListStore(object, str, str)
        self._partialVirtualStates = {}

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

        vbox.pack_start(scrolledWindow, True, True, 5)

        label = Gtk.Label(_("_Virtual controls"))
        label.set_use_underline(True)

        notebook.append_page(vbox, label)

        paned.pack2(notebook, False, False)

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
        if not self._monitoringJoystick:
            return

        i = self._getKeyIterForCode(code)
        self._keys.set_value(i, 3, True)
        self._keysView.scroll_to_cell(self._keys.get_path(i), None,
                                      False, 0.0, 0.0)

        self._setKeyHotspotHighlight(code, True)

    def keyReleased(self, code):
        """Called when a key has been released on a joystick whose type is
        handled by this editor window."""
        if not self._monitoringJoystick:
            return

        i = self._getKeyIterForCode(code)
        self._keys.set_value(i, 3, False)

        self._setKeyHotspotHighlight(code, False)

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
        self._setAxisHotspotHighlight(code, 100)
        self._axesView.scroll_to_cell(self._axes.get_path(i), None,
                                      False, 0.0, 0.0)

    def _updateHotspotWidget(self, hotspotWidget, coords = None):
        """Update the given hotspot widget."""
        if coords is None:
            coords = hotspotWidget.updateImageCoordinates()
        (x, y) = coords
        self._imageFixed.move(hotspotWidget,
                              self._pixbufXOffset + x,
                              self._pixbufYOffset + y)

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
        self._updateHotspotSelection()

    def _updateHotspotSelection(self):
        """Update the hotspot selection."""
        selectedControls = []

        (_model, i) =  self._keysView.get_selection().get_selected()
        if i is not None:
            selectedControls.append((Hotspot.CONTROL_TYPE_KEY,
                                     self._keys.get_value(i, 0)))
        (_model, i) =  self._axesView.get_selection().get_selected()
        if i is not None:
            selectedControls.append((Hotspot.CONTROL_TYPE_AXIS,
                                     self._axes.get_value(i, 0)))

        view = self._view
        if view is not None:
            for hotspotWidget in self._hotspotWidgets:
                hotspot = hotspotWidget.hotspot
                if (hotspot.controlType, hotspot.controlCode) in \
                   selectedControls:
                    hotspotWidget.select()
                else:
                    hotspotWidget.deselect()

    def _setKeyHotspotHighlight(self, code, enabled):
        """Enable or disable the highlight of the hotspot(s) for the key with
        the given code."""
        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.hotspot
            if hotspot.controlType == Hotspot.CONTROL_TYPE_KEY and \
               hotspot.controlCode == code:
                hotspotWidget.highlight(percentage = 100 if enabled else 0)

    def _setAxisHotspotHighlight(self, code, percentage):
        """Highlight the hotspot(s) of the axis with the given code."""
        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.hotspot
            if hotspot.controlType == Hotspot.CONTROL_TYPE_AXIS and \
               hotspot.controlCode == code:
                hotspotWidget.highlight(percentage = percentage)

    def _setupHotspotHighlights(self):
        """Update the highlighted status of the hotspot widgets based on the
        current status in the lists."""
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

        for hotspotWidget in self._hotspotWidgets:
            hotspot = hotspotWidget.hotspot
            if hotspot.controlType == Hotspot.CONTROL_TYPE_KEY:
                if hotspot.controlCode in highlightedKeys:
                    hotspotWidget.highlight()
                else:
                    hotspotWidget.unhighlight()
            else:
                if hotspot.controlCode in highlightedAxes:
                    percentage = 100 - 20 * self._axisHighlightTimeouts[hotspot.controlCode][1]
                    hotspotWidget.highlight(percentage = percentage)
                else:
                    hotspotWidget.unhighlight()

    def _clearHotspotSelection(self):
        """Clear the selection of all selected hotspots."""
        for hotspotWidget in self._hotspotWidgets:
            hotspotWidget.deselect()

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

        self._setupHotspotHighlights()


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
            self._setAxisHotspotHighlight(code, 80 - step * 20)
            self._axisHighlightTimeouts[code] = (timeoutID, step + 1)
            return GLib.SOURCE_CONTINUE

    def _viewChanged(self, comboBox):
        """Called when the view has changed."""
        for hotspotWidget in self._hotspotWidgets:
            self._imageFixed.remove(hotspotWidget)
        self._hotspotWidgets = []

        view = self._view
        if view is not None:
            i = self._viewSelector.get_active_iter()
            pixbuf = self._views.get_value(i, 1)
            self._image.preparePixbuf(pixbuf)

            for hotspot in view.hotspots:
                h = HotspotWidget(self, hotspot)
                self._hotspotWidgets.append(h)
                self._imageFixed.put(h, hotspot.x, hotspot.y)
            self._imageFixed.show_all()
        else:
            self._image.clearImage()

        self._updateHotspotSelection()
        self._setupHotspotHighlights()

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
        if self._view is None:
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
                        TypeEditorWindow.DraggedHotspot(hotspotWidget,
                                                        event.x, event.y,
                                                        x, y, False, withinDot)

    def _overlayMotionEvent(self, overlay, event):
        """Handle mouse motion events in the image."""
        if self._view is None:
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
                self._joystickType.updateViewHotspotDotCoordinates(hotspot,
                                                                   x, y)
            else:
                hotspot.dot.x = x
                hotspot.dot.y = y
        else:
            if finalize:
                self._joystickType.updateViewHotspotCoordinates(hotspot, x, y)
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
            self._joystickType.addViewHotspot(view, hotspot)
            hotspotWidget.clearForceHighlight()
            hotspotWidget.clearInhibitHighlight()
            hotspotWidget.unnegateHighlight()
            self._resizeImage()
        else:
            self._imageFixed.remove(hotspotWidget)
            del self._hotspotWidgets[-1]

        self._updateHotspotSelection()
        self._setupHotspotHighlights()

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
                hotspotWidget.clearForceHighlight()
                hotspotWidget.clearInhibitHighlight()
                hotspotWidget.unnegateHighlight()
                hotspotWidget.restoreHotspot(origHotspot)
                break

        dialog.destroy()

        self._forceMonitoringJoystick = False
        self._updateJoystickMonitoring()

        self._updateHotspotSelection()
        self._setupHotspotHighlights()

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

    def _virtualControlNameEdited(self, renderer, path, newName):
        """Called when the name of a virtual control has been edited."""
        i = self._virtualControls.get_iter(path)
        virtualControl = self._virtualControls.get_value(i, 0)
        if newName != virtualControl.name:
            if self._joystickType.setVirtualControlName(virtualControl,
                                                        newName):
                self._virtualControls.set_value(i, 1, newName)

    def _virtualControlDisplayNameEdited(self, renderer, path, newName):
        """Called when the display name of a virtual control has been edited."""
        i = self._virtualControls.get_iter(path)
        virtualControl = self._virtualControls.get_value(i, 0)
        if newName != virtualControl.displayName:
            if self._joystickType.setVirtualControlDisplayName(virtualControl,
                                                               newName):
                self._virtualControls.set_value(i, 2, newName)

    def _virtualControlSelected(self, selection):
        """Called when a virtual control has been selected."""
        self._virtualStates.clear()

        virtualControl = self._getSelectedVirtualControl()

        self._removeVirtualControlButton.set_sensitive(virtualControl is not None)
        self._addVirtualStateButton.set_sensitive(virtualControl is not None)

        if virtualControl is not None:
            for state in virtualControl.states:
                self._virtualStates.append([state, state.displayName,
                                            self._getStateConstraintText(state)])

    def _getSelectedVirtualControl(self):
        """Get the virtual control currently selected, if any."""
        (_model, i) = self._virtualControlsView.get_selection().get_selected()

        return None if i is None else self._virtualControls.get_value(i, 0)

    def _removeVirtualControlButtonClicked(self, button):
        """Called when the button to remove a virtual control is clicked."""
        if yesNoDialog(self, _("Are you sure to remove the selected virtual control?")):
            (_model, i) = self._virtualControlsView.get_selection().get_selected()
            virtualControl = self._virtualControls.get_value(i, 0)
            self._joystickType.deleteVirtualControl(virtualControl)
            self._virtualControls.remove(i)

    def _addVirtualControlButtonClicked(self, button):
        """Called when the button to add a new virtual control is clicked."""
        index = self._virtualControls.iter_n_children(None)

        dialog = NewVirtualControlDialog(self, _("New virtual control"))
        dialog.show()

        response = dialog.run()

        if response==Gtk.ResponseType.OK:
            (baseControlType, baseControlCode) = dialog.baseControl
            virtualControl = self._joystickType.newVirtualControl(dialog.name,
                                                                  dialog.displayName,
                                                                  baseControlType,
                                                                  baseControlCode)

            if virtualControl is not None:
                i = self._virtualControls.append([virtualControl,
                                                  dialog.name, dialog.displayName])
                self._virtualControlsView.get_selection().select_iter(i)
                self._virtualControlsView.scroll_to_cell(self._virtualControls.get_path(i),
                                                         None, False, 0.0, 0.0)

        dialog.destroy()

    def _virtualStateDisplayNameEdited(self, renderer, path, newName):
        """Called when the display name of a virtual state has been edited."""
        i = self._virtualStates.get_iter(path)
        virtualState = self._virtualStates.get_value(i, 0)
        if newName != virtualState.displayName:
            if self._joystickType.setVirtualStateDisplayName(self._getSelectedVirtualControl(),
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

    def _addVirtualStateButtonClicked(self, button):
        virtualControl = self._getSelectedVirtualControl()

        number = self._virtualStates.iter_n_children(None)+1
        while True:
            displayName = "State " + str(number)
            if virtualControl.findStateByDisplayName(displayName) is None:
                break
            number += 1

        state = DisplayVirtualState(displayName)

        dialog = VirtualStateEditor(self, virtualControl, state, _("_Add"))

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
        if yesNoDialog(self, _("Are you sure to remove the selected virtual state?")):
            (_model, i) = self._virtualStatesView.get_selection().get_selected()
            virtualState = self._virtualStates.get_value(i, 0)

            self._joystickType.deleteVirtualState(self._getSelectedVirtualControl(),
                                                  virtualState)
            self._virtualStates.remove(i)

    def _editVirtualStateButtonClicked(self, button):
        """Called when a virtual state is to be edited."""
        virtualControl = self._getSelectedVirtualControl()
        virtualState = self._getSelectedVirtualState()

        dialog = VirtualStateEditor(self, virtualControl, virtualState,
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
