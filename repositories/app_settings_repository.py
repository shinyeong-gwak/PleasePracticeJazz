import json
from pathlib import Path


FILE_PATH = Path("data/music/app_settings.json")

DEFAULT_SETTINGS = {
    "country": "kr",
    "timeZone": "Asia/Seoul",
    "weekStartDay": 0,
}

COUNTRY_OPTIONS = {
    "kr": {
        "label": "\uc11c\uc6b8",
        "timeZone": "Asia/Seoul",
    },
    "jp": {
        "label": "\uc77c\ubcf8",
        "timeZone": "Asia/Tokyo",
    },
    "us": {
        "label": "\ubbf8\uad6d",
        "timeZone": "America/New_York",
    },
    "utc": {
        "label": "UTC",
        "timeZone": "UTC",
    },
}

WEEKDAY_LABELS = [
    "\uc6d4",
    "\ud654",
    "\uc218",
    "\ubaa9",
    "\uae08",
    "\ud1a0",
    "\uc77c",
]


def ensure_file():
    FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not FILE_PATH.exists():
        FILE_PATH.write_text(
            json.dumps(
                DEFAULT_SETTINGS,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def load_all():
    ensure_file()

    try:
        data = json.loads(FILE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}

    return normalize_settings(data)


def save_all(settings):
    FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    FILE_PATH.write_text(
        json.dumps(
            normalize_settings(settings),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def normalize_week_start_day(value):
    try:
        week_start_day = int(value)
    except (TypeError, ValueError):
        week_start_day = DEFAULT_SETTINGS["weekStartDay"]

    if week_start_day < 0 or week_start_day > 6:
        week_start_day = DEFAULT_SETTINGS["weekStartDay"]

    return week_start_day


def normalize_country(value):
    country = str(value or "").strip().lower()
    return country if country in COUNTRY_OPTIONS else DEFAULT_SETTINGS["country"]


def normalize_settings(settings):
    settings = settings or {}
    country = normalize_country(settings.get("country"))
    time_zone = COUNTRY_OPTIONS[country]["timeZone"]

    if settings.get("timeZone") in [option["timeZone"] for option in COUNTRY_OPTIONS.values()]:
        time_zone = settings.get("timeZone") or time_zone

    return {
        "country": country,
        "timeZone": time_zone,
        "weekStartDay": normalize_week_start_day(settings.get("weekStartDay")),
    }


def get_settings():
    return load_all()


def update_settings(payload):
    current = load_all()
    current.update(payload or {})
    saved = normalize_settings(current)
    save_all(saved)
    return saved


def get_time_zone_name():
    return get_settings()["timeZone"]


def get_week_start_day():
    return get_settings()["weekStartDay"]


def get_country_label():
    return COUNTRY_OPTIONS[get_settings()["country"]]["label"]


def get_weekday_labels(start_day=None):
    start_day = normalize_week_start_day(
        get_week_start_day() if start_day is None else start_day
    )
    return WEEKDAY_LABELS[start_day:] + WEEKDAY_LABELS[:start_day]
