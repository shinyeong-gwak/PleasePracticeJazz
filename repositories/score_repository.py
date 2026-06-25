from pathlib import Path


SCORES_DIR = Path("downloads/scores")


def get_recent_files(limit=10):

    if not SCORES_DIR.exists():
        return []

    files = sorted(
        SCORES_DIR.glob("*.musicxml"),
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )

    return [
        file.name
        for file in files[:limit]
    ]
