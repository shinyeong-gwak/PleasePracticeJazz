import json
from pathlib import Path
from urllib.parse import urlencode
from shutil import which

from core.render import render_page
from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pdf2image import convert_from_path

from repositories import realbook_repository


router = APIRouter()
SCORE_DIR = Path("downloads/scores")
REALBOOK_DIR = Path("downloads/realbook")
REALBOOK_PAGE_CACHE_DIR = Path("data/music/realbook_pages")
POPLLER_CANDIDATE_DIRS = [
    Path("/Users/shinyeonggwak/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin"),
    Path("lib/poppler/bin"),
    Path("/opt/homebrew/bin"),
    Path("/usr/local/bin"),
]


@router.get("/music/render")
def licks_page(request: Request):

    return render_page(
        request,
        "music/render.html",
        "악보 파일 렌더"
    )


@router.get("/score-list")
async def score_list():
    files = sorted(SCORE_DIR.glob("*.musicxml"))
    return [f.name for f in files]


@router.get("/score-source/{filename}")
async def score_source(filename: str):
    safe_name = Path(filename).name
    file_path = SCORE_DIR / safe_name

    return Response(
        content=file_path.read_text(encoding="utf-8"),
        media_type="application/vnd.recordare.musicxml+xml"
    )


@router.get("/score-download/{filename}")
async def score_download(filename: str):
    safe_name = Path(filename).name
    file_path = SCORE_DIR / safe_name

    return FileResponse(
        file_path,
        media_type="application/vnd.recordare.musicxml+xml",
        filename=safe_name
    )


@router.get("/music/realbook/resolve")
async def resolve_realbook(
        book: str = Query(default=""),
        title: str = Query(default=""),
        page: str = Query(default="")):

    result = realbook_repository.resolve_realbook_page(
        book=book,
        title=title,
        page=page
    )

    if not result.get("success"):
        return JSONResponse(
            result,
            status_code=404
        )

    file_name = result["fileName"]
    page_number = result["page"]
    query = urlencode({
        "file": file_name,
        "page": page_number,
        "title": result.get("title", ""),
        "book": result.get("book", "")
    })

    result["fileUrl"] = f"/music/realbook/file/{file_name}"
    result["viewUrl"] = f"/music/realbook/view?{query}"

    return JSONResponse(result)


@router.get("/music/realbook/file/{filename}")
async def realbook_file(filename: str):
    safe_name = Path(filename).name
    file_path = REALBOOK_DIR / safe_name

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=safe_name,
        content_disposition_type="inline",
    )


def _find_poppler_path() -> str | None:
    for candidate in POPPLER_CANDIDATE_DIRS:
        if (candidate / "pdfinfo").exists() and (candidate / "pdftoppm").exists():
            return str(candidate)

    if which("pdfinfo") and which("pdftoppm"):
        return None

    return None


def _json_utf8_response(message: str, status_code: int) -> Response:
    return Response(
        content=json.dumps({"message": message}, ensure_ascii=False),
        status_code=status_code,
        media_type="application/json; charset=utf-8",
    )


def _realbook_page_cache_path(file_name: str, page: int) -> Path:
    return REALBOOK_PAGE_CACHE_DIR / Path(file_name).stem / f"page-{page}.png"


def _render_realbook_page_png(file_name: str, page: int) -> Path:
    safe_name = Path(file_name).name
    pdf_path = REALBOOK_DIR / safe_name

    if not pdf_path.exists():
        raise FileNotFoundError(safe_name)

    page_number = max(1, page)
    cache_path = _realbook_page_cache_path(safe_name, page_number)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    source_mtime = pdf_path.stat().st_mtime
    if cache_path.exists() and cache_path.stat().st_mtime >= source_mtime:
        return cache_path

    images = convert_from_path(
        str(pdf_path),
        first_page=page_number,
        last_page=page_number,
        fmt="png",
        dpi=180,
        thread_count=1,
        single_file=True,
        poppler_path=_find_poppler_path(),
    )

    if not images:
        raise RuntimeError("Failed to render PDF page")

    images[0].save(cache_path, format="PNG")
    return cache_path


@router.get("/music/realbook/page/{filename}")
async def realbook_page(filename: str, page: int = Query(default=1)):
    safe_name = Path(filename).name

    try:
        cache_path = _render_realbook_page_png(safe_name, page)
    except FileNotFoundError:
        return _json_utf8_response("PDF 파일을 찾을 수 없습니다.", 404)
    except Exception as exc:
        return _json_utf8_response(
            f"PDF 페이지를 이미지로 변환하지 못했습니다: {exc}",
            500,
        )

    return FileResponse(
        cache_path,
        media_type="image/png",
        filename=cache_path.name,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/music/realbook/view")
def realbook_view(
        request: Request,
        file: str = Query(default=""),
        page: int = Query(default=1),
        title: str = Query(default=""),
        book: str = Query(default="")):

    safe_name = Path(file).name
    page_number = max(1, page)

    return render_page(
        request,
        "music/realbook_viewer.html",
        "Real Book PDF",
        {
            "pdf_file_name": safe_name,
            "pdf_page": page_number,
            "pdf_title": title,
            "pdf_book": book,
            "pdf_file_url": f"/music/realbook/file/{safe_name}",
            "pdf_direct_url": f"/music/realbook/file/{safe_name}#page={page_number}&view=FitH",
            "pdf_image_url": f"/music/realbook/page/{safe_name}?page={page_number}",
        }
    )
