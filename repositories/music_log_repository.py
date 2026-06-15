import json
from pathlib import Path
from datetime import datetime

FILE_PATH = Path("data/music/sync_logs.json")


def add_log(
        playlist_name: str,
        url: str,
        status: str,
        message: str):

    logs = get_all()

    logs.append({
        "time": datetime.now().isoformat(),
        "playlistName": playlist_name,
        "url": url,
        "status": status,
        "message": message
    })

    save_all(logs)


def get_all():

    if not FILE_PATH.exists():
        return []

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_all(logs):

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            logs,
            f,
            ensure_ascii=False,
            indent=4
        )