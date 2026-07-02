from repositories.db import execute, get_or_create_user_id, query_rows


def add_log(playlist_name: str, url: str, status: str, message: str):
    user_id = get_or_create_user_id()

    execute(
        """
        UPDATE playlist
        SET source_url = COALESCE(NULLIF(:'url', ''), source_url),
            updated_at = now(),
            last_sync_at = now()
        WHERE user_id = :'user_id'::uuid
          AND name = :'playlist_name'
        """,
        {
            "user_id": user_id,
            "playlist_name": playlist_name,
            "url": url,
        },
    )


def get_all():
    user_id = get_or_create_user_id()
    return query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                p.updated_at AS "time",
                p.name AS "playlistName",
                p.source_url AS url,
                CASE
                    WHEN p.last_sync_at IS NULL THEN 'UNKNOWN'
                    ELSE 'SUCCESS'
                END AS status,
                COALESCE(p.source_url, '') AS message
            FROM playlist p
            WHERE p.user_id = :'user_id'::uuid
            ORDER BY p.updated_at DESC
        ) AS t
        """,
        {"user_id": user_id},
    )
