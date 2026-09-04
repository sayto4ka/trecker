"""
main.py — точка входа приложения «Трекер привычек» на PySide6.
Единое окно: все экраны переключаются внутри одного QStackedWidget,
отдельные окна/диалоги не используются.
Запуск:  python main.py
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QStackedWidget, QLineEdit, QMessageBox,
)

from models import HabitStore, today, THEME_COLORS
from widgets import (
    TopBar, WeekStrip, ReminderPreviewCard, ReminderRow, HomeActionCard,
    HabitRow, AddHabitForm, SettingsToggleRow, SettingsNavRow, FontSizeRow,
    ThemeSwatchRow, BottomNav, primary_button,
    COLOR_APP_BG, COLOR_ONBOARD_BG, COLOR_TEXT_DARK, COLOR_TEXT_MUTED,
)

# индексы экранов в QStackedWidget
IDX_ONBOARDING = 0
IDX_HOME = 1
IDX_HABITS = 2
IDX_ADD_HABIT = 3
IDX_REMINDERS = 4
IDX_SETTINGS = 5
IDX_THEMES = 6

NAV_TABS = {IDX_HOME: 0, IDX_REMINDERS: 1, IDX_SETTINGS: 2}


# ------------------------------------------------------------------ Онбординг
class OnboardingPage(QWidget):
    def __init__(self, on_submit, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {COLOR_ONBOARD_BG};")
        self.on_submit = on_submit

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 90, 28, 28)
        outer.setSpacing(18)
        outer.setAlignment(Qt.AlignTop)

        title = QLabel("Приветствуем!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 26px; font-weight: 800;")
        outer.addWidget(title)
        outer.addSpacing(140)

        subtitle = QLabel("Введите ваше имя")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 20px; font-weight: 800;")
        outer.addWidget(subtitle)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ваше имя")
        self.name_edit.setAlignment(Qt.AlignCenter)
        self.name_edit.setFixedHeight(42)
        self.name_edit.setStyleSheet(
            "QLineEdit { background-color: white; border: 1px solid #e5e5e5; border-radius: 10px; "
            "font-size: 14px; color: #1c1c22; }"
        )
        self.name_edit.returnPressed.connect(self._submit)
        outer.addWidget(self.name_edit)

        caption = QLabel("При первом использовании приложения потребуется ввести ваше имя.")
        caption.setAlignment(Qt.AlignCenter)
        caption.setWordWrap(True)
        caption.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        outer.addWidget(caption)

        outer.addSpacing(20)
        continue_btn = primary_button("Продолжить", "#9268AE")
        continue_btn.clicked.connect(self._submit)
        outer.addWidget(continue_btn)

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

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 12)
        outer.setSpacing(16)

        self.greeting_lbl = QLabel()
        self.greeting_lbl.setStyleSheet("color: white; font-size: 19px; font-weight: 800;")
        outer.addWidget(self.greeting_lbl)

        self.reminder_slot = QVBoxLayout()
        outer.addLayout(self.reminder_slot)

        self.week_strip = WeekStrip(store)
        outer.addWidget(self.week_strip)

        outer.addStretch()

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.habits_card = HomeActionCard("Мои привычки", "📋", store.theme)
        self.habits_card.clicked.connect(lambda: mw.go_to(IDX_HABITS))
        self.add_card = HomeActionCard("Добавить привычку", "➕", "#94a3b8")
        self.add_card.clicked.connect(lambda: mw.go_to(IDX_ADD_HABIT))
        cards_row.addWidget(self.habits_card)
        cards_row.addWidget(self.add_card)
        outer.addLayout(cards_row)

        self.refresh()

    def refresh(self):
        name = self.store.settings.get("name") or "Друг"
        self.greeting_lbl.setText(f"{self.store.greeting()},\n{name}")

        while self.reminder_slot.count():
            item = self.reminder_slot.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        card = ReminderPreviewCard(self.store)
        card.clicked.connect(lambda: self.mw.go_to(IDX_REMINDERS))
        self.reminder_slot.addWidget(card)

        self.habits_card.setStyleSheet(
            f"QFrame {{ background-color: {self.store.theme}; border-radius: 18px; }}"
        )


# ------------------------------------------------------------------ Мои привычки
class HabitsPage(QWidget):
    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(12)

        top = TopBar("Мои привычки", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to(IDX_HOME))
        outer.addWidget(top)

        self.list_area = QScrollArea()
        self.list_area.setWidgetResizable(True)
        self.list_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        self.list_area.setWidget(self.list_container)
        outer.addWidget(self.list_area, 1)

        self.refresh()

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
        if not self.store.habits:
            empty = QLabel("Пока нет привычек.\nДобавьте первую с главного экрана.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; padding: 30px; font-size: 13px;")
            self.list_layout.addWidget(empty)
        else:
            for h in self.store.habits:
                row = HabitRow(h, self.store.theme)
                row.toggled.connect(self.on_toggle)
                row.incremented.connect(self.on_increment)
                row.deleted.connect(self.on_delete)
                self.list_layout.addWidget(row)
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

        self.form = AddHabitForm(store.theme)
        self.form.submitted.connect(self.on_submit)
        outer.addWidget(self.form)
        outer.addStretch()

    def on_submit(self, data: dict):
        self.store.add_habit(**data)
        self.mw.habits_page.refresh()
        self.mw.home_page.refresh()
        self.mw.reminders_page.refresh()
        self.mw.go_to(IDX_HABITS)
        # сброс формы для следующего использования
        self.form.name_edit.clear()
        self.form.target_spin.setValue(1)
        self.form.unit_edit.setText("раз")
        self.form.reminder_check.setChecked(False)


# ------------------------------------------------------------------ Ближайшие задачи
class RemindersPage(QWidget):
    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(12)

        top = TopBar("Ближайшие задачи")
        outer.addWidget(top)

        self.list_area = QScrollArea()
        self.list_area.setWidgetResizable(True)
        self.list_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(10)
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
            empty.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; padding: 30px; font-size: 13px;")
            self.list_layout.addWidget(empty)
        else:
            for h in upcoming:
                self.list_layout.addWidget(ReminderRow(h))
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

        top = TopBar("Настройки")
        outer.addWidget(top)

        self.notif_row = SettingsToggleRow("Уведомления", store.settings.get("notifications", True))
        self.notif_row.toggled.connect(store.set_notifications)
        outer.addWidget(self.notif_row)

        self.theme_row = SettingsNavRow("Темы приложения")
        self.theme_row.clicked.connect(lambda: mw.go_to(IDX_THEMES))
        outer.addWidget(self.theme_row)

        self.font_row = FontSizeRow(store.settings.get("font_size", "M"))
        self.font_row.changed.connect(store.set_font_size)
        outer.addWidget(self.font_row)

        outer.addStretch()


# ------------------------------------------------------------------ Темы приложения
class ThemesPage(QWidget):
    def __init__(self, store: HabitStore, mw: "MainWindow", parent=None):
        super().__init__(parent)
        self.store = store
        self.mw = mw

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 12)
        outer.setSpacing(14)

        top = TopBar("Темы приложения", show_back=True)
        top.back_clicked.connect(lambda: mw.go_to(IDX_SETTINGS))
        outer.addWidget(top)

        info = QLabel("Тема приложения выбирается случайно из списка ниже каждый день:")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 14px; font-weight: 600;")
        outer.addWidget(info)

        swatches_box = QVBoxLayout()
        swatches_box.setSpacing(10)
        for name, color in THEME_COLORS:
            swatches_box.addWidget(ThemeSwatchRow(name, color, active=(color == store.theme)))
        outer.addLayout(swatches_box)
        outer.addStretch()


# ------------------------------------------------------------------ Главное окно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Трекер привычек")
        self.resize(390, 740)
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLOR_APP_BG}; }}")

        self.store = HabitStore()
        self.store.maybe_reroll_theme()

        central = QWidget()
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.onboarding_page = OnboardingPage(self.on_name_submitted)
        self.home_page = HomePage(self.store, self)
        self.habits_page = HabitsPage(self.store, self)
        self.add_habit_page = AddHabitPage(self.store, self)
        self.reminders_page = RemindersPage(self.store, self)
        self.settings_page = SettingsPage(self.store, self)
        self.themes_page = ThemesPage(self.store, self)

        for page in (self.onboarding_page, self.home_page, self.habits_page,
                     self.add_habit_page, self.reminders_page,
                     self.settings_page, self.themes_page):
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


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
