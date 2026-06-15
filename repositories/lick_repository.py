from pathlib import Path

LICKS_DIR = Path("downloads/licks")


def get_all():

    if not LICKS_DIR.exists():
        return []

    return sorted([
        file.name
        for file in LICKS_DIR.glob("*.mp3")
    ])