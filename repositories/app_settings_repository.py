from repositories.db import execute, get_or_create_user_id, query_one


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

TIMEZONE_TO_COUNTRY = {
    option["timeZone"]: country
    for country, option in COUNTRY_OPTIONS.items()
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


def normalize_time_zone(value, country=None):
    time_zone = str(value or "").strip()

    if time_zone in TIMEZONE_TO_COUNTRY:
        return time_zone

    if country:
        return COUNTRY_OPTIONS[normalize_country(country)]["timeZone"]

    return DEFAULT_SETTINGS["timeZone"]


def infer_country(time_zone):
    return TIMEZONE_TO_COUNTRY.get(
        normalize_time_zone(time_zone),
        DEFAULT_SETTINGS["country"],
    )


def normalize_settings(settings):
    settings = settings or {}
    time_zone = normalize_time_zone(
        settings.get("timeZone"),
        settings.get("country"),
    )

    return {
        "country": infer_country(time_zone),
        "timeZone": time_zone,
        "weekStartDay": normalize_week_start_day(settings.get("weekStartDay")),
    }


def _select_settings_row(user_id):
    return query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                user_id::text AS "userId",
                locale,
                time_zone AS "timeZone",
                week_start_day AS "weekStartDay"
            FROM user_settings
            WHERE user_id = :'user_id'::uuid
            LIMIT 1
        ) AS t
        """,
        {"user_id": user_id},
    )


def ensure_settings_row():
    user_id = get_or_create_user_id()
    settings = _select_settings_row(user_id)
    if settings:
        return settings

    execute(
        """
        INSERT INTO user_settings (user_id, locale, time_zone, week_start_day)
        VALUES (
            :'user_id'::uuid,
            :'locale',
            :'time_zone',
            :'week_start_day'::int
        )
        ON CONFLICT (user_id) DO NOTHING
        """,
        {
            "user_id": user_id,
            "locale": "ko-KR",
            "time_zone": DEFAULT_SETTINGS["timeZone"],
            "week_start_day": DEFAULT_SETTINGS["weekStartDay"],
        },
    )

    return _select_settings_row(user_id)


def load_all():
    row = ensure_settings_row()
    return normalize_settings(row)


def save_all(settings):
    normalized = normalize_settings(settings)
    user_id = get_or_create_user_id()

    execute(
        """
        INSERT INTO user_settings (user_id, locale, time_zone, week_start_day)
        VALUES (
            :'user_id'::uuid,
            :'locale',
            :'time_zone',
            :'week_start_day'::int
        )
        ON CONFLICT (user_id) DO UPDATE SET
            locale = EXCLUDED.locale,
            time_zone = EXCLUDED.time_zone,
            week_start_day = EXCLUDED.week_start_day,
            updated_at = now()
        """,
        {
            "user_id": user_id,
            "locale": "ko-KR",
            "time_zone": normalized["timeZone"],
            "week_start_day": normalized["weekStartDay"],
        },
    )

    return normalized


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
