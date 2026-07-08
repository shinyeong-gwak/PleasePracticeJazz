from repositories.db import execute, get_or_create_user_id, query_one, query_rows


def _get_playlist_row(playlist_name):
    user_id = get_or_create_user_id()
    return query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id, name, source_url AS url
            FROM playlist
            WHERE user_id = :'user_id'::uuid
              AND name = :'name'
            ORDER BY created_at DESC
            LIMIT 1
        ) AS t
        """,
        {"user_id": user_id, "name": playlist_name},
    )


def _ensure_playlist(playlist_name, url):
    user_id = get_or_create_user_id()
    playlist = _get_playlist_row(playlist_name)

    if playlist:
        execute(
            """
            UPDATE playlist
            SET source_url = :'url',
                updated_at = now(),
                last_sync_at = now()
            WHERE id = :'playlist_id'::uuid
              AND user_id = :'user_id'::uuid
            """,
            {
                "url": url,
                "playlist_id": playlist["id"],
                "user_id": user_id,
            },
        )
        return playlist["id"]

    created = query_one(
        """
        WITH inserted AS (
            INSERT INTO playlist (user_id, name, source_url, last_sync_at)
            VALUES (
                :'user_id'::uuid,
                :'name',
                :'url',
                now()
            )
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "user_id": user_id,
            "name": playlist_name,
            "url": url,
        },
    )

    return created["id"] if created else None


def _upsert_audio_track(item):
    file_name = item.get("filename") or ""
    file_path = str(item.get("filePath") or f"downloads/mp3/{file_name}")

    row = query_one(
        """
        WITH inserted AS (
            INSERT INTO audio_track (
                file_name,
                file_path,
                source_type,
                source_url,
                duration_sec
            )
            VALUES (
                :'file_name',
                :'file_path',
                :'source_type',
                :'source_url',
                NULLIF(:'duration_sec', '')::int
            )
            ON CONFLICT (file_path) DO UPDATE SET
                file_name = EXCLUDED.file_name,
                source_type = EXCLUDED.source_type,
                source_url = EXCLUDED.source_url,
                duration_sec = EXCLUDED.duration_sec,
                updated_at = now()
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "file_name": file_name,
            "file_path": file_path,
            "source_type": "youtube" if item.get("url") else "local",
            "source_url": item.get("url") or "",
            "duration_sec": item.get("durationSec") or "",
        },
    )
    return row["id"] if row else None


def get_all():
    user_id = get_or_create_user_id()
    playlists = query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                p.name,
                p.source_url AS url,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', at.id::text,
                            'title', COALESCE(at.file_name, at.file_path),
                            'artist', '',
                            'url', COALESCE(at.source_url, ''),
                            'filename', at.file_name,
                            'filePath', at.file_path
                        )
                        ORDER BY pt.position, at.created_at, at.id
                    ) FILTER (WHERE at.id IS NOT NULL),
                    '[]'::json
                ) AS items
            FROM playlist p
            LEFT JOIN playlist_track pt
                ON pt.playlist_id = p.id
            LEFT JOIN audio_track at
                ON at.id = pt.track_id
            WHERE p.user_id = :'user_id'::uuid
              AND LEFT(p.name, 2) <> '__'
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ) AS t
        """,
        {"user_id": user_id},
    )

    return {
        playlist["name"]: {
            "url": playlist["url"],
            "source": "youtube",
            "items": playlist["items"] or [],
        }
        for playlist in playlists
    }


def save_all(state):
    for playlist_name, playlist_state in (state or {}).items():
        save_playlist_state(playlist_name, playlist_state)


def get_playlist_state(playlist_name):
    return get_all().get(playlist_name, {})


def save_playlist_state(playlist_name, playlist_state):
    url = playlist_state.get("url") or ""
    playlist_id = _ensure_playlist(playlist_name, url)

    execute(
        """
        DELETE FROM playlist_track
        WHERE playlist_id = :'playlist_id'::uuid
        """,
        {"playlist_id": playlist_id},
    )

    for index, item in enumerate(playlist_state.get("items", []), start=1):
        track_id = _upsert_audio_track(item)
        if not track_id:
            continue

        execute(
            """
            INSERT INTO playlist_track (
                playlist_id,
                track_id,
                position
            )
            VALUES (
                :'playlist_id'::uuid,
                :'track_id'::uuid,
                :'position'::int
            )
            ON CONFLICT (playlist_id, track_id) DO UPDATE SET
                position = EXCLUDED.position
            """,
            {
                "playlist_id": playlist_id,
                "track_id": track_id,
                "position": index,
            },
        )


def iter_other_playlist_tracks(playlist_name):
    rows = query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT at.file_name AS filename
            FROM playlist p
            JOIN playlist_track pt ON pt.playlist_id = p.id
            JOIN audio_track at ON at.id = pt.track_id
            WHERE p.user_id = :'user_id'::uuid
              AND LEFT(p.name, 2) <> '__'
              AND p.name <> :'playlist_name'
        ) AS t
        """,
        {"playlist_name": playlist_name, "user_id": get_or_create_user_id()},
    )

    for row in rows:
        yield row
