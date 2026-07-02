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
        {
            "user_id": user_id,
            "name": playlist_name,
        },
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
                            'id', pi.youtube_video_id,
                            'title', COALESCE(pi.title, pi.file_name),
                            'artist', '',
                            'url', pi.source_url,
                            'filename', pi.file_name
                        )
                    ) FILTER (WHERE pi.id IS NOT NULL),
                    '[]'::json
                ) AS items
            FROM playlist p
            LEFT JOIN playlist_item pi
                ON pi.playlist_id = p.id
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
        DELETE FROM playlist_item
        WHERE playlist_id = :'playlist_id'::uuid
        """,
        {"playlist_id": playlist_id},
    )

    for item in playlist_state.get("items", []):
        execute(
            """
            INSERT INTO playlist_item (
                playlist_id,
                file_name,
                file_path,
                source_url,
                title,
                youtube_video_id,
                downloaded_at
            )
            VALUES (
                :'playlist_id'::uuid,
                :'file_name',
                :'file_path',
                :'source_url',
                :'title',
                :'youtube_video_id',
                now()
            )
            """,
            {
                "playlist_id": playlist_id,
                "file_name": item.get("filename") or "",
                "file_path": str(item.get("filePath") or item.get("filename") or ""),
                "source_url": item.get("url") or "",
                "title": item.get("title") or "",
                "youtube_video_id": item.get("id") or "",
            },
        )


def iter_other_playlist_items(playlist_name):
    user_id = get_or_create_user_id()
    rows = query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT pi.file_name AS filename
            FROM playlist p
            JOIN playlist_item pi ON pi.playlist_id = p.id
            WHERE p.user_id = :'user_id'::uuid
              AND LEFT(p.name, 2) <> '__'
              AND p.name <> :'playlist_name'
        ) AS t
        """,
        {
            "user_id": user_id,
            "playlist_name": playlist_name,
        },
    )

    for row in rows:
        yield row
