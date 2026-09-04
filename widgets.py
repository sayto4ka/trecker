"""
widgets.py — переиспользуемые виджеты нового дизайна.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QTimeEdit, QGraphicsDropShadowEffect,
)

from models import Habit, HabitStore, WEEKDAYS_RU_SHORT, MONTHS_RU, THEME_COLORS, today

# ---------------------------------------------------------------- базовая палитра (не зависит от темы)
COLOR_APP_BG = "#64748b"        # slate-500 — фон приложения
COLOR_ONBOARD_BG = "#f7cfe0"    # pink-200 — фон онбординга
COLOR_CARD_WHITE = "#ffffff"
COLOR_CARD_TRANSLUCENT = "rgba(255,255,255,0.55)"
COLOR_TEXT_DARK = "#1c1c22"
COLOR_TEXT_MUTED = "rgba(28,28,34,0.6)"
COLOR_NAV_BG = "#d4d4d8"        # zinc-300

ICON_CHOICES = ["⭐", "💧", "🏃", "📖", "🧘", "🍎", "😴", "💊", "✍️", "🎯", "🚭", "💪"]


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
    """Заголовок экрана; при show_back=True показывает стрелку назад слева."""

    back_clicked = Signal()

    def __init__(self, title: str, show_back: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        left_slot = QPushButton("←") if show_back else QLabel("")
        left_slot.setFixedSize(36, 36)
        if show_back:
            left_slot.setStyleSheet(
                "QPushButton { background-color: rgba(255,255,255,0.55); border-radius: 10px; "
                "font-size: 16px; font-weight: 700; color: #1c1c22; }"
                "QPushButton:hover { background-color: rgba(255,255,255,0.8); }"
            )
            left_slot.clicked.connect(self.back_clicked.emit)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 16px; font-weight: 700;")

        right_spacer = QLabel("")
        right_spacer.setFixedSize(36, 36)

        layout.addWidget(left_slot)
        layout.addWidget(title_lbl, 1)
        layout.addWidget(right_spacer)


# ------------------------------------------------------------------ Week strip
class DayCell(QFrame):
    def __init__(self, day_num: int, weekday_letters: str, is_today: bool, parent=None):
        super().__init__(parent)
        self.setFixedSize(38, 50)
        self.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_CARD_TRANSLUCENT}; border-radius: 10px; "
            + (f"border: 2px solid white;" if is_today else "border: 2px solid transparent;")
            + " }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 6, 2, 6)
        layout.setSpacing(2)
        num = QLabel(str(day_num))
        num.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setBold(True)
        f.setPointSize(11)
        num.setFont(f)
        num.setStyleSheet(f"color: {COLOR_TEXT_DARK}; background: transparent; border: none;")
        layout.addWidget(num)
        if is_today:
            dot = QLabel("•")
            dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet("color: white; background: transparent; border: none;")
            layout.addWidget(dot)


class WeekStrip(QWidget):
    """Строка месяца, дней недели и чисел — без окраски статуса (как в новом дизайне)."""

    def __init__(self, store: HabitStore, parent=None):
        super().__init__(parent)
        self.store = store
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        t = today()
        month_lbl = QLabel(MONTHS_RU[t.month - 1])
        month_lbl.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 14px; font-weight: 700;")
        outer.addWidget(month_lbl)

        weekday_row = QHBoxLayout()
        weekday_row.setSpacing(6)
        for wd in WEEKDAYS_RU_SHORT:
            lbl = QLabel(wd)
            lbl.setFixedWidth(38)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px; font-weight: 600;")
            weekday_row.addWidget(lbl)
        outer.addLayout(weekday_row)

        days_row = QHBoxLayout()
        days_row.setSpacing(6)
        for d in store.week_dates():
            cell = DayCell(d.day, WEEKDAYS_RU_SHORT[d.weekday()], d == t)
            days_row.addWidget(cell)
        outer.addLayout(days_row)


# ------------------------------------------------------------------ Reminder preview (Home)
class ReminderPreviewCard(QFrame):
    """Мини-виджет «Ближайшие задачи» на главном экране — кликабельный, ведёт на полный список."""

    clicked = Signal()

    def __init__(self, store: HabitStore, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_CARD_TRANSLUCENT}; border-radius: 16px; }} "
            f"QLabel {{ background: transparent; }}"
        )
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QLabel("Ближайшие задачи")
        header.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 15px; font-weight: 700;")
        layout.addWidget(header)

        upcoming = store.upcoming_reminders()
        if not upcoming:
            empty = QLabel("На сегодня всё сделано 🎉")
            empty.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            layout.addWidget(empty)
        else:
            for h in upcoming[:2]:
                row = QHBoxLayout()
                name = QLabel(f"{h.icon}  {h.name}")
                name.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 13px; font-weight: 600;")
                row.addWidget(name)
                row.addStretch()
                t_lbl = QLabel(h.reminder_time)
                t_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
                row.addWidget(t_lbl)
                layout.addLayout(row)
            if len(upcoming) > 2:
                more = QLabel(f"и ещё {len(upcoming) - 2}...")
                more.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
                layout.addWidget(more)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ------------------------------------------------------------------ Reminders full list row
class ReminderRow(QFrame):
    def __init__(self, habit: Habit, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_CARD_WHITE}; border-radius: 16px; }}"
        )
        add_shadow(self, blur=16, y_offset=3, alpha=35)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        layout.addWidget(icon_badge(habit.icon, habit.id, 36))
        name = QLabel(habit.name)
        name.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 14px; font-weight: 700;")
        layout.addWidget(name, 1)
        t_lbl = QLabel(habit.reminder_time or "")
        t_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; font-weight: 600;")
        layout.addWidget(t_lbl)


# ------------------------------------------------------------------ Home action card
class HomeActionCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, emoji: str, bg_color: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(180)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border-radius: 18px; }}")
        add_shadow(self, blur=18, y_offset=5, alpha=60)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        e = QLabel(emoji)
        e.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setPointSize(30)
        e.setFont(f)
        layout.addWidget(e)

        t = QLabel(title)
        t.setAlignment(Qt.AlignCenter)
        t.setWordWrap(True)
        t.setStyleSheet("color: white; font-size: 15px; font-weight: 700;")
        layout.addWidget(t)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ------------------------------------------------------------------ Habit row (Мои привычки)
class HabitRow(QFrame):
    toggled = Signal(str)
    deleted = Signal(str)
    incremented = Signal(str)

    def __init__(self, habit: Habit, accent: str, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_CARD_WHITE}; border-radius: 14px; }}")
        add_shadow(self, blur=14, y_offset=3, alpha=30)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 10, 10)
        layout.setSpacing(12)

        layout.addWidget(icon_badge(habit.icon, habit.id, 38))

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        title = QLabel(habit.name)
        title.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 14px; font-weight: 700;")
        text_box.addWidget(title)

        progress = habit.progress_for(today())
        done = habit.is_done(today())
        sub_text = f"{progress}/{habit.target} {habit.unit}"
        if habit.reminder_time:
            sub_text += f"   ⏰ {habit.reminder_time}"
        sub = QLabel(sub_text)
        sub.setStyleSheet(f"color: {'#1f8f52' if done else 'rgba(28,28,34,0.55)'}; font-size: 12px;")
        text_box.addWidget(sub)
        layout.addLayout(text_box, 1)

        if habit.target > 1:
            plus_btn = QPushButton("+1")
            plus_btn.setFixedSize(36, 30)
            plus_btn.setStyleSheet(
                f"QPushButton {{ background-color: {accent}; color: white; border-radius: 9px; font-weight: 700; }}"
            )
            plus_btn.clicked.connect(lambda: self.incremented.emit(habit.id))
            layout.addWidget(plus_btn)

        self.check = QCheckBox()
        self.check.setFixedSize(26, 26)
        self.check.setStyleSheet(checkbox_style(22, checked_color="#34c471"))
        self.check.setChecked(done)
        self.check.stateChanged.connect(lambda _: self.toggled.emit(habit.id))
        layout.addWidget(self.check)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #9a9aa8; border: none; font-weight: bold; }"
            "QPushButton:hover { color: #e05545; }"
        )
        del_btn.clicked.connect(lambda: self.deleted.emit(habit.id))
        layout.addWidget(del_btn)


# ------------------------------------------------------------------ Settings row helpers
class SettingsToggleRow(QFrame):
    toggled = Signal(bool)

    def __init__(self, title: str, checked: bool, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_CARD_TRANSLUCENT}; border-radius: 12px; }} QLabel {{ background: transparent; }}")
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


class SettingsNavRow(QFrame):
    clicked = Signal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_CARD_TRANSLUCENT}; border-radius: 12px; }} QLabel {{ background: transparent; }}")
        self.setCursor(Qt.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 15px; font-weight: 600;")
        layout.addWidget(lbl, 1)
        chevron = QLabel("›")
        chevron.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 18px; font-weight: 700;")
        layout.addWidget(chevron)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class FontSizeRow(QFrame):
    changed = Signal(str)

    def __init__(self, current: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_CARD_TRANSLUCENT}; border-radius: 12px; }} QLabel {{ background: transparent; }}")
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


class ThemeSwatchRow(QFrame):
    """Одна строка палитры тем на экране 'Темы приложения' — только отображение, без выбора кликом."""

    def __init__(self, name: str, color: str, active: bool, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(f"QFrame {{ background-color: {color}; border-radius: 22px; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 14, 0)
        lbl = QLabel(name.capitalize())
        lbl.setStyleSheet("color: white; font-size: 13px; font-weight: 700;")
        layout.addWidget(lbl, 1)
        dot = QLabel()
        dot.setFixedSize(22, 22)
        dot.setStyleSheet(
            f"background-color: {'white' if active else 'rgba(255,255,255,0.35)'}; "
            f"border-radius: 11px; border: 2px solid rgba(0,0,0,0.35);"
        )
        layout.addWidget(dot)


# ------------------------------------------------------------------ Add habit form (встроенный экран)
class AddHabitForm(QFrame):
    """Форма добавления привычки как экран (не диалог)."""

    submitted = Signal(dict)

    def __init__(self, accent: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_CARD_TRANSLUCENT}; border-radius: 18px; }} "
                            f"QLabel {{ background: transparent; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        field_style = (
            "QLineEdit, QSpinBox, QComboBox, QTimeEdit { background-color: rgba(255,255,255,0.85); "
            "color: #1c1c22; border: 1px solid rgba(0,0,0,0.15); border-radius: 10px; padding: 8px; }"
        )
        self.setStyleSheet(self.styleSheet() + field_style)

        def field_label(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 13px; font-weight: 600;")
            return l

        layout.addWidget(field_label("Название"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Медитация")
        layout.addWidget(self.name_edit)

        layout.addWidget(field_label("Иконка"))
        self.icon_combo = QComboBox()
        self.icon_combo.addItems(ICON_CHOICES)
        layout.addWidget(self.icon_combo)

        row = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(field_label("Цель в день"))
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 100)
        self.target_spin.setValue(1)
        col1.addWidget(self.target_spin)
        row.addLayout(col1)

        col2 = QVBoxLayout()
        col2.addWidget(field_label("Единица"))
        self.unit_edit = QLineEdit()
        self.unit_edit.setText("раз")
        col2.addWidget(self.unit_edit)
        row.addLayout(col2)
        layout.addLayout(row)

        self.reminder_check = QCheckBox("Добавить напоминание")
        self.reminder_check.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 13px;")
        layout.addWidget(self.reminder_check)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setEnabled(False)
        self.reminder_check.toggled.connect(self.time_edit.setEnabled)
        layout.addWidget(self.time_edit)

        save_btn = primary_button("Сохранить привычку", accent)
        save_btn.clicked.connect(self._on_submit)
        layout.addWidget(save_btn)

    def _on_submit(self):
        reminder = self.time_edit.time().toString("HH:mm") if self.reminder_check.isChecked() else None
        data = {
            "name": self.name_edit.text().strip() or "Новая привычка",
            "icon": self.icon_combo.currentText(),
            "target": self.target_spin.value(),
            "unit": self.unit_edit.text().strip() or "раз",
            "reminder_time": reminder,
        }
        self.submitted.emit(data)


# ------------------------------------------------------------------ Bottom nav
class BottomNav(QFrame):
    def __init__(self, on_select, parent=None):
        super().__init__(parent)
        self.on_select = on_select
        self.setFixedHeight(60)
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_NAV_BG}; border-radius: 26px; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        self.buttons = []
        for i, (icon, name) in enumerate([("🏠", "home"), ("⏰", "reminders"), ("⚙️", "settings")]):
            btn = QPushButton(icon)
            btn.setCheckable(True)
            btn.setFixedSize(44, 44)
            btn.setStyleSheet(
                "QPushButton { background-color: transparent; border-radius: 14px; font-size: 18px; }"
                "QPushButton:checked { background-color: rgba(0,0,0,0.12); }"
            )
            btn.clicked.connect(lambda _, idx=i: self.on_select(idx))
            layout.addWidget(btn)
            self.buttons.append(btn)
        self.set_checked(0)

    def set_checked(self, idx: Optional[int]):
        for i, b in enumerate(self.buttons):
            b.setChecked(i == idx)
