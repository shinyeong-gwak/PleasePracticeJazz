from pathlib import Path

from repositories.db import execute, get_or_create_user_id, query_one, query_rows


ROOT_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = ROOT_DIR / "downloads"
MP3_DIR = DOWNLOADS_DIR / "mp3"


def _safe_relative_path(value):
    text = str(value or "").strip().replace("\\", "/")
    relative = Path(text)

    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Invalid path")

    return relative


def resolve_audio_path(value):
    relative = _safe_relative_path(value)
    text = relative.as_posix()

    if text.startswith("downloads/"):
        path = (ROOT_DIR / relative).resolve()
    else:
        path = (MP3_DIR / relative).resolve()

    downloads_base = DOWNLOADS_DIR.resolve()
    if path != downloads_base and downloads_base not in path.parents:
        raise ValueError("Invalid path")

    if path.suffix.lower() != ".mp3":
        raise ValueError("Invalid audio file")

    return path


def resolve_mp3_path(value):
    return resolve_audio_path(value)


def _relative_key(path):
    return path.resolve().relative_to(ROOT_DIR).as_posix()


def _display_name(file_name):
    path = Path(str(file_name or ""))
    return path.stem or path.name


def _load_pool_tracks():
    return query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                at.id::text AS id,
                at.file_name AS "fileName",
                at.file_path AS "filePath",
                regexp_replace(at.file_name, '\\.mp3$', '', 'i') AS "displayName",
                COALESCE(NULLIF(at.source_type, ''), 'local') AS "sourceType",
                COALESCE(at.source_url, '') AS "sourceUrl",
                at.duration_sec AS "durationSec"
            FROM audio_track at
            WHERE at.file_path LIKE 'downloads/mp3/%'
            ORDER BY at.file_name
        ) AS t
        """
    )


def _load_folders():
    user_id = get_or_create_user_id()
    return query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                id::text AS id,
                parent_id::text AS "parentId",
                name,
                sort_order AS "sortOrder"
            FROM audio_folder
            WHERE user_id = :'user_id'::uuid
            ORDER BY sort_order, name
        ) AS t
        """,
        {"user_id": user_id},
    )


def _load_library_items():
    user_id = get_or_create_user_id()
    return query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                li.id::text AS id,
                li.folder_id::text AS "folderId",
                li.track_id::text AS "trackId",
                COALESCE(NULLIF(li.display_name, ''), at.file_name) AS "displayName",
                li.sort_order AS "sortOrder",
                at.file_name AS "fileName",
                at.file_path AS "filePath",
                COALESCE(NULLIF(at.source_type, ''), 'local') AS "sourceType",
                COALESCE(at.source_url, '') AS "sourceUrl",
                at.duration_sec AS "durationSec"
            FROM audio_library_item li
            JOIN audio_track at ON at.id = li.track_id
            WHERE li.user_id = :'user_id'::uuid
            ORDER BY li.sort_order, COALESCE(NULLIF(li.display_name, ''), at.file_name)
        ) AS t
        """,
        {"user_id": user_id},
    )


def _folder_node(name, folder_id=None, parent_id=None):
    return {
        "type": "folder",
        "id": folder_id or "",
        "parentId": parent_id or "",
        "name": name,
        "children": [],
    }


def _track_node(item):
    return {
        "type": "file",
        "id": item.get("id") or "",
        "trackId": item.get("trackId") or item.get("id") or "",
        "folderId": item.get("folderId") or "",
        "name": item.get("displayName") or _display_name(item.get("fileName")),
        "fileName": item.get("fileName") or "",
        "path": item.get("filePath") or "",
        "sourceType": item.get("sourceType") or "local",
        "sourceUrl": item.get("sourceUrl") or "",
        "durationSec": item.get("durationSec"),
        "sortOrder": item.get("sortOrder") or 0,
    }


def _build_library_tree(folders, items):
    root = _folder_node("라이브러리")
    by_id = {"": root}

    for folder in folders:
        by_id[folder["id"]] = _folder_node(
            folder.get("name") or "Untitled",
            folder.get("id"),
            folder.get("parentId"),
        )

    for folder in folders:
        node = by_id[folder["id"]]
        parent = by_id.get(folder.get("parentId") or "", root)
        parent["children"].append(node)

    for item in items:
        parent = by_id.get(item.get("folderId") or "", root)
        parent["children"].append(_track_node(item))

    return root


def get_mp3_files():
    return [track["filePath"] for track in _load_pool_tracks()]


def get_mp3_tree():
    return {
        "library": _build_library_tree(_load_folders(), _load_library_items()),
        "pool": _load_pool_tracks(),
    }


def create_folder(parent_id, name):
    user_id = get_or_create_user_id()
    folder_name = str(name or "").strip()
    parent_id = str(parent_id or "").strip() or None

    if not folder_name:
        raise ValueError("폴더 이름을 입력해 주세요.")

    duplicated = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM audio_folder
            WHERE user_id = :'user_id'::uuid
              AND COALESCE(parent_id, '00000000-0000-0000-0000-000000000000'::uuid)
                  = COALESCE(NULLIF(:'parent_id', '')::uuid, '00000000-0000-0000-0000-000000000000'::uuid)
              AND name = :'name'
            LIMIT 1
        ) AS t
        """,
        {
            "user_id": user_id,
            "parent_id": parent_id or "",
            "name": folder_name,
        },
    )
    if duplicated:
        raise ValueError("같은 이름의 폴더가 이미 있어요.")

    created = query_one(
        """
        WITH inserted AS (
            INSERT INTO audio_folder (user_id, parent_id, name)
            VALUES (
                :'user_id'::uuid,
                NULLIF(:'parent_id', '')::uuid,
                :'name'
            )
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "user_id": user_id,
            "parent_id": parent_id or "",
            "name": folder_name,
        },
    )
    return created["id"] if created else None


def rename_folder(folder_id, name):
    user_id = get_or_create_user_id()
    folder_name = str(name or "").strip()

    if not folder_id:
        raise ValueError("폴더를 선택해 주세요.")

    if not folder_name:
        raise ValueError("새 폴더 이름을 입력해 주세요.")

    execute(
        """
        UPDATE audio_folder
        SET name = :'name',
            updated_at = now()
        WHERE id = :'folder_id'::uuid
          AND user_id = :'user_id'::uuid
        """,
        {
            "folder_id": folder_id,
            "user_id": user_id,
            "name": folder_name,
        },
    )


def delete_folder(folder_id):
    user_id = get_or_create_user_id()

    if not folder_id:
        raise ValueError("폴더를 선택해 주세요.")

    child = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM audio_folder
            WHERE user_id = :'user_id'::uuid
              AND parent_id = :'folder_id'::uuid
            LIMIT 1
        ) AS t
        """,
        {
            "user_id": user_id,
            "folder_id": folder_id,
        },
    )
    if child:
        raise ValueError("하위 폴더가 있는 폴더만 삭제할 수 있어요.")

    item = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM audio_library_item
            WHERE user_id = :'user_id'::uuid
              AND folder_id = :'folder_id'::uuid
            LIMIT 1
        ) AS t
        """,
        {
            "user_id": user_id,
            "folder_id": folder_id,
        },
    )
    if item:
        raise ValueError("비어 있는 폴더만 삭제할 수 있어요.")

    execute(
        """
        DELETE FROM audio_folder
        WHERE id = :'folder_id'::uuid
          AND user_id = :'user_id'::uuid
        """,
        {
            "folder_id": folder_id,
            "user_id": user_id,
        },
    )


def _next_library_sort(user_id, folder_id=None):
    row = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_sort
            FROM audio_library_item
            WHERE user_id = :'user_id'::uuid
              AND COALESCE(folder_id, '00000000-0000-0000-0000-000000000000'::uuid)
                  = COALESCE(NULLIF(:'folder_id', '')::uuid, '00000000-0000-0000-0000-000000000000'::uuid)
        ) AS t
        """,
        {
            "user_id": user_id,
            "folder_id": folder_id or "",
        },
    )
    return int(row["nextSort"]) if row else 0


def add_track_to_library(track_id, folder_id=None):
    user_id = get_or_create_user_id()
    folder_id = str(folder_id or "").strip() or None
    next_sort = _next_library_sort(user_id, folder_id)

    row = query_one(
        """
        WITH inserted AS (
            INSERT INTO audio_library_item (
                user_id,
                track_id,
                folder_id,
                display_name,
                sort_order
            )
            SELECT
                :'user_id'::uuid,
                at.id,
                NULLIF(:'folder_id', '')::uuid,
                regexp_replace(at.file_name, '\\.mp3$', '', 'i'),
                :'sort_order'::int
            FROM audio_track at
            WHERE at.id = :'track_id'::uuid
            ON CONFLICT (user_id, track_id) DO UPDATE SET
                folder_id = EXCLUDED.folder_id,
                display_name = EXCLUDED.display_name,
                sort_order = EXCLUDED.sort_order,
                updated_at = now()
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "user_id": user_id,
            "track_id": track_id,
            "folder_id": folder_id or "",
            "sort_order": next_sort,
        },
    )
    return row["id"] if row else None


def move_track_to_folder(track_id, folder_id=None):
    user_id = get_or_create_user_id()
    folder_id = str(folder_id or "").strip() or None
    next_sort = _next_library_sort(user_id, folder_id)

    row = query_one(
        """
        WITH updated AS (
            UPDATE audio_library_item
            SET folder_id = NULLIF(:'folder_id', '')::uuid,
                sort_order = :'sort_order'::int,
                updated_at = now()
            WHERE user_id = :'user_id'::uuid
              AND track_id = :'track_id'::uuid
            RETURNING id::text AS id
        )
        SELECT row_to_json(updated)
        FROM updated
        """,
        {
            "user_id": user_id,
            "track_id": track_id,
            "folder_id": folder_id or "",
            "sort_order": next_sort,
        },
    )
    return row["id"] if row else None


def reorder_track(track_id, direction):
    user_id = get_or_create_user_id()
    direction = str(direction or "").strip().lower()
    if direction not in {"up", "down"}:
        raise ValueError("Invalid direction")

    current = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                id::text AS id,
                COALESCE(folder_id::text, '') AS "folderId",
                sort_order AS "sortOrder"
            FROM audio_library_item
            WHERE user_id = :'user_id'::uuid
              AND track_id = :'track_id'::uuid
            LIMIT 1
        ) AS t
        """,
        {
            "user_id": user_id,
            "track_id": track_id,
        },
    )
    if not current:
        return None

    if direction == "up":
        target = query_one(
            """
            SELECT row_to_json(t)
            FROM (
                SELECT
                    id::text AS id,
                    sort_order AS "sortOrder"
                FROM audio_library_item
                WHERE user_id = :'user_id'::uuid
                  AND COALESCE(folder_id, '00000000-0000-0000-0000-000000000000'::uuid)
                      = COALESCE(NULLIF(:'folder_id', '')::uuid, '00000000-0000-0000-0000-000000000000'::uuid)
                  AND sort_order < :'sort_order'::int
                ORDER BY sort_order DESC, id
                LIMIT 1
            ) AS t
            """,
            {
                "user_id": user_id,
                "folder_id": current["folderId"],
                "sort_order": current["sortOrder"],
            },
        )
    else:
        target = query_one(
            """
            SELECT row_to_json(t)
            FROM (
                SELECT
                    id::text AS id,
                    sort_order AS "sortOrder"
                FROM audio_library_item
                WHERE user_id = :'user_id'::uuid
                  AND COALESCE(folder_id, '00000000-0000-0000-0000-000000000000'::uuid)
                      = COALESCE(NULLIF(:'folder_id', '')::uuid, '00000000-0000-0000-0000-000000000000'::uuid)
                  AND sort_order > :'sort_order'::int
                ORDER BY sort_order ASC, id
                LIMIT 1
            ) AS t
            """,
            {
                "user_id": user_id,
                "folder_id": current["folderId"],
                "sort_order": current["sortOrder"],
            },
        )

    if not target:
        return current["id"]

    execute(
        """
        UPDATE audio_library_item
        SET sort_order = CASE
                WHEN id = :'current_id'::uuid THEN :'target_sort'::int
                WHEN id = :'target_id'::uuid THEN :'current_sort'::int
            END,
            updated_at = now()
        WHERE id IN (:'current_id'::uuid, :'target_id'::uuid)
        """,
        {
            "current_id": current["id"],
            "target_id": target["id"],
            "current_sort": current["sortOrder"],
            "target_sort": target["sortOrder"],
        },
    )
    return current["id"]


def _resolve_audio_track_id(source_file):
    source_text = str(source_file or "").strip()
    if not source_text:
        return None

    source_path = resolve_audio_path(source_text)
    source_name = source_path.name
    source_relative = _relative_key(source_path)

    row = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM audio_track
            WHERE file_path = :'file_path'
               OR file_name = :'file_name'
            ORDER BY created_at DESC
            LIMIT 1
        ) AS t
        """,
        {
            "file_path": source_relative,
            "file_name": source_name,
        },
    )
    return row["id"] if row else None


def sync_created_audio_file(file_path, source_url=None):
    path = Path(file_path).resolve()
    downloads_base = DOWNLOADS_DIR.resolve()
    if path != downloads_base and downloads_base not in path.parents:
        raise ValueError("Invalid path")

    if path.suffix.lower() != ".mp3":
        raise ValueError("Invalid audio file")

    relative_path = _relative_key(path)
    row = query_one(
        """
        WITH inserted AS (
            INSERT INTO audio_track (
                file_name,
                file_path,
                source_type,
                source_url
            )
            VALUES (
                :'file_name',
                :'file_path',
                'generated',
                :'source_url'
            )
            ON CONFLICT (file_path) DO UPDATE SET
                file_name = EXCLUDED.file_name,
                updated_at = now()
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "file_name": path.name,
            "file_path": relative_path,
            "source_url": source_url or "",
        },
    )

    if row:
        add_track_to_library(row["id"])

    return row["id"] if row else None


def register_generated_clip(
    output_file,
    source_file,
    start_sec=None,
    end_sec=None,
    pitch_shift=0,
    tempo_ratio=1.0,
):
    output_path = Path(output_file).resolve()
    downloads_base = DOWNLOADS_DIR.resolve()
    if output_path != downloads_base and downloads_base not in output_path.parents:
        raise ValueError("Invalid path")

    if output_path.suffix.lower() != ".mp3":
        raise ValueError("Invalid audio file")

    source_track_id = _resolve_audio_track_id(source_file)
    if not source_track_id:
        raise ValueError("Source track not found")

    row = query_one(
        """
        WITH inserted AS (
            INSERT INTO clip (
                user_id,
                source_track_id,
                file_name,
                file_path,
                start_sec,
                end_sec,
                pitch_shift,
                tempo_ratio
            )
            VALUES (
                :'user_id'::uuid,
                :'source_track_id'::uuid,
                :'file_name',
                :'file_path',
                NULLIF(:'start_sec', '')::numeric(12, 3),
                NULLIF(:'end_sec', '')::numeric(12, 3),
                :'pitch_shift'::int,
                :'tempo_ratio'::numeric(8, 4)
            )
            ON CONFLICT (file_path) DO UPDATE SET
                source_track_id = EXCLUDED.source_track_id,
                file_name = EXCLUDED.file_name,
                start_sec = EXCLUDED.start_sec,
                end_sec = EXCLUDED.end_sec,
                pitch_shift = EXCLUDED.pitch_shift,
                tempo_ratio = EXCLUDED.tempo_ratio,
                updated_at = now()
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "user_id": get_or_create_user_id(),
            "source_track_id": source_track_id,
            "file_name": output_path.name,
            "file_path": _relative_key(output_path),
            "start_sec": "" if start_sec is None else start_sec,
            "end_sec": "" if end_sec is None else end_sec,
            "pitch_shift": pitch_shift,
            "tempo_ratio": tempo_ratio,
        },
    )

    return row["id"] if row else None
