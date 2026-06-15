from pydantic import BaseModel
from services import musicxml_service
from core.render import *
from fastapi import Request

class XMLRequest(BaseModel):
    xml: str


from fastapi.responses import Response

@app.post("/render")
async def render(req: XMLRequest):
    svg = musicxml_service.render_musicxml_to_svg(req.xml)
    return Response(content=svg, media_type="image/svg+xml")

@app.get("/music/render")
def licks_page(request: Request):

    return render_page(
        request,
        "music/render.html",
        "악보 파일 렌더"
    )