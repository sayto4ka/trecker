"""
widgets.py — переиспользуемые виджеты нового дизайна.
"""
from __future__ import annotations

import re
import os
import calendar
from datetime import date, timedelta
from typing import Optional

from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy as _QSP
from PySide6.QtCore import QRect, QPoint, QSize as _QSize

from PySide6.QtCore import Qt, Signal, QSize, QPointF, QRectF
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QFrame,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QTimeEdit, QGraphicsDropShadowEffect,
    QScrollArea, QSizePolicy, QAbstractButton
)

from models import Habit, HabitStore, WEEKDAYS_RU_SHORT, MONTHS_RU, THEME_COLORS, today, MARK_COLORS, PERIODS, str_to_date

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

# ---------------------------------------------------------------- базовая палитра (не зависит от темы)
COLOR_APP_BG = "#0d0d0f"        # статичный фон приложения — строго по дизайну
COLOR_ONBOARD_BG = "#bababa"    # фон онбординга (обновлено по новому HTML/CSS макету)
COLOR_CARD_WHITE = "#ffffff"
COLOR_CARD_TRANSLUCENT = "rgba(255,255,255,0.55)"
COLOR_TEXT_DARK = "#1c1c22"
COLOR_TEXT_MUTED = "rgba(28,28,34,0.6)"
COLOR_NAV_BG = "#d4d4d8"        # zinc-300

# фиксированные цвета карточек на главном экране — НЕ зависят от случайного фона
COLOR_HABITS_CARD = "#5D5FEF"
COLOR_ADD_CARD = "#B9AEDD"
COLOR_HOME_CARD_BG = "#272732"   # фон обеих карточек на главном экране (новый тёмный дизайн)

ICON_CHOICES = ["⭐", "💧", "🏃", "📖", "🧘", "🍎", "😴", "💊", "✍️", "🎯", "🚭", "💪"]
FONT_SCALE = 1.0
_FONT_SIZE_RE = re.compile(r"font-size:\s*(\d+)px")
_orig_set_style_sheet = QWidget.setStyleSheet


def _scaled_set_style_sheet(self, css: str):
    if css:
        css = _FONT_SIZE_RE.sub(lambda m: f"font-size:{max(1, round(int(m.group(1)) * FONT_SCALE))}px", css)
    _orig_set_style_sheet(self, css)


QWidget.setStyleSheet = _scaled_set_style_sheet


def set_font_scale(scale: float):
    global FONT_SCALE
    FONT_SCALE = scale

def res_icon(filename: str) -> QIcon:
    return QIcon(os.path.join(RESOURCES_DIR, filename))


def hide_scrollbar(scroll_area) -> None:
    """Полностью убирает визуальные элементы скроллбара (полосу, ползунок, стрелки) —
    один Policy=AlwaysOff иногда не убирает нативные стрелки Windows-темы полностью,
    поэтому дополнительно обнуляем их через QSS."""
    from PySide6.QtWidgets import QScrollArea
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    no_bar_qss = (
        "QScrollBar:vertical, QScrollBar:horizontal { width: 0px; height: 0px; background: transparent; border: none; margin: 0px; }"
        "QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: transparent; }"
        "QScrollBar::add-line, QScrollBar::sub-line { width: 0px; height: 0px; background: transparent; border: none; }"
        "QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }"
    )
    scroll_area.verticalScrollBar().setStyleSheet(no_bar_qss)
    scroll_area.horizontalScrollBar().setStyleSheet(no_bar_qss)

def subtle_scrollbar_qss() -> str:
    """Тонкий, малозаметный скроллбар вместо нативного (с обрезанными стрелками OS)."""
    return (
        "QScrollBar:horizontal { height: 5px; background: transparent; margin: 0px; }"
        "QScrollBar::handle:horizontal { background: rgba(255,255,255,0.18); border-radius: 2px; min-width: 24px; }"
        "QScrollBar::handle:horizontal:hover { background: rgba(255,255,255,0.32); }"
        "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; border: none; background: transparent; }"
        "QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }"
        "QScrollBar:vertical { width: 0px; background: transparent; }"
    )

def tinted_pixmap(filename: str, size: int, color: str) -> "QPixmap":
    """Перекрашивает силуэт PNG-иконки (сохраняя альфа-канал) в нужный цвет —
    исходные ресурсы тёмно-серые и на тёмном фоне почти не видны."""
    from PySide6.QtGui import QPixmap
    src = res_icon(filename).pixmap(size, size)
    tinted = QPixmap(src.size())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, src)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(color))
    painter.end()
    return tinted

def circular_icon_pixmap(filename: str, diameter: int, bg_color: str = "#d9d9d9", padding_ratio: float = 0.18):
    from PySide6.QtGui import QPixmap, QPainterPath
    pm = QPixmap(diameter, diameter)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, diameter, diameter)
    painter.setClipPath(path)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(bg_color))
    painter.drawEllipse(0, 0, diameter, diameter)
    inner = max(1, int(diameter * (1 - 2 * padding_ratio)))
    src = res_icon(filename).pixmap(inner, inner)
    scaled = src.scaled(inner, inner, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    x = (diameter - scaled.width()) // 2
    y = (diameter - scaled.height()) // 2
    painter.drawPixmap(x, y, scaled)
    painter.end()
    return pm

def badge_color(key: str) -> str:
    return THEME_COLORS[hash(key) % len(THEME_COLORS)][1]


def add_shadow(widget: QWidget, blur=20, y_offset=4, alpha=45):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_offset)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)


def icon_badge(icon: str, key: str, size: int = 40) -> QLabel:
    lbl = QLabel(icon)
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignCenter)
    f = QFont()
    f.setPointSize(max(11, size // 3))
    lbl.setFont(f)
    lbl.setStyleSheet(f"background-color: {badge_color(key)}; border-radius: {size // 2}px;")
    return lbl


def primary_button(text: str, accent: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(
        f"QPushButton {{ background-color: {accent}; color: white; border-radius: 12px; "
        f"padding: 12px; font-weight: 700; font-size: 14px; }}"
        f"QPushButton:hover {{ background-color: {accent}; opacity: 0.9; }}"
    )
    return btn


# ------------------------------------------------------------------ TopBar

class TopBar(QWidget):
    """Заголовок экрана; при show_back=True показывает стрелку назад слева.
    Текст светлый — все страницы теперь на тёмном фоне приложения."""

    back_clicked = Signal()


    def __init__(self, title: str, show_back: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        left_slot = QPushButton("←") if show_back else QLabel("")
        left_slot.setFixedSize(40, 40)
        if show_back:
            left_slot.setStyleSheet(
                "QPushButton { background-color: rgba(255,255,255,0.16); border-radius: 20px; "
                "font-size: 16px; font-weight: 700; color: #ffffff; }"
                "QPushButton:hover { background-color: rgba(255,255,255,0.28); }"
            )
            left_slot.setCursor(Qt.PointingHandCursor)
            left_slot.clicked.connect(self.back_clicked.emit)

        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 16px; font-weight: 700;")

        right_spacer = QLabel("")
        right_spacer.setFixedSize(40, 40)

        layout.addWidget(left_slot)
        layout.addWidget(self.title_lbl, 1)
        layout.addWidget(right_spacer)

    def set_title(self, text: str):
        self.title_lbl.setText(text)    

# ------------------------------------------------------------------ Week strip
class DayCell(QFrame):
    """Ячейка дня. Прошедшие/сегодняшние дни — светлее, будущие — темнее и приглушённее,
    как в дизайне. Сегодняшний день выделяется белой заливкой; маркер-«таблетка» под ним
    рисуется отдельным элементом ниже (не внутри самой карточки)."""

    def __init__(self, day_num: int, weekday_letters: str, is_today: bool, is_past_or_today: bool, parent=None):
        super().__init__(parent)
        if is_today:
            self.setFixedSize(40, 58)
            bg = "#ffffff"
        elif is_past_or_today:
            self.setFixedSize(36, 52)
            bg = "rgba(255,255,255,0.7)"
        else:
            self.setFixedSize(36, 52)
            bg = "rgba(255,255,255,0.3)"
        self.setStyleSheet(f"QFrame {{ background-color: {bg}; border-radius: 10px; border: none; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 6, 2, 4)
        layout.setSpacing(3)
        num = QLabel(str(day_num))
        num.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setBold(True)
        f.setPointSize(11)
        num.setFont(f)
        num.setStyleSheet("color: #0d0d0f; background: transparent; border: none;")
        layout.addWidget(num)


class TodayMarker(QWidget):
    """Маленькая белая «таблетка»-индикатор под текущим днём, отдельно от карточки дня.
    Рисуется вручную (а не через QSS border-radius на QLabel), потому что стилевой
    движок иногда скругляет скруглённый прямоугольник только с одной стороны."""

    def __init__(self, visible: bool, parent=None):
        super().__init__(parent)
        self._visible = visible
        self.setFixedSize(28, 12)

    def paintEvent(self, event):
        if not self._visible:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#fcfdff"))
        h = 8
        y = (self.height() - h) / 2
        painter.drawRoundedRect(QRectF(0, y, self.width(), h), h / 2, h / 2)


class WeekStrip(QWidget):
    """Строка месяца (кликабельно), дней недели и чисел."""

    month_clicked = Signal()

    def __init__(self, store: HabitStore, font_family: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.store = store
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        t = today()
        month_btn = QPushButton(MONTHS_RU[t.month - 1])
        month_btn.setCursor(Qt.PointingHandCursor)
        month_btn.setStyleSheet(
            "QPushButton { background-color: rgba(160,164,169,0.2); color: rgba(255,255,255,0.7); "
            "border: 1px solid rgba(253,253,253,0.5); border-radius: 15px; padding: 5px 16px; "
            "font-weight: 600; text-align: left; }"
            "QPushButton:hover { background-color: rgba(160,164,169,0.35); }"
        )
        if font_family:
            month_btn.setFont(QFont(font_family, 10))
        month_btn.clicked.connect(self.month_clicked.emit)
        month_row = QHBoxLayout()
        month_row.addWidget(month_btn)
        month_row.addStretch()
        outer.addLayout(month_row)

        weekday_row = QHBoxLayout()
        weekday_row.setSpacing(6)
        for wd in WEEKDAYS_RU_SHORT:
            lbl = QLabel(wd)
            lbl.setFixedWidth(38)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px; font-weight: 600;")
            if font_family:
                lbl.setFont(QFont(font_family, 9))
            weekday_row.addWidget(lbl)
        outer.addLayout(weekday_row)

        days_row = QHBoxLayout()        #bug fix from DeepSeek
        days_row.setSpacing(6)
        for d in store.week_dates():
            is_today = d == t
            cell = DayCell(d.day, WEEKDAYS_RU_SHORT[d.weekday()], is_today, d <= t)

            # одна вертикальная колонка: карточка сверху, маркер снизу
            col = QVBoxLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(4)
            col.addWidget(cell, 0, Qt.AlignHCenter)          # карточка по центру колонки
            col.addWidget(TodayMarker(is_today), 0, Qt.AlignHCenter)  # pill по центру колонки

            wrapper = QWidget()
            wrapper.setLayout(col)
            # ширина колонки = максимальная ширина среди карточек (40 у сегодня, 36 у остальных)
            wrapper.setFixedWidth(40)
            days_row.addWidget(wrapper, 0, Qt.AlignTop)
        outer.addLayout(days_row)

# ------------------------------------------------------------------ Reminder preview (Home)
class DoubleChevronDown(QWidget):
    """Двойной шеврон-«галочка» вниз (индикатор разворачивания списка).
    Рисуется вручную, чтобы не зависеть от того, есть ли нужный глиф в шрифте
    (иначе на некоторых системах символ подменяется цветным emoji)."""

    def __init__(self, size: int = 16, color: str = "rgba(255,255,255,0.5)", parent=None):
        super().__init__(parent)
        self._color = QColor(color) if not color.startswith("rgba") else _parse_rgba(color)
        self.setFixedSize(size, size + 4)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self._color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        w = self.width()
        for y_off in (2, 8):
            painter.drawPolyline([QPointF(2, y_off), QPointF(w / 2, y_off + 5), QPointF(w - 2, y_off)])


def _parse_rgba(rgba_str: str) -> QColor:
    nums = rgba_str[rgba_str.index("(") + 1: rgba_str.index(")")].split(",")
    r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
    a = float(nums[3])
    c = QColor(r, g, b)
    c.setAlphaF(a)
    return c


class ReminderPreviewCard(QFrame):
    """Мини-виджет «Ближайшие задачи» на главном экране — кликабельный, ведёт на полный список.
    Будильник ставится только у ближайшей по времени задачи (при равенстве времени — у всех таких)."""

    clicked = Signal()

    def __init__(self, store: HabitStore, font_family: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background-color: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.18); "
            "border-radius: 12px; } "
            "QLabel { background: transparent; border: none; }"
        )
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        def styled(lbl: QLabel, size: int, bold: bool = False):
            if font_family:
                f = QFont(font_family, size)
                if bold:
                    f.setBold(True)
                lbl.setFont(f)
            return lbl

        header_row = QHBoxLayout()
        header = QLabel("Ближайшие задачи")
        header.setStyleSheet("color: white; font-size: 15px; font-weight: 700;")
        styled(header, 12, bold=True)
        header_row.addWidget(header)
        header_row.addStretch()
        chevrons = DoubleChevronDown(size=16, color="rgba(255,255,255,0.5)")
        header_row.addWidget(chevrons)
        layout.addLayout(header_row)

        upcoming = store.upcoming_reminders()
        if not upcoming:
            empty = QLabel("На сегодня всё сделано 🎉")
            empty.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px;")
            styled(empty, 10)
            layout.addWidget(empty)
        else:
            nearest_time = upcoming[0].reminder_time
            for h in upcoming[:2]:
                row = QHBoxLayout()
                name = QLabel(h.name)
                name.setStyleSheet("color: white; font-size: 13px; font-weight: 600;")
                styled(name, 11, bold=True)
                row.addWidget(name)
                row.addStretch()
                t_lbl = QLabel(h.reminder_time)
                t_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 13px;")
                styled(t_lbl, 11)
                row.addWidget(t_lbl)
                if h.reminder_time == nearest_time:
                    alarm = QLabel()
                    alarm.setPixmap(tinted_pixmap("alarm_icon.png", 18, "#f2f2f5"))
                    row.addWidget(alarm)
                layout.addLayout(row)
            if len(upcoming) > 2:
                more = QLabel(f"и ещё {len(upcoming) - 2}...")
                more.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px;")
                styled(more, 9)
                layout.addWidget(more)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ------------------------------------------------------------------ Reminders full list row
class ReminderRow(QFrame):
    """Карточка задачи в списке «Ближайшие задачи» — строго по новому дизайну:
    белая карточка 82px, название + время, будильник только у ближайшей по времени."""

    def __init__(self, habit: Habit, is_nearest: bool = False, font_family: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(82)
        self.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_CARD_WHITE}; border-radius: 19px; }}"
        )
        add_shadow(self, blur=16, y_offset=3, alpha=35)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(17, 0, 57 if is_nearest else 22, 0)
        layout.setSpacing(12)

        name = QLabel(habit.name)
        name_font = QFont(font_family, 12) if font_family else QFont()
        name_font.setBold(True)
        name.setFont(name_font)
        name.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 16px; font-weight: 600;")
        layout.addWidget(name, 1)

        t_lbl = QLabel(habit.reminder_time or "")
        t_font = QFont(font_family, 12) if font_family else QFont()
        t_font.setBold(True)
        t_lbl.setFont(t_font)
        t_lbl.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 16px; font-weight: 600;")
        layout.addWidget(t_lbl)

        if is_nearest:
            alarm = QLabel(self)
            alarm.setPixmap(tinted_pixmap("alarm_icon.png", 22, COLOR_TEXT_DARK))
            alarm.setFixedSize(35, 35)
            alarm.setAlignment(Qt.AlignCenter)
            alarm.move(self.width() - 45, 22)
            self._alarm_lbl = alarm
        else:
            self._alarm_lbl = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._alarm_lbl:
            self._alarm_lbl.move(self.width() - 45, 22)


class PlusIcon(QWidget):
    """Аккуратный, ровно отцентрированный плюсик, нарисованный вручную —
    текстовый глиф «+» в разных шрифтах смещается и выглядит не по центру круга.
    Обе полосы объединяются в один путь и заливаются одной заливкой, чтобы в месте
    пересечения не было двойного альфа-смешения (тёмной точки в центре)."""

    def __init__(self, size: int = 44, color: str = "rgba(0,0,0,0.7)", thickness: int = 7, parent=None):
        super().__init__(parent)
        self._color = _parse_rgba(color) if color.startswith("rgba") else QColor(color)
        self._thickness = thickness
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        from PySide6.QtGui import QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        t = self._thickness
        margin = t / 2 + 2
        r = t / 2

        vertical = QPainterPath()
        vertical.addRoundedRect(QRectF(cx - t / 2, margin, t, h - 2 * margin), r, r)
        horizontal = QPainterPath()
        horizontal.addRoundedRect(QRectF(margin, cy - t / 2, w - 2 * margin, t), r, r)

        plus_path = vertical.united(horizontal)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawPath(plus_path)


# ------------------------------------------------------------------ Home action card
class HomeActionCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, emoji: str, bg_color: str,
                 font_family: Optional[str] = None, preview_lines: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(200)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border: 1px solid white; "
                            f"border-radius: 12px; }} "
                            f"QLabel {{ background: transparent; border: none; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(10)

        t = QLabel(title)
        t.setAlignment(Qt.AlignCenter)
        t.setWordWrap(True)
        t.setStyleSheet("color: white; font-size: 15px; font-weight: 700;")
        if font_family:
            tf = QFont(font_family, 12)
            tf.setBold(True)
            t.setFont(tf)
        layout.addWidget(t)

        if not preview_lines:
            circle = QFrame()
            circle.setFixedSize(90, 90)
            circle.setStyleSheet("background-color: rgba(255,255,255,0.45); border-radius: 45px;")
            circle_layout = QVBoxLayout(circle)
            circle_layout.setContentsMargins(0, 0, 0, 0)
            plus = PlusIcon(size=48, color="rgba(0,0,0,0.7)", thickness=8)
            circle_layout.addWidget(plus, 0, Qt.AlignCenter)

            layout.addStretch(1)
            circle_row = QHBoxLayout()
            circle_row.addStretch()
            circle_row.addWidget(circle)
            circle_row.addStretch()
            layout.addLayout(circle_row)

        if not preview_lines:
            layout.addStretch(1)

        if preview_lines:
            layout.addSpacing(6)
            for _ in range(2):
                row = QHBoxLayout()
                row.setSpacing(8)
                dot = QFrame()
                dot.setFixedSize(20, 20)
                dot.setStyleSheet("background-color: #d9d9d9; border-radius: 10px;")
                row.addWidget(dot)
                lines_box = QVBoxLayout()
                lines_box.setSpacing(4)
                bar1 = QFrame()
                bar1.setFixedSize(70, 6)
                bar1.setStyleSheet("background-color: #d9d9d9; border-radius: 3px;")
                bar2 = QFrame()
                bar2.setFixedSize(45, 6)
                bar2.setStyleSheet("background-color: #d9d9d9; border-radius: 3px;")
                lines_box.addWidget(bar1)
                lines_box.addWidget(bar2)
                row.addLayout(lines_box)
                row.addStretch()
                layout.addLayout(row)
            layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ------------------------------------------------------------------ Habit row (Мои привычки)
class HabitRow(QFrame):
    """Карточка привычки на экране «Мои привычки» — строго по макету:
    аватар с иконкой, название, серия (🔥 + число), время и периодичность
    справа, ниже — тёмная карточка с сеткой дней текущего месяца.

    Вся карточка МАСШТАБИРУЕТСЯ по ширине (шрифты, отступы, аватар, кнопка
    удаления) — иначе на узком окне шапка (аватар + время + периодичность)
    просто не помещается и обрезается краем окна."""

    toggled = Signal(str)
    deleted = Signal(str)
    incremented = Signal(str)

    BASE_WIDTH = 358   # ширина карточки, под которую подобраны исходные размеры
    MIN_SCALE = 0.6
    MAX_SCALE = 1.25

    def __init__(self, habit: Habit, accent: str, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.accent = accent
        self.setStyleSheet(
            "QFrame#habitCard { background-color: rgba(167,163,163,0.7); border-radius: 30px; } "
            "QLabel { background: transparent; border: none; }"
        )
        self.setObjectName("habitCard")
        add_shadow(self, blur=16, y_offset=4, alpha=40)

        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(18, 16, 18, 18)
        self.outer.setSpacing(12)

        # ---------- шапка: иконка / название / серия / время / периодичность ----------
        self.header = QHBoxLayout()
        self.header.setSpacing(14)

        self.avatar = QLabel()
        self.avatar.setPixmap(res_icon(habit.icon).pixmap(40, 40))
        self.avatar.setFixedSize(66, 66)
        self.avatar.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setPointSize(26)
        self.avatar.setFont(f)
        self.avatar.setStyleSheet("background-color: #d9d9d9; border-radius: 33px;")
        self.header.addWidget(self.avatar)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self.name_lbl = QLabel(habit.name)
        self.name_lbl.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 700;")
        text_col.addWidget(self.name_lbl)

        streak_row = QHBoxLayout()
        streak_row.setSpacing(4)
        self.flame_lbl = QLabel("🔥")
        self.flame_lbl.setStyleSheet("font-size: 14px;")
        streak_row.addWidget(self.flame_lbl)
        self.streak_lbl = QLabel(str(habit.current_streak()))
        self.streak_lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 600;")
        streak_row.addWidget(self.streak_lbl)
        streak_row.addStretch()
        text_col.addLayout(streak_row)
        self.header.addLayout(text_col, 1)

        meta_col = QVBoxLayout()
        meta_col.setSpacing(2)
        meta_col.setAlignment(Qt.AlignRight)
        self.time_lbl = None
        if habit.reminder_time:
            self.time_lbl = QLabel(habit.reminder_time)
            self.time_lbl.setAlignment(Qt.AlignRight)
            self.time_lbl.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700;")
            meta_col.addWidget(self.time_lbl)
        freq_text = {"day": "Каждый день", "week": "Каждую неделю", "month": "Каждый месяц"}
        self.freq_lbl = QLabel(freq_text.get(habit.period, "Каждый день"))
        self.freq_lbl.setAlignment(Qt.AlignRight)
        self.freq_lbl.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 11px; font-weight: 600;")
        meta_col.addWidget(self.freq_lbl)
        self.header.addLayout(meta_col)

        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(22, 22)
        self.del_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: rgba(255,255,255,0.45); font-weight: bold; }"
            "QPushButton:hover { color: #ff6b5e; }"
        )
        self.del_btn.clicked.connect(lambda: self.deleted.emit(habit.id))
        self.header.addWidget(self.del_btn, 0, Qt.AlignTop)

        self.outer.addLayout(self.header)

        self.plus_btn = None
        if habit.target > 1:
            plus_row = QHBoxLayout()
            plus_row.addStretch()
            self.plus_btn = QPushButton(f"+1 ({habit.progress_for(today())}/{habit.target} {habit.unit})")
            self.plus_btn.setFixedHeight(26)
            self.plus_btn.setStyleSheet(
                f"QPushButton {{ background-color: {accent}; color: white; border-radius: 9px; "
                f"font-weight: 700; font-size: 11px; padding: 0 10px; }}"
            )
            self.plus_btn.clicked.connect(lambda: self.incremented.emit(habit.id))
            plus_row.addWidget(self.plus_btn)
            self.outer.addLayout(plus_row)

        # ---------- карточка месяца с сеткой дней ----------
        self.month_grid = _MonthGrid(habit, self)
        self.outer.addWidget(self.month_grid)

        self._last_scale = 1.0

    def refresh(self):
        pass

    def apply_scale(self, scale: float):
        scale = max(self.MIN_SCALE, min(self.MAX_SCALE, scale))
        if abs(scale - self._last_scale) < 0.02:
            return
        self._last_scale = scale

        def s(px: int) -> int:
            return max(1, round(px * scale))

        self.outer.setContentsMargins(s(18), s(16), s(18), s(18))
        self.outer.setSpacing(s(12))
        self.header.setSpacing(s(14))

        avatar_size = s(66)
        self.avatar.setFixedSize(avatar_size, avatar_size)
        avatar_font = self.avatar.font()
        avatar_font.setPointSize(max(10, s(26)))
        self.avatar.setFont(avatar_font)
        self.avatar.setStyleSheet(f"background-color: #d9d9d9; border-radius: {avatar_size // 2}px;")

        self.name_lbl.setStyleSheet(f"color: #ffffff; font-size: {s(16)}px; font-weight: 700;")
        self.flame_lbl.setStyleSheet(f"font-size: {s(14)}px;")
        self.streak_lbl.setStyleSheet(f"color: #ffffff; font-size: {s(14)}px; font-weight: 600;")
        if self.time_lbl:
            self.time_lbl.setStyleSheet(f"color: #ffffff; font-size: {s(15)}px; font-weight: 700;")
        self.freq_lbl.setStyleSheet(f"color: rgba(255,255,255,0.75); font-size: {s(11)}px; font-weight: 600;")

        self.del_btn.setFixedSize(s(22), s(22))

        if self.plus_btn:
            self.plus_btn.setFixedHeight(s(26))
            self.plus_btn.setStyleSheet(
                f"QPushButton {{ background-color: {self.accent}; color: white; border-radius: {s(9)}px; "
                f"font-weight: 700; font-size: {s(11)}px; padding: 0 {s(10)}px; }}"
            )

        self.month_grid.apply_scale(scale)


class _MonthGrid(QFrame):
    """Тёмная карточка «Август» + сетка дней месяца (9 колонок, как в макете).
    Цвет выполненных дней — habit.color; будущие дни — белые; прошедшие
    невыполненные — полупрозрачно-белые. Клик по ячейке «сегодня» отмечает
    привычку выполненной/невыполненной.

    Ячейки МАСШТАБИРУЮТСЯ под доступную ширину карточки (а не фиксированные
    24px) — при изменении размера окна сетка целиком подстраивается, чтобы
    всё помещалось без обрезки и лишней прокрутки."""

    COLS = 9
    MIN_CELL = 14
    MAX_CELL = 28

    def __init__(self, habit: Habit, row: "HabitRow", parent=None):
        super().__init__(parent)
        self.habit = habit
        self.row = row
        self.setStyleSheet("QFrame { background-color: #5a5858; border-radius: 26px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        t = today()
        month_lbl = QLabel(MONTHS_RU[t.month - 1])
        month_lbl.setAlignment(Qt.AlignCenter)
        month_lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700; background: transparent;")
        layout.addWidget(month_lbl)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(8)
        layout.addLayout(self.grid_layout)

        self._cells = []  # (button, mark, bg_color)
        days_in_month = calendar.monthrange(t.year, t.month)[1]
        for day in range(1, days_in_month + 1):
            d = date(t.year, t.month, day)
            r, c = divmod(day - 1, self.COLS)

            cell_col = QVBoxLayout()
            cell_col.setSpacing(3)

            day_lbl = QLabel(str(day))
            day_lbl.setAlignment(Qt.AlignCenter)
            day_lbl.setStyleSheet("color: #ffffff; font-size: 10px; background: transparent;")
            cell_col.addWidget(day_lbl)
            
            if d > t:
                bg = "#ffffff"
            elif habit.is_done(d):
                bg = habit.color
            else:
                bg = "rgba(255,255,255,0.7)"

            if d == t:
                cell = QPushButton()
                cell.setCursor(Qt.PointingHandCursor)
                cell.clicked.connect(lambda: self.row.toggled.emit(habit.id))
            else:
                cell = QPushButton()
                cell.setEnabled(False)
            cell.setFixedSize(24, 24)
            cell.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; border-radius: 10px; border: none; }} "
                f"QPushButton:disabled {{ background-color: {bg}; }}"
            )
            cell_col.addWidget(cell)

            mark = QLabel()
            mark.setFixedSize(24, 3)
            mark.setStyleSheet(
                "background-color: #d9d9d9; border-radius: 2px;" if d == t else "background: transparent;"
            )
            cell_col.addWidget(mark)

            self.grid_layout.addLayout(cell_col, r, c)
            self._cells.append((cell, mark, bg, day_lbl))

        self._last_cell_size = 24

    def apply_scale(self, scale: float):
        """Пересчитывает размер ячеек напрямую от общего масштаба карточки (а не от
        собственной ширины) — так же, как HabitRow, чтобы не зависеть от порядка
        разрешения размеров в layout-системе Qt."""
        cell_size = max(self.MIN_CELL, min(self.MAX_CELL, round(24 * scale)))
        if cell_size == self._last_cell_size:
            return
        self._last_cell_size = cell_size
        spacing = max(3, round(cell_size * 0.3))
        self.grid_layout.setSpacing(spacing)
        radius = max(4, round(cell_size * 0.42))
        month_margin_h = max(8, round(16 * scale))
        month_margin_v = max(6, round(14 * scale))
        self.layout().setContentsMargins(month_margin_h, month_margin_v, month_margin_h, month_margin_v)
        for cell, mark, bg, day_lbl in self._cells:
            day_lbl.setStyleSheet(f"color: #ffffff; font-size: {max(8, round(cell_size * 0.42))}px; background: transparent;")
            cell.setFixedSize(cell_size, cell_size)
            cell.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; border-radius: {radius}px; border: none; }} "
                f"QPushButton:disabled {{ background-color: {bg}; }}"
            )
            mark.setFixedSize(cell_size, max(2, int(cell_size * 0.12)))


# ------------------------------------------------------------------ Settings row helpers
class ToggleSwitch(QAbstractButton):
    """Тумблер-«пилюля» (трек + кружок), нарисованный вручную — как в HTML-макете
    экрана «Настройки» (42x24, зелёный/серый)."""

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(42, 24)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        h = self.height()
        painter.setBrush(QColor("#34c471") if self.isChecked() else QColor("#d9d9d9"))
        painter.drawRoundedRect(self.rect(), h / 2, h / 2)
        d = h - 4
        x = self.width() - d - 2 if self.isChecked() else 2
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(x, 2, d, d)


class SettingsPillRow(QFrame):
    """Белая «пилюля» настройки с эмодзи-иконкой и тумблером — клик в любом
    месте карточки (кроме самого тумблера) тоже переключает значение."""

    toggled = Signal(bool)

    def __init__(self, title: str, icon: str, checked: bool, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QFrame { background-color: #272732; border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; } "
            "QLabel { background: transparent; border: none; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(12)

        lbl = QLabel(title)
        lbl.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700;")
        layout.addWidget(lbl, 1)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_lbl)

        self.switch = ToggleSwitch(checked)
        self.switch.toggled.connect(self.toggled.emit)
        layout.addWidget(self.switch)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.switch.toggle()
        super().mousePressEvent(event)


class FontSizeExpander(QFrame):
    """Раскрывающаяся карточка «Размер шрифта» — заголовок (клик) показывает/скрывает
    ряд S/M/L и пояснение, шеврон переворачивается, как в HTML-макете."""

    changed = Signal(str)

    def __init__(self, current: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame#fontExpander { background-color: #272732; border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; } "
            "QLabel { background: transparent; border: none; }"
        )
        self.setObjectName("fontExpander")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.header = QFrame()
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.mousePressEvent = lambda e: self._toggle()
        head = QHBoxLayout(self.header)
        head.setContentsMargins(16, 14, 16, 14)
        head.setSpacing(12)
        lbl = QLabel("Размер шрифта")
        lbl.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700;")
        head.addWidget(lbl, 1)
        aa = QLabel("Aa")
        aa.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 16px; font-weight: 800;")
        head.addWidget(aa)
        self.chev = QLabel("▾")
        self.chev.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 13px;")
        head.addWidget(self.chev)
        outer.addWidget(self.header)

        self.body = QWidget()
        body = QVBoxLayout(self.body)
        body.setContentsMargins(16, 0, 16, 16)
        body.setSpacing(10)

        size_row = QHBoxLayout()
        size_row.setSpacing(8)
        self.buttons = {}
        for size in ("S", "M", "L"):
            b = QPushButton(size)
            b.setCheckable(True)
            b.setChecked(size == current)
            b.setFixedHeight(34)
            b.setStyleSheet(
                "QPushButton { background-color: rgba(255,255,255,0.08); color: #ffffff; border-radius: 10px; font-weight: 700; }"
                "QPushButton:checked { background-color: #5D5FEF; color: white; }"
            )
            b.clicked.connect(lambda _, s=size: self._select(s))
            self.buttons[size] = b
            size_row.addWidget(b)
        body.addLayout(size_row)

        hint = QLabel("Размер применяется ко всем экранам приложения и не влияет на настройки устройства.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px; font-weight: 600;")
        body.addWidget(hint)

        outer.addWidget(self.body)
        self.body.setVisible(False)

    def _toggle(self):
        opening = not self.body.isVisible()
        self.body.setVisible(opening)
        self.chev.setText("▴" if opening else "▾")

    def _select(self, size: str):
        for s, b in self.buttons.items():
            b.setChecked(s == size)
        self.changed.emit(size)


class HelpRow(QFrame):
    """Тёмная строка секции «Помощь» — иконка в бейдже, название, шеврон."""

    clicked = Signal()

    def __init__(self, icon: str, title: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QFrame { background-color: #272732; border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; } "
            "QLabel { background: transparent; border: none; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(12)

        ico = QLabel(icon)
        ico.setFixedSize(30, 30)
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet("background-color: rgba(93,95,239,0.18); border-radius: 9px; font-size: 14px;")
        layout.addWidget(ico)

        lbl = QLabel(title)
        lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 600;")
        layout.addWidget(lbl, 1)

        chev = QLabel("›")
        chev.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 14px;")
        layout.addWidget(chev)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ------------------------------------------------------------------ Add habit form (встроенный экран)
class AddHabitForm(QFrame):
    """Форма добавления привычки как экран (не диалог).

    Структура, тексты, порядок полей и цвета взяты дословно из HTML/CSS
    макета экрана «Добавить привычку» (index.html): название → иконка →
    периодичность → цель/единица → напоминание → цвет отметки серии → кнопка.
    """

    submitted = Signal(dict)
    icon_pick_requested = Signal()
    
    def __init__(self, accent: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame#addHabitSheet { background-color: #d9d9d9; border-radius: 24px; } "
            "QLabel { background: transparent; border: none; }"
        )
        self.setObjectName("addHabitSheet")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(4)

        field_style = (
            "QLineEdit, QSpinBox, QComboBox, QTimeEdit { background-color: #ffffff; "
            "color: #000000; border: 1px solid #dfdfdf; border-radius: 10px; padding: 6px 10px; }"
        )
        self.setStyleSheet(self.styleSheet() + field_style)

        def label(text, size=13, bold=False, top_margin=0):
            l = QLabel(text)
            weight = 600 if bold else 400
            l.setStyleSheet(f"color: #000000; font-size: {size}px; font-weight: {weight}; "
                             f"margin-top: {top_margin}px;")
            l.setWordWrap(True)
            return l

        # ---------- Название привычки ----------
        layout.addWidget(label("Название привычки", size=14, bold=True))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        # ---------- Иконка ----------
        layout.addSpacing(10)
        layout.addWidget(label("Выберите то, что больше подходит к вашей привычке"))
        layout.addSpacing(8)

        icon_row = QHBoxLayout()
        icon_row.setSpacing(12)

        self.icon_btn = QPushButton("?")
        self.icon_btn.setFixedSize(60, 60)
        self.icon_btn.setCursor(Qt.PointingHandCursor)
        self.icon_btn.setStyleSheet(
            "QPushButton { background-color: #ffffff; border: 2px solid #000000; "
            "border-radius: 30px; font-size: 26px; color: #000000; }"
            "QPushButton:hover { background-color: #f5f5f5; }"
        )
        self.icon_btn.clicked.connect(self._open_icon_menu)
        icon_row.addWidget(self.icon_btn)

        icon_row.addWidget(label("Выбрать иконку", size=11, bold=True), 1)
        layout.addLayout(icon_row)
        self.selected_icon = None

        # ---------- Периодичность ----------
        layout.addSpacing(14)
        layout.addWidget(label("Выберите периодичность", size=14))
        layout.addSpacing(8)

        period_row = QHBoxLayout()
        period_row.setSpacing(10)
        self.period_buttons = {}
        for key, text in PERIODS:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(27)
            btn.clicked.connect(lambda _, k=key: self._select_period(k))
            period_row.addWidget(btn)
            self.period_buttons[key] = btn
        layout.addLayout(period_row)
        self._select_period("day")

        # ---------- Цель в день / Единица измерения ----------
        layout.addSpacing(14)
        goal_row = QHBoxLayout()
        goal_row.setSpacing(16)

        col1 = QVBoxLayout()
        self.goal_label = label(self._goal_label_text("day"), size=14)
        col1.addWidget(self.goal_label)
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 100)
        self.target_spin.setValue(1)
        self.target_spin.setButtonSymbols(QSpinBox.NoButtons)
        col1.addWidget(self.target_spin)
        goal_row.addLayout(col1)

        col2 = QVBoxLayout()
        col2.addWidget(label("Единица измерения", size=14))
        self.unit_edit = QLineEdit()
        self.unit_edit.setText("раз")
        col2.addWidget(self.unit_edit)
        goal_row.addLayout(col2, 1)
        layout.addLayout(goal_row)

        # ---------- Добавить напоминание ----------
        layout.addSpacing(14)
        reminder_row = QHBoxLayout()
        reminder_row.addWidget(label("Добавить напоминание", size=14), 1)
        self.reminder_btn = QPushButton()
        self.reminder_btn.setCheckable(True)
        
        self.reminder_btn.setFixedSize(30, 30)
        self.reminder_btn.setStyleSheet(
            "QPushButton { background-color: #ffffff; border-radius: 10px; border: none; } "
            "QPushButton:checked { background-color: #ffffff; }"
        )
        self.reminder_btn.toggled.connect(self._on_reminder_toggled)
        reminder_row.addWidget(self.reminder_btn)
        layout.addLayout(reminder_row)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setEnabled(False)
        self.time_edit.setButtonSymbols(QTimeEdit.NoButtons)
        self.reminder_btn.toggled.connect(self.time_edit.setEnabled)
        layout.addSpacing(8)
        layout.addWidget(self.time_edit)

        # ---------- Цвет отметки серии ----------
        layout.addSpacing(14)
        layout.addWidget(label("Выберите цвет отметки серии", size=14))
        layout.addSpacing(8)

        swatch_card = QFrame()
        swatch_card.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_APP_BG}; border: 4px solid #8b8888; border-radius: 25px; }}"
        )
        swatch_layout = QVBoxLayout(swatch_card)
        swatch_layout.setContentsMargins(14, 14, 14, 14)
        swatch_layout.setSpacing(10)
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        row1.setSpacing(10)
        row2.setSpacing(10)
        self.color_buttons = {}
        for i, hexcode in enumerate(MARK_COLORS):
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {hexcode}; border-radius: 10px; border: none; }} "
                f"QPushButton:checked {{ border: 2px solid #ffffff; }}"
            )
            btn.clicked.connect(lambda _, c=hexcode: self._select_color(c))
            (row1 if i < 6 else row2).addWidget(btn)
            self.color_buttons[hexcode] = btn
        swatch_layout.addLayout(row1)
        swatch_layout.addLayout(row2)
        layout.addWidget(swatch_card)
        self._select_color(MARK_COLORS[0])

        # ---------- Кнопка сохранения ----------
        layout.addSpacing(18)
        save_btn = QPushButton("Добавить привычку")
        save_btn.setFixedHeight(44)
        save_btn.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #000000; border: 2px solid #000000; "
            "border-radius: 20px; font-size: 14px; } "
            "QPushButton:hover { background-color: #f5f5f5; }"
        )
        save_btn.clicked.connect(self._on_submit)
        layout.addWidget(save_btn)

        self._apply_period_styles()

    def _goal_label_text(self, period_key: str) -> str:
        return {"day": "Цель в день", "week": "Цель в неделю", "month": "Цель в месяц"}[period_key]

    def _select_period(self, key: str):
        self.selected_period = key
        self._apply_period_styles()
        if hasattr(self, "goal_label"):
            self.goal_label.setText(self._goal_label_text(key))

    def _apply_period_styles(self):
        for key, btn in self.period_buttons.items():
            selected = key == getattr(self, "selected_period", "day")
            btn.setChecked(selected)
            border = "2px solid #000000" if selected else "1px solid #dfdfdf"
            btn.setStyleSheet(
                f"QPushButton {{ background-color: #ffffff; color: #000000; border: {border}; "
                f"border-radius: 14px; font-size: 13px; }}"
            )

    def _open_icon_menu(self):
        self.icon_pick_requested.emit()

    def set_icon(self, filename: str):
        self.selected_icon = filename
        self.icon_btn.setIcon(res_icon(filename))
        self.icon_btn.setIconSize(QSize(28, 28))
        self.icon_btn.setText("")

    def _on_reminder_toggled(self, checked: bool):
        if checked:
            self.reminder_btn.setIcon(QIcon())
            self.reminder_btn.setText("✓")
            self.reminder_btn.setStyleSheet(
                "QPushButton { background-color: #ffffff; border-radius: 10px; border: none; "
                "color: #1fa855; font-size: 16px; font-weight: 700; }"
            )
        else:
            self.reminder_btn.setText("")
            
            self.reminder_btn.setStyleSheet(
                "QPushButton { background-color: #ffffff; border-radius: 10px; border: none; }"
            )

    def _select_color(self, hexcode: str):
        self.selected_color = hexcode
        for c, btn in self.color_buttons.items():
            btn.setChecked(c == hexcode)

    def _on_submit(self):
        reminder = self.time_edit.time().toString("HH:mm") if self.reminder_btn.isChecked() else None
        data = {
            "name": self.name_edit.text().strip() or "Новая привычка",
            "icon": self.selected_icon or "⭐",
            "target": self.target_spin.value(),
            "unit": self.unit_edit.text().strip() or "раз",
            "reminder_time": reminder,
            "period": getattr(self, "selected_period", "day"),
            "color": getattr(self, "selected_color", MARK_COLORS[0]),
        }
        self.submitted.emit(data)

    def reset(self):
        self.name_edit.clear()
        self.selected_icon = None
        self.icon_btn.setIcon(QIcon())
        self.icon_btn.setText("?")
        self._select_period("day")
        self.target_spin.setValue(1)
        self.unit_edit.setText("раз")
        self.reminder_btn.setChecked(False)
        self._select_color(MARK_COLORS[0])

ICON_CATEGORIES = [
    ("Здоровье", "icon_health.png"),
    ("Образование и саморазвитие", "icon_education.png"),
    ("Работа и продуктивность", "icon_work.png"),
    ("Личное развитие", "icon_personal.png"),
    ("Развлечения и игры", "icon_fun.png"),
    ("Дом и быт", "icon_home.png"),
]


CATEGORY_SUBICONS = {
    "Здоровье": [
        ("Бег", "health_run.png"),
        ("Ходьба", "health_walk.png"),
        ("Велосипед", "health_bike.png"),
        ("Плавание", "health_swim.png"),
        ("Йога", "health_yoga.png"),
        ("Спортзал", "health_gym.png"),
        ("Здоровое питание", "health_food.png"),
        ("Вода", "health_water.png"),
        ("Сон", "health_sleep.png"),
        ("Сердце", "health_heart.png"),
        ("Зуб", "health_tooth.png"),
        ("Гигиена", "health_hygiene.png"),
        ("Осмотр", "health_checkup.png"),
        ("Витамины и таблетки", "health_vitamins.png"),
    ],
    "Образование и саморазвитие": [
        ("Книги", "edu_books.png"),
        ("Учёба", "edu_study.png"),
        ("Заметки", "edu_notes.png"),
        ("География", "edu_geography.png"),
        ("Иностранные языки", "edu_languages.png"),
        ("Идея", "edu_idea.png"),
        ("Головоломки", "edu_puzzles.png"),
        ("Музыка", "edu_music.png"),
        ("Рисование", "edu_drawing.png"),
        ("Программиро-"
        "вание", "edu_programming.png"),
        ("Наушники", "edu_headphones.png"),
    ],
   "Работа и продуктивность": [
        ("Ноутбук", "work_laptop.png"),
        ("График", "work_chart.png"),
        ("Календарь", "work_calendar.png"),
        ("Клипборд", "work_clipboard.png"),
        ("Будильник", "work_alarm.png"),
        ("Скрепка", "work_paperclip.png"),
        ("Встреча", "work_meeting.png"),
        ("Кубок", "work_trophy.png"),
        ("Звонки", "work_calls.png"),
        ("Энергия", "work_energy.png"),
        ("Папка", "work_folder.png"),
        ("Письмо", "work_mail.png"),
    ],
    "Личное развитие": [
        ("Звезда", "personal_star.png"),
        ("Солнце", "personal_sun.png"),
        ("Луна", "personal_moon.png"),
        ("Голубь", "personal_dove.png"),
        ("Огонь", "personal_fire.png"),
        ("Растение", "personal_plant.png"),
        ("Цветок", "personal_flower.png"),
        ("Лотос", "personal_lotus.png"),
        ("Молитва", "personal_prayer.png"),
        ("Медитация", "personal_meditation.png"),
        ("Маски", "personal_masks.png"),
        ("Компас", "personal_compass.png"),
        ("Ключ", "personal_key.png"),
    ],
    "Развлечения и игры": [
        ("Джойстик", "entertainment_joystick.png"),
        ("Кубики", "entertainment_dice.png"),
        ("Шахматы", "entertainment_chess.png"),
        ("Кино", "entertainment_movie.png"),
        ("Караоке", "entertainment_karaoke.png"),
        ("Телевизор", "entertainment_tv.png"),
        ("Гитара", "entertainment_guitar.png"),
        ("Пианино", "entertainment_piano.png"),
        ("Баскетбол", "entertainment_basketball.png"),
        ("Футбол", "entertainment_football.png"),
        ("Волейбол", "entertainment_volleyball.png"),
        ("Теннис", "entertainment_tennis.png"),
        ("Дартс", "entertainment_darts.png"),
        ("Игральные карты", "entertainment_cards.png"),
    ],
    "Дом и быт": [
        ("Веник", "home_broom.png"),
        ("Мыло", "home_soap.png"),
        ("Швабра с ведром", "home_mop.png"),
        ("Корзина с одеждой", "home_laundry.png"),
        ("Тележка", "home_cart.png"),
        ("Сковородка", "home_pan.png"),
        ("Кастрюля", "home_pot.png"),
        ("Инструменты", "home_tools.png"),
        ("Зеркало", "home_mirror.png"),
        ("Горшок с растением", "home_plant.png"),
        ("Игрушки", "home_toys.png"),
        ("Мусорное ведро", "home_trash.png"),
        ("Котик", "home_cat.png"),
        ("Собачка", "home_dog.png"),
    ]
}

class FlowLayout(QLayout):
    """Заворачивает виджеты на новую строку по ширине контейнера — как текст.
    Убирает необходимость вручную считать число колонок под ширину окна."""

    def __init__(self, parent=None, margin=0, h_spacing=12, v_spacing=12):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = _QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += _QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(left, top, -right, -bottom)
        x, y = effective.x(), effective.y()
        line_height = 0

        for item in self._items:
            item_size = item.sizeHint()
            next_x = x + item_size.width() + self._h_spacing
            if next_x - self._h_spacing > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + self._v_spacing
                next_x = x + item_size.width() + self._h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))
            x = next_x
            line_height = max(line_height, item_size.height())

        return y + line_height - rect.y() + bottom
    
class IconPickerPage(QWidget):
    """Экран «Выбор иконки»: сетка категорий → сетка иконок внутри категории."""

    icon_chosen = Signal(str)

    def __init__(self, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.mw = mw
        self.current_category: Optional[str] = None
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(16)

        self.top = TopBar("Выбор иконки", show_back=True)
        self.top.back_clicked.connect(self._on_back)
        outer.addWidget(self.top)

        self.chip = QLabel("")
        self.chip.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); color: #ffffff; "
            "font-size: 14px; font-weight: 700; border-radius: 16px; padding: 8px 16px;"
        )
        self.chip.setVisible(False)
        outer.addWidget(self.chip, 0, Qt.AlignLeft)

        self.grid_host = QWidget()
        self.grid = FlowLayout(self.grid_host, margin=0, h_spacing=16, v_spacing=20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setWidget(self.grid_host)
        hide_scrollbar(scroll)
        outer.addWidget(scroll, 1)

        self._show_categories()

    

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_cell(self, filename: str, label_text: str, on_click, size: int = 64):
        cell = QWidget()
        cell.setFixedWidth(size + 40)
        col = QVBoxLayout(cell)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(8)

        btn = QPushButton()
        btn.setFixedSize(size, size)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIcon(QIcon(circular_icon_pixmap(filename, size)))
        btn.setIconSize(QSize(size, size))
        btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; }"
        )
        btn.clicked.connect(on_click)
        col.addWidget(btn, 0, Qt.AlignHCenter)

        lbl = QLabel()
        lbl.setTextFormat(Qt.RichText)
        lbl.setText(f'<div style="word-wrap: break-word;">{label_text}</div>')
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedWidth(size + 40)
        lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600;")
        col.addWidget(lbl)

        self.grid.addWidget(cell)
    

    def _show_categories(self):
        self.current_category = None
        self.chip.setVisible(False)
        self.top.set_title("Выбор иконки")
        self._clear_grid()
        for name, filename in ICON_CATEGORIES:
            self._add_cell(filename, name, lambda _=False, n=name: self._show_subicons(n), size=64)

    def _show_subicons(self, category: str):
        self.current_category = category
        self.chip.setText(category)
        self.chip.setVisible(True)
        self._clear_grid()
        items = CATEGORY_SUBICONS.get(category, [])
        for name, filename in items:
            self._add_cell(filename, name, lambda _=False, f=filename: self.icon_chosen.emit(f), size=64)

    def _on_back(self):
        if self.current_category is not None:
            self._show_categories()
        else:
            self.mw.go_to_add_habit()

# ------------------------------------------------------------------ Статистика: кольцо прогресса
class RingProgress(QWidget):
    """Кольцевой индикатор (донат) — прогресс дня, как в дизайне статистики."""

    def __init__(self, percent: int, color: str = "#5D5FEF", size: int = 96, thickness: int = 10, parent=None):
        super().__init__(parent)
        self.percent = max(0, min(100, percent))
        self.color = QColor(color)
        self.thickness = thickness
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.thickness / 2, self.thickness / 2,
                       self.width() - self.thickness, self.height() - self.thickness)
        pen_bg = QPen(QColor(255, 255, 255, 20))
        pen_bg.setWidth(self.thickness)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 0, 360 * 16)

        pen_fg = QPen(self.color)
        pen_fg.setWidth(self.thickness)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)
        span = int(360 * 16 * self.percent / 100)
        painter.drawArc(rect, 90 * 16, -span)

        painter.setPen(QColor("#ffffff"))
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.percent}%")


# ------------------------------------------------------------------ Статистика: карточки
def _stat_tile(value: str, label: str, delta: str, delta_kind: str = "up") -> QFrame:
    tile = QFrame()
    tile.setStyleSheet(
        "QFrame { background-color: #272732; border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; } "
        "QLabel { background: transparent; border: none; }"
    )
    lay = QVBoxLayout(tile)
    lay.setContentsMargins(14, 14, 14, 14)
    lay.setSpacing(4)

    v = QLabel(value)
    v.setStyleSheet("color: #ffffff; font-size: 26px; font-weight: 800;")
    lay.addWidget(v)

    l = QLabel(label)
    l.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 11px; font-weight: 600;")
    lay.addWidget(l)

    colors = {"up": "#34c471", "down": "#ff6b5e", "neutral": "rgba(255,255,255,0.4)"}
    d = QLabel(delta)
    d.setStyleSheet(f"color: {colors.get(delta_kind, colors['up'])}; font-size: 11px; font-weight: 700;")
    lay.addWidget(d)

    return tile


class BarChartCard(QFrame):
    """Столбчатый график активности — высота столбцов пропорциональна значению (0-100)."""

    def __init__(self, title: str, subtitle: str, labels: list, values: list,
                 highlight_index: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background-color: #272732; border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; } "
            "QLabel { background: transparent; border: none; }"
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(14)

        head = QHBoxLayout()
        h4 = QLabel(title)
        h4.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")
        head.addWidget(h4)
        head.addStretch()
        sub = QLabel(subtitle)
        sub.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px; font-weight: 600;")
        head.addWidget(sub)
        outer.addLayout(head)

        chart_h = 130
        min_bar_col = 34 if len(values) <= 12 else 30

        bars_host = QWidget()
        bars_row = QHBoxLayout(bars_host)
        bars_row.setSpacing(6)

        for i, (label, val) in enumerate(zip(labels, values)):
            col = QVBoxLayout()
            col.setSpacing(6)
            col.addStretch()
            bar = QFrame()
            bar.setFixedHeight(max(4, round(chart_h * val / 100)))
            bar.setMinimumWidth(10)
            bar.setMaximumWidth(40)
            color = "#B9AEDD" if i == highlight_index else "#5D5FEF"
            bar.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
            col.addWidget(bar)
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(False)
            lbl.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px; font-weight: 600;")
            col.addWidget(lbl)
            col_widget = QWidget()
            col_widget.setLayout(col)
            col_widget.setFixedHeight(chart_h + 20)
            col_widget.setMinimumWidth(min_bar_col)
            bars_row.addWidget(col_widget, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }" + subtle_scrollbar_qss())
        scroll.setWidget(bars_host)
        scroll.setFixedHeight(chart_h + 36)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        outer.addWidget(scroll)


class HeatmapCard(QFrame):
    """Тепловая карта активности за N недель (14x7 ячеек по умолчанию)."""

    LEVEL_COLORS = [
        "rgba(255,255,255,0.06)", "rgba(93,95,239,0.25)",
        "rgba(93,95,239,0.5)", "rgba(93,95,239,0.75)", "#5D5FEF",
    ]

    def __init__(self, levels: list, weeks: int, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background-color: #272732; border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; } "
            "QLabel { background: transparent; border: none; }"
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        head = QHBoxLayout()
        h4 = QLabel("Активность")
        h4.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")
        head.addWidget(h4)
        head.addStretch()
        sub = QLabel(f"последние {weeks} недель")
        sub.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px; font-weight: 600;")
        head.addWidget(sub)
        outer.addLayout(head)

        grid = QGridLayout()
        grid.setSpacing(4)
        for week in range(weeks):
            for day in range(7):
                lvl = levels[week][day] if week < len(levels) and day < len(levels[week]) else 0
                cell = QFrame()
                cell.setFixedSize(14, 14)
                cell.setStyleSheet(
                    f"background-color: {self.LEVEL_COLORS[lvl]}; border-radius: 3px;"
                )
                grid.addWidget(cell, day, week)
        outer.addLayout(grid)

        legend = QHBoxLayout()
        legend.addStretch()
        less = QLabel("меньше")
        less.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 10px; font-weight: 600;")
        legend.addWidget(less)
        for color in self.LEVEL_COLORS:
            i = QFrame()
            i.setFixedSize(10, 10)
            i.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
            legend.addWidget(i)
        more = QLabel("больше")
        more.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 10px; font-weight: 600;")
        legend.addWidget(more)
        outer.addLayout(legend)


class HabitStatRow(QFrame):
    """Строка статистики по одной привычке — иконка, серия, прогресс-бар %."""

    def __init__(self, habit: Habit, percent: int, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background-color: #272732; border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; } "
            "QLabel { background: transparent; border: none; }"
        )
        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(12)

        icon = QLabel()
        icon.setPixmap(res_icon(habit.icon).pixmap(22, 22))
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("background-color: #d9d9d9; border-radius: 20px;")
        outer.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(2)
        name = QLabel(habit.name)
        name.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")
        info.addWidget(name)
        sub = QLabel(f"Серия 🔥 {habit.current_streak()} · {len(habit.completions)} дней")
        sub.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px; font-weight: 600;")
        info.addWidget(sub)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(4)
        bar_bg.setStyleSheet("background-color: rgba(255,255,255,0.08); border-radius: 2px;")
        bar_bg_layout = QHBoxLayout(bar_bg)
        bar_bg_layout.setContentsMargins(0, 0, 0, 0)
        bar_bg_layout.addStretch(max(0, 100 - percent))
        fill = QFrame()
        fill.setStyleSheet(f"background-color: {habit.color}; border-radius: 2px;")
        bar_bg_layout.insertWidget(0, fill, percent)
        info.addWidget(bar_bg)
        outer.addLayout(info, 1)

        pct = QLabel(f"{percent}%")
        pct.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 800;")
        outer.addWidget(pct)


# ------------------------------------------------------------------ Экран «Статистика»
class StatsPage(QWidget):
    """Экран статистики — открывается по нижней навигации (иконка графика)."""

    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw
        self.period = "week"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 0)
        outer.setSpacing(14)

        top = TopBar("Статистика", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to_home())
        outer.addWidget(top)

        switch_row = QHBoxLayout()
        switch_row.setContentsMargins(4, 4, 4, 4)
        switch_row.setSpacing(4)
        switch_frame = QFrame()
        switch_frame.setStyleSheet(
            "QFrame { background-color: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); "
            "border-radius: 14px; }"
        )
        switch_layout = QHBoxLayout(switch_frame)
        switch_layout.setContentsMargins(4, 4, 4, 4)
        switch_layout.setSpacing(4)
        self.period_buttons = {}
        for key, text in (("week", "Неделя"), ("month", "Месяц"), ("year", "Год")):
            b = QPushButton(text)
            b.setCheckable(True)
            b.setFixedHeight(30)
            b.clicked.connect(lambda _, k=key: self._select_period(k))
            switch_layout.addWidget(b)
            self.period_buttons[key] = b
        outer.addWidget(switch_frame)

        self.content_host = QWidget()
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setWidget(self.content_host)
        hide_scrollbar(scroll)
        outer.addWidget(scroll, 1)

        self._select_period("week")

    def refresh(self):
        self._select_period(self.period)

    def _select_period(self, period: str):
        self.period = period
        for key, b in self.period_buttons.items():
            selected = key == period
            b.setChecked(selected)
            b.setStyleSheet(
                "QPushButton { background-color: %s; color: %s; border: none; border-radius: 10px; "
                "font-size: 12px; font-weight: 700; }" % (
                    "#5D5FEF" if selected else "transparent",
                    "#ffffff" if selected else "rgba(255,255,255,0.55)",
                )
            )
        self._rebuild()

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            self._clear_item(item)

    def _clear_item(self, item):
        w = item.widget()
        if w:
            w.deleteLater()
            return
        layout = item.layout()
        if layout:
            while layout.count():
                self._clear_item(layout.takeAt(0))
            layout.deleteLater()

    def _rebuild(self):
        self._clear_content()
        store = self.store
        t = today()
        days_map = {"week": 7, "month": 30, "year": 365}
        days = days_map[self.period]

        # ---------- сводка 2x2 ----------
        rate = self._completion_rate(days)
        best_streak = max((h.current_streak() for h in store.habits), default=0)
        active = len(store.habits)
        marks = sum(1 for h in store.habits for k in h.completions if str_to_date(k) >= t - timedelta(days=days - 1))

        summary = QGridLayout()
        summary.setSpacing(10)
        summary.addWidget(_stat_tile(f"{round(rate)}%", "Выполнено", "▲ за период"), 0, 0)
        summary.addWidget(_stat_tile(str(best_streak), "Лучшая серия", "🔥 дней подряд"), 0, 1)
        summary.addWidget(_stat_tile(str(active), "Активных", "привычек"), 1, 0)
        summary.addWidget(_stat_tile(str(marks), "Отметок", "за период"), 1, 1)
        summary.setColumnStretch(0, 1)
        summary.setColumnStretch(1, 1)
        self.content_layout.addLayout(summary)

        # ---------- график ----------
        labels, values, hl = self._chart_data()
        self.content_layout.addWidget(BarChartCard("Активность", self._chart_subtitle(), labels, values, hl))

        # ---------- кольцо прогресса дня ----------
        today_habits = [h for h in store.habits if str_to_date(h.created) <= t]
        today_done = sum(1 for h in today_habits if h.is_done(t))
        today_pct = round(today_done / len(today_habits) * 100) if today_habits else 0
        ring_card = QFrame()
        ring_card.setStyleSheet(
            "QFrame { background-color: #272732; border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; } "
            "QLabel { background: transparent; border: none; }"
        )
        ring_layout = QHBoxLayout(ring_card)
        ring_layout.setContentsMargins(16, 16, 16, 16)
        ring_layout.setSpacing(18)
        ring_layout.addWidget(RingProgress(today_pct, color="#5D5FEF"))
        ring_info = QVBoxLayout()
        ring_info.setSpacing(4)
        ring_title = QLabel("Прогресс дня")
        ring_title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")
        ring_info.addWidget(ring_title)
        ring_text = QLabel(f"Выполнено {today_done} из {len(today_habits)} запланированных привычек.")
        ring_text.setWordWrap(True)
        ring_text.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 12px;")
        ring_info.addWidget(ring_text)
        ring_layout.addLayout(ring_info, 1)
        self.content_layout.addWidget(ring_card)

        # ---------- тепловая карта ----------
        self.content_layout.addWidget(HeatmapCard(self._heatmap_levels(), weeks=14))

        # ---------- по привычкам ----------
        section = QLabel("По привычкам")
        section.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")
        self.content_layout.addWidget(section)
        for h in store.habits:
            created = str_to_date(h.created)
            start = max(t - timedelta(days=days - 1), created)
            span = (t - start).days + 1
            done = sum(1 for i in range(span) if h.is_done(start + timedelta(days=i)))
            pct = round(done / span * 100) if span else 0
            self.content_layout.addWidget(HabitStatRow(h, pct))

        self.content_layout.addStretch()

    def _completion_rate(self, days: int) -> float:
        store = self.store
        t = today()
        if not store.habits:
            return 0.0
        total = done = 0
        for h in store.habits:
            created = str_to_date(h.created)
            start = max(t - timedelta(days=days - 1), created)
            span = (t - start).days + 1
            if span <= 0:
                continue
            total += span
            done += sum(1 for i in range(span) if h.is_done(start + timedelta(days=i)))
        return (done / total * 100) if total else 0.0

    def _chart_subtitle(self) -> str:
        return {"week": "Пн–Вс", "month": "4 недели", "year": "Янв–Дек"}[self.period]

    def _chart_data(self):
        store = self.store
        t = today()
        if self.period == "week":
            dates = store.week_dates()
            labels = [WEEKDAYS_RU_SHORT[d.weekday()] for d in dates]
            values = []
            for d in dates:
                active = [h for h in store.habits if str_to_date(h.created) <= d]
                values.append(round(sum(1 for h in active if h.is_done(d)) / len(active) * 100) if active else 0)
            hl = dates.index(t) if t in dates else None
            return labels, values, hl
        if self.period == "month":
            labels, values = [], []
            for w in range(3, -1, -1):
                w_start = t - timedelta(days=t.weekday() + 7 * w)
                w_end = w_start + timedelta(days=6)
                active = [h for h in store.habits if str_to_date(h.created) <= w_end]
                total = done = 0
                for h in active:
                    for i in range(7):
                        d = w_start + timedelta(days=i)
                        if d > t or str_to_date(h.created) > d:
                            continue
                        total += 1
                        done += 1 if h.is_done(d) else 0
                values.append(round(done / total * 100) if total else 0)
                labels.append(f"Н{4 - w}")
            return labels, values, len(values) - 1
        # year
        labels, values = [], []
        for m in range(12):
            month_num = m + 1
            active = [h for h in store.habits if str_to_date(h.created).year <= t.year
                      and (str_to_date(h.created).year < t.year or str_to_date(h.created).month <= month_num)]
            total = done = 0
            days_in_month = calendar.monthrange(t.year, month_num)[1]
            for h in active:
                for day in range(1, days_in_month + 1):
                    d = date(t.year, month_num, day)
                    if d > t or str_to_date(h.created) > d:
                        continue
                    total += 1
                    done += 1 if h.is_done(d) else 0
            values.append(round(done / total * 100) if total else 0)
            labels.append(MONTHS_RU[m][:3])
        return labels, values, t.month - 1

    def _heatmap_levels(self):
        store = self.store
        t = today()
        levels = []
        for week in range(13, -1, -1):
            week_levels = []
            for day in range(7):
                d = t - timedelta(days=week * 7 + (6 - day))
                active = [h for h in store.habits if str_to_date(h.created) <= d]
                if not active or d > t:
                    week_levels.append(0)
                    continue
                rate = sum(1 for h in active if h.is_done(d)) / len(active)
                if rate <= 0:
                    lvl = 0
                elif rate < 0.25:
                    lvl = 1
                elif rate < 0.5:
                    lvl = 2
                elif rate < 0.75:
                    lvl = 3
                else:
                    lvl = 4
                week_levels.append(lvl)
            levels.append(week_levels)
        return levels

class _CalendarHeaderStack(QWidget):
    """Красная шапка с 'гнёздами' под скобы, как в оригинальном макете.
    Пины/гнёзда — оверлей поверх self.card, пересчитывается в resizeEvent,
    растяжение окна не задето."""

    PIN_W, PIN_H = 46, 88
    PIN_X_FRAC = (0.267, 0.771)   # центр пина, доля от ширины карточки
    SOCKET_D = 55
    SOCKET_TOP = 8                # от верха card
    TOP_MARGIN = 34                # место над card, куда вылезают пины

    def __init__(self, card: QWidget, parent=None):
        super().__init__(parent)
        self.card = card
        self.card.setParent(self)

        self.sockets = []
        self.pins = []
        for _ in range(2):
            socket = QFrame(self)
            socket.setFixedSize(self.SOCKET_D, self.SOCKET_D)
            socket.setStyleSheet(
                f"background-color: #b93e3e; border-radius: {self.SOCKET_D // 2}px;"
            )
            self.sockets.append(socket)

            pin = QFrame(self)
            pin.setFixedSize(self.PIN_W, self.PIN_H)
            pin.setStyleSheet(
                f"background-color: #d9d9d9; border-radius: {self.PIN_W // 2}px;"
            )
            self.pins.append(pin)

        self.card.raise_()
        for s in self.sockets:
            s.raise_()
        for p in self.pins:
            p.raise_()

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        self.card.setGeometry(0, self.TOP_MARGIN, w, h - self.TOP_MARGIN)

        for socket, pin, frac in zip(self.sockets, self.pins, self.PIN_X_FRAC):
            cx = int(w * frac)
            socket.move(cx - self.SOCKET_D // 2, self.TOP_MARGIN + self.SOCKET_TOP)
            pin.move(cx - self.PIN_W // 2, 0)
            socket.raise_()
            pin.raise_()
        self.card.raise_()
        for socket, pin in zip(self.sockets, self.pins):
            socket.raise_()
            pin.raise_()
        super().resizeEvent(event)

    def sizeHint(self):
        return self.card.sizeHint() + QSize(0, self.TOP_MARGIN)

# ------------------------------------------------------------------ Экран «Календарь»
class CalendarPage(QWidget):
    """Полноэкранный календарь месяца — открывается по клику на название месяца
    в WeekStrip на главном экране."""

    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw
        t = today()
        self.view_year = t.year
        self.view_month = t.month

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 0)
        outer.setSpacing(14)

        top = TopBar("Календарь", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to_home())
        outer.addWidget(top)

        self.card = QFrame()
        self.card.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 30px; }")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 18)
        card_layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(87)
        header.setStyleSheet(
            "QFrame { background-color: #e64646; border-top-left-radius: 30px; border-top-right-radius: 30px; }"
        )
        card_layout.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(20, 16, 20, 0)
        body.setSpacing(10)

        nav_row = QHBoxLayout()
        self.month_year_lbl = QLabel()
        self.month_year_lbl.setStyleSheet("color: #000000; font-size: 22px; font-weight: 800;")
        nav_row.addWidget(self.month_year_lbl)
        nav_row.addStretch()
        for symbol, delta in (("◀", -1), ("▶", 1)):
            btn = QPushButton(symbol)
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.PointingHandCursor)
            f = QFont()
            f.setPointSize(16)
            f.setBold(True)
            btn.setFont(f)
            btn.setStyleSheet(
                "QPushButton { background-color: #d9d9d9; border-radius: 18px; border: none; color: #000000; "
                "padding-bottom: 3px; } "
                "QPushButton:hover { background-color: #cfcfcf; }"
            )
            btn.clicked.connect(lambda _, d=delta: self._shift_month(d))
            nav_row.addWidget(btn)
        body.addLayout(nav_row)

        self.month_strip_host = QWidget()
        self.month_strip_layout = QHBoxLayout(self.month_strip_host)
        self.month_strip_layout.setContentsMargins(0, 0, 0, 0)
        self.month_strip_layout.setSpacing(6)
        strip_scroll = QScrollArea()
        strip_scroll.setWidgetResizable(True)
        strip_scroll.setFrameShape(QFrame.NoFrame)
        strip_scroll.setFixedHeight(38)
        strip_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        strip_scroll.setWidget(self.month_strip_host)
        hide_scrollbar(strip_scroll)
        body.addWidget(strip_scroll)

        weekday_row = QHBoxLayout()
        weekday_row.setSpacing(0)
        for wd in WEEKDAYS_RU_SHORT:
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #000000; font-size: 12px;")
            weekday_row.addWidget(lbl, 1)
        body.addLayout(weekday_row)

        self.days_grid = QGridLayout()
        self.days_grid.setSpacing(6)
        for c in range(7):
            self.days_grid.setColumnStretch(c, 1)
        body.addLayout(self.days_grid)

        card_layout.addLayout(body)

        self.header_stack = _CalendarHeaderStack(self.card)
        outer.addWidget(self.header_stack)
        outer.addStretch()
        outer.addStretch()

        self._rebuild()

    def _shift_month(self, delta: int):
        m = self.view_month + delta
        y = self.view_year
        if m < 1:
            m, y = 12, y - 1
        elif m > 12:
            m, y = 1, y + 1
        self.view_month, self.view_year = m, y
        self._rebuild()

    def _select_month(self, month_num: int, year: int):
        self.view_month = month_num
        self.view_year = year
        self._rebuild()

    def refresh(self):
        t = today()
        self.view_year, self.view_month = t.year, t.month
        self._rebuild()

    def _rebuild(self):
        self.month_year_lbl.setText(f"{MONTHS_RU[self.view_month - 1]}   {self.view_year}")
        self._rebuild_month_strip()
        self._rebuild_days()

    def _rebuild_month_strip(self):
        while self.month_strip_layout.count():
            item = self.month_strip_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for offset in range(-3, 5):
            idx = self.view_month - 1 + offset
            y = self.view_year + idx // 12
            m = idx % 12 + 1
            selected = offset == 0
            btn = QPushButton(MONTHS_RU[m - 1][:3])
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background-color: %s; color: #000000; border: none; border-radius: 10px; "
                "font-size: 12px; font-weight: %s; padding: 0 10px; }" % (
                    "#d9d9d9" if selected else "transparent",
                    "700" if selected else "400",
                )
            )
            btn.clicked.connect(lambda _, mm=m, yy=y: self._select_month(mm, yy))
            self.month_strip_layout.addWidget(btn)

    def _rebuild_days(self):
        while self.days_grid.count():
            item = self.days_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        t = today()
        first = date(self.view_year, self.view_month, 1)
        days_in_month = calendar.monthrange(self.view_year, self.view_month)[1]
        lead = first.weekday()

        prev_month = self.view_month - 1 or 12
        prev_year = self.view_year if self.view_month > 1 else self.view_year - 1
        prev_days = calendar.monthrange(prev_year, prev_month)[1]

        cells = [(prev_days - lead + 1 + i, False, None) for i in range(lead)]
        for day in range(1, days_in_month + 1):
            cells.append((day, True, date(self.view_year, self.view_month, day)))
        next_num = 1
        while len(cells) % 7 != 0:
            cells.append((next_num, False, None))
            next_num += 1

        for idx, (day_num, in_month, d) in enumerate(cells):
            r, c = divmod(idx, 7)
            cell = QVBoxLayout()
            cell.setSpacing(2)

            is_today = in_month and d == t
            num_lbl = QLabel(str(day_num))
            num_lbl.setAlignment(Qt.AlignCenter)
            color = "#000000" if in_month else "#0000004c"
            extra = "background-color: #A7A1A1; border-radius: 10px;" if is_today else ""
            num_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 700; {extra}")
            num_lbl.setFixedHeight(30)
            cell.addWidget(num_lbl)

            wrapper = QWidget()
            wrapper.setLayout(cell)
            self.days_grid.addWidget(wrapper, r, c)

# ------------------------------------------------------------------ Профиль
class ProfileRow(QFrame):
    clicked = Signal()

    def __init__(self, icon: str, label: str, value: str = "", danger: bool = False, chevron: bool = True, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QFrame { background: transparent; } "
            "QFrame:hover { background-color: rgba(255,255,255,0.04); }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        ico = QLabel(icon)
        ico.setFixedSize(32, 32)
        ico.setAlignment(Qt.AlignCenter)
        ico_bg = "rgba(255,107,94,0.18)" if danger else "rgba(93,95,239,0.18)"
        ico.setStyleSheet(f"background-color: {ico_bg}; border-radius: 10px; font-size: 15px;")
        layout.addWidget(ico)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 600;")
        layout.addWidget(lbl, 1)
        self.label_lbl = lbl

        self.value_lbl = None
        if value:
            self.value_lbl = QLabel(value)
            self.value_lbl.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 13px; font-weight: 600;")
            layout.addWidget(self.value_lbl)

        if chevron:
            chev = QLabel("›")
            chev.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 14px;")
            layout.addWidget(chev)

    def set_label(self, text: str):
        self.label_lbl.setText(text)

    def set_value(self, text: str):
        if self.value_lbl:
            self.value_lbl.setText(text)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class ProfileRowsCard(QFrame):
    """Карточка-контейнер со скруглёнными углами и разделителями между строками."""

    def __init__(self, rows: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background-color: #272732; border: 1px solid rgba(255,255,255,0.1); "
            "border-radius: 16px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for i, row in enumerate(rows):
            layout.addWidget(row)
            if i < len(rows) - 1:
                line = QFrame()
                line.setFixedHeight(1)
                line.setStyleSheet("background-color: rgba(255,255,255,0.06);")
                layout.addWidget(line)


class ProfilePage(QWidget):
    """Экран «Профиль» — аватар, мини-статистика, аккаунт, данные."""

    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(20)

        top = TopBar("Профиль", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to_home())
        outer.addWidget(top)

        head = QVBoxLayout()
        head.setSpacing(0)
        head.setAlignment(Qt.AlignCenter)

        self.avatar = QLabel()
        self.avatar.setFixedSize(96, 96)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet(
            "background-color: #5D5FEF; border-radius: 48px; color: #ffffff; "
            "font-size: 42px; font-weight: 800;"
        )
        head.addWidget(self.avatar, 0, Qt.AlignHCenter)
        head.addSpacing(14)

        self.name_lbl = QLabel()
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 800;")
        head.addWidget(self.name_lbl)

        self.since_lbl = QLabel()
        self.since_lbl.setAlignment(Qt.AlignCenter)
        self.since_lbl.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px; font-weight: 600;")
        head.addSpacing(4)
        head.addWidget(self.since_lbl)

        outer.addLayout(head)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        self.stat_widgets = {}
        for key, label in (("habits", "Привычек"), ("streak", "Серия"), ("marks", "Отметок")):
            box = QFrame()
            box.setStyleSheet("QFrame { background-color: #272732; border-radius: 14px; }")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(8, 12, 8, 12)
            box_layout.setSpacing(3)
            v = QLabel("0")
            v.setAlignment(Qt.AlignCenter)
            v.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 800;")
            l = QLabel(label.upper())
            l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 10px; font-weight: 700;")
            box_layout.addWidget(v)
            box_layout.addWidget(l)
            self.stat_widgets[key] = v
            stats_row.addWidget(box, 1)
        outer.addLayout(stats_row)

        acc_title = QLabel("АККАУНТ")
        acc_title.setStyleSheet(
            "color: rgba(255,255,255,0.4); font-size: 11px; font-weight: 700; margin-left: 4px;"
        )
        outer.addWidget(acc_title)
        
        self.username_row = ProfileRow("✎", self.store.settings.get("name", "") or "Пользователь", chevron=False)
        self.username_row.clicked.connect(self._edit_name)
        outer.addWidget(ProfileRowsCard([self.username_row]))

        data_title = QLabel("ДАННЫЕ")
        data_title.setStyleSheet(
            "color: rgba(255,255,255,0.4); font-size: 11px; font-weight: 700; margin-left: 4px;"
        )
        outer.addWidget(data_title)

        reset_row = ProfileRow("🗑", "Сбросить данные пользователя", danger=True, chevron=False)
        reset_row.clicked.connect(self._reset_data)
        outer.addWidget(ProfileRowsCard([reset_row]))

        outer.addStretch()

        delete_btn = QPushButton("Удалить профиль")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setFixedHeight(46)
        delete_btn.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid rgba(255,107,94,0.35); "
            "border-radius: 16px; color: #ff6b5e; font-size: 14px; font-weight: 700; } "
            "QPushButton:hover { background-color: rgba(255,107,94,0.08); }"
        )
        delete_btn.clicked.connect(self._delete_profile)
        outer.addWidget(delete_btn)

    def refresh(self):
        name = self.store.settings.get("name") or "Пользователь"
        self.name_lbl.setText(name)
        self.avatar.setText(name[0].upper() if name else "?")
        self.since_lbl.setText(self.store.joined_label())
        self.username_row.set_label(name)
        stats = self.store.profile_stats()
        for key, v in self.stat_widgets.items():
            v.setText(str(stats[key]))

    def _edit_name(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Имя пользователя", "Введите имя:",
                                         text=self.store.settings.get("name", ""))
        if ok and name.strip():
            self.store.set_name(name)
            self.refresh()

    def _reset_data(self):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Сбросить данные",
            "Удалить все привычки и отметки? Это действие необратимо.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.store.habits = []
            self.store.save()
            self.refresh()

    def _delete_profile(self):
        from PySide6.QtWidgets import QMessageBox, QApplication
        reply = QMessageBox.question(
            self, "Удалить профиль",
            "Профиль и все данные будут удалены безвозвратно.\nПриложение будет закрыто.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.store.wipe()                 # чистим habits.json и состояние
            QApplication.instance().quit()    # вырубаем приложение

# ------------------------------------------------------------------ Bottom nav
class BottomNav(QFrame):
    """Нижняя навигация: домик / статистика / профиль.
    ВАЖНО: экраны 'Статистика' и 'Профиль' пока не описаны в дизайне —
    временно ведут на 'Ближайшие задачи' и 'Настройки' соответственно."""

    def __init__(self, on_select, parent=None):
        super().__init__(parent)
        self.on_select = on_select
        self.setFixedHeight(60)
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_NAV_BG}; border-radius: 26px; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        self.buttons = []
        # домик 
        home_btn = QPushButton()
        home_btn.setIcon(res_icon("home_icon.png"))
        home_btn.setIconSize(QSize(22, 22))
        home_btn.setCheckable(True)
        home_btn.setFixedSize(44, 44)
        home_btn.setStyleSheet(
            "QPushButton { background-color: transparent; border-radius: 14px; }"
            "QPushButton:checked { background-color: rgba(0,0,0,0.12); }"
        )
        home_btn.clicked.connect(lambda: self.on_select(1))
        layout.addWidget(home_btn)
        self.buttons.append(home_btn)

        layout.addStretch()

        # статистика (средняя иконка панели)
        stats_btn = QPushButton()
        stats_btn.setIcon(res_icon("stats_icon.png"))
        stats_btn.setIconSize(QSize(22, 22))
        stats_btn.setCheckable(True)
        stats_btn.setFixedSize(44, 44)
        stats_btn.setStyleSheet(
            "QPushButton { background-color: transparent; border-radius: 14px; }"
            "QPushButton:checked { background-color: rgba(0,0,0,0.12); }"
        )
        stats_btn.clicked.connect(lambda: self.on_select(7))
        layout.addWidget(stats_btn)
        self.buttons.append(stats_btn)
        layout.addStretch()

        # человек
        person_btn = QPushButton()
        person_btn.setIcon(res_icon("person_icon.png"))
        person_btn.setIconSize(QSize(22, 22))
        person_btn.setCheckable(True)
        person_btn.setFixedSize(44, 44)
        person_btn.setStyleSheet(
            "QPushButton { background-color: transparent; border-radius: 14px; }"
            "QPushButton:checked { background-color: rgba(0,0,0,0.12); }"
        )
        person_btn.clicked.connect(lambda: self.on_select(9))
        layout.addWidget(person_btn)
        self.buttons.append(person_btn)

        self.set_checked(0)

    def set_checked(self, idx: Optional[int]):
        for i, b in enumerate(self.buttons):
            b.setChecked(i == idx)