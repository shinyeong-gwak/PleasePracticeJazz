from repositories.db import execute, query_one, query_rows


def _get_playlist_row(playlist_name):
    return query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id, name, source_url AS url
            FROM playlist
            WHERE name = :'name'
            ORDER BY created_at DESC
            LIMIT 1
        ) AS t
        """,
        {"name": playlist_name},
    )


def _ensure_playlist(playlist_name, url):
    playlist = _get_playlist_row(playlist_name)

    if playlist:
        execute(
            """
            UPDATE playlist
            SET source_url = :'url',
                updated_at = now(),
                last_sync_at = now()
            WHERE id = :'playlist_id'::uuid
            """,
            {
                "url": url,
                "playlist_id": playlist["id"],
            },
        )
        return playlist["id"]

    created = query_one(
        """
        WITH inserted AS (
            INSERT INTO playlist (name, source_url, last_sync_at)
            VALUES (
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
                title,
                source_type,
                source_url,
                youtube_video_id,
                duration_sec
            )
            VALUES (
                :'file_name',
                :'file_path',
                :'title',
                :'source_type',
                :'source_url',
                :'youtube_video_id',
                NULLIF(:'duration_sec', '')::int
            )
            ON CONFLICT (file_path) DO UPDATE SET
                file_name = EXCLUDED.file_name,
                title = EXCLUDED.title,
                source_type = EXCLUDED.source_type,
                source_url = EXCLUDED.source_url,
                youtube_video_id = EXCLUDED.youtube_video_id,
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
            "title": item.get("title") or file_name,
            "source_type": "youtube" if item.get("url") else "local",
            "source_url": item.get("url") or "",
            "youtube_video_id": item.get("id") or "",
            "duration_sec": item.get("durationSec") or "",
        },
    )
    return row["id"] if row else None


def get_all():
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
                            'id', at.youtube_video_id,
                            'title', COALESCE(at.title, at.file_name),
                            'artist', '',
                            'url', at.source_url,
                            'filename', at.file_name,
                            'filePath', at.file_path
                        )
                        ORDER BY pt.position, COALESCE(at.title, at.file_name)
                    ) FILTER (WHERE at.id IS NOT NULL),
                    '[]'::json
                ) AS items
            FROM playlist p
            LEFT JOIN playlist_track pt
                ON pt.playlist_id = p.id
            LEFT JOIN audio_track at
                ON at.id = pt.track_id
            WHERE LEFT(p.name, 2) <> '__'
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ) AS t
        """
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
            WHERE LEFT(p.name, 2) <> '__'
              AND p.name <> :'playlist_name'
        ) AS t
        """,
        {"playlist_name": playlist_name},
    )

    for row in rows:
        yield row
