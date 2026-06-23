from pathlib import Path
import json
from uuid import uuid4

METADATA_FILE = Path(
    "data/music/lick_metadata.json"
)

LICKS_DIR = Path("downloads/licks")


def normalize_metadata(metadata):

    changed = False

    for mp3, items in metadata.items():
        for item in items:
            if not item.get("id"):
                item["id"] = uuid4().hex
                changed = True

            if not item.get("file"):
                item["file"] = mp3
                changed = True

    return metadata, changed


def load_metadata():

    if METADATA_FILE.exists():
        metadata = json.loads(
            METADATA_FILE.read_text(
                encoding="utf-8"
            )
        )
    else:
        metadata = {}

    metadata, changed = normalize_metadata(metadata)

    if changed:
        METADATA_FILE.write_text(
            json.dumps(
                metadata,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    return metadata


def get_all():

    if not LICKS_DIR.exists():
        return []

    return sorted([
        file.name
        for file in LICKS_DIR.glob("*.mp3")
    ])

def save(data):
    metadata = load_metadata()

    mp3 = data["file"]

    if not mp3:
        return {"success": False}

    metadata.setdefault(mp3, [])
    lick_id = data.get("id")

    payload = dict(data)

    if not lick_id:
        payload["id"] = uuid4().hex
        metadata[mp3].append(payload)
    else:
        updated = False

        for index, item in enumerate(metadata[mp3]):
            if item.get("id") == lick_id:
                metadata[mp3][index] = payload
                updated = True
                break

        if not updated:
            metadata[mp3].append(payload)

    METADATA_FILE.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return {
        "success": True,
        "id": payload["id"]
    }

def get_metadata():
    return load_metadata()


def delete(mp3, lick_id):

    if not METADATA_FILE.exists():
        return {"success": False}

    metadata = load_metadata()

    if mp3 not in metadata:
        return {"success": False}

    metadata[mp3] = [
        item
        for item in metadata[mp3]
        if item.get("id") != lick_id
    ]

    if not metadata[mp3]:
        metadata.pop(mp3)

    METADATA_FILE.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return {"success": True}
