import json
import re
import shutil
import subprocess
from pathlib import Path


REALBOOK_DIR = Path("downloads/realbook")
CACHE_FILE = Path("data/music/realbook_matches.json")
BOOK_FILE_MAP = {
    "Real Book 1": "Real-Book-1.pdf",
    "Real Book 2": "Real-Book-2.pdf",
    "Real Book 3": "Real-Book-3.pdf",
    "New Real Book 1": "New-Real-Book.pdf",
    "New Real Book 2": "New-Real-Book-2.pdf",
    "New Real Book 3": "New-Real-Book-3.pdf",
}
BOOK_LABEL_MAP = {
    file_name: label
    for label, file_name in BOOK_FILE_MAP.items()
}


def normalize_title(value: str) -> str:
    return re.sub(
        r"[\W_]+",
        "",
        str(value or "").casefold(),
        flags=re.UNICODE
    )


def resolve_book_file_name(book_name: str) -> str:
    value = str(book_name or "").strip()

    if not value:
        return ""

    if value in BOOK_FILE_MAP:
        return BOOK_FILE_MAP[value]

    if value in BOOK_LABEL_MAP:
        return value

    return value


def get_book_label(book_name: str) -> str:
    value = str(book_name or "").strip()

    if not value:
        return ""

    if value in BOOK_FILE_MAP:
        return value

    return BOOK_LABEL_MAP.get(value, value)


def get_pdf_path(book_name: str) -> Path | None:
    file_name = resolve_book_file_name(book_name)

    if not file_name:
        return None

    path = REALBOOK_DIR / file_name
    return path if path.exists() else None


def load_cache():
    if not CACHE_FILE.exists():
        return {}

    try:
        return json.loads(
            CACHE_FILE.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError:
        return {}


def save_cache(cache):
    CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )
    CACHE_FILE.write_text(
        json.dumps(
            cache,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def find_page_by_title(pdf_path: Path, title: str):
    normalized_query = normalize_title(title)

    if not normalized_query:
        return None

    cache = load_cache()
    file_cache = cache.setdefault(pdf_path.name, {})
    cached_page = file_cache.get(normalized_query)

    if isinstance(cached_page, int) and cached_page > 0:
        return cached_page

    if shutil.which("osascript") is None:
        return None

    script = f"""
ObjC.import('Foundation');
ObjC.import('PDFKit');

const path = {json.dumps(str(pdf_path.resolve()))};
const query = {json.dumps(normalized_query)};

function normalize(value) {{
  return String(value || '')
    .toLowerCase()
    .replace(/[\\W_]+/gu, '');
}}

const url = $.NSURL.fileURLWithPath(path);
const doc = $.PDFDocument.alloc.initWithURL(url);

if (!doc) {{
  console.log(JSON.stringify({{ page: 0 }}));
}} else {{
  let pageNumber = 0;

  for (let index = 0; index < doc.pageCount; index += 1) {{
    const page = doc.pageAtIndex(index);
    const raw = page ? page.string : null;
    const text = raw ? ObjC.unwrap(raw) : '';

    if (normalize(text).includes(query)) {{
      pageNumber = index + 1;
      break;
    }}
  }}

  console.log(JSON.stringify({{ page: pageNumber }}));
}}
"""

    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript"],
            input=script,
            text=True,
            capture_output=True,
            check=False
        )
    except FileNotFoundError:
        return None

    output_lines = [
        line.strip()
        for line in (result.stdout + "\n" + result.stderr).splitlines()
        if line.strip().startswith("{")
    ]

    if not output_lines:
        return None

    try:
        payload = json.loads(output_lines[-1])
    except json.JSONDecodeError:
        return None

    page = int(payload.get("page") or 0)

    if page > 0:
        file_cache[normalized_query] = page
        save_cache(cache)
        return page

    return None


def resolve_realbook_page(book: str, title: str = "", page: str = ""):
    pdf_path = get_pdf_path(book)

    if pdf_path is None:
        return {
            "success": False,
            "message": "선택한 악보집 PDF를 찾을 수 없습니다."
        }

    resolved_page = find_page_by_title(
        pdf_path,
        title
    )

    if resolved_page is None:
        try:
            fallback_page = int(str(page or "").strip())
        except ValueError:
            fallback_page = 0

        if fallback_page > 0:
            resolved_page = fallback_page

    if resolved_page is None or resolved_page <= 0:
        return {
            "success": False,
            "message": "곡 제목이나 페이지 번호로 악보를 찾지 못했습니다."
        }

    return {
        "success": True,
        "fileName": pdf_path.name,
        "page": resolved_page,
        "book": get_book_label(book),
        "title": str(title or "").strip()
    }
