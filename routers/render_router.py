from pathlib import Path
from urllib.parse import urlencode

from core.render import render_page
from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from repositories import realbook_repository


router = APIRouter()
SCORE_DIR = Path("downloads/scores")
REALBOOK_DIR = Path("downloads/realbook")


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


@router.get("/music/realbook/view")
def realbook_view(
        request: Request,
        file: str = Query(default=""),
        page: int = Query(default=1),
        title: str = Query(default=""),
        book: str = Query(default="")):

    safe_name = Path(file).name

    return render_page(
        request,
        "music/realbook_viewer.html",
        "Real Book PDF",
        {
            "pdf_file_name": safe_name,
            "pdf_page": max(1, page),
            "pdf_title": title,
            "pdf_book": book,
            "pdf_file_url": f"/music/realbook/file/{safe_name}",
            "pdf_embed_url": f"/music/realbook/file/{safe_name}#page={max(1, page)}&view=FitH",
        }
    )
