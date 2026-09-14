"""
widgets.py — переиспользуемые виджеты нового дизайна.
"""
from __future__ import annotations

import os
import calendar
from datetime import date, timedelta
from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize, QPointF, QRectF
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QFrame,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QTimeEdit, QGraphicsDropShadowEffect,
)

from models import Habit, HabitStore, WEEKDAYS_RU_SHORT, MONTHS_RU, THEME_COLORS, today, MARK_COLORS, PERIODS

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


def checkbox_style(size: int = 24, checked_color: str = "#34c471") -> str:
    return (
        f"QCheckBox::indicator {{ width: {size}px; height: {size}px; border-radius: {size // 4 + 2}px; "
        f"border: 2px solid rgba(0,0,0,0.35); background-color: rgba(255,255,255,0.6); }}"
        f"QCheckBox::indicator:checked {{ background-color: {checked_color}; border: 2px solid {checked_color}; }}"
    )


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

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 16px; font-weight: 700;")

        right_spacer = QLabel("")
        right_spacer.setFixedSize(40, 40)

        layout.addWidget(left_slot)
        layout.addWidget(title_lbl, 1)
        layout.addWidget(right_spacer)


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

        self.avatar = QLabel(habit.icon)
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
class SettingsToggleRow(QFrame):
    toggled = Signal(bool)

    def __init__(self, title: str, checked: bool, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_CARD_TRANSLUCENT}; border-radius: 12px; }} QLabel {{ background: transparent; border: none; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 15px; font-weight: 600;")
        layout.addWidget(lbl, 1)
        self.switch = QCheckBox()
        self.switch.setFixedSize(30, 28)
        self.switch.setStyleSheet(checkbox_style(24, checked_color="#34c471"))
        self.switch.setChecked(checked)
        self.switch.stateChanged.connect(lambda _: self.toggled.emit(self.switch.isChecked()))
        layout.addWidget(self.switch)


class FontSizeRow(QFrame):
    changed = Signal(str)

    def __init__(self, current: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_CARD_TRANSLUCENT}; border-radius: 12px; }} QLabel {{ background: transparent; border: none; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        lbl = QLabel("Размер шрифта")
        lbl.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 15px; font-weight: 600;")
        layout.addWidget(lbl, 1)

        self.buttons = {}
        group_box = QHBoxLayout()
        group_box.setSpacing(4)
        for size in ("S", "M", "L"):
            b = QPushButton(size)
            b.setCheckable(True)
            b.setFixedSize(30, 30)
            b.setChecked(size == current)
            b.setStyleSheet(
                "QPushButton { background-color: rgba(255,255,255,0.5); color: #1c1c22; border-radius: 8px; "
                "font-weight: 700; }"
                "QPushButton:checked { background-color: #6366f1; color: white; }"
            )
            b.clicked.connect(lambda _, s=size: self._select(s))
            self.buttons[size] = b
            group_box.addWidget(b)
        layout.addLayout(group_box)

    def _select(self, size: str):
        for s, b in self.buttons.items():
            b.setChecked(s == size)
        self.changed.emit(size)


# ------------------------------------------------------------------ Add habit form (встроенный экран)
class AddHabitForm(QFrame):
    """Форма добавления привычки как экран (не диалог).

    Структура, тексты, порядок полей и цвета взяты дословно из HTML/CSS
    макета экрана «Добавить привычку» (index.html): название → иконка →
    периодичность → цель/единица → напоминание → цвет отметки серии → кнопка.
    """

    submitted = Signal(dict)

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
        # TODO: здесь позже откроется меню выбора иконки привычки.
        pass

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
        self.icon_btn.setText("?")
        self._select_period("day")
        self.target_spin.setValue(1)
        self.unit_edit.setText("раз")
        self.reminder_btn.setChecked(False)
        self._select_color(MARK_COLORS[0])


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
        # домик (image "home-fill.svg" в макете)
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

        # график/статистика (средняя иконка панели)
        stats_btn = QPushButton()
        stats_btn.setIcon(res_icon("stats_icon.png"))
        stats_btn.setIconSize(QSize(22, 22))
        stats_btn.setCheckable(True)
        stats_btn.setFixedSize(44, 44)
        stats_btn.setStyleSheet(
            "QPushButton { background-color: transparent; border-radius: 14px; }"
            "QPushButton:checked { background-color: rgba(0,0,0,0.12); }"
        )
        stats_btn.clicked.connect(lambda: self.on_select(4))
        layout.addWidget(stats_btn)
        self.buttons.append(stats_btn)
        layout.addStretch()

        # человечек (image "person.svg" в макете)
        person_btn = QPushButton()
        person_btn.setIcon(res_icon("person_icon.png"))
        person_btn.setIconSize(QSize(22, 22))
        person_btn.setCheckable(True)
        person_btn.setFixedSize(44, 44)
        person_btn.setStyleSheet(
            "QPushButton { background-color: transparent; border-radius: 14px; }"
            "QPushButton:checked { background-color: rgba(0,0,0,0.12); }"
        )
        person_btn.clicked.connect(lambda: self.on_select(5))
        layout.addWidget(person_btn)
        self.buttons.append(person_btn)

        self.set_checked(0)

    def set_checked(self, idx: Optional[int]):
        for i, b in enumerate(self.buttons):
            b.setChecked(i == idx)