import json
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4


FILE_PATH = Path("data/music/daily_reports.json")
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
WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]


def now_iso():

    return datetime.now().isoformat(timespec="seconds")


def ensure_file():

    FILE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not FILE_PATH.exists():
        FILE_PATH.write_text(
            json.dumps(
                {
                    "weeks": {},
                    "insights": {
                        category: []
                        for category in INSIGHT_CATEGORIES
                    }
                },
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )


def get_week_range(target_date=None):

    if target_date is None:
        target_date = date.today()

    start = target_date - timedelta(
        days=target_date.weekday()
    )
    end = start + timedelta(days=6)

    return start, end


def get_week_key(target_date=None):

    start, _ = get_week_range(target_date)
    return start.isoformat()


def get_week_label(target_date=None):

    start, end = get_week_range(target_date)
    return (
        f"{start.month}.{start.day} - "
        f"{end.month}.{end.day} Report"
    )


def parse_item_date(value):

    text = str(value or "").strip()

    if not text:
        return None

    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def load_all():

    ensure_file()

    return json.loads(
        FILE_PATH.read_text(
            encoding="utf-8"
        )
    )


def save_all(data):

    ensure_file()

    FILE_PATH.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


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


def normalize_homework_item(item):

    item.setdefault("id", uuid4().hex)
    item["title"] = str(
        item.get("title") or "제목 없는 숙제"
    ).strip() or "제목 없는 숙제"
    item["memo"] = str(
        item.get("memo") or "메모 없음"
    ).strip() or "메모 없음"
    item.setdefault("createdAt", now_iso())
    item.setdefault("updatedAt", item["createdAt"])
    return item


def normalize_practice_item(item):

    item.setdefault("id", uuid4().hex)
    item["title"] = str(
        item.get("title") or "이름 없는 연습"
    ).strip() or "이름 없는 연습"
    item["bpm"] = str(item.get("bpm") or "").strip()
    item["book"] = str(item.get("book") or "").strip()
    item["page"] = str(item.get("page") or "").strip()
    item["spotifyUrl"] = str(item.get("spotifyUrl") or "").strip()
    item["status"] = str(
        item.get("status") or "normal"
    ).strip() or "normal"
    item["topics"] = normalize_topics(
        item.get("topics")
    )
    item["memo"] = str(item.get("memo") or "").strip()
    item["metronome"] = bool(item["bpm"])
    item.setdefault("createdAt", now_iso())
    item.setdefault("updatedAt", item["createdAt"])
    return item


def normalize_ensemble_item(item):

    normalized = normalize_practice_item(item)
    normalized["title"] = str(
        item.get("title") or "이름 없는 합주 노트"
    ).strip() or "이름 없는 합주 노트"
    return normalized


def ensure_week_report(data, week_key=None):

    if week_key is None:
        week_key = get_week_key()

    weeks = data.setdefault("weeks", {})
    report = weeks.setdefault(
        week_key,
        {
            "weekKey": week_key,
            "weekLabel": get_week_label(),
            "homework": [],
            "practice": [],
            "ensemble": []
        }
    )

    report.setdefault("weekKey", week_key)
    report.setdefault("weekLabel", get_week_label())
    report.setdefault("homework", [])
    report.setdefault("practice", [])
    report.setdefault("ensemble", [])

    report["homework"] = [
        normalize_homework_item(item)
        for item in report["homework"]
    ]
    report["practice"] = [
        normalize_practice_item(item)
        for item in report["practice"]
    ]
    report["ensemble"] = [
        normalize_ensemble_item(item)
        for item in report["ensemble"]
    ]

    return report


def ensure_insights(data):

    insights = data.setdefault("insights", {})

    for category in INSIGHT_CATEGORIES:
        items = insights.setdefault(category, [])
        normalized = []

        for item in items:
            item.setdefault("id", uuid4().hex)
            item["title"] = str(
                item.get("title") or "제목 없는 인사이트"
            ).strip() or "제목 없는 인사이트"
            item["memo"] = str(
                item.get("memo") or ""
            ).strip()
            item.setdefault("createdAt", now_iso())
            item.setdefault("updatedAt", item["createdAt"])
            normalized.append(item)

        insights[category] = normalized

    return insights


def get_current_report():

    data = load_all()
    report = ensure_week_report(data)
    ensure_insights(data)
    save_all(data)
    return report


def get_all_reports():

    data = load_all()
    weeks = data.setdefault("weeks", {})

    normalized = []

    for week_key in sorted(weeks.keys()):
        normalized.append(
            ensure_week_report(
                data,
                week_key
            )
        )

    ensure_insights(data)
    save_all(data)
    return normalized


def get_insights():

    data = load_all()
    insights = ensure_insights(data)
    save_all(data)
    return insights


def get_tune_suggestions():

    data = load_all()
    weeks = data.setdefault("weeks", {})
    suggestions = []
    seen = set()

    for week_key in sorted(weeks.keys()):
        report = ensure_week_report(data, week_key)

        for collection_name in ["practice", "ensemble"]:
            for item in report.get(collection_name, []):
                title = str(item.get("title") or "").strip()

                if not title or title in seen:
                    continue

                seen.add(title)
                suggestions.append(title)

    save_all(data)
    return suggestions


def get_first_activity_date():

    data = load_all()
    weeks = data.setdefault("weeks", {})
    first_date = None

    for week_key in sorted(weeks.keys()):
        report = ensure_week_report(data, week_key)

        for collection_name in ["homework", "practice", "ensemble"]:
            for item in report.get(collection_name, []):
                created_date = parse_item_date(
                    item.get("createdAt")
                )

                if created_date is None:
                    continue

                if first_date is None or created_date < first_date:
                    first_date = created_date

    save_all(data)
    return first_date or date.today()


def build_week_archive(report):

    week_start = date.fromisoformat(report["weekKey"])
    daily_buckets = []

    for offset in range(7):
        current_day = week_start + timedelta(days=offset)
        daily_buckets.append(
            {
                "date": current_day.isoformat(),
                "weekday": WEEKDAY_LABELS[offset],
                "label": f"{current_day.month}.{current_day.day}",
                "practice": [],
                "ensemble": [],
                "count": 0,
                "missingMetronome": False,
            }
        )

    bucket_by_date = {
        bucket["date"]: bucket
        for bucket in daily_buckets
    }

    for bucket_name in ["practice", "ensemble"]:
        for item in report.get(bucket_name, []):
            item_date = parse_item_date(
                item.get("createdAt")
            )

            if item_date is None:
                continue

            bucket = bucket_by_date.get(
                item_date.isoformat()
            )

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
        bucket["isBad"] = (
            bucket["count"] == 0
            or bucket["missingMetronome"]
        )

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

    weeks = data.setdefault("weeks", {})
    weeks[report["weekKey"]] = report
    save_all(data)
    return report


def add_homework(payload):

    data = load_all()
    report = ensure_week_report(data)
    item = normalize_homework_item(
        {
            "id": uuid4().hex,
            "title": payload.get("title"),
            "memo": payload.get("memo"),
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        }
    )
    report["homework"].insert(0, item)
    replace_current_report(data, report)
    return report


def update_homework(homework_id, payload):

    data = load_all()
    report = ensure_week_report(data)

    for item in report["homework"]:
        if item.get("id") != homework_id:
            continue

        item["title"] = str(
            payload.get("title") or item.get("title")
        ).strip() or "제목 없는 숙제"
        item["memo"] = str(
            payload.get("memo") or item.get("memo")
        ).strip() or "메모 없음"
        item["updatedAt"] = now_iso()
        break

    replace_current_report(data, report)
    return report


def merge_homework(source_id, target_id):

    if source_id == target_id:
        return get_current_report()

    data = load_all()
    report = ensure_week_report(data)
    source = None
    target = None

    for item in report["homework"]:
        if item.get("id") == source_id:
            source = item
        if item.get("id") == target_id:
            target = item

    if not source or not target:
        return report

    merged_lines = [
        target.get("memo", "").strip(),
        source.get("memo", "").strip()
    ]
    target["memo"] = "\n".join(
        line
        for line in merged_lines
        if line
    ) or "메모 없음"
    target["updatedAt"] = now_iso()

    report["homework"] = [
        item
        for item in report["homework"]
        if item.get("id") != source_id
    ]

    replace_current_report(data, report)
    return report


def delete_homework(homework_id):

    data = load_all()
    report = ensure_week_report(data)
    report["homework"] = [
        item
        for item in report["homework"]
        if item.get("id") != homework_id
    ]
    replace_current_report(data, report)
    return report


def add_practice(payload):

    data = load_all()
    report = ensure_week_report(data)
    item = normalize_practice_item(
        {
            "id": uuid4().hex,
            "title": payload.get("title"),
            "bpm": payload.get("bpm"),
            "book": payload.get("book"),
            "page": payload.get("page"),
            "spotifyUrl": payload.get("spotifyUrl"),
            "status": payload.get("status"),
            "topics": payload.get("topics"),
            "memo": payload.get("memo"),
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        }
    )
    report["practice"].append(item)
    replace_current_report(data, report)
    return report


def update_practice(practice_id, payload):

    data = load_all()
    report = ensure_week_report(data)

    for item in report["practice"]:
        if item.get("id") != practice_id:
            continue

        item.update(
            normalize_practice_item(
                {
                    **item,
                    "title": payload.get("title", item.get("title")),
                    "bpm": payload.get("bpm", item.get("bpm")),
                    "book": payload.get("book", item.get("book")),
                    "page": payload.get("page", item.get("page")),
                    "spotifyUrl": payload.get("spotifyUrl", item.get("spotifyUrl")),
                    "status": payload.get("status", item.get("status")),
                    "topics": payload.get("topics", item.get("topics")),
                    "memo": payload.get("memo", item.get("memo")),
                    "updatedAt": now_iso()
                }
            )
        )
        break

    replace_current_report(data, report)
    return report


def delete_practice(practice_id):

    data = load_all()
    report = ensure_week_report(data)
    report["practice"] = [
        item
        for item in report["practice"]
        if item.get("id") != practice_id
    ]
    replace_current_report(data, report)
    return report


def add_ensemble(payload):

    data = load_all()
    report = ensure_week_report(data)
    item = normalize_ensemble_item(
        {
            "id": uuid4().hex,
            "title": payload.get("title"),
            "bpm": payload.get("bpm"),
            "book": payload.get("book"),
            "page": payload.get("page"),
            "spotifyUrl": payload.get("spotifyUrl"),
            "status": payload.get("status"),
            "topics": payload.get("topics"),
            "memo": payload.get("memo"),
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        }
    )
    report["ensemble"].insert(0, item)
    replace_current_report(data, report)
    return report


def update_ensemble(ensemble_id, payload):

    data = load_all()
    report = ensure_week_report(data)

    for item in report["ensemble"]:
        if item.get("id") != ensemble_id:
            continue

        item.update(
            normalize_ensemble_item(
                {
                    **item,
                    "title": payload.get("title", item.get("title")),
                    "bpm": payload.get("bpm", item.get("bpm")),
                    "book": payload.get("book", item.get("book")),
                    "page": payload.get("page", item.get("page")),
                    "spotifyUrl": payload.get("spotifyUrl", item.get("spotifyUrl")),
                    "status": payload.get("status", item.get("status")),
                    "topics": payload.get("topics", item.get("topics")),
                    "memo": payload.get("memo", item.get("memo")),
                    "updatedAt": now_iso()
                }
            )
        )
        break

    replace_current_report(data, report)
    return report


def delete_ensemble(ensemble_id):

    data = load_all()
    report = ensure_week_report(data)
    report["ensemble"] = [
        item
        for item in report["ensemble"]
        if item.get("id") != ensemble_id
    ]
    replace_current_report(data, report)
    return report


def add_insight(payload):

    data = load_all()
    insights = ensure_insights(data)
    category = payload.get("category", "rhythm")

    if category not in INSIGHT_CATEGORIES:
        category = "rhythm"

    item = {
        "id": uuid4().hex,
        "title": str(
            payload.get("title") or "제목 없는 인사이트"
        ).strip() or "제목 없는 인사이트",
        "memo": str(
            payload.get("memo") or ""
        ).strip(),
        "createdAt": now_iso(),
        "updatedAt": now_iso()
    }

    insights[category].insert(0, item)
    save_all(data)
    return insights


def update_insight(category, insight_id, payload):

    data = load_all()
    insights = ensure_insights(data)

    if category not in INSIGHT_CATEGORIES:
        return insights

    for item in insights[category]:
        if item.get("id") != insight_id:
            continue

        item["title"] = str(
            payload.get("title") or item.get("title")
        ).strip() or "제목 없는 인사이트"
        item["memo"] = str(
            payload.get("memo") or item.get("memo")
        ).strip()
        item["updatedAt"] = now_iso()
        break

    save_all(data)
    return insights


def delete_insight(category, insight_id):

    data = load_all()
    insights = ensure_insights(data)

    if category not in INSIGHT_CATEGORIES:
        return insights

    insights[category] = [
        item
        for item in insights[category]
        if item.get("id") != insight_id
    ]

    save_all(data)
    return insights


def build_calendar_summary(days=140):

    today = date.today()
    first_activity_date = get_first_activity_date()
    start = first_activity_date
    all_reports = get_all_reports()
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
            "weekdayIndex": current_day.weekday(),
            "weekKey": get_week_key(current_day),
        }

    for report in all_reports:
        for bucket_name in ["practice", "ensemble"]:
            for item in report.get(bucket_name, []):
                created = str(item.get("createdAt") or "")
                day_key = created[:10]

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
            for report in sorted(
                all_reports,
                key=lambda item: item["weekKey"],
                reverse=True
            )
        ],
        "bookOptions": BOOK_OPTIONS,
    }
