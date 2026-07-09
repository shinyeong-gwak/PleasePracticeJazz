import re
from uuid import uuid4

from repositories.db import (
    execute,
    get_or_create_user_id,
    query_one,
    query_rows,
)

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


def _load_lick_files_from_db():
    return query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT DISTINCT ON (file_name)
                file_name AS "fileName",
                sort_key AS "sortKey"
            FROM (
                SELECT
                    COALESCE(c.file_name, l.name) AS file_name,
                    COALESCE(l.updated_at, l.created_at, c.updated_at, c.created_at) AS sort_key
                FROM lick l
                LEFT JOIN clip c ON c.id = l.clip_id
                WHERE l.user_id = :'user_id'::uuid
                  AND COALESCE(c.file_name, l.name, '') <> ''

                UNION ALL

                SELECT
                    c.file_name,
                    COALESCE(c.updated_at, c.created_at) AS sort_key
                FROM clip c
                WHERE c.user_id = :'user_id'::uuid
                  AND COALESCE(c.file_name, '') <> ''
            ) AS combined
            ORDER BY file_name, sort_key DESC
        ) AS t
        ORDER BY "sortKey" DESC, "fileName"
        """,
        {"user_id": get_or_create_user_id()},
    )


def get_all():
    rows = _load_lick_files_from_db()
    if rows:
        return [
            row["fileName"]
            for row in rows
            if str(row.get("fileName") or "").strip()
        ]

    return []


def get_recent_files(limit=10):
    rows = _load_lick_files_from_db()
    if rows:
        return [
            row["fileName"]
            for row in rows[:limit]
            if str(row.get("fileName") or "").strip()
        ]

    return []


def _resolve_clip_id(file_name):
    file_name = str(file_name or "").strip()
    if not file_name:
        return None

    user_id = get_or_create_user_id()
    row = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM clip
            WHERE user_id = :'user_id'::uuid
              AND file_name = :'file_name'
            ORDER BY created_at DESC
            LIMIT 1
        ) AS t
        """,
        {
            "user_id": user_id,
            "file_name": file_name,
        },
    )
    return row["id"] if row else None


def load_metadata():
    user_id = get_or_create_user_id()
    rows = query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                COALESCE(c.file_name, l.name) AS file,
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
            LEFT JOIN clip c ON c.id = l.clip_id
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
            clip_id,
            name,
            key,
            time_signature,
            chords,
            degrees,
            melody,
            melody_rhythm,
            voicing,
            voicing_rhythm,
            created_at,
            updated_at
        )
        VALUES (
            :'id'::uuid,
            :'user_id'::uuid,
            NULLIF(:'clip_id', '')::uuid,
            :'name',
            :'key',
            :'time_signature',
            :'chords',
            :'degrees',
            :'melody',
            :'melody_rhythm',
            :'voicing',
            :'voicing_rhythm',
            now(),
            now()
        )
        ON CONFLICT (id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            clip_id = EXCLUDED.clip_id,
            name = EXCLUDED.name,
            key = EXCLUDED.key,
            time_signature = EXCLUDED.time_signature,
            chords = EXCLUDED.chords,
            degrees = EXCLUDED.degrees,
            melody = EXCLUDED.melody,
            melody_rhythm = EXCLUDED.melody_rhythm,
            voicing = EXCLUDED.voicing,
            voicing_rhythm = EXCLUDED.voicing_rhythm,
            updated_at = now()
        """,
        {
            "id": lick_id,
            "user_id": user_id,
            "clip_id": _resolve_clip_id(file_name) or "",
            "name": payload.get("name") or file_name,
            "key": payload.get("key") or "",
            "time_signature": payload.get("time") or "",
            "chords": payload.get("chords") or "",
            "degrees": payload.get("degrees") or "",
            "melody": payload.get("melody") or "",
            "melody_rhythm": payload.get("melodyRhythm") or "",
            "voicing": payload.get("voicing") or "",
            "voicing_rhythm": payload.get("voicingRhythm") or "",
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
