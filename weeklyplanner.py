import sys
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import random
import unittest
from ics import Calendar


from PySide6.QtCore import Qt, QRectF, QPointF, QMimeData, QSize, Signal, QTimer, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QDrag, QFont, QCursor, QIcon, QPixmap, QImage
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsView, QGraphicsScene, QGraphicsObject, QGraphicsTextItem,
    QToolButton, QListWidget, QLineEdit, QCheckBox,
    QListWidgetItem, QSizePolicy, QScrollArea, QSplitter, QFileDialog, QMessageBox
)


START_HOUR = 6
END_HOUR = 24  
SNAP_MINUTES = 15
COLUMN_WIDTH = 160      
HEADER_HEIGHT = 26
PADDING = 4
HANDLE_HEIGHT = 8
TIME_LABEL_WIDTH = 44
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DEFAULT_GRID_MIN_HEIGHT = 500
SPACE_BELOW_CAL = 16  

LIGHT_MODE = {
    "window_bg": "#f6f7fb",
    "header_bg": "#ffffff",
    "header_pen": "#e6e6e6",
    "text": "#1f3b70",
    "event_pen": "#3a6fe2",
    "event_bg": "#dbe7ff",
    "event_text": "#1f3b70",
    "column_grid": "#e6e6e6",
    "row_grid": "#ececec",
    "label_text": "#606060",
    "todo_bg": "#ffffff",
    "todo_border": "#d7dbe7",
    "todo_done_text": "#babedc",
    "todo_handle": "#88aaff",
}
DARK_MODE = {
    "window_bg": "#232536",
    "header_bg": "#292a3a",
    "header_pen": "#33344b",
    "text": "#e5eaf6",
    "event_pen": "#99bbff",
    "event_bg": "#3a415c",
    "event_text": "#e5eaf6",
    "column_grid": "#33344b",
    "row_grid": "#282b3e",
    "label_text": "#babedc",
    "todo_bg": "#282a3a",
    "todo_border": "#33344b",
    "todo_done_text": "#606060",
    "todo_handle": "#88aaff",
}
mode_colors = LIGHT_MODE.copy()

# 4 event color themes for each mode
EVENT_COLOR_THEMES_LIGHT = [
    {"event_pen": "#3a6fe2",  "event_bg": "#dbe7ff", "event_text": "#1f3b70"},
    {"event_pen": "#bbb321",  "event_bg": "#fff699", "event_text": "#7d6f00"},
    {"event_pen": "#48b07b",  "event_bg": "#d2f5e3", "event_text": "#226947"},
    {"event_pen": "#c56868",  "event_bg": "#f8dad7", "event_text": "#8a2727"},
]

EVENT_COLOR_THEMES_DARK = [
    {"event_pen": "#99bbff",  "event_bg": "#3a415c", "event_text": "#e5eaf6"},
    {"event_pen": "#ffe169",  "event_bg": "#292b1c", "event_text": "#bca900"},
    {"event_pen": "#4bb991",  "event_bg": "#303e37", "event_text": "#73ffd5"},
    {"event_pen": "#fa8080",  "event_bg": "#472a3a", "event_text": "#ffd2d2"},
]


def set_mode(light=True):
    """
    Sets the global color theme for the application.

    Args:
        light (bool): If True, sets light mode colors. Otherwise, sets dark mode colors.
    """

    global mode_colors
    if light:
        mode_colors = LIGHT_MODE.copy()
    else:
        mode_colors = DARK_MODE.copy()


SUN_SVG = """<svg width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5" fill="#fdc13d"/><g stroke="#fdc13d" stroke-width="2"><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></g></svg>"""
MOON_SVG = """<svg width="24" height="24" viewBox="0 0 24 24"><path fill="#babedc" d="M19 13A7 7 0 0 1 11 5c0-.48.04-.95.1-1.41A9 9 0 1 0 20.41 18.9c-.46.06-.93.1-1.41.1a7 7 0 0 1-7-7Z"/></svg>"""
HANDLE_SVG = """<svg width="16" height="16" viewBox="0 0 16 16">
<circle cx="8" cy="8" r="4" fill="#88aaff" />
<path d="M8.5 5v3.5h2" stroke="#fff" stroke-width="1.5" stroke-linecap="round" fill="none"/>
</svg>"""
CALENDAR_IMPORT_SVG = """
<svg width="24" height="24" viewBox="0 0 24 24">
    <rect x="3" y="5" width="18" height="16" rx="5" fill="#dbe7ff" stroke="#3a6fe2" stroke-width="2"/>
    <rect x="7" y="12" width="4" height="4" rx="1" fill="#3a6fe2"/>
    <rect x="13" y="12" width="4" height="4" rx="1" fill="#3a6fe2"/>
</svg>"""


def svg_icon(svg_str):
    """
    Generates a QIcon from an SVG string.

    Args:
        svg_str (str): The SVG XML data.

    Returns:
        QIcon: The generated icon.
    """
    image = QImage(24, 24, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    from PySide6.QtSvg import QSvgRenderer
    renderer = QSvgRenderer(bytearray(svg_str, encoding="utf-8"))
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QIcon(QPixmap.fromImage(image))


def snap_minutes(minutes: int) -> int:
    """
    Snap the given minute value to the nearest SNAP_MINUTES increment.

    Args:
        minutes (int): The number of minutes to snap.

    Returns:
        int: Snapped value, always >= 0.
    """
    r = minutes % SNAP_MINUTES
    if r >= SNAP_MINUTES / 2:
        minutes += (SNAP_MINUTES - r)
    else:
        minutes -= r
    return max(0, minutes)


def week_monday(date: datetime) -> datetime:
    """
    Returns the Monday of the week corresponding to the given date.

    Args:
        date (datetime): Any date.

    Returns:
        datetime: Date representing the Monday of that week.
    """
    return date - timedelta(days=(date.weekday() - 0) % 7)


@dataclass
class CalendarEvent:
    """
    Represents a single event in the calendar.

    Attributes:
        title (str): The event's title.
        start (datetime): The event's start datetime.
        duration_min (int): Duration in minutes.
        color_idx (int): Theme color index (default 0).
    """
    title: str
    start: datetime
    duration_min: int
    color_idx: int = 0      # <--- NEW


class CalendarModel:
    """
    Holds and manages a list of CalendarEvent objects.
    """

    def __init__(self):
        """
        Initializes the CalendarModel with an empty event list.
        """
        self.events: list[CalendarEvent] = []

    def add_event(self, event: CalendarEvent):
        """
        Adds an event to the calendar.

        Args:
            event (CalendarEvent): Event to add.
        """
        self.events.append(event)

    def remove_event(self, event: CalendarEvent):
        """
        Removes an event from the calendar.

        Args:
            event (CalendarEvent): Event to remove.
        """
        self.events = [e for e in self.events if e is not event]


class CalendarScene(QGraphicsScene):
    """
    Manages the visual, scene-based calendar grid and its events.
    Draws background, header, and holds EventItem objects.
    """

    def __init__(self, week_start: datetime, model: CalendarModel):
        """
        Initializes a scene for a specific week.

        Args:
            week_start (datetime): Date of the week's Monday.
            model (CalendarModel): Event model to display.
        """
        super().__init__()
        self.week_start = week_start
        self.model = model
        self.total_minutes = (END_HOUR - START_HOUR) * 60
        self.n_days = 7
        self.column_width = COLUMN_WIDTH
        self.grid_height = DEFAULT_GRID_MIN_HEIGHT
        self.scene_width = self.column_width * self.n_days + TIME_LABEL_WIDTH
        self.setSceneRect(0, 0, self.scene_width,
                          HEADER_HEIGHT + self.grid_height + SPACE_BELOW_CAL)
        self._minute_pixel_factor = self.grid_height / self.total_minutes
        self._draw_background()

    def minutes_to_pixels(self, minutes: int) -> float:
        """
        Converts calendar minutes to pixels on the grid.

        Args:
            minutes (int): Minutes from the start of the day.

        Returns:
            float: Pixel position.
        """
        return minutes * self._minute_pixel_factor

    def pixels_to_minutes(self, pixels: float) -> int:
        """
        Converts pixels to rounded minutes based on the grid.

        Args:
            pixels (float): Pixel position.

        Returns:
            int: Minutes from day start.
        """
        return int(round(pixels / self._minute_pixel_factor))

    def set_size(self, pixel_width, pixel_height):
        """
        Resizes the calendar scene and re-calculates grid dimensions.

        Args:
            pixel_width (int): New width in pixels.
            pixel_height (int): New height in pixels.
        """
        self.n_days = 7
        self.column_width = max(
            80, (pixel_width - TIME_LABEL_WIDTH) // self.n_days)
        self.scene_width = self.column_width * self.n_days + TIME_LABEL_WIDTH
        self.grid_height = max(300, pixel_height)
        self._minute_pixel_factor = self.grid_height / self.total_minutes
        self.setSceneRect(0, 0, self.scene_width,
                          HEADER_HEIGHT + self.grid_height + SPACE_BELOW_CAL)
        self.refresh_background()

    def day_index_to_x(self, day_index: int) -> float:
        """
        Returns the X coordinate for starting column of the given weekday index.

        Args:
            day_index (int): Index of day (0=Monday).

        Returns:
            float: X position.
        """
        return TIME_LABEL_WIDTH + day_index * self.column_width

    def x_to_day_index(self, x: float) -> int:
        """
        Converts an x pixel coordinate to the corresponding day index.

        Args:
            x (float): X pixel position.

        Returns:
            int: Day index.
        """
        idx = int((x - TIME_LABEL_WIDTH) // self.column_width)
        return max(0, min(self.n_days-1, idx))

    def day_bottom_y(self) -> float:
        """
        Returns the bottom y coordinate for day's events in the scene.

        Returns:
            float: Y position of the day's bottom.
        """
        return HEADER_HEIGHT + self.grid_height

    def _draw_background(self):
        """
        Draws the background of the calendar grid, headers, and labels.
        """
        self.setBackgroundBrush(QBrush(QColor(mode_colors["window_bg"])))
        header_pen = QPen(QColor(mode_colors["header_pen"]))
        header_brush = QBrush(QColor(mode_colors["header_bg"]))
        font = QFont("Arial", 10)
        for i in range(self.n_days):
            x = self.day_index_to_x(i)
            header_rect = self.addRect(
                QRectF(x, 0, self.column_width, HEADER_HEIGHT), header_pen, header_brush)
            header_rect.setZValue(-10)
            day_date = self.week_start + timedelta(days=i)
            label = f"{DAY_NAMES[i]} {day_date.strftime('%d %b')}"
            text_item = self.addText(label, font)
            text_item.setDefaultTextColor(QColor(mode_colors["text"]))
            text_item.setPos(x + 6, 3)
            text_item.setZValue(-5)
        label_font = QFont("Arial", 9)
        label_color = QColor(mode_colors["label_text"])
        for h in range(START_HOUR, END_HOUR + 1):
            y = HEADER_HEIGHT + self.minutes_to_pixels((h - START_HOUR) * 60)
            label = f"{h:02d}:00"
            text_item = QGraphicsTextItem(label)
            text_item.setFont(label_font)
            text_item.setDefaultTextColor(label_color)
            text_item.setPos(6, y - 9)
            text_item.setZValue(1)
            self.addItem(text_item)
        v_pen = QPen(QColor(mode_colors["column_grid"]))
        v_pen.setWidth(1)
        for i in range(self.n_days+1):
            x = TIME_LABEL_WIDTH + i * self.column_width
            self.addLine(x, HEADER_HEIGHT, x, HEADER_HEIGHT +
                         self.grid_height, v_pen)
        h_pen = QPen(QColor(mode_colors["row_grid"]))
        for h in range(START_HOUR, END_HOUR + 1):
            y = HEADER_HEIGHT + self.minutes_to_pixels((h - START_HOUR) * 60)
            line = self.addLine(TIME_LABEL_WIDTH, y,
                                self.scene_width, y, h_pen)
            line.setZValue(-10)

    def refresh_background(self):
        """
        Clears and redraws the calendar scene background and event items.
        """
        self.clear()
        self._draw_background()
        for e in self.model.events:
            self.add_event_item(e)

    def add_event_item(self, event: CalendarEvent) -> 'EventItem':
        """
        Adds a visual EventItem representing an event to the scene.

        Args:
            event (CalendarEvent): Event to add.

        Returns:
            EventItem: The graphical event item created.
        """
        item = EventItem(self.model, event, self.week_start, self)
        self.addItem(item)
        return item

    def keyPressEvent(self, event):
        """
        Handles key press events (mainly for deletion).
        """
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            for item in list(self.selectedItems()):
                if isinstance(item, EventItem):
                    self.model.remove_event(item.calendar_event)
                    self.removeItem(item)
            event.accept()
        else:
            super().keyPressEvent(event)


class CalendarView(QGraphicsView):
    """
    QGraphicsView displaying a CalendarScene with drag-and-drop support for tasks.
    """

    def __init__(self, scene: CalendarScene, model: CalendarModel):
        """
        Initialize the calendar view with a scene and event model.

        Args:
            scene (CalendarScene): The scene to display.
            model (CalendarModel): The event model.
        """
        super().__init__(scene)
        self.model = model
        self.scene_ref = scene
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(180)
        self.setMinimumWidth(TIME_LABEL_WIDTH + COLUMN_WIDTH * 3)

    def resizeEvent(self, event):
        """
        Resize the view and update grid size and dimensions.
        """
        super().resizeEvent(event)
        available_width = self.viewport().width()
        available_height = self.viewport().height() - HEADER_HEIGHT
        self.scene_ref.set_size(available_width, available_height)

    def dragEnterEvent(self, event):
        """
        Accept drag if it's a valid todo payload.
        """
        mime = event.mimeData()
        if mime.hasFormat("application/x-task-todo"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        Accept move event only in the event grid area.
        """
        mime = event.mimeData()
        if mime.hasFormat("application/x-task-todo"):
            p = event.position()
            scene_pos = self.mapToScene(p.toPoint())
            if scene_pos.y() >= HEADER_HEIGHT:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        On drop, create a CalendarEvent in the proper location from dragged todo.
        """
        mime = event.mimeData()
        if not mime.hasFormat("application/x-task-todo"):
            event.ignore()
            return
        data = mime.data("application/x-task-todo").data()
        tpl = json.loads(bytes(data).decode("utf-8"))
        title = tpl.get("title", "Untitled")
        duration_min = int(tpl.get("duration_min", 60))
        scene_pos = self.mapToScene(event.position().toPoint())
        day_index = self.scene_ref.x_to_day_index(scene_pos.x())
        y = max(HEADER_HEIGHT, min(scene_pos.y(), self.scene_ref.day_bottom_y()))
        minutes_from_day_start = snap_minutes(
            int((y - HEADER_HEIGHT) / self.scene_ref._minute_pixel_factor))
        day_date = self.scene_ref.week_start + timedelta(days=day_index)
        start_dt = day_date.replace(hour=START_HOUR, minute=0, second=0,
                                    microsecond=0) + timedelta(minutes=minutes_from_day_start)
        event_obj = CalendarEvent(
            title=title, start=start_dt, duration_min=duration_min)
        self.model.add_event(event_obj)
        self.scene_ref.add_event_item(event_obj)
        event.acceptProposedAction()


class EventItem(QGraphicsObject):
    """
    QGraphicsObject representing a single calendar event box.
    Supports moving, resizing, selecting, and color selection popup.
    """

    def __init__(self, model: CalendarModel, calendar_event: CalendarEvent, week_start: datetime, scene: 'CalendarScene'):
        """
        Construct the visual event item for the given event.

        Args:
            model (CalendarModel): Event data model.
            calendar_event (CalendarEvent): The event being represented.
            week_start (datetime): Start of the calendar week.
            scene (CalendarScene): Parent scene instance.
        """
        super().__init__()
        self.model = model
        self.calendar_event = calendar_event
        self.week_start = week_start
        self.scene_ref = scene
        self.setFlags(
            QGraphicsObject.ItemIsMovable |
            QGraphicsObject.ItemIsSelectable |
            QGraphicsObject.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.resizing = False
        self._drag_start_y = 0.0
        self._initial_height = 0.0
        self._width = self.scene_ref.column_width - 2 * PADDING
        self._update_geometry_from_event()

    def boundingRect(self) -> QRectF:
        """
        Return the rectangle occupied by the event item.

        Returns:
            QRectF: Bounds of the event box.
        """
        return QRectF(
            0, 0,
            self.scene_ref.column_width - 2 * PADDING,
            self.scene_ref.minutes_to_pixels(self.calendar_event.duration_min)
        )

    def paint(self, painter: QPainter, option, widget=None):
        """
        Paint the event box, title, and time range.
        """
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)
        # Color theme selection
        if mode_colors == LIGHT_MODE:
            theme = EVENT_COLOR_THEMES_LIGHT[self.calendar_event.color_idx % 4]
        else:
            theme = EVENT_COLOR_THEMES_DARK[self.calendar_event.color_idx % 4]
        painter.setPen(QPen(QColor(theme["event_pen"]), 1))
        painter.setBrush(QBrush(QColor(theme["event_bg"])))
        painter.drawRoundedRect(rect, 6, 6)

        start_str = self.calendar_event.start.strftime("%a %H:%M")
        end_time = self.calendar_event.start + \
            timedelta(minutes=self.calendar_event.duration_min)
        end_str = end_time.strftime("%H:%M")
        text = f"{self.calendar_event.title}\n{start_str} - {end_str}"

        box_height = rect.height()
        if box_height < 48:
            # For very short event boxes, use minimal margin
            text_rect = rect.adjusted(3, 2, -3, -2)
        else:
            # For normal/large event boxes, keep more margin and room for resizer handle
            text_rect = rect.adjusted(6, 6, -6, -HANDLE_HEIGHT - 2)

        painter.setPen(QColor(theme["event_text"]))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(text_rect, Qt.TextWordWrap, text)

    def hoverMoveEvent(self, event):
        """
        Update cursor on mouse hover for resize zone.
        """
        if event.pos().y() >= self.boundingRect().height() - HANDLE_HEIGHT:
            self.setCursor(QCursor(Qt.SizeVerCursor))
        else:
            self.setCursor(QCursor(Qt.OpenHandCursor))
        super().hoverMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
        Show color selection popup on double-click.
        """
        if event.button() == Qt.LeftButton:
            # Show popup for color selection
            color_themes = EVENT_COLOR_THEMES_LIGHT if mode_colors == LIGHT_MODE else EVENT_COLOR_THEMES_DARK
            popup = EventColorPopup(
                color_themes, parent=self.scene().views()[0])
            popup.color_selected.connect(self._set_color_idx)
            global_pos = self.scene().views()[0].mapToGlobal(self.scene().views()[
                0].mapFromScene(self.scenePos() + event.pos()))
            popup.move(global_pos.x() + 10, global_pos.y())
            popup.show()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def _set_color_idx(self, idx):
        """
        Set event color index and redraw.
        """
        self.calendar_event.color_idx = idx
        self.update()
        if self.scene():
            self.scene().update()

    def mousePressEvent(self, event):
        """
        Start resizing on handle, otherwise prepare for dragging.
        """
        if event.button() == Qt.LeftButton:
            if event.pos().y() >= self.boundingRect().height() - HANDLE_HEIGHT:
                self.resizing = True
                self._drag_start_y = event.pos().y()
                self._initial_height = self.boundingRect().height()
                self.setCursor(QCursor(Qt.SizeVerCursor))
                event.accept()
                return
            else:
                self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Resize event duration interactively or move event.
        """
        if self.resizing:
            dy = event.pos().y() - self._drag_start_y
            new_height = max(self.scene_ref.minutes_to_pixels(
                SNAP_MINUTES), self._initial_height + dy)
            col_top_scene_y = self.y()
            day_bottom_scene_y = self.scene_ref.day_bottom_y()
            max_height = day_bottom_scene_y - col_top_scene_y
            new_height = min(new_height, max_height)
            new_minutes = snap_minutes(
                int(new_height / self.scene_ref._minute_pixel_factor))
            self.calendar_event.duration_min = max(SNAP_MINUTES, new_minutes)
            self.scene_ref.update()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Finish resizing or moving.
        """
        if self.resizing:
            self.resizing = False
            self._update_geometry_from_event()
            self.setCursor(QCursor(Qt.OpenHandCursor))
            event.accept()
            return
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """
        Track position changes and update start time/column accordingly.
        """
        if change == QGraphicsObject.ItemPositionChange and not self.resizing:
            new_pos: QPointF = value
            col_idx = self.scene_ref.x_to_day_index(new_pos.x())
            col_x = self.scene_ref.day_index_to_x(col_idx) + PADDING
            y = max(HEADER_HEIGHT, new_pos.y())
            max_y = self.scene_ref.day_bottom_y(
            ) - self.scene_ref.minutes_to_pixels(self.calendar_event.duration_min)
            y = min(y, max_y)
            minutes_from_start = snap_minutes(
                int((y - HEADER_HEIGHT) / self.scene_ref._minute_pixel_factor))
            day_date = self.week_start + timedelta(days=col_idx)
            new_start = day_date.replace(
                hour=START_HOUR, minute=0, second=0, microsecond=0) + timedelta(minutes=minutes_from_start)
            self.calendar_event.start = new_start
            return QPointF(col_x, HEADER_HEIGHT + self.scene_ref.minutes_to_pixels(minutes_from_start))
        return super().itemChange(change, value)

    def _update_geometry_from_event(self):
        """
        Update this item's position and geometry from current event start/duration.
        """
        delta_days = (self.calendar_event.start.date() -
                      self.week_start.date()).days
        col_idx = max(0, min(6, delta_days))
        col_x = self.scene_ref.day_index_to_x(col_idx) + PADDING
        minutes_since_start = (
            (self.calendar_event.start.hour - START_HOUR) * 60 + self.calendar_event.start.minute)
        minutes_since_start = max(
            0, min((END_HOUR - START_HOUR) * 60 - SNAP_MINUTES, minutes_since_start))
        snapped = snap_minutes(minutes_since_start)
        y = HEADER_HEIGHT + self.scene_ref.minutes_to_pixels(snapped)
        self.setPos(QPointF(col_x, y))
        self.prepareGeometryChange()


class TodoItemWidget(QWidget):
    """
    Widget representing one to-do task in a day's to-do list.

    Signals:
        remove_requested: Emitted when user requests this item to be deleted.
    """
    remove_requested = Signal(QWidget)  # already present

    def __init__(self, text="", checked=False, parent=None):
        """
        Initialize todo item widget with text and checked state.

        Args:
            text (str): Task title.
            checked (bool): Completion state.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(4)
        self.handle = QToolButton()
        self.handle.setIcon(svg_icon(HANDLE_SVG))
        self.handle.setIconSize(QSize(16, 16))
        self.handle.setStyleSheet(
            "QToolButton { border:none;background:transparent;padding:1px; }")
        self.handle.setCursor(Qt.OpenHandCursor)
        self.handle.pressed.connect(self.start_drag)
        lay.addWidget(self.handle)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        lay.addWidget(self.checkbox)
        lay.addSpacing(8)
        self.edit = QLineEdit(text)
        self.edit.setStyleSheet(
            "border:none;background:transparent;font-size:12px;")
        lay.addWidget(self.edit)
        self.delete_btn = QToolButton()
        self.delete_btn.setText("×")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setStyleSheet(
            "QToolButton { border:none; color:#d22; font-weight:bold; font-size:17px; }"
            "QToolButton:hover { background: #ffd2d2; }"
        )
        self.delete_btn.setToolTip("Delete To-do")
        self.delete_btn.clicked.connect(self._emit_remove_requested)
        lay.addWidget(self.delete_btn)

        # <---- Connect the checkbox toggled event to a slot
        self.checkbox.stateChanged.connect(self._update_text_style)

        self._update_text_style()  # Initial style

    def _emit_remove_requested(self):
        """
        Emit the remove_requested signal for deletion.
        """
        self.remove_requested.emit(self)

    def _update_text_style(self):
        """
        Update styling of text based on completion state.
        """
        if self.checkbox.isChecked():
            self.edit.setStyleSheet(
                f'''
                border:none;background:transparent;
                color:{mode_colors['todo_done_text']};
                font-size:12px;
                text-decoration: line-through;
                '''
            )
            self._show_confetti()
        else:
            self.edit.setStyleSheet(
                f'''
                border:none;background:transparent;
                color:{mode_colors['text']};
                font-size:12px;
                '''
            )

    def _show_confetti(self):
        """
        Show confetti animation when task marked as done.
        """
        # Find global position for effect (around checkbox or lineedit)
        widget = self.checkbox
        pos = widget.mapToGlobal(widget.rect().center())
        parent_widget = self.window()
        local_pos = parent_widget.mapFromGlobal(pos)
        ConfettiBurstWidget(parent_widget, local_pos)

    def start_drag(self):
        """
        Start drag-and-drop for this todo item.
        """
        mime = QMimeData()
        payload = {"title": self.edit.text(), "duration_min": 60}
        mime.setData("application/x-task-todo",
                     json.dumps(payload).encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)

    @property
    def text(self):
        """
        Get the current text of the to-do item.

        Returns:
            str: Current text in lineedit.
        """
        return self.edit.text()


class DayTodoList(QWidget):
    """
    Widget holding the to-do list for a single day.
    """

    def __init__(self, day_name, parent=None):
        """
        Create a to-do list widget for a given day.

        Args:
            day_name (str): Name of the day (e.g., "Mon").
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)
        self.day_name = day_name
        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(2, 2, 2, 2)
        self.outer.setSpacing(4)
        lab = QLabel(f"To-do ({day_name})")
        lab.setStyleSheet(
            f"font-weight:bold; font-size:13px; color:{mode_colors['text']};")
        self.outer.addWidget(lab, alignment=Qt.AlignLeft)
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.NoSelection)
        self.list.setSpacing(2)
        self.list.setStyleSheet(f"""
            QListWidget {{
                background:{mode_colors['todo_bg']};
                border-radius:10px;
                border:1px solid {mode_colors['todo_border']};
            }}
            QListWidget::item:selected {{
                background: transparent;
            }}
        """)
        self.outer.addWidget(self.list)
        addbar = QHBoxLayout()
        addbar.setSpacing(2)
        self.addbox = QLineEdit()
        self.addbox.setPlaceholderText("Add to-do...")
        self.addbox.setStyleSheet(
            "border-radius:7px; font-size:13px; padding:3px;")
        addbar.addWidget(self.addbox)
        self.add_btn = QToolButton()
        self.add_btn.setText("+")
        self.add_btn.setFixedSize(22, 22)
        self.add_btn.setStyleSheet(
            "font-weight:bold; font-size:17px; border:none; padding:2px;")
        addbar.addWidget(self.add_btn)
        self.outer.addLayout(addbar)
        self.addbox.returnPressed.connect(self._add_todo_from_box)
        self.add_btn.clicked.connect(self._add_todo_from_box)

    def _add_todo_from_box(self):
        """
        Add a new to-do item from the input box, if non-empty.
        """
        text = self.addbox.text().strip()
        if text:
            self.add_todo(text)
            self.addbox.clear()

    def add_todo(self, text="", checked=False):
        """
        Add a todo item widget with given text and checked state.

        Args:
            text (str): Title of the task.
            checked (bool): Task completion state.
        """
        if not text.strip():
            return
        widg = TodoItemWidget(text, checked, parent=self)
        # Connect the delete signal
        widg.remove_requested.connect(self.remove_todo_widget)
        item = QListWidgetItem()
        item.setSizeHint(widg.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, widg)
        QTimer.singleShot(0, lambda: widg.edit.setFocus())

    def remove_todo_widget(self, widg):
        """
        Remove a specific todo item widget.

        Args:
            widg (TodoItemWidget): Widget to remove.
        """
        for i in range(self.list.count()):
            item = self.list.item(i)
            if self.list.itemWidget(item) is widg:
                self.list.takeItem(i)
                widg.deleteLater()  # Cleanup widget
                break

    def todos(self):
        """
        Get a list of all to-dos in the list.

        Returns:
            list[dict]: List of todos (title, checked status).
        """
        out = []
        for i in range(self.list.count()):
            widg = self.list.itemWidget(self.list.item(i))
            out.append({"title": widg.edit.text(),
                       "checked": widg.checkbox.isChecked()})
        return out


class TodoListsRow(QWidget):
    """
    Container widget displaying seven DayTodoList panels for the week.
    """

    def __init__(self):
        """
        Initialize with all weekdays' todo lists.
        """
        super().__init__()
        self.todo_lists_bar = QHBoxLayout(self)
        self.todo_lists_bar.setContentsMargins(10, 10, 10, 10)
        self.todo_lists_bar.setSpacing(7)
        self.list_widgets = []
        for i, day in enumerate(DAY_NAMES):
            lst = DayTodoList(day)
            lst.setMaximumWidth(9999)
            lst.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.todo_lists_bar.addWidget(lst)
            self.list_widgets.append(lst)
        self.setLayout(self.todo_lists_bar)

    def set_column_width(self, width):
        """
        Set maximum and minimum widths for each todo column.

        Args:
            width (int): Desired width per column.
        """
        for l in self.list_widgets:
            l.setMaximumWidth(width)
            l.setMinimumWidth(40)


class EventColorPopup(QWidget):
    """
    Popup widget for picking event color themes.

    Signals:
        color_selected: Emitted with selected color index.
    """
    color_selected = Signal(int)

    def __init__(self, base_colors, parent=None):
        """
        Create popup for color choices.

        Args:
            base_colors (list): List of color theme dicts.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent, Qt.Popup)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)
        self.setFixedHeight(34)
        for idx, theme in enumerate(base_colors):
            btn = QToolButton(self)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: {theme['event_bg']};
                    border: 2px solid {theme['event_pen']};
                    border-radius: 14px;
                }}
                QToolButton:hover {{
                    border: 2px solid #ffae00;
                }}
            """)
            btn.clicked.connect(lambda _, ix=idx: self._color_chosen(ix))
            lay.addWidget(btn)
        self.setLayout(lay)

    def _color_chosen(self, idx):
        """
        Emit selected color index and close popup.

        Args:
            idx (int): Selected color theme index.
        """
        self.color_selected.emit(idx)
        self.close()


class RoundedWidget(QWidget):
    """
    Widget with rounded corners for use as application background.
    """

    def __init__(self, radius=20):
        """
        Initialize rounded widget.

        Args:
            radius (int): Corner radius, default 20.
        """
        super().__init__()
        self.radius = radius
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        """
        Paint a rounded rectangle as the background.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.setBrush(QBrush(QColor(mode_colors["window_bg"])))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.radius, self.radius)


class ConfettiBurstWidget(QWidget):
    """
    Temporary widget for confetti burst animation.
    """

    def __init__(self, parent, pos, count=20):
        """
        Create confetti burst with random colored particles.

        Args:
            parent (QWidget): Parent window to display over.
            pos (QPoint): Center position for the burst.
            count (int): Number of particles.
        """
        super().__init__(parent)
        self.resize(parent.size())
        self.particles = []
        self.duration = 700  # milliseconds
        cx, cy = pos.x(), pos.y()
        for _ in range(count):
            angle = random.uniform(-0.7, 0.7)
            speed = random.uniform(5, 11)
            color = random.choice(
                ['#fa8080', '#48b07b', '#3a6fe2', '#ffe169', '#bbb321', '#c56868'])
            self.particles.append({
                "x": cx, "y": cy,
                "vx": speed * random.uniform(0.7, 1.0) * random.choice([-1, 1]),
                "vy": -speed * random.uniform(0.7, 1.0),
                "radius": random.randint(4, 7),
                "color": color,
                "angle": angle
            })
        self.elapsed = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(28)
        self.show()

    def animate(self):
        """
        Advance animation frame, move particles, close after duration.
        """
        self.elapsed += 28
        # Move particles
        for p in self.particles:
            p['x'] += p['vx'] * (self.timer.interval()/60)
            p['y'] += p['vy'] * (self.timer.interval()/60)
            p['vy'] += 0.7  # gravity
        self.repaint()
        if self.elapsed > self.duration:
            self.timer.stop()
            self.close()

    def paintEvent(self, event):
        """
        Draw animated confetti particles.
        """
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        for p in self.particles:
            qp.setBrush(QColor(p['color']))
            qp.setPen(Qt.NoPen)
            qp.drawEllipse(QPoint(int(p['x']), int(
                p['y'])), p['radius'], p['radius'])


class TestUtils(unittest.TestCase):
    """
    Unit tests for utility functions and data models in the weekly calendar application.
    """

    def test_snap_minutes(self):
        """
        Test that snap_minutes correctly rounds values to the nearest SNAP_MINUTES increment.
        """
        self.assertEqual(snap_minutes(12), 15)
        self.assertEqual(snap_minutes(21), 15)
        self.assertEqual(snap_minutes(37), 30)
        self.assertEqual(snap_minutes(0), 0)
        self.assertEqual(snap_minutes(60), 60)

    def test_week_monday(self):
        """
        Test that week_monday returns the correct Monday for a given date.
        """
        from datetime import datetime
        dt = datetime(2024, 4, 2)
        self.assertEqual(week_monday(dt).weekday(), 0)

    def test_calendar_event(self):
        """
        Test that CalendarEvent initializes its attributes properly.
        """
        from datetime import datetime
        e = CalendarEvent("Test Event", datetime(2024, 4, 1, 10, 0), 60)
        self.assertEqual(e.title, "Test Event")
        self.assertEqual(e.duration_min, 60)

    def test_calendar_model_add_remove(self):
        """
        Test that CalendarModel can add and remove events correctly.
        """
        m = CalendarModel()
        ev = CalendarEvent("Test", datetime(2024, 4, 1, 10, 0), 30)
        m.add_event(ev)
        self.assertIn(ev, m.events)
        m.remove_event(ev)
        self.assertNotIn(ev, m.events)

    def test_import_events_from_ics(self):
        """
        Test that importing events from a non-existent ICS file returns an Exception.
        """
        result = import_events_from_ics("no_file.ics")
        self.assertIsInstance(result, Exception)


def import_events_from_ics(filename):
    """
    Imports calendar events from an iCalendar (.ics) file.

    Args:
        filename (str): Path to .ics file.

    Returns:
        list[CalendarEvent] or Exception: List of imported events or the error encountered.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
        cal = Calendar(data)
        imported_events = []
        for event in cal.events:
            if not event.begin:
                continue
            start = event.begin.datetime
            duration = event.duration.total_seconds() / 60 if event.duration else 60
            title = event.name or "Imported Event"
            imported_events.append(CalendarEvent(
                title=title,
                start=start,
                duration_min=int(duration),
                color_idx=0
            ))

        return imported_events
    except Exception as e:
        return e  # Return error object for UI display


class MainWindow(QMainWindow):
    """
    Main window for the weekly planner application.
    Combines calendar, controls, and todo panels.
    """

    def __init__(self):
        """
        Set up the main interface, calendar, todo lists, and controls.
        """
        super().__init__()
        self.mode_light = False    # Start in dark mode
        set_mode(self.mode_light)
        self.setWindowTitle("Weekly Calendar (Mon–Sun)")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        today = datetime.now()
        self.week_start = week_monday(today).replace(
            hour=0, minute=0, second=0, microsecond=0)
        self.model = CalendarModel()
        self.scene = CalendarScene(self.week_start, self.model)
        self.view = CalendarView(self.scene, self.model)

        self.round_central = RoundedWidget(radius=24)
        layout = QVBoxLayout(self.round_central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        bar = QHBoxLayout()
        bar.setContentsMargins(16, 12, 16, 4)
        bar.setSpacing(8)

        # ------ SMALLER EXIT AND MINIMIZE BUTTONS ------
        self.close_btn = QToolButton()
        self.close_btn.setFixedSize(12, 12)
        self.close_btn.setStyleSheet("""
            QToolButton { background:#ff5f57; border:none; border-radius:4.5px;}
            QToolButton:hover { background:#e04845;}""")
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self.close)
        bar.addWidget(self.close_btn)

        self.min_btn = QToolButton()
        self.min_btn.setFixedSize(12, 12)
        self.min_btn.setStyleSheet("""
            QToolButton {
                background:#febc2e; border:none; border-radius:4.5px;
            }
            QToolButton:hover { background:#e1a317;}
        """)
        self.min_btn.setToolTip("Minimize")
        self.min_btn.clicked.connect(self.showMinimized)
        bar.addWidget(self.min_btn)

        bar.addSpacing(6)
        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(
            svg_icon(SUN_SVG if self.mode_light else MOON_SVG))
        self.toggle_btn.setIconSize(QSize(28, 28))
        self.toggle_btn.setStyleSheet(
            "QToolButton { border-radius:14px; background:transparent; }")
        self.toggle_btn.clicked.connect(self.toggle_mode)
        bar.addWidget(self.toggle_btn, alignment=Qt.AlignLeft)

        week_label = QLabel(self._week_label_text())
        week_label.setStyleSheet(
            "font-weight: bold; font-size: 18px; color: %s;" % mode_colors["text"])
        bar.addWidget(week_label, alignment=Qt.AlignVCenter)
        bar.addStretch(1)
        layout.addLayout(bar)

        # ------------ ZOOM BUTTONS -------------
        self.zoom_in_btn = QToolButton()
        self.zoom_in_btn.setText("＋")
        self.zoom_in_btn.setFixedSize(24, 24)
        self.zoom_in_btn.setStyleSheet(f"""
            QToolButton {{
                font-size:18px;
                font-weight:bold;
                border:none;
                background: {mode_colors['header_bg']};
                color: {mode_colors['text']};
                border-radius: 12px;
            }}
            QToolButton:hover {{
                background: {mode_colors['event_bg']};
                color: {mode_colors['event_pen']};
            }}
        """)
        self.zoom_in_btn.setToolTip("Zoom In (vertical)")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        bar.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QToolButton()
        self.zoom_out_btn.setText("－")
        self.zoom_out_btn.setFixedSize(24, 24)
        self.zoom_out_btn.setStyleSheet(f"""
            QToolButton {{
                font-size:18px;
                font-weight:bold;
                border:none;
                background: {mode_colors['header_bg']};
                color: {mode_colors['text']};
                border-radius: 12px;
            }}
            QToolButton:hover {{
                background: {mode_colors['event_bg']};
                color: {mode_colors['event_pen']};
            }}
        """)
        self.zoom_out_btn.setToolTip("Zoom Out (vertical)")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        bar.addWidget(self.zoom_out_btn)
        self.calendar_zoom = 1.0  # 1.0 is normal, higher means zoomed in

        # ------------ IMPORT BUTTON -------------
        self.import_btn = QToolButton()
        self.import_btn.setText("Import .ics")
        self.import_btn.setFixedSize(60, 20)
        self.import_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                border-radius: 8px;
                background: {mode_colors['header_bg']};
                color: {mode_colors['text']};
                font-size: 8px;
                font-weight: normal;
            }}
            QToolButton:hover {{
                background: {mode_colors['event_bg']};
                color: {mode_colors['event_pen']};
            }}
        """)
        self.import_btn.setToolTip("Import events from a .ics file")
        self.import_btn.clicked.connect(self.import_events)
        bar.addWidget(self.import_btn, alignment=Qt.AlignVCenter)

        # --- Splitter for calendar/todos sections ---
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet(
            "QSplitter::handle { background: #444457; border-radius:4px;}")

        # --- Scrollable calendar view + space below before splitter
        scroll_area_container = QWidget()
        scroll_area_container_layout = QVBoxLayout(scroll_area_container)
        scroll_area_container_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area_container_layout.setSpacing(0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setWidget(self.view)
        scroll_area_container_layout.addWidget(self.scroll_area)
        spacer = QWidget()
        spacer.setFixedHeight(SPACE_BELOW_CAL)
        scroll_area_container_layout.addWidget(spacer)
        splitter.addWidget(scroll_area_container)

        # --- Todo lists row ---
        self.todos_row_widget = TodoListsRow()
        self.todos_row_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.todos_row_widget)

        layout.addWidget(splitter)
        self.setCentralWidget(self.round_central)
        self.resize(1200, 710)

        QTimer.singleShot(0, lambda: splitter.setSizes(
            [int(self.height()*0.72), int(self.height()*0.28)]))
        # Added: Fix initial todo width
        QTimer.singleShot(0, self._set_initial_todo_widths)

        self.offset = None

    def _set_initial_todo_widths(self):
        """
        Set initial column widths for todos after window display.
        """
        w = self.view.viewport().width()
        per_column = max(80, (w - TIME_LABEL_WIDTH) // 7)
        self.todos_row_widget.set_column_width(per_column)

    def resizeEvent(self, ev):
        """
        Adjust sizes of calendar and todo lists after window resize.
        """
        super().resizeEvent(ev)
        w = self.view.viewport().width()
        if hasattr(self.scene, "set_size"):
            self.scene.set_size(w, self.view.viewport().height()-HEADER_HEIGHT)
        per_column = max(80, (w - TIME_LABEL_WIDTH) // 7)
        self.todos_row_widget.set_column_width(per_column)

    def _week_label_text(self) -> str:
        """
        Generate display label text for the current week range.

        Returns:
            str: Week label string.
        """
        end = self.week_start + timedelta(days=6)
        return f"Week of {self.week_start.strftime('%d %b %Y')} — {end.strftime('%d %b %Y')}"

    def toggle_mode(self):
        """
        Toggle between dark and light mode UI.
        """
        self.mode_light = not self.mode_light
        set_mode(self.mode_light)
        self.toggle_btn.setIcon(
            svg_icon(SUN_SVG if self.mode_light else MOON_SVG))
        self.scene.refresh_background()
        # Update styles of todo lists and labels
        for lst in self.todos_row_widget.list_widgets:
            lst.list.setStyleSheet(f"""
                QListWidget {{
                    background:{mode_colors['todo_bg']};
                    border-radius:10px;
                    border:1px solid {mode_colors['todo_border']};
                }}
                QListWidget::item:selected {{
                    background: transparent;
                }}
            """)
            for j in range(lst.list.count()):
                widg = lst.list.itemWidget(lst.list.item(j))
                if widg.checkbox.isChecked():
                    widg.edit.setStyleSheet(f"""
                        border:none;background:transparent;color:{mode_colors['todo_done_text']};
                        font-size:12px;text-decoration: line-through;
                    """)
                else:
                    widg.edit.setStyleSheet(
                        f"border:none;background:transparent;color:{mode_colors['text']};font-size:12px;"
                    )
            # ------ UPDATE PLUS BUTTON FOR ALL TODO PANELS ------------------
            lst.add_btn.setStyleSheet(f"""
                font-weight:bold; font-size:17px; border:none; padding:2px;
                background: {mode_colors['header_bg']};
                color: {mode_colors['text']};
                border-radius:9px;
            """)
        # Update events with new color scheme
        for item in self.scene.items():
            if isinstance(item, EventItem):
                item.update()
        self.round_central.update()
        self.view.setBackgroundBrush(QBrush(QColor(mode_colors["window_bg"])))
        for w in self.findChildren(QLabel):
            w.setStyleSheet("color: %s;" % mode_colors["text"])

        # ------ UPDATE ZOOM BUTTONS ------------------
        self.zoom_in_btn.setStyleSheet(f"""
            QToolButton {{
                font-size:18px; font-weight:bold; border:none;
                background: {mode_colors['header_bg']};
                color: {mode_colors['text']};
                border-radius: 12px;
            }}
            QToolButton:hover {{
                background: {mode_colors['event_bg']};
                color: {mode_colors['event_pen']};
            }}
        """)
        self.zoom_out_btn.setStyleSheet(f"""
            QToolButton {{
                font-size:18px; font-weight:bold; border:none;
                background: {mode_colors['header_bg']};
                color: {mode_colors['text']};
                border-radius: 12px;
            }}
            QToolButton:hover {{
                background: {mode_colors['event_bg']};
                color: {mode_colors['event_pen']};
            }}
        """)

        # ------ UPDATE IMPORT BUTTON ------------------
        self.import_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                border-radius: 8px;
                background: {mode_colors['header_bg']};
                color: {mode_colors['text']};
                font-size: 8px;
                font-weight: normal;
            }}
            QToolButton:hover {{
                background: {mode_colors['event_bg']};
                color: {mode_colors['event_pen']};
            }}
        """)

        self.setWindowTitle("Weekly Planner")

        self.update()

    def mousePressEvent(self, event):
        """
        Begin window drag/move for frameless window.
        """
        if event.button() == Qt.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """
        Move window if drag is in progress.
        """
        if self.offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        """
        Finish window drag/move.
        """
        self.offset = None

    def zoom_in(self):
        """
        Increase calendar vertical zoom.
        """
        self.calendar_zoom = min(3.0, self.calendar_zoom + 0.25)
        self._update_calendar_zoom()

    def zoom_out(self):
        """
        Decrease calendar vertical zoom.
        """
        self.calendar_zoom = max(0.5, self.calendar_zoom - 0.25)
        self._update_calendar_zoom()

    def _update_calendar_zoom(self):
        """
        Update calendar grid height and scene after zoom change.
        """
        base_height = DEFAULT_GRID_MIN_HEIGHT
        new_height = int(base_height * self.calendar_zoom)
        self.scene.set_size(self.view.viewport().width(), new_height)
        self.view.setMinimumHeight(HEADER_HEIGHT + new_height)
        self.scroll_area.setWidgetResizable(True)
        self.scene.update()

    def import_events(self):
        """
        Open file dialog and import events from selected .ics file.
        """
        file, _ = QFileDialog.getOpenFileName(
            self, "Select .ics calendar file", "", "iCalendar Files (*.ics);;All Files (*)")
        if not file:
            return
        result = import_events_from_ics(file)
        if isinstance(result, Exception):
            QMessageBox.warning(
                self, "Import Error", f"Could not import events from file.\n\nError: {result}")
            return
        count_added = 0
        shown_start = self.week_start
        shown_end = self.week_start + timedelta(days=7)
        for ev in result:
            ev_start = ev.start
            if ev_start.tzinfo is not None:
                ev_start = ev_start.replace(tzinfo=None)
            if (ev_start >= shown_start) and (ev_start < shown_end):
                self.model.add_event(ev)
                self.scene.add_event_item(ev)
                count_added += 1
        if count_added == 0:
            QMessageBox.information(
                self, "Import Complete", "No events found in selected .ics file for this week.")
        else:
            QMessageBox.information(
                self, "Import Complete", f"Imported {count_added} events for this week.")


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("appicon.png"))
    app.setApplicationName("Weekly Planner")
    win = MainWindow()
    win.setWindowIcon(QIcon("appicon.png"))
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_tests = False  # Set to True to run tests, False to run the app
    if run_tests:
        unittest.main()
    else:
        main()
