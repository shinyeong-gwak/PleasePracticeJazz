from pathlib import Path
import json

METADATA_FILE = Path(
    "data/music/lick_metadata.json"
)

LICKS_DIR = Path("downloads/licks")


def get_all():

    if not LICKS_DIR.exists():
        return []

    return sorted([
        file.name
        for file in LICKS_DIR.glob("*.mp3")
    ])

def save(data):

    if METADATA_FILE.exists():

        metadata = json.loads(
            METADATA_FILE.read_text(
                encoding="utf-8"
            )
        )

    else:
        metadata = {}

    mp3 = data["file"]

    if not mp3:
        return {"success": False}

    metadata.setdefault(mp3, [])

    metadata[mp3].append(data)

    METADATA_FILE.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return {
        "success": True
    }

def get_metadata():

    if not METADATA_FILE.exists():
        return {}

    return json.loads(
        METADATA_FILE.read_text(
            encoding="utf-8"
        )
    )