import json
from pathlib import Path

FILE_PATH = Path("data/music/playlist_sync_state.json")


def get_all():

    if not FILE_PATH.exists():
        return {}

    return json.loads(
        FILE_PATH.read_text(encoding="utf-8")
    )


def save_all(state):

    FILE_PATH.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def get_playlist_state(playlist_name):

    return get_all().get(playlist_name, {})


def save_playlist_state(playlist_name, playlist_state):

    state = get_all()
    state[playlist_name] = playlist_state
    save_all(state)


def iter_other_playlist_items(playlist_name):

    state = get_all()

    for name, playlist_state in state.items():
        if name == playlist_name:
            continue

        for item in playlist_state.get("items", []):
            yield item
