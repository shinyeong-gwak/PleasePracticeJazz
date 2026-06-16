from fastapi import APIRouter, Request

from repositories import lick_repository
from core.render import render_page

router = APIRouter()


@router.get("/licks")
def licks_page(request):
    licks = lick_repository.get_all()

    return render_page(
        request,
        "music/licks.html",
        "Lick 연습",
        {"licks": licks}
    )

@router.post("/music/licks/save")
async def save_lick(request: Request):

    data = await request.json()

    return lick_repository.save(data)

@router.get("/music/licks/metadata")
def get_lick_metadata():

    return lick_repository.get_metadata()