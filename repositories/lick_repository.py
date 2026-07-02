from pathlib import Path
import re
from uuid import uuid4

from repositories.db import (
    execute,
    get_or_create_user_id,
    query_one,
    query_rows,
)


METADATA_PLAYLIST_NAME = "__licks__"
METADATA_PLAYLIST_URL = "internal://licks"
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


def _ensure_metadata_playlist():
    user_id = get_or_create_user_id()
    playlist = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM playlist
            WHERE user_id = :'user_id'::uuid
              AND name = :'name'
            LIMIT 1
        ) AS t
        """,
        {"user_id": user_id, "name": METADATA_PLAYLIST_NAME},
    )

    if playlist:
        return playlist["id"]

    created = query_one(
        """
        WITH inserted AS (
            INSERT INTO playlist (user_id, name, source_url)
            VALUES (
                :'user_id'::uuid,
                :'name',
                :'url'
            )
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "user_id": user_id,
            "name": METADATA_PLAYLIST_NAME,
            "url": METADATA_PLAYLIST_URL,
        },
    )

    return created["id"] if created else None


def _ensure_playlist_item(playlist_id, file_name):
    item = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM playlist_item
            WHERE playlist_id = :'playlist_id'::uuid
              AND file_name = :'file_name'
            LIMIT 1
        ) AS t
        """,
        {
            "playlist_id": playlist_id,
            "file_name": file_name,
        },
    )

    if item:
        return item["id"]

    created = query_one(
        """
        WITH inserted AS (
            INSERT INTO playlist_item (
                playlist_id,
                file_name,
                file_path,
                source_url,
                title,
                downloaded_at
            )
            VALUES (
                :'playlist_id'::uuid,
                :'file_name',
                :'file_path',
                :'source_url',
                :'title',
                now()
            )
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "playlist_id": playlist_id,
            "file_name": file_name,
            "file_path": str(METADATA_DIR / file_name),
            "source_url": f"{METADATA_PLAYLIST_URL}/{file_name}",
            "title": file_name,
        },
    )

    return created["id"] if created else None


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
                COALESCE(pi.file_name, c.file_name) AS file,
                c.id::text AS id,
                c.name,
                c.key,
                c.time_signature AS time,
                c.chords,
                c.degrees,
                c.melody,
                c.melody_rhythm AS "melodyRhythm",
                c.voicing,
                c.voicing_rhythm AS "voicingRhythm"
            FROM clip c
            JOIN playlist_item pi ON pi.id = c.playlist_item_id
            JOIN playlist p ON p.id = pi.playlist_id
            WHERE p.user_id = :'user_id'::uuid
              AND p.name = :'playlist_name'
            ORDER BY c.created_at, c.id
        ) AS t
        """,
        {
            "user_id": user_id,
            "playlist_name": METADATA_PLAYLIST_NAME,
        },
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
    playlist_id = _ensure_metadata_playlist()
    playlist_item_id = _ensure_playlist_item(playlist_id, file_name)

    payload = dict(data)
    payload, _ = normalize_lick_item(payload)

    lick_id = payload.get("id") or uuid4().hex

    execute(
        """
        INSERT INTO clip (
            id,
            user_id,
            playlist_item_id,
            name,
            key,
            time_signature,
            chords,
            degrees,
            melody,
            melody_rhythm,
            voicing,
            voicing_rhythm,
            file_name,
            file_path,
            created_at,
            updated_at
        )
        VALUES (
            :'id'::uuid,
            :'user_id'::uuid,
            :'playlist_item_id'::uuid,
            :'name',
            :'key',
            :'time_signature',
            :'chords',
            :'degrees',
            :'melody',
            :'melody_rhythm',
            :'voicing',
            :'voicing_rhythm',
            :'file_name',
            :'file_path',
            now(),
            now()
        )
        ON CONFLICT (id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            playlist_item_id = EXCLUDED.playlist_item_id,
            name = EXCLUDED.name,
            key = EXCLUDED.key,
            time_signature = EXCLUDED.time_signature,
            chords = EXCLUDED.chords,
            degrees = EXCLUDED.degrees,
            melody = EXCLUDED.melody,
            melody_rhythm = EXCLUDED.melody_rhythm,
            voicing = EXCLUDED.voicing,
            voicing_rhythm = EXCLUDED.voicing_rhythm,
            file_name = EXCLUDED.file_name,
            file_path = EXCLUDED.file_path,
            updated_at = now()
        """,
        {
            "id": lick_id,
            "user_id": user_id,
            "playlist_item_id": playlist_item_id,
            "name": payload.get("name") or "",
            "key": payload.get("key") or "",
            "time_signature": payload.get("time") or "",
            "chords": payload.get("chords") or "",
            "degrees": payload.get("degrees") or "",
            "melody": payload.get("melody") or "",
            "melody_rhythm": payload.get("melodyRhythm") or "",
            "voicing": payload.get("voicing") or "",
            "voicing_rhythm": payload.get("voicingRhythm") or "",
            "file_name": file_name,
            "file_path": str(METADATA_DIR / file_name),
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
        DELETE FROM clip
        WHERE file_name = :'file_name'
          AND id = :'id'::uuid
        """,
        {
            "file_name": mp3,
            "id": lick_id,
        },
    )

    return {"success": True}
