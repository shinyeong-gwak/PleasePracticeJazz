from pathlib import Path

from repositories.db import execute, get_or_create_user_id, query_one, query_rows


ROOT_DIR = Path(__file__).resolve().parent.parent
MP3_DIR = ROOT_DIR / "downloads" / "mp3"
MP3_METADATA_PLAYLIST_NAME = "__mp3_files__"
MP3_METADATA_PLAYLIST_URL = "internal://mp3"


def _safe_relative_path(value):
    text = str(value or "").strip().replace("\\", "/")
    relative = Path(text)

    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Invalid path")

    return relative


def resolve_mp3_path(value):
    base = MP3_DIR.resolve()
    path = (MP3_DIR / _safe_relative_path(value)).resolve()

    if path != base and base not in path.parents:
        raise ValueError("Invalid path")

    return path


def _relative_key(path):
    return path.relative_to(MP3_DIR).as_posix()


def _storage_path(relative_path):
    return f"downloads/mp3/{relative_path}"


def _normalize_item_path(row):
    file_path = str(row.get("filePath") or row.get("file_path") or "").replace("\\", "/")
    file_name = str(row.get("fileName") or row.get("file_name") or "").replace("\\", "/")

    if file_path.startswith("downloads/mp3/"):
        return file_path[len("downloads/mp3/"):]

    if file_path.startswith(str(MP3_DIR).replace("\\", "/")):
        return Path(file_path).relative_to(MP3_DIR).as_posix()

    if "/" in file_path and file_path.lower().endswith(".mp3"):
        return file_path

    return file_name or file_path


def _ensure_mp3_metadata_playlist():
    user_id = get_or_create_user_id()
    playlist = query_one(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT id::text AS id
            FROM playlist
            WHERE user_id = :'user_id'::uuid
              AND name = :'name'
            LIMIT 1
        ) AS t
        """,
        {
            "user_id": user_id,
            "name": MP3_METADATA_PLAYLIST_NAME,
        },
    )

    if playlist:
        return playlist["id"]

    created = query_one(
        """
        WITH inserted AS (
            INSERT INTO playlist (user_id, name, source_url)
            VALUES (
                :'user_id'::uuid,
                :'name',
                :'url'
            )
            RETURNING id::text AS id
        )
        SELECT row_to_json(inserted)
        FROM inserted
        """,
        {
            "user_id": user_id,
            "name": MP3_METADATA_PLAYLIST_NAME,
            "url": MP3_METADATA_PLAYLIST_URL,
        },
    )

    return created["id"] if created else None


def _load_db_mp3_rows():
    user_id = get_or_create_user_id()
    return query_rows(
        """
        SELECT row_to_json(t)
        FROM (
            SELECT
                pi.id::text AS id,
                pi.file_name AS "fileName",
                pi.file_path AS "filePath",
                pi.source_url AS "sourceUrl",
                COALESCE(pi.title, pi.file_name) AS title,
                p.name AS "playlistName"
            FROM playlist p
            JOIN playlist_item pi ON pi.playlist_id = p.id
            WHERE p.user_id = :'user_id'::uuid
              AND (
                pi.file_path LIKE 'downloads/mp3/%'
                OR pi.file_path NOT LIKE 'downloads/%'
              )
            ORDER BY COALESCE(pi.title, pi.file_name), pi.created_at
        ) AS t
        """,
        {"user_id": user_id},
    )


def sync_mp3_filesystem_items():
    MP3_DIR.mkdir(parents=True, exist_ok=True)
    playlist_id = _ensure_mp3_metadata_playlist()
    existing_paths = {
        _normalize_item_path(row)
        for row in _load_db_mp3_rows()
    }

    for file in MP3_DIR.rglob("*.mp3"):
        relative_path = _relative_key(file)
        if relative_path in existing_paths:
            continue

        execute(
            """
            INSERT INTO playlist_item (
                playlist_id,
                file_name,
                file_path,
                source_url,
                title,
                downloaded_at
            )
            VALUES (
                :'playlist_id'::uuid,
                :'file_name',
                :'file_path',
                :'source_url',
                :'title',
                now()
            )
            """,
            {
                "playlist_id": playlist_id,
                "file_name": file.name,
                "file_path": _storage_path(relative_path),
                "source_url": f"{MP3_METADATA_PLAYLIST_URL}/{relative_path}",
                "title": file.name,
            },
        )

    return _load_db_mp3_rows()


def _folder_node(name, path):
    return {
        "type": "folder",
        "name": name,
        "path": path,
        "children": [],
    }


def _get_or_create_child_folder(parent, name, path):
    for child in parent["children"]:
        if child["type"] == "folder" and child["path"] == path:
            return child

    child = _folder_node(name, path)
    parent["children"].append(child)
    return child


def _add_folder_path(root, relative_path):
    text = str(relative_path or "").strip().replace("\\", "/")
    if not text:
        return

    current = root
    accumulated = []
    for part in Path(text).parts:
        accumulated.append(part)
        current = _get_or_create_child_folder(
            current,
            part,
            Path(*accumulated).as_posix(),
        )


def _add_file_path(root, relative_path, row=None):
    text = str(relative_path or "").strip().replace("\\", "/")
    if not text:
        return

    parts = Path(text).parts
    current = root
    accumulated = []

    for part in parts[:-1]:
        accumulated.append(part)
        current = _get_or_create_child_folder(
            current,
            part,
            Path(*accumulated).as_posix(),
        )

    current["children"].append(
        {
            "type": "file",
            "name": row.get("title") or parts[-1] if row else parts[-1],
            "fileName": parts[-1],
            "path": text,
            "playlistItemId": row.get("id") if row else "",
            "sourceUrl": row.get("sourceUrl") if row else "",
            "playlistName": row.get("playlistName") if row else "",
        }
    )


def get_mp3_files():
    rows = sync_mp3_filesystem_items()
    return sorted([
        path
        for path in (_normalize_item_path(row) for row in rows)
        if path.lower().endswith(".mp3")
    ])


def get_mp3_tree():
    MP3_DIR.mkdir(parents=True, exist_ok=True)
    rows = sync_mp3_filesystem_items()
    tree = _folder_node("MP3", "")

    for folder in MP3_DIR.rglob("*"):
        if folder.is_dir():
            _add_folder_path(tree, _relative_key(folder))

    seen = set()
    for row in rows:
        relative_path = _normalize_item_path(row)
        if not relative_path.lower().endswith(".mp3") or relative_path in seen:
            continue
        seen.add(relative_path)
        _add_file_path(tree, relative_path, row)

    return tree


def create_folder(parent_path, name):
    folder_name = str(name or "").strip().replace("\\", "").replace("/", "")
    if not folder_name:
        raise ValueError("폴더 이름을 입력해주세요.")

    parent = resolve_mp3_path(parent_path or "")
    if not parent.exists() or not parent.is_dir():
        raise ValueError("상위 폴더를 찾을 수 없어요.")

    target = parent / folder_name
    if target.exists():
        raise ValueError("이미 같은 이름의 폴더가 있어요.")

    target.mkdir(exist_ok=False)
    return get_mp3_tree()


def rename_folder(path, name):
    folder = resolve_mp3_path(path)
    folder_name = str(name or "").strip().replace("\\", "").replace("/", "")
    old_relative = _relative_key(folder)

    if folder == MP3_DIR.resolve():
        raise ValueError("기본 폴더 이름은 바꿀 수 없어요.")

    if not folder.exists() or not folder.is_dir():
        raise ValueError("폴더를 찾을 수 없어요.")

    if not folder_name:
        raise ValueError("새 폴더 이름을 입력해주세요.")

    target = folder.parent / folder_name
    if target.exists():
        raise ValueError("이미 같은 이름의 폴더가 있어요.")

    folder.rename(target)
    new_relative = _relative_key(target)
    user_id = get_or_create_user_id()
    execute(
        """
        UPDATE playlist_item pi
        SET file_path =
            :'new_prefix' || substring(pi.file_path from char_length(:'old_prefix') + 1)
        FROM playlist p
        WHERE p.id = pi.playlist_id
          AND p.user_id = :'user_id'::uuid
          AND pi.file_path LIKE :'old_like'
        """,
        {
            "user_id": user_id,
            "old_prefix": _storage_path(old_relative),
            "new_prefix": _storage_path(new_relative),
            "old_like": f"{_storage_path(old_relative)}/%",
        },
    )
    return get_mp3_tree()


def delete_folder(path):
    folder = resolve_mp3_path(path)

    if folder == MP3_DIR.resolve():
        raise ValueError("기본 폴더는 삭제할 수 없어요.")

    if not folder.exists() or not folder.is_dir():
        raise ValueError("폴더를 찾을 수 없어요.")

    if any(folder.iterdir()):
        raise ValueError("비어 있는 폴더만 삭제할 수 있어요.")

    folder.rmdir()
    return get_mp3_tree()
