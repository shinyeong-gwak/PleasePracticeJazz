import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote_plus

from repositories.db import query_one


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
GENERIC_BOOK_VALUES = {
    "",
    "리얼북",
    "realbook",
    "real book",
}


def normalize_title(value: str) -> str:
    decoded = unquote_plus(str(value or ""))
    return re.sub(
        r"[\W_]+",
        "",
        decoded.casefold(),
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


def is_generic_book_name(book_name: str) -> bool:
    return str(book_name or "").strip().lower() in GENERIC_BOOK_VALUES


def get_searchable_books(book_name: str):
    if not is_generic_book_name(book_name):
        pdf_path = get_pdf_path(book_name)
        if pdf_path is None:
            return []
        return [
            {
                "label": get_book_label(book_name),
                "fileName": pdf_path.name,
                "path": pdf_path,
            }
        ]

    books = []
    seen = set()

    for label, file_name in BOOK_FILE_MAP.items():
        pdf_path = REALBOOK_DIR / file_name
        if not pdf_path.exists():
            continue
        books.append(
            {
                "label": label,
                "fileName": file_name,
                "path": pdf_path,
            }
        )
        seen.add(file_name)

    for pdf_path in sorted(REALBOOK_DIR.glob("*.pdf")):
        if pdf_path.name in seen:
            continue
        books.append(
            {
                "label": BOOK_LABEL_MAP.get(pdf_path.name, pdf_path.stem),
                "fileName": pdf_path.name,
                "path": pdf_path,
            }
        )

    return books


def find_page_by_title_in_db(book_name: str, title: str):
    query_text = unquote_plus(str(title or "")).strip()
    normalized_query = normalize_title(query_text)
    search_all_books = is_generic_book_name(book_name)
    book_label = get_book_label(book_name)
    file_name = resolve_book_file_name(book_name)

    if not normalized_query:
        return None

    if not search_all_books and not book_label:
        return None

    book_filter_sql = ""
    if not search_all_books:
        book_filter_sql = """
            WHERE sb.title = :'book_title'
               OR split_part(
                    sb.pdf_path,
                    '/',
                    array_length(string_to_array(sb.pdf_path, '/'), 1)
                  ) = :'file_name'
        """

    row = query_one(
        f"""
        WITH candidate_book AS (
            SELECT
                sb.id,
                sb.title AS book_title,
                split_part(
                    sb.pdf_path,
                    '/',
                    array_length(string_to_array(sb.pdf_path, '/'), 1)
                ) AS file_name
            FROM music.sheet_book sb
            {book_filter_sql}
        ),
        candidate_song AS (
            SELECT
                s.id,
                s.title,
                s.normalized_title,
                CASE
                    WHEN s.normalized_title = :'normalized_title' THEN 4
                    WHEN s.normalized_title LIKE :'normalized_prefix' THEN 3
                    WHEN s.normalized_title LIKE :'normalized_contains' THEN 2
                    WHEN similarity(s.normalized_title, :'normalized_title') >= 0.45 THEN 1
                    ELSE 0
                END AS match_rank,
                similarity(s.normalized_title, :'normalized_title') AS title_similarity
            FROM music.song s
            WHERE s.normalized_title = :'normalized_title'
               OR s.normalized_title LIKE :'normalized_prefix'
               OR s.normalized_title LIKE :'normalized_contains'
               OR similarity(s.normalized_title, :'normalized_title') >= 0.45
        ),
        ranked_match AS (
            SELECT
                sbs.page,
                cb.book_title,
                cb.file_name,
                cs.title,
                cs.normalized_title,
                sbs.bookmark_title,
                CASE
                    WHEN cs.match_rank >= 2 THEN cs.match_rank * 10
                    ELSE 0
                END
                + (cs.title_similarity * 100)
                + (
                    similarity(
                        regexp_replace(
                            lower(coalesce(sbs.bookmark_title, '')),
                            '[^[:alnum:]]+',
                            '',
                            'g'
                        ),
                        :'normalized_title'
                    ) * 40
                ) AS score,
                cs.match_rank,
                cs.title_similarity,
                similarity(
                    regexp_replace(
                        lower(coalesce(sbs.bookmark_title, '')),
                        '[^[:alnum:]]+',
                        '',
                        'g'
                    ),
                    :'normalized_title'
                ) AS bookmark_similarity
            FROM candidate_book cb
            JOIN music.sheet_book_song sbs
              ON sbs.sheet_book_id = cb.id
            JOIN candidate_song cs
              ON cs.id = sbs.song_id
            WHERE cs.match_rank > 0
               OR similarity(
                    regexp_replace(
                        lower(coalesce(sbs.bookmark_title, '')),
                        '[^[:alnum:]]+',
                        '',
                        'g'
                    ),
                    :'normalized_title'
                ) >= 0.5
            ORDER BY
                score DESC,
                cs.match_rank DESC,
                cs.title_similarity DESC,
                bookmark_similarity DESC,
                CASE
                    WHEN cb.book_title = :'book_title' THEN 0
                    ELSE 1
                END,
                length(cs.normalized_title) ASC,
                sbs.page ASC
            LIMIT 1
        )
        SELECT row_to_json(t)
        FROM (
            SELECT
                page,
                book_title AS "bookTitle",
                file_name AS "fileName",
                title,
                normalized_title,
                bookmark_title,
                score,
                match_rank,
                title_similarity,
                bookmark_similarity
            FROM ranked_match
            WHERE score >= 35
        ) AS t
        """,
        {
            "book_title": book_label,
            "file_name": file_name,
            "normalized_title": normalized_query,
            "normalized_prefix": f"{normalized_query}%",
            "normalized_contains": f"%{normalized_query}%",
        },
    )

    if not row:
        return None

    try:
        page = int(row.get("page") or 0)
    except (TypeError, ValueError):
        return None

    if page <= 0:
        return None

    return {
        "page": page,
        "fileName": str(row.get("fileName") or "").strip(),
        "book": str(row.get("bookTitle") or "").strip(),
        "title": str(row.get("title") or "").strip(),
    }


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
    query_text = unquote_plus(str(title or "")).strip()
    normalized_query = normalize_title(query_text)

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
const queryRaw = {json.dumps(query_text)};

function normalize(value) {{
  return String(value || '')
    .toLowerCase()
    .replace(/\\+/g, ' ')
    .replace(/&/g, ' and ')
    .replace(/\\bst[.]?\\b/gu, ' street ')
    .replace(/\\bmt[.]?\\b/gu, ' mount ')
    .replace(/\\bft[.]?\\b/gu, ' fort ')
    .replace(/[’']/gu, '')
    .replace(/[^\\p{{L}}\\p{{N}}]+/gu, ' ')
    .trim()
    .replace(/\\s+/g, ' ');
}}

function compact(value) {{
  return normalize(value).replace(/\\s+/g, '');
}}

function scorePage(text, query) {{
  const normalizedText = normalize(text);
  const compactText = normalizedText.replace(/\\s+/g, '');
  const normalizedQuery = normalize(query);
  const compactQuery = compact(query);

  if (!normalizedQuery || !compactQuery) {{
    return {{ score: 0, exact: false }};
  }}

  if (compactText.includes(compactQuery)) {{
    return {{ score: 10, exact: true }};
  }}

  const stopwords = new Set(['a', 'an', 'and', 'of', 'the', 'on', 'in']);
  const queryTokens = normalizedQuery
    .split(' ')
    .filter(Boolean);
  const textTokens = normalizedText
    .split(' ')
    .filter(Boolean);
  const filteredQueryTokens = queryTokens.filter(
    token => token.length > 1 && !stopwords.has(token)
  );

  if (!filteredQueryTokens.length) {{
    return {{ score: 0, exact: false }};
  }}

  let matched = 0;
  let orderedIndex = -1;
  let orderedMatches = 0;

  for (const token of filteredQueryTokens) {{
    const foundIndex = textTokens.findIndex(
      candidate =>
        candidate === token ||
        candidate.startsWith(token) ||
        token.startsWith(candidate)
    );

    if (foundIndex >= 0) {{
      matched += 1;

      const nextOrderedIndex = textTokens.findIndex(
        (candidate, index) =>
          index > orderedIndex &&
          (
            candidate === token ||
            candidate.startsWith(token) ||
            token.startsWith(candidate)
          )
      );

      if (nextOrderedIndex >= 0) {{
        orderedIndex = nextOrderedIndex;
        orderedMatches += 1;
      }}
    }}
  }}

  const overlapRatio = matched / filteredQueryTokens.length;
  const orderedRatio = orderedMatches / filteredQueryTokens.length;
  const phraseBonus = filteredQueryTokens.length >= 2 &&
    compactText.includes(filteredQueryTokens.join('')) ? 0.25 : 0;
  const score = overlapRatio + (orderedRatio * 0.35) + phraseBonus;

  return {{
    score,
    exact: false
  }};
}}

const url = $.NSURL.fileURLWithPath(path);
const doc = $.PDFDocument.alloc.initWithURL(url);

if (!doc) {{
  console.log(JSON.stringify({{ page: 0 }}));
}} else {{
  let pageNumber = 0;
  let bestPage = 0;
  let bestScore = 0;

  for (let index = 0; index < doc.pageCount; index += 1) {{
    const page = doc.pageAtIndex(index);
    const raw = page ? page.string : null;
    const text = raw ? ObjC.unwrap(raw) : '';

    const result = scorePage(text, queryRaw);

    if (result.exact) {{
      pageNumber = index + 1;
      break;
    }}

    if (result.score > bestScore) {{
      bestScore = result.score;
      bestPage = index + 1;
    }}
  }}

  if (!pageNumber && bestScore >= 0.72) {{
    pageNumber = bestPage;
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
    search_books = get_searchable_books(book)

    if not search_books:
        return {
            "success": False,
            "message": "선택한 악보집 PDF를 찾을 수 없습니다."
        }

    matched = find_page_by_title_in_db(book, title)
    selected_book = None

    if matched:
        selected_book = next(
            (
                candidate
                for candidate in search_books
                if candidate["fileName"] == matched.get("fileName")
            ),
            None,
        )
        if selected_book is None and matched.get("fileName"):
            pdf_path = REALBOOK_DIR / matched["fileName"]
            if pdf_path.exists():
                selected_book = {
                    "label": matched.get("book") or get_book_label(matched["fileName"]),
                    "fileName": matched["fileName"],
                    "path": pdf_path,
                }

    if matched is None:
        for candidate in search_books:
            resolved_page = find_page_by_title(
                candidate["path"],
                title
            )
            if resolved_page:
                matched = {
                    "page": resolved_page,
                    "fileName": candidate["fileName"],
                    "book": candidate["label"],
                    "title": str(title or "").strip(),
                }
                selected_book = candidate
                break

    if matched is None:
        try:
            fallback_page = int(str(page or "").strip())
        except ValueError:
            fallback_page = 0

        if fallback_page > 0:
            selected_book = search_books[0]
            matched = {
                "page": fallback_page,
                "fileName": selected_book["fileName"],
                "book": selected_book["label"],
                "title": str(title or "").strip(),
            }

    if matched is None or int(matched.get("page") or 0) <= 0:
        return {
            "success": False,
            "message": "곡 제목이나 페이지 번호로 악보를 찾지 못했습니다."
        }

    return {
        "success": True,
        "fileName": matched["fileName"],
        "page": int(matched["page"]),
        "book": matched.get("book") or (selected_book["label"] if selected_book else get_book_label(book)),
        "title": matched.get("title") or str(title or "").strip(),
    }
