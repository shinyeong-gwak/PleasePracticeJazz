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
    rows = query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                id::text AS id,
                file_name AS "fileName",
                file_path AS "filePath",
                COALESCE(NULLIF(source_type, ''), 'local') AS "sourceType",
                COALESCE(source_url, '') AS "sourceUrl",
                duration_sec AS "durationSec"
            FROM audio_track
            ORDER BY file_name
        ) AS t
        """
    )

    for row in rows:
        row["displayName"] = _display_name(row.get("fileName"))
    return rows


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
        "name": item.get("displayName") or _display_name(item.get("fileName")),
        "fileName": item.get("fileName") or "",
        "path": item.get("filePath") or "",
        "sourceType": item.get("sourceType") or "local",
        "sourceUrl": item.get("sourceUrl") or "",
        "durationSec": item.get("durationSec"),
    }


def _build_library_tree(folders, items):
    root = _folder_node("내 라이브러리")
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
    pool = _load_pool_tracks()
    library = _build_library_tree(_load_folders(), _load_library_items())
    return {
        "library": library,
        "pool": pool,
    }


def create_folder(parent_id, name):
    user_id = get_or_create_user_id()
    folder_name = str(name or "").strip()
    parent_id = str(parent_id or "").strip() or None

    if not folder_name:
        raise ValueError("폴더 이름을 입력해주세요.")

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
        raise ValueError("이미 같은 이름의 폴더가 있어요.")

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
        raise ValueError("폴더를 선택해주세요.")

    if not folder_name:
        raise ValueError("새 폴더 이름을 입력해주세요.")

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
        raise ValueError("폴더를 선택해주세요.")

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
        raise ValueError("하위 폴더가 없는 폴더만 삭제할 수 있어요.")

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


def add_track_to_library(track_id, folder_id=None):
    user_id = get_or_create_user_id()
    folder_id = str(folder_id or "").strip() or None
    row = query_one(
        """
        WITH inserted AS (
            INSERT INTO audio_library_item (
                user_id,
                track_id,
                folder_id,
                display_name
            )
            SELECT
                :'user_id'::uuid,
                at.id,
                NULLIF(:'folder_id', '')::uuid,
                regexp_replace(at.file_name, '\\.mp3$', '', 'i')
            FROM audio_track at
            WHERE at.id = :'track_id'::uuid
            ON CONFLICT (user_id, track_id) DO UPDATE SET
                folder_id = EXCLUDED.folder_id,
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
