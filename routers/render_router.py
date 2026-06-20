from pathlib import Path

from pydantic import BaseModel

from core.render import *
from fastapi import Request, APIRouter
from fastapi.responses import Response, FileResponse

router = APIRouter()

@router.get("/music/render")
def licks_page(request: Request):

    return render_page(
        request,
        "music/render.html",
        "악보 파일 렌더"
    )

SCORE_DIR = Path("downloads/scores")
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
