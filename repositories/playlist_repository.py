from repositories.db import execute, query_rows


def get_all():
    return query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                name,
                source_url AS url
            FROM playlist
            WHERE LEFT(name, 2) <> '__'
            ORDER BY created_at DESC
        ) AS t
        """
    )


def save_all(playlists):
    execute(
        """
        DELETE FROM playlist
        WHERE LEFT(name, 2) <> '__'
        """
    )

    for playlist in playlists or []:
        add(playlist.get("name") or "", playlist.get("url") or "")


def add(name, url):
    execute(
        """
        INSERT INTO playlist (name, source_url)
        VALUES (
            :'name',
            :'url'
        )
        """,
        {
            "name": name,
            "url": url,
        },
    )


def delete(name, url):
    execute(
        """
        DELETE FROM playlist
        WHERE name = :'name'
          AND source_url = :'url'
        """,
        {
            "name": name,
            "url": url,
        },
    )
