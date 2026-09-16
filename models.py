"""
models.py — модель данных и хранилище (JSON) для трекера привычек.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

DATA_DIR = os.path.join(os.path.expanduser("~"), ".habit_tracker")
DATA_FILE = os.path.join(DATA_DIR, "habits.json")

WEEKDAYS_RU_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS_RU = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
             "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

# Палитра тем (название, hex) — используется и для тем приложения, и для бейджей привычек
THEME_COLORS = [
    ("розовый", "#CE7979"),
    ("зелёный", "#89CD74"),
    ("бирюзовый", "#99B8E8"),
    ("жёлтый", "#D1D55B"),
    ("фиолетовый", "#9268AE"),
]

FONT_SIZES = ["S", "M", "L"]

# Палитра «цвет отметки серии» — 12 цветов, ровно как заданы в HTML-макете
# экрана «Добавить привычку» (top-561 / top-603, слева направо).
MARK_COLORS = [
    "#39ff14", "#4a90e2", "#9a23e8", "#ffd700", "#dd0202", "#a8e6cf",
    "#00f0ff", "#ff8800", "#ff007a", "#ffd3b6", "#3700ff", "#f200ff",
]

# Периодичность привычки — ровно как в макете: День / Неделя / Месяц
PERIODS = [("day", "День"), ("week", "Неделя"), ("month", "Месяц")]


def today() -> date:
    return date.today()


def date_to_str(d: date) -> str:
    return d.isoformat()


def str_to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


@dataclass
class Habit:
    id: str
    name: str
    icon: str = "⭐"
    target: int = 1                 # сколько раз в день нужно выполнить
    unit: str = "раз"               # единица измерения (раз, стаканов, страниц...)
    period: str = "day"             # периодичность: day / week / month
    color: str = MARK_COLORS[0]     # цвет отметки серии (палитра MARK_COLORS)
    reminder_time: Optional[str] = None   # "HH:MM" или None
    created: str = field(default_factory=lambda: date_to_str(today()))
    completions: Dict[str, int] = field(default_factory=dict)

    def progress_for(self, d: date) -> int:
        return self.completions.get(date_to_str(d), 0)

    def is_done(self, d: date) -> bool:
        return self.progress_for(d) >= self.target

    def current_streak(self) -> int:
        """Текущая серия подряд выполненных дней, считая от сегодня
        (если сегодня ещё не отмечено — считаем от вчера)."""
        d = today()
        if not self.is_done(d):
            d -= timedelta(days=1)
        streak = 0
        while self.is_done(d):
            streak += 1
            d -= timedelta(days=1)
        return streak

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Habit":
        return Habit(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Привычка"),
            icon=data.get("icon", "⭐"),
            target=data.get("target", 1),
            unit=data.get("unit", "раз"),
            period=data.get("period", "day"),
            color=data.get("color", MARK_COLORS[0]),
            reminder_time=data.get("reminder_time"),
            created=data.get("created", date_to_str(today())),
            completions=data.get("completions", {}),
        )

def default_settings() -> dict:
    return {
        "name": None,
        "notifications": True,
        "font_size": "M",
        "joined": None,
    }

def default_settings() -> dict:
    return {
        "name": None,
        "notifications": True,
        "font_size": "M",
    }


class HabitStore:
    """Хранит список привычек, настройки пользователя и умеет считать статистику."""

    def __init__(self):
        self.habits: List[Habit] = []
        self.settings: dict = default_settings()
        self.load()

    def profile_stats(self) -> dict:
        total_habits = len(self.habits)
        best_streak = max((h.current_streak() for h in self.habits), default=0)
        total_marks = sum(len(h.completions) for h in self.habits)
        return {"habits": total_habits, "streak": best_streak, "marks": total_marks}

    def wipe(self):
        """Полностью удаляет файл данных и сбрасывает состояние в памяти."""
        try:
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
        except OSError:
            pass
        self.habits = []
        self.settings = default_settings()
        
    def joined_label(self) -> str:
        raw = self.settings.get("joined")
        if not raw:
            return ""
        d = str_to_date(raw)
        return f"с нами с {d.day} {MONTHS_RU[d.month - 1].lower()} {d.year}"


    # ---------- персистентность ----------
    def load(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.habits = [Habit.from_dict(h) for h in raw.get("habits", [])]
                loaded_settings = raw.get("settings", {})
                self.settings = {**default_settings(), **loaded_settings}
            except (json.JSONDecodeError, OSError):
                self.habits = []
                self.settings = default_settings()
        else:
            self.habits = []
            self.settings = default_settings()
            self.save()

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"habits": [h.to_dict() for h in self.habits], "settings": self.settings},
                f, ensure_ascii=False, indent=2,
            )

    # ---------- онбординг / настройки ----------
    def has_name(self) -> bool:
        return bool(self.settings.get("name"))

    def set_name(self, name: str):
        self.settings["name"] = name.strip()
        if not self.settings.get("joined"):
            self.settings["joined"] = date_to_str(today())
        self.save()

    def set_notifications(self, enabled: bool):
        self.settings["notifications"] = bool(enabled)
        self.save()

    def set_font_size(self, size: str):
        if size in FONT_SIZES:
            self.settings["font_size"] = size
            self.save()

    # ---------- CRUD привычек ----------
    def add_habit(self, name: str, icon: str, target: int, unit: str,
                  reminder_time: Optional[str], period: str = "day",
                  color: str = MARK_COLORS[0]) -> Habit:
        h = Habit(id=str(uuid.uuid4()), name=name, icon=icon, target=max(1, target),
                   unit=unit or "раз", reminder_time=reminder_time,
                   period=period, color=color)
        self.habits.append(h)
        self.save()
        return h

    def remove_habit(self, habit_id: str):
        self.habits = [h for h in self.habits if h.id != habit_id]
        self.save()

    def toggle_done(self, habit_id: str, d: date):
        for h in self.habits:
            if h.id == habit_id:
                if h.is_done(d):
                    h.completions.pop(date_to_str(d), None)
                else:
                    h.completions[date_to_str(d)] = h.target
        self.save()

    def increment(self, habit_id: str, d: date, step: int = 1):
        for h in self.habits:
            if h.id == habit_id:
                cur = h.progress_for(d)
                new_val = max(0, min(h.target, cur + step))
                if new_val == 0:
                    h.completions.pop(date_to_str(d), None)
                else:
                    h.completions[date_to_str(d)] = new_val
        self.save()

    # ---------- выборки ----------
    def upcoming_reminders(self) -> List[Habit]:
        """Привычки с напоминанием на сегодня, время которых ещё НЕ наступило
        (>= текущего времени устройства), и которые ещё не выполнены.
        Сортировка по времени (при совпадении — по алфавиту), поэтому первый
        элемент списка всегда реально ближайший по времени, а не просто самый
        ранний по расписанию: как только время напоминания проходит, оно
        пропадает из списка и «эстафету» принимает следующее по времени."""
        t = today()
        now_str = datetime.now().strftime("%H:%M")
        result = [
            h for h in self.habits
            if h.reminder_time and h.reminder_time >= now_str and not h.is_done(t)
        ]
        result.sort(key=lambda h: (h.reminder_time, h.name.lower()))
        return result

    def week_dates(self, anchor: Optional[date] = None) -> List[date]:
        anchor = anchor or today()
        monday = anchor - timedelta(days=anchor.weekday())
        return [monday + timedelta(days=i) for i in range(7)]

    def greeting(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Доброе утро"
        if 12 <= hour < 18:
            return "Добрый день"
        if 18 <= hour < 23:
            return "Добрый вечер"
        return "Доброй ночи"
