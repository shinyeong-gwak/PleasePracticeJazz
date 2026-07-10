import json
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from repositories import app_settings_repository
from repositories.db import (
    execute,
    get_or_create_user_id,
    query_one,
    query_rows,
)


INSIGHT_CATEGORIES = [
    "rhythm",
    "solo",
    "ensemble",
    "voicing",
]

BOOK_OPTIONS = [
    "Real Book 1",
    "Real Book 2",
    "Real Book 3",
    "New Real Book 1",
    "New Real Book 2",
    "New Real Book 3",
    "ETC",
]

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

DEFAULT_HOMEWORK_TITLE = "제목 없는 숙제"
DEFAULT_HOMEWORK_MEMO = "메모 없음"
DEFAULT_PRACTICE_TITLE = "제목 없는 연습"
DEFAULT_INSIGHT_TITLE = "제목 없는 인사이트"


def now_iso():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def get_app_timezone():
    return ZoneInfo(app_settings_repository.get_time_zone_name())


def get_week_start_day():
    return app_settings_repository.get_week_start_day()


def get_today():
    return datetime.now(get_app_timezone()).date()


def parse_timestamp(value):
    text = str(value or "").strip()

    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def get_week_range(target_date=None):
    if target_date is None:
        target_date = get_today()

    delta = (target_date.weekday() - get_week_start_day()) % 7
    start = target_date - timedelta(days=delta)
    end = start + timedelta(days=6)

    return start, end


def get_week_key(target_date=None):
    start, _ = get_week_range(target_date)
    return start.isoformat()


def get_week_label(target_date=None):
    start, end = get_week_range(target_date)
    return f"{start.month}.{start.day} - {end.month}.{end.day} Report"


def parse_item_date(value):
    text = str(value or "").strip()

    if not text:
        return None

    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None

    parsed = parse_timestamp(text)
    if parsed is None:
        return None

    return parsed.astimezone(get_app_timezone()).date()


def normalize_topics(topics):
    if isinstance(topics, str):
        topics = [
            item.strip()
            for item in topics.split(",")
            if item.strip()
        ]

    if not topics:
        return []

    return [
        str(topic).strip()
        for topic in topics
        if str(topic).strip()
    ]


def normalize_bool(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ["1", "true", "yes", "on"]

    return bool(value)


def normalize_status(value):
    text = str(value or "normal").strip().lower()
    if text == "good":
        return "GOOD"
    if text == "bad":
        return "BAD"
    return "NORMAL"


def normalize_collection(value):
    text = str(value or "practice").strip().lower()
    return "ENSEMBLE" if text == "ensemble" else "PRACTICE"


def _default_homework_item():
    return {
        "id": uuid4().hex,
        "title": DEFAULT_HOMEWORK_TITLE,
        "memo": DEFAULT_HOMEWORK_MEMO,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
        "status": "normal",
        "completedAt": None,
    }


def _default_practice_item():
    return {
        "id": uuid4().hex,
        "title": DEFAULT_PRACTICE_TITLE,
        "bpm": "",
        "book": "",
        "page": "",
        "memo": "",
        "spotifyUrl": "",
        "lickFile": "",
        "rendererFile": "",
        "status": "normal",
        "topics": [],
        "metronome": False,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }


def _default_insight_item():
    return {
        "id": uuid4().hex,
        "title": DEFAULT_INSIGHT_TITLE,
        "memo": "",
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }


def _query_user_row(sql, params=None):
    user_id = get_or_create_user_id()
    merged = {"user_id": user_id}
    if params:
        merged.update(params)
    return query_rows(sql, merged)


def _build_week_filter_sql(column_name, target_date=None):
    if target_date is None:
        return "", {}

    week_start, week_end = get_week_range(target_date)
    return (
        f"""
          AND ({column_name} AT TIME ZONE :'time_zone')::date
              BETWEEN :'week_start'::date AND :'week_end'::date
        """,
        {
            "time_zone": get_app_timezone().key,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
        },
    )


def _load_weekly_goals(target_date=None):
    week_filter_sql, week_filter_params = _build_week_filter_sql(
        "created_at",
        target_date,
    )
    return _query_user_row(
        f"""
        SELECT row_to_json(t)
        FROM (
            SELECT
                id::text AS id,
                title,
                COALESCE(memo, '') AS memo,
                lower(status::text) AS status,
                completed_at::text AS "completedAt",
                created_at::text AS "createdAt",
                updated_at::text AS "updatedAt"
            FROM weekly_goal
            WHERE user_id = :'user_id'::uuid
            {week_filter_sql}
            ORDER BY created_at DESC
        ) AS t
        """,
        week_filter_params,
    )


def _load_practice_items(target_date=None):
    week_filter_sql, week_filter_params = _build_week_filter_sql(
        "pi.created_at",
        target_date,
    )
    return _query_user_row(
        f"""
        SELECT row_to_json(t)
        FROM (
            SELECT
                pi.id::text AS id,
                CASE
                    WHEN pi.type::text = 'ENSEMBLE' THEN 'ensemble'
                    ELSE 'practice'
                END AS collection,
                pi.title,
                COALESCE(pi.bpm::text, '') AS bpm,
                COALESCE(pi.book, '') AS book,
                COALESCE(pi.page, '') AS page,
                COALESCE(pi.memo, '') AS memo,
                COALESCE(pi.spotify_url, '') AS "spotifyUrl",
                COALESCE(cl.file_name, '') AS "lickFile",
                COALESCE(sc.file_name, sc.original_file_name, '') AS "rendererFile",
                lower(pi.status::text) AS status,
                COALESCE(pi.metronome, false) AS metronome,
                COALESCE(array_agg(DISTINCT tp.name) FILTER (WHERE tp.name IS NOT NULL), '{{}}'::text[]) AS topics,
                pi.created_at::text AS "createdAt",
                pi.updated_at::text AS "updatedAt"
            FROM practice_item pi
            LEFT JOIN clip cl ON cl.id = pi.lick_id
            LEFT JOIN score sc ON sc.id = pi.score_id
            LEFT JOIN practice_topic pt ON pt.practice_id = pi.id
            LEFT JOIN topic tp ON tp.id = pt.topic_id
            WHERE pi.user_id = :'user_id'::uuid
            {week_filter_sql}
            GROUP BY
                pi.id,
                pi.type,
                pi.title,
                pi.bpm,
                pi.book,
                pi.page,
                pi.memo,
                pi.spotify_url,
                pi.status,
                pi.metronome,
                pi.created_at,
                pi.updated_at,
                cl.file_name,
                sc.file_name,
                sc.original_file_name
            ORDER BY pi.created_at DESC
        ) AS t
        """,
        week_filter_params,
    )


def _load_insights_rows():
    return _query_user_row(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                id::text AS id,
                lower(category::text) AS category,
                content,
                created_at::text AS "createdAt"
            FROM insight
            WHERE user_id = :'user_id'::uuid
            ORDER BY created_at DESC
        ) AS t
        """
    )


def _parse_insight_content(content):
    text = str(content or "").strip()
    if not text:
        return {
            "title": DEFAULT_INSIGHT_TITLE,
            "memo": "",
        }

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            "title": text,
            "memo": "",
        }

    return {
        "title": str(parsed.get("title") or DEFAULT_INSIGHT_TITLE).strip()
        or DEFAULT_INSIGHT_TITLE,
        "memo": str(parsed.get("memo") or "").strip(),
    }


def _compose_insight_content(title, memo):
    return json.dumps(
        {
            "title": str(title or DEFAULT_INSIGHT_TITLE).strip()
            or DEFAULT_INSIGHT_TITLE,
            "memo": str(memo or "").strip(),
        },
        ensure_ascii=False,
    )


def _ensure_topic_id(topic_name):
    topic_name = str(topic_name or "").strip()
    if not topic_name:
        return None

    execute(
        """
        INSERT INTO topic (name)
        VALUES (:'name')
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        """,
        {"name": topic_name},
    )

    row = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM topic
            WHERE name = :'name'
            LIMIT 1
        ) AS t
        """,
        {"name": topic_name},
    )
    return row["id"] if row else None


def _resolve_clip_id(file_name):
    file_name = str(file_name or "").strip()
    if not file_name:
        return None

    user_id = get_or_create_user_id()
    row = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM clip
            WHERE user_id = :'user_id'::uuid
              AND file_name = :'file_name'
            ORDER BY created_at DESC
            LIMIT 1
        ) AS t
        """,
        {
            "file_name": file_name,
            "user_id": user_id,
        },
    )
    return row["id"] if row else None


def _resolve_score_id(file_name):
    file_name = str(file_name or "").strip()
    if not file_name:
        return None

    user_id = get_or_create_user_id()
    row = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM score
            WHERE user_id = :'user_id'::uuid
              AND (
                file_name = :'file_name'
                OR original_file_name = :'file_name'
              )
            ORDER BY created_at DESC
            LIMIT 1
        ) AS t
        """,
        {
            "file_name": file_name,
            "user_id": user_id,
        },
    )
    return row["id"] if row else None


def _sync_practice_topics(practice_id, topics):
    execute(
        """
        DELETE FROM practice_topic
        WHERE practice_id = :'practice_id'::uuid
        """,
        {"practice_id": practice_id},
    )

    for topic_name in normalize_topics(topics):
        topic_id = _ensure_topic_id(topic_name)
        if not topic_id:
            continue

        execute(
            """
            INSERT INTO practice_topic (practice_id, topic_id)
            VALUES (:'practice_id'::uuid, :'topic_id'::uuid)
            ON CONFLICT DO NOTHING
            """,
            {
                "practice_id": practice_id,
                "topic_id": topic_id,
            },
        )


def _build_reports():
    reports = {}

    for item in _load_weekly_goals():
        item_date = parse_item_date(item.get("createdAt"))
        if item_date is None:
            continue

        week_key = get_week_key(item_date)
        report = reports.setdefault(
            week_key,
            {
                "weekKey": week_key,
                "weekLabel": get_week_label(item_date),
                "homework": [],
                "practice": [],
                "ensemble": [],
            },
        )
        report["homework"].append(item)

    for item in _load_practice_items():
        item_date = parse_item_date(item.get("createdAt"))
        if item_date is None:
            continue

        week_key = get_week_key(item_date)
        report = reports.setdefault(
            week_key,
            {
                "weekKey": week_key,
                "weekLabel": get_week_label(item_date),
                "homework": [],
                "practice": [],
                "ensemble": [],
            },
        )
        collection = "ensemble" if item.get("collection") == "ensemble" else "practice"
        report[collection].append(item)

    for report in reports.values():
        report["homework"].sort(key=lambda item: str(item.get("createdAt") or ""), reverse=True)
        report["practice"].sort(key=lambda item: str(item.get("createdAt") or ""), reverse=True)
        report["ensemble"].sort(key=lambda item: str(item.get("createdAt") or ""), reverse=True)

    return reports


def _build_report_for_week(target_date=None):
    week_key = get_week_key(target_date)
    report = {
        "weekKey": week_key,
        "weekLabel": get_week_label(target_date),
        "homework": _load_weekly_goals(target_date),
        "practice": [],
        "ensemble": [],
    }

    for item in _load_practice_items(target_date):
        collection = "ensemble" if item.get("collection") == "ensemble" else "practice"
        report[collection].append(item)

    return report


def _build_insights():
    insights = {category: [] for category in INSIGHT_CATEGORIES}

    for item in _load_insights_rows():
        category = item.get("category") or "rhythm"
        if category not in insights:
            continue

        decoded = _parse_insight_content(item.get("content"))
        insights[category].append(
            {
                "id": item.get("id") or uuid4().hex,
                "title": decoded["title"],
                "memo": decoded["memo"],
                "createdAt": item.get("createdAt") or now_iso(),
                "updatedAt": item.get("createdAt") or now_iso(),
            }
        )

    return insights


def get_current_report():
    return _build_report_for_week(get_today())


def get_all_reports(reports=None):
    if reports is None:
        reports = _build_reports()
    return sorted(reports.values(), key=lambda item: item["weekKey"], reverse=True)


def get_insights():
    return _build_insights()


def get_tune_suggestions(reports=None):
    if reports is None:
        rows = _query_user_row(
            """
            SELECT row_to_json(t)
            FROM (
                SELECT DISTINCT title
                FROM practice_item
                WHERE user_id = :'user_id'::uuid
                  AND COALESCE(title, '') <> ''
                ORDER BY title
            ) AS t
            """
        )
        return [
            str(row.get("title") or "").strip()
            for row in rows
            if str(row.get("title") or "").strip()
        ]

    suggestions = []
    seen = set()

    for report in reports:
        for collection_name in ["practice", "ensemble"]:
            for item in report.get(collection_name, []):
                title = str(item.get("title") or "").strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                suggestions.append(title)

    return suggestions


def get_first_activity_date():
    row = _query_user_row(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT MIN(created_date)::text AS "createdDate"
            FROM (
                SELECT (created_at AT TIME ZONE :'time_zone')::date AS created_date
                FROM weekly_goal
                WHERE user_id = :'user_id'::uuid
                UNION ALL
                SELECT (created_at AT TIME ZONE :'time_zone')::date AS created_date
                FROM practice_item
                WHERE user_id = :'user_id'::uuid
            ) AS combined
        ) AS t
        """,
        {"time_zone": get_app_timezone().key},
    )

    created_date = parse_item_date(row[0].get("createdDate")) if row else None
    return created_date or get_today()


def build_week_archive(report):
    week_start = date.fromisoformat(report["weekKey"])
    weekday_labels = app_settings_repository.get_weekday_labels()
    daily_buckets = []

    for offset in range(7):
        current_day = week_start + timedelta(days=offset)
        daily_buckets.append(
            {
                "date": current_day.isoformat(),
                "weekday": weekday_labels[offset],
                "label": f"{current_day.month}.{current_day.day}",
                "practice": [],
                "ensemble": [],
                "count": 0,
                "missingMetronome": False,
            }
        )

    bucket_by_date = {bucket["date"]: bucket for bucket in daily_buckets}

    for bucket_name in ["practice", "ensemble"]:
        for item in report.get(bucket_name, []):
            item_date = parse_item_date(item.get("createdAt"))
            if item_date is None:
                continue

            bucket = bucket_by_date.get(item_date.isoformat())
            if bucket is None:
                continue

            bucket[bucket_name].append(item)
            bucket["count"] += 1
            bucket["missingMetronome"] = (
                bucket["missingMetronome"]
                or not normalize_bool(item.get("metronome"))
            )

    for bucket in daily_buckets:
        bucket["isEmpty"] = bucket["count"] == 0
        bucket["isBad"] = bucket["count"] == 0 or bucket["missingMetronome"]

    return {
        "weekKey": report["weekKey"],
        "weekLabel": report["weekLabel"],
        "homework": report.get("homework", []),
        "practice": report.get("practice", []),
        "ensemble": report.get("ensemble", []),
        "dailyBuckets": daily_buckets,
        "practiceCount": len(report.get("practice", [])),
        "ensembleCount": len(report.get("ensemble", [])),
        "homeworkCount": len(report.get("homework", [])),
    }


def replace_current_report(data, report):
    return report


def add_homework(payload):
    user_id = get_or_create_user_id()
    status = normalize_status(payload.get("status"))
    completed_at = now_iso() if status == "GOOD" else None

    execute(
        """
        INSERT INTO weekly_goal (
            id,
            user_id,
            title,
            memo,
            status,
            completed_at,
            created_at,
            updated_at
        )
        VALUES (
            :'id'::uuid,
            :'user_id'::uuid,
            :'title',
            :'memo',
            :'status'::practice_status,
            NULLIF(:'completed_at', '')::timestamptz,
            now(),
            now()
        )
        """,
        {
            "id": uuid4().hex,
            "user_id": user_id,
            "title": str(payload.get("title") or DEFAULT_HOMEWORK_TITLE).strip()
            or DEFAULT_HOMEWORK_TITLE,
            "memo": str(payload.get("memo") or DEFAULT_HOMEWORK_MEMO).strip()
            or DEFAULT_HOMEWORK_MEMO,
            "status": status,
            "completed_at": completed_at or "",
        },
    )

    return get_current_report()


def update_homework(homework_id, payload):
    user_id = get_or_create_user_id()
    current = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM weekly_goal
            WHERE id = :'homework_id'::uuid
              AND user_id = :'user_id'::uuid
            LIMIT 1
        ) AS t
        """,
        {
            "homework_id": homework_id,
            "user_id": user_id,
        },
    )

    if not current:
        return get_current_report()

    status = normalize_status(payload.get("status"))

    execute(
        """
        UPDATE weekly_goal
        SET
            title = :'title',
            memo = :'memo',
            status = :'status'::practice_status,
            completed_at = NULLIF(:'completed_at', '')::timestamptz,
            updated_at = now()
        WHERE id = :'homework_id'::uuid
          AND user_id = :'user_id'::uuid
        """,
        {
            "homework_id": homework_id,
            "user_id": user_id,
            "title": str(payload.get("title") or DEFAULT_HOMEWORK_TITLE).strip()
            or DEFAULT_HOMEWORK_TITLE,
            "memo": str(payload.get("memo") or DEFAULT_HOMEWORK_MEMO).strip()
            or DEFAULT_HOMEWORK_MEMO,
            "status": status,
            "completed_at": now_iso() if status == "GOOD" else "",
        },
    )

    return get_current_report()


def merge_homework(source_id, target_id):
    if source_id == target_id:
        return get_current_report()

    current = get_current_report()
    source = None
    target = None

    for item in current.get("homework", []):
        if item.get("id") == source_id:
            source = item
        if item.get("id") == target_id:
            target = item

    if not source or not target:
        return current

    merged_lines = [
        str(target.get("memo", "")).strip(),
        str(source.get("memo", "")).strip(),
    ]
    updated_memo = "\n".join(line for line in merged_lines if line) or DEFAULT_HOMEWORK_MEMO

    execute(
        """
        UPDATE weekly_goal
        SET memo = :'memo',
            updated_at = now()
        WHERE id = :'target_id'::uuid
          AND user_id = :'user_id'::uuid
        """,
        {
            "target_id": target_id,
            "user_id": get_or_create_user_id(),
            "memo": updated_memo,
        },
    )

    delete_homework(source_id)
    return get_current_report()


def delete_homework(homework_id):
    execute(
        """
        DELETE FROM weekly_goal
        WHERE id = :'homework_id'::uuid
          AND user_id = :'user_id'::uuid
        """,
        {
            "homework_id": homework_id,
            "user_id": get_or_create_user_id(),
        },
    )
    return get_current_report()


def _upsert_practice_payload(payload, collection="practice", existing_id=None):
    user_id = get_or_create_user_id()
    item_id = existing_id or uuid4().hex
    title = str(payload.get("title") or DEFAULT_PRACTICE_TITLE).strip() or DEFAULT_PRACTICE_TITLE
    memo = str(payload.get("memo") or "").strip()
    bpm_text = str(payload.get("bpm") or "").strip()
    bpm = int(bpm_text) if bpm_text.isdigit() else None
    lick_file = payload.get("lickFile")
    renderer_file = payload.get("rendererFile")
    lick_id = _resolve_clip_id(lick_file)
    score_id = _resolve_score_id(renderer_file)
    status = normalize_status(payload.get("status"))
    topics = normalize_topics(payload.get("topics"))

    execute(
        """
        INSERT INTO practice_item (
            id,
            user_id,
            type,
            title,
            bpm,
            book,
            page,
            memo,
            spotify_url,
            metronome,
            status,
            created_at,
            updated_at,
            lick_id,
            score_id
        )
        VALUES (
            :'id'::uuid,
            :'user_id'::uuid,
            :'type'::practice_type,
            :'title',
            NULLIF(:'bpm', '')::int,
            :'book',
            :'page',
            :'memo',
            :'spotify_url',
            :'metronome'::boolean,
            :'status'::practice_status,
            now(),
            now(),
            NULLIF(:'lick_id', '')::uuid,
            NULLIF(:'score_id', '')::uuid
        )
        ON CONFLICT (id) DO UPDATE SET
            type = EXCLUDED.type,
            title = EXCLUDED.title,
            bpm = EXCLUDED.bpm,
            book = EXCLUDED.book,
            page = EXCLUDED.page,
            memo = EXCLUDED.memo,
            spotify_url = EXCLUDED.spotify_url,
            metronome = EXCLUDED.metronome,
            status = EXCLUDED.status,
            updated_at = now(),
            lick_id = EXCLUDED.lick_id,
            score_id = EXCLUDED.score_id
        """,
        {
            "id": item_id,
            "user_id": user_id,
            "type": normalize_collection(collection),
            "title": title,
            "bpm": bpm if bpm is not None else "",
            "book": str(payload.get("book") or "").strip(),
            "page": str(payload.get("page") or "").strip(),
            "memo": memo,
            "spotify_url": str(payload.get("spotifyUrl") or "").strip(),
            "metronome": "true" if bool(bpm_text) else "false",
            "status": status,
            "lick_id": lick_id or "",
            "score_id": score_id or "",
        },
    )

    _sync_practice_topics(item_id, topics)
    return get_current_report()


def add_practice(payload):
    return _upsert_practice_payload(payload, collection="practice")


def update_practice(practice_id, payload):
    return _upsert_practice_payload(payload, collection="practice", existing_id=practice_id)


def delete_practice(practice_id):
    execute(
        """
        DELETE FROM practice_item
        WHERE id = :'practice_id'::uuid
          AND user_id = :'user_id'::uuid
        """,
        {
            "practice_id": practice_id,
            "user_id": get_or_create_user_id(),
        },
    )
    return get_current_report()


def add_ensemble(payload):
    return _upsert_practice_payload(payload, collection="ensemble")


def update_ensemble(ensemble_id, payload):
    return _upsert_practice_payload(payload, collection="ensemble", existing_id=ensemble_id)


def delete_ensemble(ensemble_id):
    return delete_practice(ensemble_id)


def add_insight(payload):
    user_id = get_or_create_user_id()
    category = str(payload.get("category") or "rhythm").strip().lower()
    if category not in INSIGHT_CATEGORIES:
        category = "rhythm"

    execute(
        """
        INSERT INTO insight (id, user_id, category, content, created_at)
        VALUES (
            :'id'::uuid,
            :'user_id'::uuid,
            :'category'::insight_category,
            :'content',
            now()
        )
        """,
        {
            "id": uuid4().hex,
            "user_id": user_id,
            "category": category.upper(),
            "content": _compose_insight_content(payload.get("title"), payload.get("memo")),
        },
    )

    return get_insights()


def update_insight(category, insight_id, payload):
    category = str(category or "").strip().lower()
    if category not in INSIGHT_CATEGORIES:
        return get_insights()

    execute(
        """
        UPDATE insight
        SET content = :'content',
            created_at = created_at
        WHERE id = :'insight_id'::uuid
          AND user_id = :'user_id'::uuid
          AND category = :'category'::insight_category
        """,
        {
            "insight_id": insight_id,
            "user_id": get_or_create_user_id(),
            "category": category.upper(),
            "content": _compose_insight_content(payload.get("title"), payload.get("memo")),
        },
    )

    return get_insights()


def delete_insight(category, insight_id):
    category = str(category or "").strip().lower()
    if category not in INSIGHT_CATEGORIES:
        return get_insights()

    execute(
        """
        DELETE FROM insight
        WHERE id = :'insight_id'::uuid
          AND user_id = :'user_id'::uuid
          AND category = :'category'::insight_category
        """,
        {
            "insight_id": insight_id,
            "user_id": get_or_create_user_id(),
            "category": category.upper(),
        },
    )
    return get_insights()


def build_calendar_summary(days=140):
    today = get_today()
    first_activity_date = get_first_activity_date()
    start = first_activity_date
    all_reports = get_all_reports()
    week_start_day = get_week_start_day()
    summary = {}

    for offset in range((today - start).days + 1):
        current_day = start + timedelta(days=offset)
        day_key = current_day.isoformat()
        summary[day_key] = {
            "date": day_key,
            "count": 0,
            "missingMetronome": False,
            "level": 0,
            "soloCount": 0,
            "ensembleCount": 0,
            "weekdayIndex": (current_day.weekday() - week_start_day) % 7,
            "weekKey": get_week_key(current_day),
        }

    for report in all_reports:
        for bucket_name in ["practice", "ensemble"]:
            for item in report.get(bucket_name, []):
                item_date = parse_item_date(item.get("createdAt"))
                if item_date is None:
                    continue

                day_key = item_date.isoformat()

                if day_key not in summary:
                    continue

                summary[day_key]["count"] += 1
                summary[day_key]["missingMetronome"] = (
                    summary[day_key]["missingMetronome"]
                    or not normalize_bool(item.get("metronome"))
                )

                if bucket_name == "practice":
                    summary[day_key]["soloCount"] += 1
                else:
                    summary[day_key]["ensembleCount"] += 1

    for item in summary.values():
        if item["count"] == 0 or item["missingMetronome"]:
            item["level"] = -1
            continue

        if item["count"] >= 5:
            item["level"] = 4
        elif item["count"] >= 3:
            item["level"] = 3
        elif item["count"] >= 2:
            item["level"] = 2
        else:
            item["level"] = 1

    return {
        "days": list(summary.values()),
        "startDate": start.isoformat(),
        "endDate": today.isoformat(),
        "weeks": [
            build_week_archive(report)
            for report in sorted(all_reports, key=lambda item: item["weekKey"], reverse=True)
        ],
    }
