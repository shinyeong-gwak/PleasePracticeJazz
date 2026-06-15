from pathlib import Path

MP3_DIR = Path("downloads/mp3")


def get_mp3_files():

    if not MP3_DIR.exists():
        return []

    return sorted([
        file.name
        for file in MP3_DIR.glob("*.mp3")
    ])