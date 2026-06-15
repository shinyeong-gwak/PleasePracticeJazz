from fastapi import APIRouter

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