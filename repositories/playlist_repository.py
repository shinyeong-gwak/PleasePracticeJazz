from repositories.db import execute, get_or_create_user_id, query_rows


def _infer_source(url):
    text = str(url or "").strip().lower()
    if "spotify" in text:
        return "spotify"
    if "youtube" in text or "youtu.be" in text:
        return "youtube"
    return "link"


def get_all():
    user_id = get_or_create_user_id()
    rows = query_rows(
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
                            'title', COALESCE(NULLIF(at.file_name, ''), at.file_path),
                            'artist', '',
                            'url', COALESCE(at.source_url, ''),
                            'filename', COALESCE(at.file_name, ''),
                            'filePath', COALESCE(at.file_path, '')
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
    for row in rows:
        row["source"] = _infer_source(row.get("url"))
        row["items"] = row.get("items") or []
    return rows


def save_all(playlists):
    user_id = get_or_create_user_id()
    execute(
        """
        WITH target_playlists AS (
            SELECT id
            FROM playlist
            WHERE user_id = :'user_id'::uuid
              AND LEFT(name, 2) <> '__'
        )
        DELETE FROM playlist_track
        WHERE playlist_id IN (SELECT id FROM target_playlists)
        """,
        {"user_id": user_id},
    )
    execute(
        """
        DELETE FROM playlist
        WHERE user_id = :'user_id'::uuid
          AND LEFT(name, 2) <> '__'
        """,
        {"user_id": user_id},
    )

    for playlist in playlists or []:
        add(playlist.get("name") or "", playlist.get("url") or "")


def add(name, url):
    user_id = get_or_create_user_id()
    execute(
        """
        INSERT INTO playlist (user_id, name, source_url)
        VALUES (
            :'user_id'::uuid,
            :'name',
            :'url'
        )
        """,
        {
            "user_id": user_id,
            "name": name,
            "url": url,
        },
    )


def delete(name, url):
    user_id = get_or_create_user_id()
    execute(
        """
        DELETE FROM playlist_track
        WHERE playlist_id IN (
            SELECT id
            FROM playlist
            WHERE user_id = :'user_id'::uuid
              AND name = :'name'
              AND source_url = :'url'
        )
        """,
        {
            "user_id": user_id,
            "name": name,
            "url": url,
        },
    )

    execute(
        """
        DELETE FROM playlist
        WHERE user_id = :'user_id'::uuid
          AND name = :'name'
          AND source_url = :'url'
        """,
        {
            "user_id": user_id,
            "name": name,
            "url": url,
        },
    )
