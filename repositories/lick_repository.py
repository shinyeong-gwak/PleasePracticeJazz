from pathlib import Path
import json
import re
from uuid import uuid4

METADATA_FILE = Path(
    "data/music/lick_metadata.json"
)

LICKS_DIR = Path("downloads/licks")

NOTE_TOKEN_PATTERN = re.compile(r"[A-Ga-g][#bn]?\d")
RHYTHM_TOKEN_PATTERN = re.compile(r"(^|[\s|])!?(\d+)(~)?(?=[\s|]|$)")


def looks_like_rhythm(value):

    text = (value or "").strip()

    if not text:
        return False

    cleaned = text.replace("|", " ").strip()

    if not cleaned:
        return True

    tokens = cleaned.split()

    return all(
        token.startswith("*")
        or bool(RHYTHM_TOKEN_PATTERN.fullmatch(f" {token}"))
        for token in tokens
    )


def has_note_tokens(value):

    return bool(
        NOTE_TOKEN_PATTERN.search(
            (value or "").strip()
        )
    )


def normalize_lick_item(item):

    changed = False

    voicing = item.get("voicing", "") or ""
    voicing_rhythm = item.get("voicingRhythm", "") or ""

    if (
        not voicing_rhythm.strip()
        and looks_like_rhythm(voicing)
        and not has_note_tokens(voicing)
    ):
        item["voicingRhythm"] = voicing
        item["voicing"] = ""
        changed = True

    elif (
        has_note_tokens(voicing_rhythm)
        and looks_like_rhythm(voicing)
        and not has_note_tokens(voicing)
    ):
        item["voicing"] = voicing_rhythm
        item["voicingRhythm"] = voicing
        changed = True

    return item, changed


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

            _, item_changed = normalize_lick_item(item)
            changed = changed or item_changed

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
    payload, _ = normalize_lick_item(payload)

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
