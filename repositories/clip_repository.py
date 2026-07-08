from pathlib import Path

MP3_DIR = Path("downloads/mp3")


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


def get_mp3_files():

    if not MP3_DIR.exists():
        return []

    return sorted([
        _relative_key(file)
        for file in MP3_DIR.rglob("*.mp3")
    ])


def _build_node(path):
    if path.is_dir():
        children = [
            _build_node(child)
            for child in path.iterdir()
            if child.is_dir() or child.suffix.lower() == ".mp3"
        ]
        children.sort(key=lambda node: (node["type"] != "folder", node["name"].lower()))
        return {
            "type": "folder",
            "name": path.name,
            "path": "" if path == MP3_DIR else _relative_key(path),
            "children": children,
        }

    return {
        "type": "file",
        "name": path.name,
        "path": _relative_key(path),
    }


def get_mp3_tree():
    MP3_DIR.mkdir(parents=True, exist_ok=True)
    tree = _build_node(MP3_DIR)
    tree["name"] = "MP3"
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
