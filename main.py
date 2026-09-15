"""
main.py — точка входа приложения «Трекер привычек» на PySide6.
Единое окно: все экраны переключаются внутри одного QStackedWidget,
отдельные окна/диалоги не используются.
Запуск:  python main.py
"""
import os
import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QStackedWidget, QLineEdit, QMessageBox, QFrame,
)

from models import HabitStore, today
from widgets import (
    TopBar, CalendarPage, StatsPage, WeekStrip, ReminderPreviewCard, ReminderRow, HomeActionCard,
        HabitRow, AddHabitForm, SettingsToggleRow, FontSizeRow, IconPickerPage,
    BottomNav, primary_button, res_icon, hide_scrollbar,
    COLOR_APP_BG, COLOR_ONBOARD_BG, COLOR_TEXT_DARK, COLOR_TEXT_MUTED,
    COLOR_HABITS_CARD, COLOR_ADD_CARD, COLOR_HOME_CARD_BG,
)

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# индексы экранов в QStackedWidget
IDX_ONBOARDING = 0
IDX_HOME = 1
IDX_HABITS = 2
IDX_ADD_HABIT = 3
IDX_REMINDERS = 4
IDX_SETTINGS = 5
IDX_ICON_PICKER = 6
IDX_STATS = 7
IDX_CALENDAR = 8

NAV_TABS = {IDX_HOME: 0, IDX_STATS: 1, IDX_SETTINGS: 2}


def load_custom_fonts():
    """Регистрирует шрифты в QFontDatabase, возвращает словарь их семейств."""
    families = {}
    paths = {
        "fascinate": "FascinateInline-Regular.ttf",
        "epunda": "EpundaSlab-Variable.ttf",
        "shrikhand": "Shrikhand-Regular.ttf",
        "arima": "Arima-Variable.ttf",
    }
    for key, filename in paths.items():
        fid = QFontDatabase.addApplicationFont(os.path.join(FONTS_DIR, filename))
        fams = QFontDatabase.applicationFontFamilies(fid)
        families[key] = fams[0] if fams else "Arial"
    return families


# ------------------------------------------------------------------ Онбординг
class OnboardingPage(QWidget):
    def __init__(self, on_submit, fonts, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {COLOR_ONBOARD_BG};")
        self.on_submit = on_submit

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 0, 28, 0)
        outer.setSpacing(0)

        outer.addStretch(9)

        title = QLabel("Приветствуем!")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont(fonts["fascinate"])
        title_font.setPointSize(18)
        title_font.setBold(False)
        title.setFont(title_font)
        title.setStyleSheet("color: rgba(0,0,0,0.8); background: transparent;")
        outer.addWidget(title)

        outer.addStretch(19)

        subtitle = QLabel("Введите ваше имя")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont(fonts["fascinate"])
        subtitle_font.setPointSize(18)
        subtitle_font.setBold(False)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: rgba(0,0,0,0.8); background: transparent;")
        outer.addWidget(subtitle)

        outer.addSpacing(18)

        # Поле ввода собрано вручную (рамка + текст + иконка 30x30),
        # чтобы иконка отправки была строго нужного размера, как в макете.
        input_box = QFrame()
        input_box.setFixedHeight(42)
        input_box.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #dfdfdf; border-radius: 10px; }"
        )
        input_row = QHBoxLayout(input_box)
        input_row.setContentsMargins(16, 2, 4, 2)
        input_row.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("...")
        self.name_edit.setStyleSheet(
            "QLineEdit { background: transparent; border: none; font-size: 14px; color: #828282; }"
        )
        self.name_edit.returnPressed.connect(self._submit)
        input_row.addWidget(self.name_edit, 1)

        submit_btn = QPushButton()
        submit_btn.setIcon(QIcon(os.path.join(RESOURCES_DIR, "submit_icon.png")))
        submit_btn.setIconSize(QSize(30, 30))
        submit_btn.setFixedSize(34, 34)
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; }"
        )
        submit_btn.clicked.connect(self._submit)
        input_row.addWidget(submit_btn)

        outer.addWidget(input_box)

        outer.addSpacing(8)

        caption = QLabel("При первом использовании приложения потребуется\nввести ваше имя.")
        caption.setAlignment(Qt.AlignCenter)
        caption_font = QFont(fonts["epunda"])
        caption_font.setPointSize(8)
        caption.setFont(caption_font)
        caption.setStyleSheet("color: #000000; background: transparent;")
        outer.addWidget(caption)

        outer.addStretch(46)

    def _submit(self):
        name = self.name_edit.text().strip()
        if not name:
            name = "Друг"
        self.on_submit(name)



# ------------------------------------------------------------------ Главный экран
class HomePage(QWidget):
    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw
        self.fonts = mw.fonts

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 12)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        self.greeting_lbl = QLabel()
        self.greeting_lbl.setStyleSheet("color: white;")
        greet_font = QFont(self.fonts.get("shrikhand", "Arial"), 15)
        greet_font.setItalic(True)
        self.greeting_lbl.setFont(greet_font)
        header_row.addWidget(self.greeting_lbl, 1)

        settings_btn = QPushButton()
        settings_btn.setIcon(res_icon("settings_icon.png"))
        settings_btn.setIconSize(QSize(22, 22))
        settings_btn.setFixedSize(30, 30)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        settings_btn.clicked.connect(lambda: mw.go_to(IDX_SETTINGS))
        header_row.addWidget(settings_btn, 0, Qt.AlignTop)
        outer.addLayout(header_row)

        self.week_strip = WeekStrip(store, font_family=self.fonts.get("arima"))
        self.week_strip.month_clicked.connect(self.on_month_clicked)
        outer.addWidget(self.week_strip)

        self.reminder_slot = QVBoxLayout()
        outer.addLayout(self.reminder_slot)

        outer.addStretch()

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.habits_card = HomeActionCard(
            "Мои привычки", "📋", COLOR_HOME_CARD_BG,
            font_family=self.fonts.get("arima"), preview_lines=True,
        )
        self.habits_card.clicked.connect(lambda: mw.go_to(IDX_HABITS))
        self.add_card = HomeActionCard(
            "Добавить привычку", "➕", COLOR_HOME_CARD_BG,
            font_family=self.fonts.get("arima"),
        )
        self.add_card.clicked.connect(lambda: mw.go_to(IDX_ADD_HABIT))
        cards_row.addWidget(self.habits_card)
        cards_row.addWidget(self.add_card)
        outer.addLayout(cards_row)

        self.refresh()

    def on_month_clicked(self):
        self.mw.go_to(IDX_CALENDAR)

    def refresh(self):
        name = self.store.settings.get("name") or "Друг"
        self.greeting_lbl.setText(f"{self.store.greeting()},\n{name}")

        while self.reminder_slot.count():
            item = self.reminder_slot.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        card = ReminderPreviewCard(self.store, font_family=self.fonts.get("arima"))
        card.clicked.connect(lambda: self.mw.go_to(IDX_REMINDERS))
        self.reminder_slot.addWidget(card)


# ------------------------------------------------------------------ Мои привычки
class HabitsPage(QWidget):
    # Реальная «естественная» ширина карточки при исходных (немасштабированных)
    # размерах — измерено по sizeHint шапки карточки (аватар+текст+время+периодичность).
    # Именно от неё, а не от ширины окна, отталкивается масштаб: иначе при scale=1.0
    # контент всё равно не помещается и просто обрезается краем окна.
    BASE_WIDTH = 408
    MIN_SCALE = 0.55
    MAX_SCALE = 1.3

    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw
        self.rows = []
        self._scale = 1.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(12)

        top = TopBar("Мои привычки", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to(IDX_HOME))
        outer.addWidget(top)

        self.list_area = QScrollArea()
        self.list_area.setWidgetResizable(True)
        self.list_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        hide_scrollbar(self.list_area)
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        self.list_area.setWidget(self.list_container)
        outer.addWidget(self.list_area, 1)

        self.refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        available = self.width() - 32  # отступы outer.setContentsMargins(16,...,16,...)
        scale = max(self.MIN_SCALE, min(self.MAX_SCALE, available / self.BASE_WIDTH))
        if abs(scale - self._scale) < 0.02:
            return
        self._scale = scale
        for row in self.rows:
            row.apply_scale(scale)

    def on_toggle(self, habit_id: str):
        self.store.toggle_done(habit_id, today())
        self.refresh()
        self.mw.home_page.refresh()

    def on_increment(self, habit_id: str):
        self.store.increment(habit_id, today())
        self.refresh()
        self.mw.home_page.refresh()

    def on_delete(self, habit_id: str):
        reply = QMessageBox.question(
            self, "Удалить привычку", "Точно удалить эту привычку и всю её историю?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.store.remove_habit(habit_id)
            self.refresh()
            self.mw.home_page.refresh()

    def refresh(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.rows = []
        if not self.store.habits:
            empty = QLabel("Пока нет привычек.\nДобавьте первую с главного экрана.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty.setStyleSheet(f"color: rgba(255,255,255,0.6); padding: 30px; font-size: 13px;")
            self.list_layout.addWidget(empty)
        else:
            for h in self.store.habits:
                row = HabitRow(h, COLOR_HABITS_CARD)
                row.toggled.connect(self.on_toggle)
                row.incremented.connect(self.on_increment)
                row.deleted.connect(self.on_delete)
                row.apply_scale(self._scale)
                self.list_layout.addWidget(row)
                self.rows.append(row)
        self.list_layout.addStretch()


# ------------------------------------------------------------------ Добавить привычку
class AddHabitPage(QWidget):
    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(12)

        top = TopBar("Добавить привычку", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to(IDX_HOME))
        outer.addWidget(top)

        self.form = AddHabitForm(COLOR_HABITS_CARD)
        self.form.submitted.connect(self.on_submit)
        self.form.icon_pick_requested.connect(lambda: mw.go_to(IDX_ICON_PICKER))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setWidget(self.form)
        hide_scrollbar(scroll)
        outer.addWidget(scroll, 1)

    def on_submit(self, data: dict):
        self.store.add_habit(**data)
        self.mw.habits_page.refresh()
        self.mw.home_page.refresh()
        self.mw.reminders_page.refresh()
        self.mw.go_to(IDX_HABITS)
        self.form.reset()  # сброс формы для следующего использования


# ------------------------------------------------------------------ Ближайшие задачи
class RemindersPage(QWidget):
    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw
        self.fonts = mw.fonts

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(16)

        top = TopBar("Ближайшие задачи", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to(IDX_HOME))
        outer.addWidget(top)

        self.list_area = QScrollArea()
        self.list_area.setWidgetResizable(True)
        self.list_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        hide_scrollbar(self.list_area)
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(19)
        self.list_layout.addStretch()
        self.list_area.setWidget(self.list_container)
        outer.addWidget(self.list_area, 1)

        self.refresh()

    def refresh(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        upcoming = self.store.upcoming_reminders()
        if not upcoming:
            empty = QLabel("На сегодня задач больше нет 🎉")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: rgba(255,255,255,0.6); padding: 30px; font-size: 13px;")
            self.list_layout.addWidget(empty)
        else:
            nearest_time = upcoming[0].reminder_time
            for h in upcoming:
                is_nearest = h.reminder_time == nearest_time
                self.list_layout.addWidget(
                    ReminderRow(h, is_nearest=is_nearest, font_family=self.fonts.get("arima"))
                )
        self.list_layout.addStretch()


# ------------------------------------------------------------------ Настройки
class SettingsPage(QWidget):
    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(12)

        top = TopBar("Настройки", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to(IDX_HOME))
        outer.addWidget(top)

        self.notif_row = SettingsToggleRow("Уведомления", store.settings.get("notifications", True))
        self.notif_row.toggled.connect(store.set_notifications)
        outer.addWidget(self.notif_row)

        self.font_row = FontSizeRow(store.settings.get("font_size", "M"))
        self.font_row.changed.connect(store.set_font_size)
        outer.addWidget(self.font_row)

        outer.addStretch()


# ------------------------------------------------------------------ Главное окно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Трекер привычек")
        self.resize(390, 740)
        self.store = HabitStore()
        self.fonts = load_custom_fonts()
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLOR_APP_BG}; }}")

        central = QWidget()
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.onboarding_page = OnboardingPage(self.on_name_submitted, self.fonts)
        self.home_page = HomePage(self.store, self)
        self.habits_page = HabitsPage(self.store, self)
        self.add_habit_page = AddHabitPage(self.store, self)
        self.reminders_page = RemindersPage(self.store, self)
        self.settings_page = SettingsPage(self.store, self)
        self.icon_picker_page = IconPickerPage(self)
        self.icon_picker_page.icon_chosen.connect(self.on_icon_chosen)
        self.stats_page = StatsPage(self.store, self)
        self.calendar_page = CalendarPage(self.store, self)

        for page in (self.onboarding_page, self.home_page, self.habits_page,
                    self.add_habit_page, self.reminders_page,
                    self.settings_page, self.icon_picker_page, self.stats_page,
                    self.calendar_page):
            self.stack.addWidget(page)

        nav_wrap = QWidget()
        nav_wrap_layout = QVBoxLayout(nav_wrap)
        nav_wrap_layout.setContentsMargins(16, 6, 16, 14)
        self.nav = BottomNav(self.go_to)
        nav_wrap_layout.addWidget(self.nav)
        root.addWidget(nav_wrap)
        self.nav_wrap = nav_wrap

        if self.store.has_name():
            self.go_to(IDX_HOME)
        else:
            self.stack.setCurrentIndex(IDX_ONBOARDING)
            self.nav_wrap.hide()

    def go_to_home(self):
        self.go_to(IDX_HOME)

    def go_to_add_habit(self):
        self.go_to(IDX_ADD_HABIT)  
              
    def on_icon_chosen(self, emoji: str):
        self.add_habit_page.form.set_icon(emoji)
        self.go_to(IDX_ADD_HABIT)

    def on_name_submitted(self, name: str):
        self.store.set_name(name)
        self.nav_wrap.show()
        self.home_page.refresh()
        self.go_to(IDX_HOME)

    def go_to(self, idx: int):
        self.stack.setCurrentIndex(idx)
        if idx in NAV_TABS:
            self.nav_wrap.show()
            self.nav.set_checked(NAV_TABS[idx])
        else:
            self.nav.set_checked(None)
        if idx == IDX_HOME:
            self.home_page.refresh()
        elif idx == IDX_HABITS:
            self.habits_page.refresh()
        elif idx == IDX_REMINDERS:
            self.reminders_page.refresh()
        elif idx == IDX_STATS:
            self.stats_page.refresh()
        elif idx == IDX_CALENDAR:
            self.calendar_page.refresh()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
