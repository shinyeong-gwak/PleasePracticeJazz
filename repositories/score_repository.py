from pathlib import Path

from repositories.db import get_or_create_user_id, query_rows


SCORES_DIR = Path("downloads/scores")


def get_recent_files(limit=10):
    rows = query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT DISTINCT ON (resolved_file_name)
                resolved_file_name AS "fileName",
                created_at AS "createdAt"
            FROM (
                SELECT
                    COALESCE(NULLIF(file_name, ''), NULLIF(original_file_name, ''), name) AS resolved_file_name,
                    created_at
                FROM score
                WHERE user_id = :'user_id'::uuid
                  AND COALESCE(NULLIF(file_name, ''), NULLIF(original_file_name, ''), name) <> ''
            ) AS scored
            ORDER BY resolved_file_name, created_at DESC
        ) AS t
        ORDER BY "createdAt" DESC, "fileName"
        LIMIT :'limit'::int
        """,
        {
            "user_id": get_or_create_user_id(),
            "limit": limit,
        },
    )

    if rows:
        return [
            row["fileName"]
            for row in rows
            if str(row.get("fileName") or "").strip()
        ]

    if not SCORES_DIR.exists():
        return []

    files = sorted(
        SCORES_DIR.glob("*.musicxml"),
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )

    return [
        file.name
        for file in files[:limit]
    ]
