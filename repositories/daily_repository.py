import json
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4


FILE_PATH = Path("data/music/daily_reports.json")


def ensure_file():

    FILE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not FILE_PATH.exists():
        FILE_PATH.write_text(
            json.dumps(
                {"weeks": {}},
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
            "practice": []
        }
    )

    report.setdefault("weekKey", week_key)
    report.setdefault("weekLabel", get_week_label())
    report.setdefault("homework", [])
    report.setdefault("practice", [])

    return report


def get_current_report():

    data = load_all()
    report = ensure_week_report(data)

    for item in report["practice"]:
        item.setdefault("status", "normal")

    save_all(data)
    return report


def add_homework(payload):

    data = load_all()
    report = ensure_week_report(data)

    item = {
        "id": uuid4().hex,
        "title": payload.get("title", "").strip() or "제목 없는 숙제",
        "memo": payload.get("memo", "").strip() or "메모 없음"
    }

    report["homework"].insert(0, item)
    save_all(data)

    return item


def delete_homework(homework_id):

    data = load_all()
    report = ensure_week_report(data)

    before = len(report["homework"])
    report["homework"] = [
        item
        for item in report["homework"]
        if item.get("id") != homework_id
    ]

    save_all(data)

    return {"success": len(report["homework"]) != before}


def add_practice(payload):

    data = load_all()
    report = ensure_week_report(data)

    topics = payload.get("topics") or []

    item = {
        "id": uuid4().hex,
        "title": payload.get("title", "").strip() or "이름 없는 연습",
        "bpm": str(payload.get("bpm", "")).strip(),
        "book": payload.get("book", "").strip(),
        "page": str(payload.get("page", "")).strip(),
        "status": payload.get("status", "normal").strip() or "normal",
        "topics": [
            str(topic).strip()
            for topic in topics
            if str(topic).strip()
        ],
        "memo": payload.get("memo", "").strip()
    }

    report["practice"].append(item)
    save_all(data)

    return item


def delete_practice(practice_id):

    data = load_all()
    report = ensure_week_report(data)

    before = len(report["practice"])
    report["practice"] = [
        item
        for item in report["practice"]
        if item.get("id") != practice_id
    ]

    save_all(data)

    return {"success": len(report["practice"]) != before}
