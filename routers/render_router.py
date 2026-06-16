from pathlib import Path

from pydantic import BaseModel

from services import musicxml_service
from core.render import *
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse

class XMLRequest(BaseModel):
    xml: str


from fastapi.responses import Response

router = APIRouter()
class RenderRequest(BaseModel):
    filename: str


@router.post("/render")
async def render(req: RenderRequest):
    filename = Path(req.filename).name   # ../ 방지

    xml = (SCORE_DIR / filename).read_text(encoding="utf-8")

    svg = musicxml_service.render_musicxml_to_svg(xml)

    return Response(
        content=svg,
        media_type="image/svg+xml"
    )

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