from pathlib import Path
import re
from uuid import uuid4

from repositories.db import (
    execute,
    get_or_create_user_id,
    query_rows,
)


METADATA_DIR = Path("downloads/licks")

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
    return bool(NOTE_TOKEN_PATTERN.search((value or "").strip()))


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


def get_all():
    if not METADATA_DIR.exists():
        return []

    return sorted([file.name for file in METADATA_DIR.glob("*.mp3")])


def get_recent_files(limit=10):
    if not METADATA_DIR.exists():
        return []

    files = sorted(
        METADATA_DIR.glob("*.mp3"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return [file.name for file in files[:limit]]


def load_metadata():
    user_id = get_or_create_user_id()
    rows = query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                COALESCE(l.source_file_name, l.name) AS file,
                l.id::text AS id,
                l.name,
                l.key,
                l.time_signature AS time,
                l.chords,
                l.degrees,
                l.melody,
                l.melody_rhythm AS "melodyRhythm",
                l.voicing,
                l.voicing_rhythm AS "voicingRhythm"
            FROM lick l
            WHERE l.user_id = :'user_id'::uuid
            ORDER BY l.created_at, l.id
        ) AS t
        """,
        {"user_id": user_id},
    )

    metadata = {}
    for row in rows:
        metadata.setdefault(row["file"], []).append(row)

    return metadata


def save(data):
    file_name = data.get("file")
    if not file_name:
        return {"success": False}

    user_id = get_or_create_user_id()
    payload = dict(data)
    payload, _ = normalize_lick_item(payload)
    lick_id = payload.get("id") or uuid4().hex

    execute(
        """
        INSERT INTO lick (
            id,
            user_id,
            name,
            key,
            time_signature,
            chords,
            degrees,
            melody,
            melody_rhythm,
            voicing,
            voicing_rhythm,
            source_file_name,
            source_file_path,
            created_at,
            updated_at
        )
        VALUES (
            :'id'::uuid,
            :'user_id'::uuid,
            :'name',
            :'key',
            :'time_signature',
            :'chords',
            :'degrees',
            :'melody',
            :'melody_rhythm',
            :'voicing',
            :'voicing_rhythm',
            :'source_file_name',
            :'source_file_path',
            now(),
            now()
        )
        ON CONFLICT (id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            name = EXCLUDED.name,
            key = EXCLUDED.key,
            time_signature = EXCLUDED.time_signature,
            chords = EXCLUDED.chords,
            degrees = EXCLUDED.degrees,
            melody = EXCLUDED.melody,
            melody_rhythm = EXCLUDED.melody_rhythm,
            voicing = EXCLUDED.voicing,
            voicing_rhythm = EXCLUDED.voicing_rhythm,
            source_file_name = EXCLUDED.source_file_name,
            source_file_path = EXCLUDED.source_file_path,
            updated_at = now()
        """,
        {
            "id": lick_id,
            "user_id": user_id,
            "name": payload.get("name") or file_name,
            "key": payload.get("key") or "",
            "time_signature": payload.get("time") or "",
            "chords": payload.get("chords") or "",
            "degrees": payload.get("degrees") or "",
            "melody": payload.get("melody") or "",
            "melody_rhythm": payload.get("melodyRhythm") or "",
            "voicing": payload.get("voicing") or "",
            "voicing_rhythm": payload.get("voicingRhythm") or "",
            "source_file_name": file_name,
            "source_file_path": str(METADATA_DIR / file_name),
        },
    )

    return {
        "success": True,
        "id": lick_id,
    }


def get_metadata():
    return load_metadata()


def delete(mp3, lick_id):
    execute(
        """
        DELETE FROM lick
        WHERE id = :'id'::uuid
          AND user_id = :'user_id'::uuid
        """,
        {
            "id": lick_id,
            "user_id": get_or_create_user_id(),
        },
    )

    return {"success": True}
