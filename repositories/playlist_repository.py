from repositories.db import execute, get_or_create_user_id, query_rows


def get_all():
    user_id = get_or_create_user_id()
    return query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                name,
                source_url AS url
            FROM playlist
            WHERE user_id = :'user_id'::uuid
              AND LEFT(name, 2) <> '__'
            ORDER BY created_at DESC
        ) AS t
        """,
        {"user_id": user_id},
    )


def save_all(playlists):
    user_id = get_or_create_user_id()

    execute(
        """
        DELETE FROM playlist
        WHERE user_id = :'user_id'::uuid
        """,
        {"user_id": user_id},
    )

    for playlist in playlists or []:
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
                "name": playlist.get("name") or "",
                "url": playlist.get("url") or "",
            },
        )


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
