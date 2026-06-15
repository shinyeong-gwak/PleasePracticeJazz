import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FILE_PATH = BASE_DIR / "data" / "music" / "playlists.json"


def get_all():

    if not FILE_PATH.exists():
        return []

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_all(playlists):

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            playlists,
            f,
            ensure_ascii=False,
            indent=4
        )


def add(name, url):

    playlists = get_all()

    playlists.append({
        "name": name,
        "url": url
    })

    save_all(playlists)